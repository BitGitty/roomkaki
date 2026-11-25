"""RoomKaki watchdog — GitHub Actions, independent of the owner's PC (pattern: rightsatlas/scripts/watchdog.py).
Silence must never look like "all fine": checks everything that can fail quietly and messages the owner on
Telegram (@RoomKakiBot) only when something is wrong.
  python backend/watchdog.py           # check + alert (env: ROOMKAKI_BOT_TOKEN, OWNER_CHAT_ID, ALERTS_JOB_SECRET, GITHUB_TOKEN)
  python backend/watchdog.py --check   # offline self-test of the rules
"""
import json
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SB, ANON = "https://uumiwuvbxzmtxuwmutis.supabase.co", "sb_publishable_E2ECaIgR-2fLWAEeDfVnMA_5_balO9b"
REPO = "BitGitty/roomkaki"


def rules(f: dict) -> list:
    """f = facts gathered; returns plain-English problems (empty = healthy)."""
    out = []
    if not f.get("site_ok"):
        out.append("🔴 roomkaki.com is not loading properly")
    if not f.get("db_ok"):
        out.append("🔴 the database is not answering — listings won't show")
    if f.get("last_release") and f["last_release"] < (f["today"] - timedelta(days=2)).isoformat():
        out.append(f"🟠 no guide published since {f['last_release']} — the daily blog has stopped")
    if f.get("ready_guides", 99) <= 3:
        out.append(f"🟠 only {f.get('ready_guides')} guides left in the queue — write the next batch")
    if f.get("pending_hours") is not None and f["pending_hours"] >= 12:
        out.append(f"🟠 {f['pending']} new post(s) waiting for approval, oldest {f['pending_hours']:.0f} h — approve or reject")
    if f.get("tg_age_h") is not None and f["tg_age_h"] > 3:
        out.append(f"🟠 the Telegram job (alerts + channel) last ran {f['tg_age_h']:.0f} h ago")
    if f.get("market_months_old", 0) > 3:
        out.append(f"🟡 market data is {f['market_months_old']} months old — the monthly refresh may be failing")
    return out


def get(url, headers=None, data=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"User-Agent": "RoomKaki-watchdog", "Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read()


def gather() -> dict:
    f = {"today": date.today()}
    try:
        s, b = get("https://roomkaki.com/")
        f["site_ok"] = s == 200 and b"RoomKaki" in b
    except Exception:                                                # noqa: BLE001
        f["site_ok"] = False
    try:
        s, _ = get(f"{SB}/rest/v1/public_listings?select=id&limit=1", {"apikey": ANON, "Authorization": f"Bearer {ANON}"})
        f["db_ok"] = s == 200
    except Exception:                                                # noqa: BLE001
        f["db_ok"] = False
    drip = json.loads((ROOT / "blog" / "drip_state.json").read_text(encoding="utf-8"))
    f["last_release"] = drip.get("last_release")
    f["ready_guides"] = sum(1 for p in (ROOT / "blog" / "pending").glob("*.json")
                            if json.loads(p.read_text(encoding="utf-8")).get("my_review") == "gemini-native")
    sec = os.environ.get("ALERTS_JOB_SECRET")
    if sec:
        try:
            _, b = get(f"{SB}/rest/v1/rpc/job_health", {"apikey": ANON, "Authorization": f"Bearer {ANON}"}, {"p_secret": sec})
            h = json.loads(b)[0]
            f["pending"], f["pending_hours"] = h["pending"], (float(h["oldest_pending_hours"]) if h["oldest_pending_hours"] else None)
        except Exception:                                            # noqa: BLE001
            f["db_ok"] = False
    # Telegram job heartbeat (written by the job itself — PC task every 15 min, GitHub hourly as backup)
    if sec:
        try:
            _, b = get(f"{SB}/rest/v1/rpc/job_get_state", {"apikey": ANON, "Authorization": f"Bearer {ANON}"},
                       {"p_secret": sec, "p_key": "telegram_last_run"})
            last = json.loads(b)
            f["tg_age_h"] = ((datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds() / 3600) if last else 999
        except Exception:                                            # noqa: BLE001
            pass
    try:
        m = json.loads((ROOT / "market" / "market.json").read_text(encoding="utf-8"))["rent_latest"]
        y, mo = map(int, m.split("-"))
        f["market_months_old"] = (f["today"].year - y) * 12 + f["today"].month - mo
    except Exception:                                                # noqa: BLE001
        f["market_months_old"] = 99
    return f


def main() -> int:
    if "--check" in sys.argv:
        t = date(2026, 11, 24)
        ok = {"today": t, "site_ok": True, "db_ok": True, "last_release": "2026-11-24", "ready_guides": 50,
              "pending": 0, "pending_hours": None, "tg_age_h": 0.5, "market_months_old": 1}
        assert rules(ok) == [], rules(ok)
        assert len(rules({**ok, "site_ok": False})) == 1
        assert len(rules({**ok, "last_release": "2026-11-20"})) == 1, "stale blog must alert"
        assert len(rules({**ok, "pending": 2, "pending_hours": 13})) == 1, "unapproved posts must alert"
        assert len(rules({**ok, "pending": 1, "pending_hours": 2})) == 0, "fresh pending is fine"
        assert len(rules({**ok, "tg_age_h": 5})) == 1, "stalled Telegram job must alert"
        assert len(rules({**ok, "ready_guides": 2})) == 1, "low queue must alert"
        print("watchdog self-check passed (7 rules)")
        return 0
    f = gather()
    found = rules(f)
    # Monday-morning owner to-do reminder (owner 11-23: "leave those that need me and remind me again")
    now = datetime.now(timezone.utc)
    todo = json.loads((ROOT / "backend" / "owner_todo.json").read_text(encoding="utf-8")).get("items", [])
    if todo and (now.weekday() == 0 and now.hour < 6 or "--remind" in sys.argv):   # first run on Monday SGT morning
        tok, chat = os.environ.get("ROOMKAKI_BOT_TOKEN"), os.environ.get("OWNER_CHAT_ID")
        msg = "📋 RoomKaki — things only you can do this week:\n\n" + "\n\n".join(f"{i}. {t}" for i, t in enumerate(todo, 1))
        print(msg)
        if tok and chat:
            get(f"https://api.telegram.org/bot{tok}/sendMessage", data={"chat_id": chat, "text": msg, "disable_web_page_preview": True})
    summary = (f"site {'ok' if f.get('site_ok') else 'DOWN'} · db {'ok' if f.get('db_ok') else 'DOWN'} · last guide "
               f"{f.get('last_release')} · queue {f.get('ready_guides')} · pending {f.get('pending', '?')} · "
               f"telegram job {('%.1f h ago' % f['tg_age_h']) if f.get('tg_age_h') is not None else '?'}")
    print(summary)
    if not found:
        print("watchdog OK")
        return 0
    text = "RoomKaki WATCHDOG — needs attention\n\n" + "\n".join(found) + "\n\n" + summary
    print(text)
    tok, chat = os.environ.get("ROOMKAKI_BOT_TOKEN"), os.environ.get("OWNER_CHAT_ID")
    if tok and chat:
        get(f"https://api.telegram.org/bot{tok}/sendMessage", data={"chat_id": chat, "text": text})
    return 1


if __name__ == "__main__":
    sys.exit(main())
