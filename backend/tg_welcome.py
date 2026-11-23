"""Post + pin the @roomkaki channel welcome. Burmese written natively by Gemini (owner rule 11-21), saved to
BURMESE_NATIVE. Run once.  python backend/tg_welcome.py"""
import json
import os
import sys
import unicodedata
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, r"D:\_tmp\gg\episodes")
import tts_gemini as T  # noqa: E402

EN = ("Welcome to RoomKaki 🏠 — free room listings for the Myanmar community in Singapore.\n\n"
      "Here you'll get new rooms, people looking for rooms, and one renting tip a day.\n"
      "• Post your room free: https://roomkaki.com\n"
      "• Get alerts for your area: open the site, choose area + budget, tap “Get alerts on Telegram”\n"
      "• Never pay a deposit before viewing the room in person.")
PROMPT = ("You are a native Burmese writer. Write this Telegram channel welcome in natural, friendly everyday Burmese "
          "(Myanmar Unicode, not Zawgyi), the way a Myanmar person would say it, not word-by-word. Keep the links, "
          "RoomKaki and the quoted button name in English. Output ONLY the Burmese text.\n\n" + EN)


def gemini():
    for key in T.keys():
        for model in ("gemini-3.5-flash", "gemini-3.8-flash"):
            try:
                req = urllib.request.Request(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
                    data=json.dumps({"contents": [{"parts": [{"text": PROMPT}]}]}).encode(),
                    headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    return unicodedata.normalize("NFC", json.load(r)["candidates"][0]["content"]["parts"][0]["text"].strip()), model
            except Exception:                                    # noqa: BLE001
                continue
    raise SystemExit("no Gemini key worked")


my, model = gemini()
assert any("\u1000" <= c <= "\u109f" for c in my) and not any(0x1060 <= ord(c) <= 0x1097 for c in my)
(Path(r"D:\progress-ledger\BURMESE_NATIVE") / f"{date.today().isoformat()}_roomkaki_tg_welcome.txt").write_text(
    f"[Gemini {model}]\n{my}\n", encoding="utf-8")
tok, ch = os.environ["ROOMKAKI_BOT_TOKEN"], os.environ.get("ROOMKAKI_CHANNEL", "@roomkaki")


def tg(method, **p):
    req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/{method}", data=json.dumps(p).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))


r = tg("sendMessage", chat_id=ch, text=EN + "\n\n" + my, disable_web_page_preview=True)
print("posted:", r.get("ok"), "message_id", r.get("result", {}).get("message_id"))
print("pinned:", tg("pinChatMessage", chat_id=ch, message_id=r["result"]["message_id"], disable_notification=True).get("ok"))
