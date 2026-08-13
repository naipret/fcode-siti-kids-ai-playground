"""Trò 2 — Tìm Nắng Cùng AI: MASTER (FastAPI + WebSocket + Vision + TTS).

Kiến trúc: 1 máy master (màn LED + loa sân khấu) + 3 trạm (tab browser trên laptop mỗi đội).
- Trạm: webcam getUserMedia + nút "NHẬN DIỆN" → grab frame base64 → WS master.
- Master: vision GPT-4o-mini (OpenRouter) chấm đúng/sai + Kokoro TTS công bố + bảng điểm
  thời gian thực + luồng 6 vòng (điểm 3-2-1 theo thứ tự về đích).

Chạy:  python app/timnang_master.py   (port 8001 — tách khỏi Trò 1 :8000)
Stations mở:  http://<master-ip>:8001/station/A   /B   /C
Scoreboard:   http://localhost:8001/
"""
import os
import sys
import json
import time
import uuid
import asyncio
import logging
import tempfile

# Load .env (nếu có python-dotenv) — đảm bảo đọc OPENROUTER_API_KEY, KOON_VOICE,...
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timnang_data as D
from timnang_data import (OBJECTS, TEAMS, ROUNDS, RECOGNIZE_DEBOUNCE,
                          SCORE_BY_ORDER, ORDER_WORD, AUDIO_DIR, num_vi)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
import soundfile as sf

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("timnang")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(APP_DIR, "static")
TTS_DIR = tempfile.mkdtemp(prefix="timnang_tts_")

# ---------- OpenRouter (vision + text) ----------
OR_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()
OR_BASE = "https://openrouter.ai/api/v1"
OR_MODEL = os.environ.get("OR_MODEL", "openai/gpt-4o-mini")
llm = OpenAI(base_url=OR_BASE, api_key=OR_KEY, timeout=5.0) if OR_KEY else None
log.info("Vision/LLM: %s", ("OpenRouter " + OR_MODEL) if llm else "TẮT — operator duyệt tay")

# ---------- Kokoro TTS (đồng bộ init như server.py) ----------
_tts = None
try:
    from kokoro_vietnamese import KokoroVietnamese as KokoroTTS
    _TTS_OK = True
except ImportError:
    _TTS_OK = False
    log.warning("kokoro-vietnamese chưa cài — chạy pip install -e ref/Kokoro-Vietnamese[onnx]")


def get_tts():
    global _tts
    if not _TTS_OK:
        return None
    if _tts is None:
        voice = os.environ.get("KOON_VOICE", "mai_linh")
        _tts = KokoroTTS(device="cpu", voice=voice)
        log.info("Kokoro TTS sẵn sàng (giọng %s)", voice)
    return _tts


# Khởi tạo TTS ngay từ đầu (giống server.py Trò 1): load model một lần lúc boot,
# tránh lazy-init block event-loop ở lần say() đầu tiên (gây kẹt flow end_round).
_ = get_tts()


# ---------- Vision judge ----------
def _judge_vision_sync(image_b64: str, obj: dict):
    """Trả True/False/None (None = lỗi/thiếu key)."""
    if not llm:
        return None
    data_url = image_b64 if image_b64.startswith("data:") else f"data:image/jpeg;base64,{image_b64}"
    prompt = (f"Trong bức ảnh này có {obj['vision_prompt']} không? "
              f"Chấp nhận góc nhìn khác nhau, một phần vật cũng OK. "
              f'Chỉ trả JSON hợp lệ: {{"correct": true}} hoặc {{"correct": false}}.')
    try:
        r = llm.chat.completions.create(
            model=OR_MODEL,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ]}],
            temperature=0,
        )
        data = json.loads(r.choices[0].message.content.strip())
        return bool(data.get("correct"))
    except Exception as e:
        log.warning("Vision lỗi (%s)", e)
        return None


async def judge_vision(image_b64: str, obj: dict):
    return await asyncio.to_thread(_judge_vision_sync, image_b64, obj)


# ---------- Game state ----------


class Game:
    def __init__(self):
        self.phase = "idle"          # idle | announce | playing | round_end | game_over
        self.round_idx = -1
        self.object = None
        self.teams = {
            t["id"]: {"name": t["name"], "color": t["color"], "score": 0, "order": None, "last_rec": 0.0}
            for t in TEAMS
        }
        self.stations: dict[str, WebSocket] = {}   # team_id -> ws
        self.masters: set[WebSocket] = set()
        self.lock = asyncio.Lock()
        # Chờ master phát xong audio (audio_ended) — dùng cho intro để không bị
        # thông báo vòng 1 đè lên. Event set = không có gì đang chờ.
        self._audio_done = asyncio.Event()
        self._audio_done.set()
        self._tasks: set[asyncio.Task] = set()  # giữ ref task nền (start_game)

    # ---- audio wait helpers ----
    def interrupt_audio(self):
        """Giải phóng điểm chờ audio để op của operator được xử lý ngay."""
        self._audio_done.set()

    async def _wait_audio(self, timeout: float = 60.0):
        """Chờ master báo audio_ended (phát xong). Không có master → bỏ qua;
        timeout → đi tiếp (không treo flow vĩnh viễn)."""
        if not self.masters:
            return
        try:
            await asyncio.wait_for(self._audio_done.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            log.warning("[audio] không có audio_ended sau %.0fs — đi tiếp", timeout)

    def _spawn(self, coro):
        """Chạy coroutine nền (vd start_game) mà không block vòng nhận WS của master."""
        t = asyncio.create_task(coro)
        self._tasks.add(t)
        t.add_done_callback(self._tasks.discard)
        return t

    # ---- broadcast helpers ----
    async def _send(self, ws, msg):
        try:
            await ws.send_text(json.dumps(msg, ensure_ascii=False))
        except Exception:
            pass

    async def broadcast_masters(self, msg):
        for ws in list(self.masters):
            await self._send(ws, msg)

    async def broadcast_stations(self, msg):
        for ws in list(self.stations.values()):
            await self._send(ws, msg)

    async def broadcast_all(self, msg):
        await self.broadcast_masters(msg)
        await self.broadcast_stations(msg)

    def scoreboard_msg(self):
        return {
            "type": "scoreboard",
            "phase": self.phase,
            "round": self.round_idx + 1 if self.round_idx >= 0 else 0,
            "rounds": ROUNDS,
            "object": self.object["name"] if self.object else None,
            "object_vi": self.object["vi"] if self.object else None,
            "teams": [
                {"id": tid, "name": t["name"], "color": t["color"],
                 "score": t["score"], "order": t["order"]}
                for tid, t in self.teams.items()
            ],
        }

    async def sync_scoreboard(self):
        await self.broadcast_all(self.scoreboard_msg())

    # ---- TTS (chỉ phát ở master = loa sân khấu) ----
    async def say(self, text: str, wait: bool = False) -> bool:
        """Synthesize Kokoro động + phát ở master. Không bao giờ raise/block caller
        (bọc try/except + timeout) — để flow game (vd end_round) không bị kẹt khi TTS lỗi/chậm.
        wait=True → chờ master phát xong (audio_ended) trước khi đi tiếp (dùng cho intro).
        Trả True nếu đã broadcast audio."""
        tts = get_tts()
        if not tts:
            log.info("[TTS skip] %s", text[:60])
            if wait:
                delay = max(1.5, min(8.0, len(text) * 0.07))
                await asyncio.sleep(delay)
            return False
        try:
            audio, _ = await asyncio.wait_for(asyncio.to_thread(tts.synthesize, text), timeout=15)
            key = f"tts_{uuid.uuid4().hex}"
            wav_path = os.path.join(TTS_DIR, f"{key}.wav")
            sf.write(wav_path, audio, 24000)
            if wait:
                self._audio_done.clear()
            await self.broadcast_masters({"type": "play_audio", "key": key})
            if wait:
                await self._wait_audio()
            # Dọn file temp trong background sau 60s
            asyncio.create_task(self._cleanup_temp_file(wav_path, 60.0))
            return True
        except asyncio.TimeoutError:
            log.warning("[TTS timeout] synthesize quá 15s, bỏ qua: %s", text[:60])
        except Exception as e:
            log.warning("[TTS lỗi] %s — bỏ qua: %s", e, text[:60])
        return False

    async def _cleanup_temp_file(self, path: str, delay: float = 60.0):
        await asyncio.sleep(delay)
        try:
            if os.path.isfile(path):
                os.unlink(path)
        except Exception:
            pass

    async def play_or_say(self, key: str, text: str, wait: bool = False):
        """Phát pre-cache .wav/.mp3 (tức thì <200ms) nếu có; không thì Kokoro synthesize động.
        wait=True → chờ master phát xong trước khi đi tiếp."""
        wav = os.path.join(AUDIO_DIR, f"{key}.wav")
        mp3 = os.path.join(AUDIO_DIR, f"{key}.mp3")
        if os.path.isfile(wav) or os.path.isfile(mp3):
            if wait:
                self._audio_done.clear()
            await self.broadcast_masters({"type": "play_audio", "key": key})
            if wait:
                await self._wait_audio()
            return
        await self.say(text, wait=wait)

    # ---- round flow ----
    async def start_game(self):
        async with self.lock:
            if self.phase in ("announce", "playing", "round_end"):
                log.info("start_game bỏ qua — game đang chạy (phase=%s)", self.phase)
                return
            for t in self.teams.values():
                t["score"] = 0; t["order"] = None
            self.round_idx = -1
            self.phase = "announce"
        await self.broadcast_masters({"type": "stop_audio"})  # dừng TTS cũ trước khi vào intro
        self._audio_done.set()
        await self.broadcast_all({"type": "reset"})
        await self.sync_scoreboard()
        # CHỜ intro phát trọn vẹn rồi mới vào vòng 1 — tránh thông báo vòng 1 đè lên
        # intro (master chỉ có 1 thẻ <audio>, set src mới = cắt audio đang phát).
        await self.play_or_say("intro", D.INTRO_TEXT, wait=True)
        async with self.lock:
            if self.phase != "announce":
                return  # operator can thiệp giữa intro (restart) → không tự vào vòng
        await asyncio.sleep(0.3)
        await self.start_round(0)

    async def start_round(self, idx):
        self.round_idx = idx
        self.object = OBJECTS[idx]
        self.phase = "playing"
        for t in self.teams.values():
            t["order"] = None; t["last_rec"] = 0.0
        await self.sync_scoreboard()
        await self.broadcast_stations({"type": "round", "object": self.object["name"], "vi": self.object["vi"], "icon": self.object.get("icon", ""), "id": self.object.get("id", "")})
        await self.play_or_say(f"round_{self.object['id']}", D.round_text(idx, self.object))
        # KHÔNG tự timeout — ban tổ chức điều khiển tiến trình bằng nút
        # "Bỏ qua vòng" (skip) / "Vòng kế" (next_round). Vòng cũng tự kết thúc
        # khi cả 3 đội đều nhận diện đúng (all_done).

    async def end_round(self, reason):
        async with self.lock:
            if self.phase == "announce":
                # "Bỏ qua vòng" lúc intro đang đọc → chỉ rút ngắn intro; start_game
                # sẽ tự vào vòng 1 (tránh đọc "Hết vòng không!" + đúp vòng 1).
                self.interrupt_audio()
                return
            if self.phase != "playing":
                return
            self.phase = "round_end"
        # Tổng kết vòng (ngắn) + nhịp nghỉ rồi sang vòng kế
        summary = self._round_summary()
        await self.say(summary)
        await self.sync_scoreboard()
        await asyncio.sleep(2)
        if self.round_idx + 1 < ROUNDS:
            await self.start_round(self.round_idx + 1)
        else:
            await self.game_over()

    def _round_summary(self):
        if not self.object:
            return ""
        # Ngắn gọn để giảm lag chuyển vòng (đã đọc từng đội khi nhận diện đúng;
        # chi tiết điểm số hiện trên bảng điểm). Số → chữ cho TTS đọc rõ.
        return f"Hết vòng {num_vi(self.round_idx + 1)}!"

    def ranking(self):
        """Trả về danh sách đội xếp theo điểm giảm dần (dùng cho game_over)."""
        return sorted(
            [{"id": tid, "name": t["name"], "color": t["color"], "score": t["score"]}
             for tid, t in self.teams.items()],
            key=lambda r: r["score"], reverse=True,
        )

    async def game_over(self):
        self.phase = "game_over"
        ranking = self.ranking()
        winner = ranking[0]   # hoà → giữ thứ tự A/B/C (sort ổn định)
        await self.say(f"Trò chơi kết thúc! {winner['name']} là nhà vô địch với {num_vi(winner['score'])} điểm! "
                       f"Chúc mừng các bạn! Cảm ơn tất cả đã tham gia!")
        await self.broadcast_all({
            "type": "game_over",
            "winner": winner["id"],
            "winner_name": winner["name"],
            "ranking": ranking,
        })
        await self.sync_scoreboard()

    # ---- recognize (từ station) ----
    async def handle_recognize(self, team: str, image_b64: str):
        if self.phase != "playing" or not self.object:
            await self._send_station(team, {"type": "result", "correct": False, "msg": "Chờ vòng bắt đầu nhé!"})
            return
        async with self.lock:
            t = self.teams[team]
            now = time.time()
            if t["order"] is not None:
                # đã về đích vòng này — PHẢI trả result để trạm thoát trạng thái
                # "Đang nhận diện..." và nút bấm không kẹt disabled vĩnh viễn.
                await self._send_station(team, {"type": "result", "correct": None,
                                                "msg": "Đội mình đã về đích vòng này rồi!"})
                return
            if now - t["last_rec"] < RECOGNIZE_DEBOUNCE:
                await self._send_station(team, {"type": "result", "correct": False, "msg": "Chờ một chút rồi bấm lại nhé!"})
                return
            t["last_rec"] = now
            # Ghi nhớ vòng hiện tại để phát hiện kết quả "xuyên vòng" sau khi vision về
            rec_round = self.round_idx
            rec_obj_id = self.object["id"]
        # vision (ngoài lock để song song)
        correct = await judge_vision(image_b64, self.object)
        async with self.lock:
            t = self.teams[team]
            # Kết quả vision về muộn: nếu đã không còn playing hoặc vòng/vật phẩm đã
            # đổi (BTC bỏ qua/chuyển vòng trong lúc vision chạy) → LOẠI kết quả cũ,
            # không cộng điểm nhầm vào vòng kế tiếp.
            if (self.phase != "playing" or self.round_idx != rec_round
                    or not self.object or self.object["id"] != rec_obj_id):
                await self._send_station(team, {"type": "result", "correct": None,
                                                "msg": "Vòng đã chuyển — kết quả không được tính."})
                return
            if correct is None:
                await self._send_station(team, {"type": "result", "correct": None,
                                                "msg": "AI không chắc — nhờ cô chú duyệt giúp!"})
                return
            if not correct:
                await self._send_station(team, {"type": "result", "correct": False,
                                                "msg": "Chưa đúng rồi! Thử lại xem!"})
                return
            # đúng → xếp thứ tự
            order = sum(1 for tt in self.teams.values() if tt["order"] is not None) + 1
            t["order"] = order
            pts = D.get_points_by_order(order, len(self.teams))
            t["score"] += pts
        await self._send_station(team, {"type": "result", "correct": True, "order": order,
                                        "points": pts, "msg": f"Đúng rồi! Về {ORDER_WORD.get(order, order)}! Cộng {pts} điểm!"})
        await self.play_or_say(f"correct_{team}_{D.ORDER_KEY.get(order, 'x')}", D.correct_text(t['name'], order))
        await self.sync_scoreboard()
        if all(tt["order"] is not None for tt in self.teams.values()):
            await self.end_round("all_done")

    async def _send_station(self, team, msg):
        ws = self.stations.get(team)
        if ws:
            await self._send(ws, msg)

    # ---- operator ----
    async def force_accept(self, team):
        """Operator ép đúng cho đội (khi AI sai/chậm)."""
        if team not in self.teams:
            return
        async with self.lock:
            if self.phase != "playing":
                return
            t = self.teams[team]
            if t["order"] is not None:
                return
            order = sum(1 for tt in self.teams.values() if tt["order"] is not None) + 1
            t["order"] = order
            pts = D.get_points_by_order(order, len(self.teams))
            t["score"] += pts
        log.info("Operator force_accept %s -> order %d (+%d)", team, order, pts)
        await self._send_station(team, {"type": "result", "correct": True, "order": order,
                                        "points": pts, "msg": f"Đã duyệt! Về {ORDER_WORD.get(order, order)}! Cộng {pts} điểm!"})
        await self.play_or_say(f"correct_{team}_{D.ORDER_KEY.get(order, 'x')}", D.correct_text(t['name'], order))
        await self.sync_scoreboard()
        if all(tt["order"] is not None for tt in self.teams.values()):
            await self.end_round("all_done")

    async def add_point(self, team, delta):
        if team not in self.teams:
            return
        async with self.lock:
            self.teams[team]["score"] += delta
        await self.sync_scoreboard()

    async def reset(self):
        self.phase = "idle"
        self.round_idx = -1
        self.object = None
        for t in self.teams.values():
            t["score"] = 0; t["order"] = None
        await self.broadcast_masters({"type": "stop_audio"})  # dừng TTS đang phát khi chạy lại
        self._audio_done.set()  # giải phóng điểm chờ audio (intro) nếu có
        await self.broadcast_all({"type": "reset"})
        await self.sync_scoreboard()


game = Game()

# ---------- FastAPI ----------
app = FastAPI()
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def master_page():
    return FileResponse(os.path.join(STATIC_DIR, "timnang", "master.html"))


@app.get("/station/{team}")
async def station_page(team: str):
    if team not in game.teams:
        return JSONResponse({"error": "team unknown", "team": team}, status_code=404)
    html = os.path.join(STATIC_DIR, "timnang", "station.html")
    return FileResponse(html)


@app.get("/audio/{key}")
async def audio(key: str):
    extless = key.replace(".wav", "").replace(".mp3", "")
    # 1. TTS động (Kokoro say()) — temp WAV
    tts_wav = os.path.join(TTS_DIR, f"{extless}.wav")
    if os.path.isfile(tts_wav):
        return FileResponse(tts_wav, media_type="audio/wav")
    # 2. Pre-cache — .wav (Kokoro) hoặc .mp3 (edge backup) trong AUDIO_DIR
    pc_wav = os.path.join(AUDIO_DIR, f"{extless}.wav")
    if os.path.isfile(pc_wav):
        return FileResponse(pc_wav, media_type="audio/wav")
    pc_mp3 = os.path.join(AUDIO_DIR, f"{extless}.mp3")
    if os.path.isfile(pc_mp3):
        return FileResponse(pc_mp3, media_type="audio/mpeg")
    return JSONResponse({"error": "not found", "key": key}, status_code=404)


@app.get("/health")
async def health():
    return {
        "ok": True,
        "game": "timnang",
        "tts": _TTS_OK,
        "tts_voice": os.environ.get("KOON_VOICE", "mai_linh"),
        "vision": bool(llm),
        "vision_model": OR_MODEL if llm else None,
        "teams": [t["id"] for t in TEAMS],
        "objects": len(OBJECTS),
        "rounds": ROUNDS,
    }


# ---------- WebSocket: station ----------
@app.websocket("/ws/station/{team}")
async def ws_station(ws: WebSocket, team: str):
    if team not in game.teams:
        await ws.close(code=1008)
        return
    await ws.accept()
    game.stations[team] = ws
    log.info("Station [%s] kết nối", team)
    await game._send(ws, game.scoreboard_msg())
    if game.object:
        await game._send(ws, {"type": "round", "object": game.object["name"], "vi": game.object["vi"], "icon": game.object.get("icon", ""), "id": game.object.get("id", "")})
    try:
        while True:
            msg = json.loads(await ws.receive_text())
            if msg.get("type") == "recognize":
                await game.handle_recognize(team, msg.get("image", ""))
    except WebSocketDisconnect:
        log.info("Station [%s] ngắt", team)
        if game.stations.get(team) is ws:
            game.stations.pop(team, None)


# ---------- WebSocket: master/operator ----------
@app.websocket("/ws/master")
async def ws_master(ws: WebSocket):
    await ws.accept()
    game.masters.add(ws)
    log.info("Master/operator kết nối (%d)", len(game.masters))
    await game._send(ws, game.scoreboard_msg())
    try:
        while True:
            msg = json.loads(await ws.receive_text())
            t = msg.get("type")
            if t == "audio_ended":
                game.interrupt_audio()
            elif t == "op":
                a = msg.get("action")
                if a == "start":
                    # Chạy nền để vòng nhận WS của master không bị block trong lúc
                    # chờ intro phát xong (operator vẫn bấm được nút khác ngay).
                    game._spawn(game.start_game())
                elif a == "restart":
                    game.interrupt_audio()
                    await game.reset()
                elif a == "force_accept":
                    await game.force_accept(msg.get("team"))
                elif a == "add_point":
                    await game.add_point(msg.get("team"), msg.get("delta", 1))
                elif a == "skip_round":
                    await game.end_round("skip")
                elif a == "next_round":
                    if game.phase == "announce":
                        game.interrupt_audio()  # bỏ qua intro, start_game tự vào vòng 1
                    else:
                        nxt = game.round_idx + 1
                        if nxt < ROUNDS:
                            await game.start_round(nxt)
                        else:
                            await game.game_over()
    except WebSocketDisconnect:
        log.info("Master ngắt")
        game.masters.discard(ws)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
