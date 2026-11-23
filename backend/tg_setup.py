"""One-time setup (owner go 2026-11-23): create the RoomKaki bot (via BotFather) and the public RoomKaki
channel, make the bot a channel admin, save token + channel to backend/.env.local. Uses the owner's
Telethon session. Never prints the token.  python backend/tg_setup.py
"""
import asyncio
import os
import re
from pathlib import Path

from telethon import TelegramClient, functions, types

SESSION = r"D:\gamegroove-monitor\_tg_session"
ENV = Path(__file__).resolve().parent / ".env.local"
BOT_NAMES = ["RoomKakiBot", "RoomKakiSGBot", "RoomKaki_Bot", "RoomKakiAlertsBot"]
CH_NAMES = ["roomkaki", "roomkaki_sg", "roomkakisg", "roomkaki_rooms"]
CH_TITLE = "RoomKaki — Rooms in Singapore 🏠"
CH_ABOUT = ("Free room listings for the Myanmar community in Singapore. New rooms, room-wanted posts and renting "
            "tips every day. Post free: https://roomkaki.com")


def save(key, val):
    lines = [l for l in ENV.read_text(encoding="utf-8").splitlines() if not l.startswith(key + "=")]
    ENV.write_text("\n".join(lines + [f"{key}={val}"]) + "\n", encoding="utf-8")


async def ask_botfather(c, text):
    await c.send_message("BotFather", text)
    await asyncio.sleep(3)
    return (await c.get_messages("BotFather", limit=1))[0].message


async def main():
    env = ENV.read_text(encoding="utf-8")
    async with TelegramClient(SESSION, int(os.environ["TG_API_ID"]), os.environ["TG_API_HASH"]) as c:
        if "ROOMKAKI_BOT_TOKEN=" not in env:
            await ask_botfather(c, "/newbot")
            await ask_botfather(c, "RoomKaki")
            token = uname = None
            for u in BOT_NAMES:
                r = await ask_botfather(c, u)
                m = re.search(r"\d{8,12}:[A-Za-z0-9_-]{30,}", r)
                if m:
                    token, uname = m.group(0), u
                    break
            if not token:
                raise SystemExit("BotFather did not give a token (all usernames taken?)")
            save("ROOMKAKI_BOT_TOKEN", token); save("ROOMKAKI_BOT", uname)
            print("bot created:", uname)
        else:
            uname = re.search(r"ROOMKAKI_BOT=(\S+)", env).group(1)
            print("bot exists:", uname)

        if "ROOMKAKI_CHANNEL=" not in ENV.read_text(encoding="utf-8"):
            res = await c(functions.channels.CreateChannelRequest(title=CH_TITLE, about=CH_ABOUT, broadcast=True))
            ch = res.chats[0]
            chosen = None
            for n in CH_NAMES:
                try:
                    await c(functions.channels.UpdateUsernameRequest(channel=ch, username=n))
                    chosen = n
                    break
                except Exception:                       # noqa: BLE001 — username taken/invalid, try next
                    continue
            bot = await c.get_entity(uname)
            await c(functions.channels.EditAdminRequest(
                channel=ch, user_id=bot, rank="RoomKaki",
                admin_rights=types.ChatAdminRights(post_messages=True, edit_messages=True, delete_messages=True)))
            save("ROOMKAKI_CHANNEL", "@" + chosen if chosen else str(ch.id))
            print("channel created:", "@" + chosen if chosen else f"private id {ch.id}")
        else:
            print("channel exists")

asyncio.run(main())
