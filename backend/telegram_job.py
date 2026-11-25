"""RoomKaki Telegram job (GitHub Actions, every 30 min; owner go 2026-11-23).
1) Bot inbox: "/start <token>" links a room alert to the user's chat; "/stop" pauses their alerts.
2) Alerts: DM each linked user new live listings matching their filters.
3) Channel @roomkaki: post each new live listing once, and each newly published guide once.
Env: ROOMKAKI_BOT_TOKEN, ALERTS_JOB_SECRET (GitHub secrets). Uses only the public API key + job secret.
  python backend/telegram_job.py [--dry]
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

_ENV = Path(__file__).resolve().parent / ".env.local"          # PC run: secrets from the gitignored env file
if "ROOMKAKI_BOT_TOKEN" not in os.environ and _ENV.exists():
    for _l in _ENV.read_text(encoding="utf-8").splitlines():
        if "=" in _l and not _l.startswith("#"):
            _k, _v = _l.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

SB = "https://uumiwuvbxzmtxuwmutis.supabase.co"
ANON = "sb_publishable_E2ECaIgR-2fLWAEeDfVnMA_5_balO9b"
SITE = "https://roomkaki.com"
TOKEN = os.environ["ROOMKAKI_BOT_TOKEN"]
SECRET = os.environ["ALERTS_JOB_SECRET"]
CHANNEL = os.environ.get("ROOMKAKI_CHANNEL", "@roomkaki")
DRY = "--dry" in sys.argv
ROOT = Path(__file__).resolve().parent.parent


def http(url, data=None, headers=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
        return json.loads(body) if body else None


def rpc(fn, **args):
    return http(f"{SB}/rest/v1/rpc/{fn}", {"p_secret": SECRET, **args},
                {"apikey": ANON, "Authorization": f"Bearer {ANON}"})


def tg(method, **params):
    if DRY and method in ("sendMessage",):
        print("DRY", method, params.get("chat_id"), str(params.get("text", ""))[:80].replace("\n", " "))
        return {"ok": True}
    return http(f"https://api.telegram.org/bot{TOKEN}/{method}", params)


def esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


HELP = ("🏠 <b>RoomKaki</b> — free rooms for our community in Singapore.\n\n"
        "To get room alerts, choose your area and budget on the website and tap <b>Get alerts on Telegram</b>:\n"
        f"{SITE}\n\nSend /stop to pause your alerts.")


def inbox():
    upd = tg("getUpdates", timeout=0, allowed_updates=["message"]).get("result", [])
    last = None
    for u in upd:
        last = u["update_id"]
        m = u.get("message") or {}
        chat, text = (m.get("chat") or {}).get("id"), (m.get("text") or "").strip()
        if not chat or (m.get("chat") or {}).get("type") != "private":
            continue
        if text.startswith("/start ") and len(text.split()) == 2:
            what = rpc("job_link_alert", p_token=text.split()[1][:40], p_chat=chat)
            tg("sendMessage", chat_id=chat, parse_mode="HTML",
               text=(f"✅ Alert on: <b>{esc(what)}</b>\nI'll message you here when a matching room is posted.\n\nSend /stop to pause."
                     if what else "Sorry, that alert link has expired. Please make a new one on " + SITE))
        elif text == "/stop":
            n = rpc("job_stop_alerts", p_chat=chat)
            tg("sendMessage", chat_id=chat, text=f"⏸ Paused {n or 0} alert(s). Make a new one any time on {SITE}")
        else:
            tg("sendMessage", chat_id=chat, parse_mode="HTML", text=HELP, disable_web_page_preview=True)
    if last is not None and not DRY:
        tg("getUpdates", offset=last + 1, timeout=0)          # confirms them, so Telegram won't resend


def alerts():
    rows = rpc("job_alert_matches") or []
    sent = {}
    for r in rows:
        n = sent.get(r["chat_id"], 0)
        if n < 5:                                           # max 5 messages per person per run
            label = "🙋 Someone is looking for a room" if r["kind"] == "wanted" else "🏠 New room"
            tg("sendMessage", chat_id=r["chat_id"], parse_mode="HTML", disable_web_page_preview=True,
               text=(f"{label}: <b>{esc(r['title'])}</b>\nS${r['price']:,} · {esc(r['area'])}"
                     f"{' · ' + esc(r['station']) + ' MRT' if r['station'] else ''}\n{SITE}/#room-{r['listing_id']}"))
            sent[r["chat_id"]] = n + 1
        if not DRY:
            rpc("job_mark_sent", p_alert=r["alert_id"], p_listing=r["listing_id"])
    print(f"alerts: {len(rows)} matches, {sum(sent.values())} messages")


def channel():
    last = int(rpc("job_get_state", p_key="channel_last_listing") or 0)
    rows = http(f"{SB}/rest/v1/public_listings?select=id,title,price_month,area,station,listing_kind,source_url"
                f"&market_id=eq.sg&id=gt.{last}&order=id.asc&limit=10", headers={"apikey": ANON, "Authorization": f"Bearer {ANON}"})
    for r in rows:
        if r.get("source_url"):
            continue                                        # found listings stay on the site only (not ours to broadcast)
        label = "🙋 Looking for a room" if r["listing_kind"] == "wanted" else "🏠 New room"
        tg("sendMessage", chat_id=CHANNEL, parse_mode="HTML",
           text=(f"{label}\n<b>{esc(r['title'])}</b>\nS${r['price_month']:,} / month · {esc(r['area'])}"
                 f"{' · ' + esc(r['station']) + ' MRT' if r.get('station') else ''}\n\n👉 {SITE}/#room-{r['id']}"))
    if rows and not DRY:
        rpc("job_set_state", p_key="channel_last_listing", p_value=str(rows[-1]["id"]))
    # newest published guide, once
    try:
        g = json.loads((ROOT / "blog" / "latest.json").read_text(encoding="utf-8"))[0]
    except Exception:                                       # noqa: BLE001
        g = None
    posted = False
    if g and rpc("job_get_state", p_key="channel_last_guide") != g["slug"]:
        tg("sendMessage", chat_id=CHANNEL, parse_mode="HTML",
           text=f"📖 <b>{esc(g['title_en'])}</b>\n{esc(g['summary_en'])}\n\n{SITE}/blog/{g['slug']}.html")
        posted = True
        if not DRY:
            rpc("job_set_state", p_key="channel_last_guide", p_value=g["slug"])
    print(f"channel: {len(rows)} new listings checked, guide {'posted' if posted else 'already posted / none'}")


if __name__ == "__main__":
    inbox()
    alerts()
    channel()
    if not DRY:   # heartbeat for the watchdog, whichever machine ran the job (PC every 15 min, GitHub as backup)
        from datetime import datetime, timezone
        rpc("job_set_state", p_key="telegram_last_run", p_value=datetime.now(timezone.utc).isoformat(timespec="seconds"))
