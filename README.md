# F-Code SITI AI — Summer 2026 Gala

Dự án xây dựng phần mềm AI cho phần giao lưu/giải trí trên sân khấu Gala LHTT **Summer 2026 (SUM26)** tại **Trung tâm Phát huy Bình Thọ**.

Đội ngũ thực hiện: **F-Code**

---

## Trò chơi

### 1. Cùng Koon Đi Tìm Cầu Vồng (AI hội thoại) ✅ Đã hoàn thiện

Trẻ đồng hành cùng nhân vật AI **KOON** vượt qua **7 thử thách** để tìm lại 7 sắc màu cầu vồng.

- **Cách chơi**: KOON đọc câu đố → trẻ trả lời (mic hoặc gõ chữ) → ô nhập/mic **khoá lại** trong lúc LLM chấm (hiện đáp án bé vừa nói + "KOON đang nghĩ…") → đúng: **confetti + chime ăn mừng ngay** rồi mở khóa mảnh màu; sai: **chime báo sai trước** rồi KOON **đáp lại hội thoại** + gợi ý, trẻ thử lại (KHÔNG lặp lại câu hỏi → mượt). LLM chấm **theo logic câu đố** (chấp nhận nhiều đáp án hợp lý, vd "4 chân không đi" → bàn/ghế/tủ đều đúng).
- **Công nghệ**:
  - **TTS**: Kokoro Vietnamese (ONNX CPU, giọng `mai_linh`) — **pre-cache** toàn bộ câu cố định (phát tức thì <200ms) + Kokoro động cho câu phản hồi (chịu lỗi: thiếu file → tự sinh).
  - **LLM**: OpenRouter GPT-4o-mini — 1 call chấm đúng/sai **+ sinh phản hồi hội thoại** (lễ phép, gợi ý nhẹ, không tiết lộ đáp án, không bịa lý do sai sự thật, an toàn trẻ em).
  - **STT**: Web Speech API (Chrome=Google / Edge=Azure).
  - **Avatar**: Live2D `mao_pro` + lip-sync theo giọng TTS.
  - **Recap**: sau cầu vồng → KOON "hô biến" (bay ra giữa màn + particle sao/bụi cầu vồng + sound magic) → phát video recap với controls (pause/tua/âm lượng).
  - **Operator**: skip / force_correct / replay / restart — ngắt được mọi điểm chờ (cả lúc KOON đang nói và lúc chờ trẻ trả lời).
- **Thời lượng**: ~10–11 phút
- **Server**: FastAPI + WebSocket (`app/server.py`)

### 2. Tìm Nắng Cùng AI (nhận diện hình ảnh) ✅ Đã hoàn thiện

Trò đối kháng **3 đội** (A/B/C). Mỗi vòng AI gọi tên 1 vật phẩm → trẻ bốc đồ mù trong thùng → giơ trước webcam trạm đội → bấm **NHẬN DIỆN** → AI (vision) chấm đúng/sai → đội đúng trước được điểm cao hơn. **6 vòng = 6 vật phẩm** (~5 phút), điểm theo thứ tự về đích **3-2-1**.

- **Cách chơi**:
  - **Master** (màn LED sân khấu + loa): bảng điểm real-time, AI Kokoro công bố vật phẩm + kết quả + tổng kết, operator controls.
  - **3 trạm** (mỗi đội 1 laptop/tab): webcam + nút NHẬN DIỆN — trẻ **tự phục vụ hoàn toàn**, không cần người hỗ trợ.
  - Đúng → xếp thứ tự về đích (nhất/nhì/ba) → cộng điểm, AI đọc thông báo. Sai → *"Chưa đúng rồi! Thử lại xem!"* (debounce 1.5s chống spam). **Vòng kết thúc khi cả 3 đội đều đúng, hoặc operator bấm "Bỏ qua vòng" / "Vòng kế"** — KHÔNG auto-timeout, BTC tự điều khiển tiến trình theo tình hình sân khấu.
- **Công nghệ**:
  - **Vision**: OpenRouter **GPT-4o-mini** (multimodal) chấm đúng/sai theo `vision_prompt` mỗi vật — chấp nhận góc nhìn khác, một phần vật cũng OK.
  - **TTS**: Kokoro Vietnamese (giọng `mai_linh`) — công bố vật phẩm + kết quả + tổng kết vòng + tuyên bố vô địch.
  - **Realtime**: FastAPI + WebSocket (1 master + 3 stations), bảng điểm push tức thì.
  - **UX sân khấu**: confetti + chime (Web Audio) khi đúng/về đích; fanfare 7 nốt + banner VÔ ĐỊCH khi kết thúc.
  - **Operator**: ép đúng (khi AI sai/chậm — Kokoro đọc thông báo luôn), ± điểm thủ công, **bỏ qua vòng / vòng kế (tự điều khiển tiến trình, không auto-timeout)**, chạy lại.
- **Thời lượng**: ~5 phút
- **Server**: FastAPI + WebSocket (`app/timnang_master.py`)

#### 🚀 Chạy Trò 2 chi tiết (port 8001 — tách khỏi Trò 1 :8000)

```bash
# Yêu cầu: venv đã activate + đã cài Kokoro + (nên có) OPENROUTER_API_KEY
python app/timnang_master.py
```
Sẵn sàng khi log hiện:
```
INFO Kokoro TTS sẵn sàng (giọng mai_linh)
INFO Uvicorn running on http://0.0.0.0:8001
```
Kiểm tra nhanh: `curl http://localhost:8001/health` → `{"ok":true,"tts":true,"vision":true,"teams":["A","B","C"],"rounds":6}`.

**Mở các trang (Chrome/Edge):**

| Trang | URL | Dùng cho |
|---|---|---|
| **Master / bảng điểm / operator** | http://localhost:8001/ | Máy chính → màn LED sân khấu + loa |
| **Trạm đội A / B / C** | http://localhost:8001/station/A · /B · /C | Laptop mỗi đội (webcam + nút NHẬN DIỆN) |

- **Test nhanh trên 1 máy**: mở master + 3 trạm bằng `localhost` (4 tab) là chơi đủ.
- **Gala nhiều máy**: master trên máy chính; trạm mở trên laptop đội bằng **IP LAN** máy master, vd `http://192.168.1.3:8001/station/A`. Tìm IP: `ipconfig` (Windows) → dòng IPv4.

> ⚠️ **Webcam cần secure-context**: browser chỉ mở webcam qua `localhost` hoặc `https`. Trạm mở bằng IP LAN (`http://192.168.1.3...`) sẽ bị **chặn webcam**. Trên sân khấu thật (mỗi đội 1 laptop) phải chạy server qua **HTTPS** (reverse proxy + chứng chỉ) thì webcam trạm mới mở được. Test tạm thì dùng `localhost` trên cùng máy.

**Operator (BTC) — bấm trên trang Master:**

| Nút / phím | Action | Khi nào dùng |
|---|---|---|
| **▶ Bắt đầu** (phím `Enter`) | `start` — intro → vòng 1 | Bắt đầu trò |
| **↻ Chạy lại** (phím `Esc`) | `restart` — reset toàn bộ | Chơi lại từ đầu |
| **⏭ Bỏ qua vòng** | `skip_round` — kết vòng (đọc tổng kết) → vòng kế | Vòng kẹt / muốn qua |
| **⏭ Vòng kế** | `next_round` — nhảy thẳng vòng kế (không tổng kết) | Tiến nhanh |
| **✓ Ép đúng** (mỗi đội) | `force_accept` — duyệt đội đúng, xếp hạng + Kokoro đọc | AI chấm sai/chậm |
| **+1 / −1** (mỗi đội) | `add_point` — cộng/trừ điểm | Sửa điểm tay |

> 🎛 **Không có auto-timeout** — BTC tự quyết lúc qua vòng. Vòng cũng **tự kết khi cả 3 đội đều nhận diện đúng** (all_done → Kokoro đọc tổng kết → vòng kế).

**Luồng 1 vòng:**
1. BTC bấm **▶ Bắt đầu** → Kokoro đọc intro → tự vào vòng 1.
2. Mỗi vòng: Kokoro công bố vật phẩm → 3 đội bốc mù, giơ trước webcam, bấm **NHẬN DIỆN** (hoặc phím `Space` ở trạm).
3. Vision GPT-4o-mini chấm → **đúng**: xếp nhất/nhì/ba + cộng điểm (3-2-1) + Kokoro đọc thông báo. **Sai**: *"Chưa đúng rồi! Thử lại xem!"* (debounce 1.5s chống spam).
4. Cả 3 đội xong → Kokoro đọc tổng kết vòng → tự sang vòng kế. (Hoặc BTC bấm **Bỏ qua vòng** / **Vòng kế** bất cứ lúc nào.)
5. Hết 6 vòng → Kokoro tuyên bố vô địch + fanfare 7 nốt + banner **VÔ ĐỊCH**.

**Test tự động** (cần server :8001 đang chạy):
```bash
python app/scripts/_tn_test.py   # vision + WS flow + recognize round-trip
```

#### WebSocket Trò 2 (riêng, không dùng `/ws` của Trò 1)

| Endpoint | Vai trò |
|---|---|
| `/ws/master` | Master/scoreboard + operator |
| `/ws/station/{team}` | Trạm đội (A/B/C) |

**Server → Client:**
```json
{"type": "scoreboard", "phase": "playing", "round": 1, "rounds": 6, "object": "quả bóng tennis", "teams": [...]}
{"type": "round", "object": "quả bóng tennis", "vi": "quả bóng tennis"}   // gửi trạm khi mở vòng
{"type": "result", "correct": true|false|null, "order": 1, "points": 3, "msg": "..."}  // về trạm
{"type": "play_audio", "key": "tts_abc123"}                               // Kokoro → loa sân khấu
{"type": "reset"} | {"type": "game_over", "winner": "A", "winner_name": "Đội A"}
```

**Client → Server:**
```json
// Trạm:
{"type": "recognize", "image": "data:image/jpeg;base64,..."}

// Master/operator:
{"type": "op", "action": "start | restart | skip_round | next_round | force_accept | add_point", "team": "A", "delta": 1}
```

### UI/UX của Trò 1 — Các tính năng hiện tại

```
┌──────────── 48vw ────────┬─────── 52vw ────────┐
│                          │                      │
│  🔴🟠🟡🟢🔵🟣🟣        │   🌈🌈🌈 (cầu vồng)  │
│  (thanh tiến trình)      │                      │
│          ┌──────────┐    │                      │
│          │ CÂU HỎI  │    │      🦊 KOON         │
│          │ TO RÕ    │    │                      │
│          └──────────┘    │                      │
│  [status + STT heard]    │                      │
├─────────────┴────────────┴──────────────────────┤
│   [🎤 Mic] [Gửi]   Enter=gửi                    │
└─────────────────────────────────────────────────┘
```

- **Layout 2 cột**: Câu hỏi bên trái (48vw), cầu vồng + KOON bên phải (52vw) — không đè lên nhau
- **KOON to + crop**: Container min(560px, 52vh), scale 1.8x, shift Y crop từ đầu gối trở lên (half-body)
- **Progress bar 7 màu**: 7 orb dạng bóng đèn, sáng dần khi mở khoá, pulse khi active
- **Feedback tối giản**: Không overlay to — chỉ status text + confetti (60-150 mảnh) + chime âm thanh (Web Audio API)
- **Câu hỏi giữ nguyên**: Hiển thị xuyên suốt khi KOON đọc, không biến mất giữa chừng
- **Finale**: Confetti lớn + "CẦU VỒNG RỰC RỠ!" gradient + 7-nốt nhạc thang âm
- **Sao nền**: 30 ngôi sao twinkle nhẹ ở 60% trên màn hình
- **KOON vui khi đúng**: Expression exp_05 + random motion (special_01-03), tự động về Idle sau 3s
- **Recap video + "phép màu"**: Hết cầu vồng → KOON bay ra giữa màn + phóng to + particle sao/bụi cầu vồng xoay lấp lánh + sound magic (sparkle+swoosh) → KOON hô biến → flash trắng → video phát toàn màn (controls pause/tua/âm lượng, cross-fade mượt). Chưa có video → overlay animation "Recap một năm đồng hành".
- **Operator panel**: Đọc lại (R) / Bỏ qua (S) / Ép đúng (F) / Chạy lại (Esc) — **ngắt được mọi điểm chờ** (ngay cả lúc KOON đang nói hoặc đang chờ trẻ). KOON nghe được (hiện text dưới status, tự ẩn sau 4s).

---

## 🚀 Cài đặt & Chạy (Step-by-Step)

> Hai trò chạy trên **2 port riêng**: Trò 1 (Cầu Vồng) :**8000**, Trò 2 (Tìm Nắng) :**8001**. Cài đặt chung cho cả hai — chỉ khác lệnh chạy ở bước cuối. Có thể chạy **cả hai cùng lúc** trên cùng máy.

### ⚡ Chạy nhanh (TL;DR)

Nếu đã quen và có sẵn Python 3.10+ / Git — 5 lệnh sau là chạy được (chi tiết từng bước + xử lý lỗi ở dưới):

```bash
git clone --recurse-submodules <repo-url> && cd fcode-siti-AI   # 1. clone (kèm submodule Kokoro)
python -m venv .venv                                             # 2. tạo venv
.venv\Scripts\activate                                           #    activate (Windows) — Linux/mac: source .venv/bin/activate
pip install -r app/requirements.txt                              # 3. cài dependencies
copy .env.example .env                                           # 4. tạo .env → mở ra điền OPENROUTER_API_KEY (Bước 8)
python app/server.py                                             # 5a. Trò 1 (:8000)
# python app/timnang_master.py                                   #   hoặc 5b. Trò 2 (:8001)
```

Mở **http://localhost:8000** (Trò 1) hoặc **http://localhost:8001** (Trò 2) bằng Chrome/Edge.

> ⚠️ **Lần đầu tiên** còn phải **cài Kokoro TTS (~2GB)** và **sinh pre-cache giọng** — không làm thì game vẫn chạy nhưng KHÔNG có tiếng (xem **Bước 4 → Bước 7** dưới). Đây là phần tốn thời gian nhất, chỉ làm 1 lần.

### Yêu cầu hệ thống

| Thành phần | Yêu cầu |
|---|---|
| **Python** | ≥ 3.10 |
| **Trình duyệt** | **Chrome hoặc Edge** (cần Web Speech API cho mic — Trò 1; webcam — Trò 2) |
| **Mạng** | Internet khi: cài (pip), gen giọng edge-tts (tùy chọn), chạy LLM/vision (OpenRouter) và STT (Trò 1 gửi audio lên Google/Azure). **Sau khi gen Kokoro pre-cache xong, 2 trò vẫn phát được tại Gala dù mất mạng** (LLM tự fallback fuzzy match, Trò 2 operator duyệt tay). |
| **RAM** | ≥ 4GB (khuyến nghị 8GB+) |
| **CPU** | Đa lõi (TTS Kokoro chạy ONNX CPU, ~5x realtime) |
| **Ổ cứng** | ~3GB trống (model Kokoro ~2GB + deps torch/onnxruntime) |
| **HĐH** | Windows (test chính; có thể chạy Linux/macOS) |
| **Webcam** | Trò 2 — 1 webcam mỗi trạm đội (dùng webcam laptop) |
| **API key** | `OPENROUTER_API_KEY` — khuyến nghị mạnh (LLM chấm Trò 1 + vision Trò 2). Không có vẫn chạy được ở chế độ dự phòng. |

### Tổng quan nhanh (tra cứu)

| | **Trò 1 — Cầu Vồng** | **Trò 2 — Tìm Nắng** |
|---|---|---|
| Server | `python app/server.py` | `python app/timnang_master.py` |
| Port | `8000` | `8001` |
| Mở | http://localhost:8000 | http://localhost:8001/ (master) · /station/A · /B · /C |
| Data | `app/koon_data.py` | `app/timnang_data.py` |
| WS | `/ws` | `/ws/master` + `/ws/station/{team}` |
| Pre-cache giọng | `app/scripts/gen_koon_voice.py` (28 câu) | `app/scripts/gen_timnang_voice.py` (16 câu) |
| Cần API key | Có (LLM chấm + reply) | Có (vision chấm) |

---

### Bước 1: Clone repo

```bash
git clone https://github.com/bechovang/fcode-siti-AI.git
cd fcode-siti-AI
```

### Bước 2: Cập nhật submodule Kokoro TTS

```bash
git submodule update --init --recursive
```

Lệnh này clone **`ref/Kokoro-Vietnamese`** (TTS tiếng Việt, submodule duy nhất). Model ONNX ~2GB sẽ được **download tự động lần đầu** khi khởi động server hoặc khi gen giọng.

> Nếu clone bằng ZIP thay vì `git clone`, submodule sẽ trống → Kokoro không khởi động được. Phải clone qua git rồi chạy lệnh trên.

### Bước 3: Tạo virtual environment

**Windows (cmd hoặc PowerShell):**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

**PowerShell** (nếu báo lỗi chạy script bị chặn):
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

> Sau khi activate, dấu nhắc hiện `(.venv)`. **Mở terminal mới phải activate lại** trước khi chạy lệnh pip/python phía dưới.

### Bước 4: Cài Kokoro Vietnamese TTS (ONNX)

```bash
pip install -e "ref/Kokoro-Vietnamese[onnx]"
```

> ⏱ Lần đầu cài **5–15 phút** (download `torch`, `transformers`, `onnxruntime` — nặng vài GB). Nếu mạng yếu, cài từng gói: `pip install torch` rồi mới chạy lệnh trên.

Kiểm tra: `python -c "from kokoro_vietnamese import KokoroVietnamese; print('OK')"` → in `OK`.

### Bước 5: Cài các dependencies Python (cả 2 trò)

```bash
pip install -r app/requirements.txt
```

File `app/requirements.txt` gồm: `fastapi`, `uvicorn[standard]`, `openai` (→ OpenRouter), `rapidfuzz` (fuzzy match dự phòng), `soundfile` (ghi WAV Kokoro).

**Cài thêm nếu muốn chạy test tự động Trò 2** (tùy chọn):
```bash
pip install websockets pillow
```
(cần cho `app/scripts/_tn_test.py` — test vision + WebSocket flow).

### Bước 6: (Tùy chọn) Cài avatar Live2D KOON

Avatar KOON lấy từ `ref/Open-LLM-VTuber/live2d-models/` (thư mục này **gitignore** — không có sau fresh clone). Nếu thiếu, Trò 1 **tự fallback về emoji 🦊**, vẫn chơi bình thường. Muốn có avatar động:

```bash
git clone https://github.com/Open-LLM-VTuber/Open-LLM-VTuber.git ref/Open-LLM-VTuber
```

Restart server → log hiện `Live2D: /live2d (mao_pro)` và `GET /health` trả `"live2d": true`. (Model `mao_pro` = Niziiro Mao, sample Live2D free-material.)

### Bước 7: Sinh pre-cache giọng (chạy 1 lần — khuyến nghị mạnh)

Toàn bộ câu thoại **cố định** (intro, câu hỏi, phản hồi đúng/sai, công bố vật phẩm, kết quả…) được **pre-cache** bằng giọng Kokoro để phát **tức thì** (<200ms) thay vì synthesize runtime (~1–2s mỗi câu). Các file nằm trong `app/assets/audio/` (đã gitignore) nên **máy mới phải tự gen**.

**Trò 1 (KOON — 28 câu):**
```bash
python app/scripts/gen_koon_voice.py
```
→ `app/assets/audio/koon/*.wav` (intro×5, q/right/wrong×7, recap, goodbye).

**Trò 2 (Tìm Nắng — 16 câu):**
```bash
python app/scripts/gen_timnang_voice.py
```
→ `app/assets/audio/timnang/*.wav` (intro×1, mở vòng×6, thông báo đúng/thứ tự×9).

**Đổi engine gen (tùy chọn):**
```bash
KOON_GEN_ENGINE=edge python app/scripts/gen_koon_voice.py        # edge-tts vi-VN-HoaiMyNeural → .mp3 (backup, cần mạng)
KOON_GEN_ENGINE=edge python app/scripts/gen_timnang_voice.py
```
- `kokoro` (mặc định): nhất quán với TTS động, **offline** sau khi gen. Khuyến nghị cho Gala.
- `edge`: free, nhẹ, nhưng cần mạng và chất lượng thấp hơn.

> Có thêm `app/scripts/gen_koon_voice_capcut.py` — biến thể dùng CapCut TTS (cần `ref/capcut-tts-api`). Chỉ khi muốn giọng CapCut thay Kokoro/edge.

> **Bỏ qua bước này vẫn chạy được** — server sẽ synthesize Kokoro động mỗi câu (chậm hơn, nhưng 2 trò vẫn hoạt động đầy đủ).

### Bước 8: Thiết lập API key & cấu hình `.env` (khuyến nghị mạnh)

Trò 1 cần LLM chấm đáp án; Trò 2 cần vision chấm ảnh. Cả hai dùng chung `OPENROUTER_API_KEY`. **Cách dễ nhất là dùng file `.env`** — server (`server.py` / `timnang_master.py`) tự đọc khi khởi động nhờ `python-dotenv`, không phải `set`/`export` mỗi lần mở terminal.

**1) Tạo file `.env` từ mẫu có sẵn trong repo:**
```bash
copy .env.example .env          # Windows (cmd)
Copy-Item .env.example .env     # Windows (PowerShell)
cp .env.example .env            # Linux / macOS / Git Bash
```

**2) Mở file `.env`, điền key thật vào dòng `OPENROUTER_API_KEY`:**
```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx   # ← thay bằng key thật
```
Các biến còn lại (`OR_MODEL`, `KOON_VOICE`, `KOON_GEN_ENGINE`…) cứ để mặc định là chạy được ngay; mô tả đầy đủ ở mục **"Toàn bộ biến môi trường"** phía dưới.

> 🔒 **Bảo mật**: file `.env` đã được `.gitignore` nên **không bao giờ** bị đẩy lên GitHub — chỉ file mẫu `.env.example` (giá trị rỗng) mới được commit. Tuyệt đối không commit key thật.

👉 Đăng ký key miễn phí tại [OpenRouter.ai](https://openrouter.ai/). **Không có key**: Trò 1 fallback fuzzy match (kém chính xác hơn), Trò 2 operator duyệt đúng/sai bằng tay.

<details>
<summary><b>Cách thay thế: set biến môi trường trực tiếp (nếu không dùng <code>.env</code>)</b></summary>

**Windows (cmd):**
```cmd
set OPENROUTER_API_KEY=sk-or-v1-...
```
**Windows (PowerShell):**
```powershell
$env:OPENROUTER_API_KEY = "sk-or-v1-..."
```
**Linux/macOS:**
```bash
export OPENROUTER_API_KEY=sk-or-v1-...
```

> Lưu ý: `set`/`$env:` chỉ có hiệu lực trong terminal hiện tại. Để dùng lâu dài, set trong System Environment Variables (Windows) hoặc `~/.bashrc`/`~/.zshrc` (Linux/mac). Nếu đã có `.env` thì không cần bước này — `.env` được ưu tiên đọc tự động.

</details>

### Bước 9a: Chạy Trò 1 — Cầu Vồng (port 8000)

```bash
python app/server.py
```

Log kỳ vọng:
```
INFO TTS temp dir: C:\Users\...\koon_tts_xxx
INFO LLM judge: OpenRouter openai/gpt-4o-mini
INFO Kokoro TTS sẵn sàng (giọng mai_linh, device=cpu)
INFO STT: browser Web Speech API (Chrome=Google / Edge=Azure)
INFO Live2D: /live2d (mao_pro) — từ ref/Open-LLM-VTuber/live2d-models
INFO Uvicorn running on http://0.0.0.0:8000
```

→ Mở **http://localhost:8000** bằng **Chrome/Edge**:
- Bấm **"🧪 Test mic / STT"** để kiểm tra nhận diện giọng nói.
- Bấm **"Bắt đầu"** → KOON sẽ chào và đặt câu hỏi!

### Bước 9b: Chạy Trò 2 — Tìm Nắng (port 8001)

```bash
python app/timnang_master.py
```
→ Mở **http://localhost:8001/** (master/operator) + **/station/A · /B · /C** (tram đội).

📖 **Hướng dẫn chạy chi tiết** — operator controls (Bắt đầu/Bỏ qua vòng/Ép đúng…), chơi nhiều máy qua IP LAN, lưu ý webcam cần HTTPS, luồng 1 vòng, test — xem mục **"🚀 Chạy Trò 2 chi tiết"** ở phần Trò 2 phía trên.

### Bước 9c: Chạy cả hai trò cùng lúc

Mở **2 terminal riêng** (mỗi terminal `activate` venv rồi chạy 1 server):
```bash
# Terminal 1 — Trò 1
python app/server.py            # :8000

# Terminal 2 — Trò 2
python app/timnang_master.py    # :8001
```
2 port khác nhau nên không xung đột. Trên sân khấu có thể chạy cả 2 trên cùng 1 máy chính.

### Bước 10: Kiểm tra trạng thái

```bash
# Trò 1
curl http://localhost:8000/health        # → {"tts":true,"llm":true,"stt":"web-speech","live2d":true,"video":...}

# Trò 2
curl http://localhost:8001/health        # → {"vision":true,"tts":true,...}
```

**Test tự động Trò 2** (cần server Trò 2 đang chạy + đã cài `websockets`/`pillow`):
```bash
python app/scripts/_tn_test.py           # vision judge + WS flow + recognize round-trip
```

> ⚠️ **Lưu ý mic trên mạng LAN (Trò 1)**: browser chỉ cho phép mic qua `localhost` hoặc **HTTPS**. Nếu trẻ truy cập bằng IP LAN (vd `http://192.168.x.x:8000`) thay vì `localhost`, phải chạy qua HTTPS (reverse proxy + chứng chỉ) — nếu không mic bị chặn. Trò 2 dùng webcam cũng chịu quy tắc tương tự (secure context).

---

## ⚙️ Tuỳ chỉnh

### Đổi giọng KOON

Kokoro có 14 giọng tiếng Việt:

| Giọng | Mô tả |
|---|---|
| `mai_linh` | 🥇 Nữ, dễ thương — **mặc định** |
| `diem_trinh` | Nữ, nhẹ nhàng |
| `thuc_trinh` | Nữ, tự nhiên |
| `ngoc_huyen` | Nữ, trẻ trung |
| `my_yen` | Nữ, ấm áp |
| `mai_loan` | Nữ, chậm rãi |
| `phat_tai` | Nam, vui vẻ |
| `hung_thinh` | Nam |
| `manh_dung` | Nam |
| `thanh_dat` | Nam |
| `tuan_ngoc` | Nam |
| `duc_an` | Nam |
| `duc_duy` | Nam |
| `storyvert` | Giọng kể chuyện |

```cmd
set KOON_VOICE=diem_trinh
python app/server.py
```

### Đổi model LLM

```cmd
set OR_MODEL=anthropic/claude-sonnet-4
set OR_MODEL=google/gemini-2.0-flash-001
```

### Sinh lại pre-cache giọng

```bash
# Trò 1 — KOON (28 câu)
python app/scripts/gen_koon_voice.py                          # Kokoro (mặc định) → .wav
KOON_GEN_ENGINE=edge python app/scripts/gen_koon_voice.py     # edge-tts → .mp3 (backup)

# Trò 2 — Tìm Nắng (16 câu)
python app/scripts/gen_timnang_voice.py                       # Kokoro → .wav
KOON_GEN_ENGINE=edge python app/scripts/gen_timnang_voice.py  # edge-tts → .mp3
```

### Toàn bộ biến môi trường

> 💡 Copy file mẫu **`.env.example`** (đã có sẵn trong repo) thành **`.env`** rồi điền giá trị — server đọc tự động. Bảng dưới liệt kê đầy đủ các biến (xem Bước 8 để biết cách tạo `.env`).

| Biến | Mặc định | Bắt buộc | Mô tả |
|---|---|---|---|
| `OPENROUTER_API_KEY` | - | ⚠️ Nên có | API key cho LLM (Trò 1) + vision (Trò 2) trên OpenRouter |
| `OR_MODEL` | `openai/gpt-4o-mini` | ❌ | Model trên OpenRouter (cả 2 trò dùng chung) |
| `KOON_VOICE` | `mai_linh` | ❌ | Giọng TTS Kokoro (14 giọng VN) — dùng cho cả 2 trò |
| `KOON_GEN_ENGINE` | `kokoro` | ❌ | Engine gen pre-cache: `kokoro` (.wav) hoặc `edge` (.mp3) |
| `KOON_VOICE_EDGE` | `vi-VN-HoaiMyNeural` | ❌ | Giọng edge-tts (chỉ dùng khi `KOON_GEN_ENGINE=edge`) |
| `KOON_RATE` | `-5%` | ❌ | Tốc độ edge-tts (chỉ dùng khi `KOON_GEN_ENGINE=edge`) |
| `CAPCUT_VOICE` | `BV421_vivn_streaming` | ❌ | Giọng CapCut TTS ("Nhỏ Ngọt Ngào" vi-VN) — chỉ cho script `gen_koon_voice_capcut.py` |

---

## 🌐 API Endpoints

| Endpoint | Method | Mô tả |
|---|---|---|
| `/` | GET | Trang chủ (giao diện game) |
| `/ws` | WebSocket | Kết nối game real-time |
| `/audio/{key}` | GET | Lấy file audio (WAV Kokoro động, hoặc WAV pre-cache, hoặc MP3 edge backup) |
| `/video/{file}` | GET | Phục vụ video recap từ `app/assets/video/` |
| `/health` | GET | Kiểm tra trạng thái server (TTS/LLM/STT/Live2D/video) |

### WebSocket Messages

**Server → Client:**
```json
{"type": "play_audio", "key": "tts_abc123", "tts": true}   // tts=true: Kokoro động; tts=false: pre-cache
{"type": "state", "phase": "ask", "idx": 0, "unlocked": [], "total": 7}
{"type": "show_question", "text": "...", "color": "Đỏ", "hex": "#e74c3c"}
{"type": "await_answer"}
{"type": "correct_answer", "hex": "#e74c3c"}   // ĐÚNG: confetti + chime đúng + magic particle NGAY khi chấm xong (trước khi KOON nói)
{"type": "wrong_answer"}                        // SAI: chime báo sai (to) + "❌ Chưa đúng…"; server đợi ~0.6s rồi mới để KOON nói (không đè tiếng)
{"type": "unlock_color", "hex": "#e74c3c"}      // sáng vòm cầu vồng + chấm tiến trình (sau khi KOON đã xác nhận xong)
{"type": "rainbow"}
{"type": "magic_reveal"}                       // KOON bay giữa + particle + sound (hô biến)
{"type": "play_video", "url": "/video/recap.mp4"}   // có file mp4 → phát video
{"type": "show_recap_overlay"}                 // không có video → overlay animation fallback
{"type": "stop_audio"}                         // operator skip/replay → dừng audio+lip-sync
{"type": "ready"}
{"type": "reset"}
```

**Client → Server:**
```json
{"type": "start"}
{"type": "audio_ended"}
{"type": "answer", "text": "dưa hấu", "stt": "web-speech"}   // "stt": "web-speech" (mic) hoặc bỏ trống (gõ tay)
{"type": "video_ended"}                        // hết video recap
{"type": "overlay_ended"}                      // hết overlay fallback
{"type": "op", "action": "skip"}               // skip | force_correct | replay | restart
```

---

## 🏗 Cấu trúc thư mục

```
├── app/                        # Ứng dụng Python chính
│   ├── server.py               # 🎯 Trò 1 — FastAPI + WebSocket + Kokoro TTS + LLM chấm/reply (:8000)
│   ├── koon_data.py            # 📦 Trò 1 — Dữ liệu 7 câu hỏi + đáp án + gợi ý + alias + path video
│   ├── timnang_master.py       # 🎯 Trò 2 — FastAPI + WebSocket + Vision + Kokoro TTS + scoreboard (:8001)
│   ├── timnang_data.py         # 📦 Trò 2 — 6 vật phẩm (vision_prompt) + 3 đội + điểm 3-2-1
│   ├── requirements.txt        # 📦 Deps Python (fastapi/uvicorn/openai/rapidfuzz/soundfile)
│   ├── assets/                 # (gitignored phần lớn)
│   │   ├── audio/
│   │   │   ├── koon/           # 🔊 Pre-cache giọng KOON (28 câu — gen bằng gen_koon_voice.py)
│   │   │   ├── timnang/        # 🔊 Pre-cache giọng Trò 2 (16 câu — gen bằng gen_timnang_voice.py)
│   │   │   ├── koon_edge_backup/  # edge-tts backup (.mp3) cho KOON
│   │   │   └── sfx/            # 🔉 Hiệu ứng âm thanh (webfx — sinh ở client, thường rỗng)
│   │   └── video/              # 🎬 Video recap (.mp4 — thả file vào là chạy; ưu tiên recap.mp4)
│   ├── scripts/                # Scripts phụ trợ
│   │   ├── gen_koon_voice.py        # Sinh pre-cache giọng KOON (Kokoro mặc định / edge backup)
│   │   ├── gen_timnang_voice.py     # Sinh pre-cache giọng Trò 2 (Kokoro / edge)
│   │   ├── gen_koon_voice_capcut.py # Biến thể CapCut TTS (cần ref/capcut-tts-api)
│   │   └── _tn_test.py              # 🧪 Test Trò 2 (vision + WS flow + recognize round-trip)
│   └── static/
│       ├── index.html          # 🖥 Trò 1 — Giao diện + Live2D KOON + magic transition + recap
│       ├── timnang/            # 🖥 Trò 2 — master.html (scoreboard) + station.html (webcam đội)
│       └── libs/               # 🧩 pixi v6 + Cubism core + pixi-live2d-display (vendor local)
├── docs/                       # Tài liệu dự án
│   ├── source-brief.md         # Tổng hợp yêu cầu
│   ├── kich-ban-koon.md        # Kịch bản chi tiết Trò 1
│   └── kich-ban-timnang.md     # Kịch bản chi tiết Trò 2
├── ref/                        # Reference implementations
│   ├── Kokoro-Vietnamese/      # ✅ TTS tiếng Việt (ONNX, 14 giọng) — submodule duy nhất (tracked)
│   ├── Open-LLM-VTuber/        # 🦊 Nguồn model Live2D (mao_pro) — gitignore, không commit
│   ├── pipecat/                # ⏸️ Real-time voice pipeline (future)
│   └── ...                     # Các reference khác (capcut-tts-api, v-tts, viet-asr...)
├── thongtin/                   # Tài liệu gốc (.docx)
├── .gitignore
├── .gitmodules
└── README.md
```

---

## Kiến trúc hệ thống

### Pipeline xử lý

```
┌──────────────────────────┐        ┌──────────────────────────────┐
│ Client (Chrome / Edge)   │  WS    │ FastAPI Server                │
│                          │◄──────►│                              │
│ 🎤 Mic → Web Speech API  │ text   │  Session Flow (7 thử thách)   │
│   nhận diện tiếng Việt   │───────►│      │                       │
│                          │        │      ├─► Pre-cache .wav (tức thì)│
│ 🔊 <audio> phát TTS      │        │      ├─► LLM chấm + reply      │
│   từ /audio/{key}        │◄───────│      │   (logic câu đố + hội thoại)│
│ 🎬 <video> recap + magic │        │      └─► Kokoro TTS → WAV (động)│
└──────────────────────────┘ audio  │           (ONNX CPU)          │
                                    └──────────────────────────────┘
```

### Luồng chấm đáp án (`judge_and_reply`)

1. **Fuzzy match** trước (alias trong `koon_data.py`) → đúng đáp án dự định → dùng **pre-cache right** (nhanh).
2. Nếu không khớp → **LLM** chấm theo **logic câu đố** (accept bất kỳ đáp án hợp lý, vd "ghế" cho "4 chân không đi") + sinh **reply hội thoại**:
   - **Đúng** (đáp án thay thế) → KOON nói reply động xác nhận (vd *"Đúng rồi! Ghế cũng có bốn chân..."*).
   - **Sai** → KOON đáp lại + gợi ý nhẹ, không tiết lộ đáp án, không bịa lý do sai sự thật.
3. **Fallback** (không LLM / lỗi) → fuzzy + template reply.

Câu hỏi chỉ đọc **1 lần** (replay = R để đọc lại); khi sai KOON chỉ phản hồi, không lặp câu hỏi.

### Recap video

Thả bất kỳ `.mp4` nào vào `app/assets/video/` (ưu tiên `recap.mp4`, không thì lấy file đầu theo alphabet) → server tự nhận, KOON "hô biến" rồi phát. Chưa có file → overlay animation "Recap một năm đồng hành".

### TTS Performance

| Độ dài câu | Thời gian gen | Hệ số |
|---|---|---|
| 3 giây nói | ~0.55 giây | 5.4x realtime |
| 10 giây nói | ~2 giây | 5x realtime |

---

## 🔧 Troubleshooting

### "Kokoro Vietnamese chưa cài" khi chạy server

```bash
pip install -e "ref/Kokoro-Vietnamese[onnx]"
```

### Lỗi port đã được dùng (8000 / 8001)

```bash
# Windows: tìm và kill process đang giữ port
netstat -ano | findstr :8000      # Trò 1 ; hoặc :8001 cho Trò 2
taskkill /PID <PID> /F
```
Vd quên tắt server Trò 1 rồi chạy lại → báo `address already in use` → kill theo PID rồi chạy lại.

### Không có OpenRouter key — 2 trò vẫn chạy được không?

Có, nhưng ở chế độ dự phòng:
- **Trò 1**: chấm đáp án bằng **fuzzy match** (so khớp chữ cái) — kém chính xác hơn LLM nhưng vẫn hoạt động.
- **Trò 2**: vision tắt → operator **duyệt đúng/sai bằng tay** (nút *Ép đúng* trên master).

### Mic / STT không nhận giọng nói

- Dùng **Chrome hoặc Edge** (Firefox/Safari có thể không hỗ trợ Web Speech API).
- Cấp quyền mic cho site (icon khoá/mic góc trình duyệt).
- Cần **internet** (STT gửi audio lên Google/Azure).
- Nếu truy cập bằng IP thay vì `localhost` → phải dùng **HTTPS** (browser chỉ cho phép mic trên localhost hoặc HTTPS).
- Bấm **"🧪 Test mic / STT"** ở màn start để kiểm tra nhanh — kết quả hiện kèm engine đang dùng.
- Trên sân khấu nếu STT vẫn nhận sai: operator bấm **F (Ép đúng)** để KOON tiếp tục.

### KOON vẫn là emoji 🦊 (Live2D không hiện)

Avatar Live2D lấy từ `ref/Open-LLM-VTuber/live2d-models/` (thư mục này **gitignore** — không có sau fresh clone). Nếu thiếu, game tự **fallback về emoji 🦊**, vẫn chơi bình thường. Để có avatar:

```bash
git clone https://github.com/Open-LLM-VTuber/Open-LLM-VTuber.git ref/Open-LLM-VTuber
```

Restart server → log hiện `Live2D: /live2d (mao_pro)` và `/health` trả `"live2d": true`. (Model mao_pro = Niziiro Mao, sample Live2D free-material.)

### Giọng đọc bị "robot" / không tự nhiên

Thử đổi giọng:
```cmd
set KOON_VOICE=thuc_trinh
```

Hoặc dùng `storyvert` (giọng kể chuyện, chậm hơn nhưng cảm xúc hơn).

---

## 📚 Tham khảo

- [Kokoro Vietnamese](https://github.com/iamdinhthuan/Kokoro-Vietnamese) — TTS tiếng Việt ONNX CPU
- [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API) — STT trong browser (Chrome=Google / Edge=Azure)
- [Pipecat](https://github.com/pipecat-ai/pipecat) — Real-time voice pipeline framework (future consideration)
- [OpenRouter](https://openrouter.ai/) — Unified LLM API