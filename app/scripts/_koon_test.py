"""Test Trò 1 (KOON Cầu Vồng): WS flow + fuzzy matching + operator controls."""
import sys
import os
import asyncio
import json

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import websockets
import server as S
import koon_data as K


def test_fuzzy_matching():
    print("=== FUZZY MATCHING TEST ===")
    ch = K.CHALLENGES[0]  # dưa hấu
    test_cases = [
        ("dưa hấu", True),
        ("dua hau", True),  # unaccented
        ("trái dưa hấu ạ", True),  # polite phrase
        ("qua dua ho", True),  # typo alias
        ("quả táo", False),  # wrong
    ]
    all_passed = True
    for text, expected in test_cases:
        res = S.judge_fuzzy(text, ch)
        passed = res == expected
        if not passed:
            all_passed = False
        print(f"  '{text}' -> {res} (Kỳ vọng: {expected}) {'✅' if passed else '❌'}")
    return all_passed


async def test_ws_flow():
    print("\n=== KOON WS FLOW TEST ===")
    url = "ws://127.0.0.1:8000/ws"
    async with websockets.connect(url) as ws:
        ready = json.loads(await ws.recv())
        print(f"  Connected: {ready.get('type')}")

        # Start game
        await ws.send(json.dumps({"type": "start"}))
        events = []

        # Read intro messages
        for _ in range(30):
            try:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=15.0))
                events.append(msg.get("type"))
                if msg.get("type") == "play_audio":
                    # Simulate client finishing audio playback
                    await ws.send(json.dumps({"type": "audio_ended"}))
                elif msg.get("type") == "await_answer":
                    print("  Received await_answer!")
                    break
            except asyncio.TimeoutError:
                print("  Waiting for intro...")

        print(f"  Events received during flow: {events[:6]}...")

        # Test answering incorrectly
        print("  Sending wrong answer...")
        await ws.send(json.dumps({"type": "answer", "text": "quả chuối"}))

        got_wrong = False
        for _ in range(15):
            try:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=15.0))
                if msg.get("type") == "wrong_answer":
                    got_wrong = True
                elif msg.get("type") == "play_audio":
                    await ws.send(json.dumps({"type": "audio_ended"}))
                elif msg.get("type") == "await_answer":
                    print("  Received await_answer after wrong answer!")
                    break
            except asyncio.TimeoutError:
                print("  Waiting for wrong answer feedback...")
        print(f"  Received wrong_answer event: {got_wrong} {'✅' if got_wrong else '❌'}")

        # Test answering correctly
        print("  Sending correct answer (dưa hấu)...")
        await ws.send(json.dumps({"type": "answer", "text": "dưa hấu"}))

        got_unlock = False
        for _ in range(15):
            try:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=15.0))
                if msg.get("type") in ("unlock_color", "correct_answer"):
                    got_unlock = True
                elif msg.get("type") == "play_audio":
                    await ws.send(json.dumps({"type": "audio_ended"}))
                elif msg.get("type") == "show_question":
                    print(f"  Question 2 showed AFTER correct unlock: {msg.get('text')[:30]}...")
                    break
            except asyncio.TimeoutError:
                print("  Waiting for correct answer feedback...")
        print(f"  Received unlock_color/correct_answer event: {got_unlock} {'✅' if got_unlock else '❌'}")

        # Reset
        await ws.send(json.dumps({"type": "op", "action": "restart"}))
        print("  Sent restart op ✅")


async def main():
    fuzzy_ok = test_fuzzy_matching()
    try:
        await test_ws_flow()
    except Exception as e:
        print(f"  WS Test skip/error (cần server :8000 đang chạy): {e}")


if __name__ == "__main__":
    asyncio.run(main())
