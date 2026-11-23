"""E2E test of room alerts with a real Telegram user (owner's session): create alert via the public RPC,
/start the bot, run the job, read the bot's reply, then /stop and delete the test alert.
  python backend/tg_e2e_test.py"""
import asyncio
import json
import os
import subprocess
import sys
import urllib.request

from telethon import TelegramClient

SB, ANON = "https://uumiwuvbxzmtxuwmutis.supabase.co", "sb_publishable_E2ECaIgR-2fLWAEeDfVnMA_5_balO9b"


def create_alert():
    req = urllib.request.Request(f"{SB}/rest/v1/rpc/create_alert", data=json.dumps(
        {"p_market": "sg", "p_kind": "offer", "p_query": "e2e-test-woodlands", "p_max_price": 700}).encode(),
        headers={"apikey": ANON, "Authorization": f"Bearer {ANON}", "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))


def run_job():
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "telegram_job.py")],
                       capture_output=True, text=True, encoding="utf-8")
    print("job:", (r.stdout + r.stderr).strip()[-200:])


async def main():
    token = create_alert()
    async with TelegramClient(r"D:\gamegroove-monitor\_tg_session", int(os.environ["TG_API_ID"]), os.environ["TG_API_HASH"]) as c:
        await c.send_message("RoomKakiBot", f"/start {token}")
        await asyncio.sleep(2)
        run_job()
        await asyncio.sleep(3)
        reply = (await c.get_messages("RoomKakiBot", limit=1))[0].message
        print("bot reply to /start:", reply.replace("\n", " ")[:120])
        ok_start = "Alert on" in reply and "e2e-test-woodlands" in reply
        await c.send_message("RoomKakiBot", "/stop")
        await asyncio.sleep(2)
        run_job()
        await asyncio.sleep(3)
        reply2 = (await c.get_messages("RoomKakiBot", limit=1))[0].message
        print("bot reply to /stop:", reply2[:80])
        ok_stop = "Paused 1" in reply2
    print("E2E:", "PASS" if ok_start and ok_stop else "FAIL")
    return token

tok = asyncio.run(main())
subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "run_sql.py"), "-c",
                f"DELETE FROM room_alerts WHERE token = '{tok}'"], capture_output=True)
