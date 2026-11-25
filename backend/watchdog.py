"""RoomKaki watchdog — GitHub Actions, independent of the owner's PC (pattern: rightsatlas/scripts/watchdog.py).
Silence must never look like "all fine": checks everything that can fail quietly and messages the owner on
Telegram (@RoomKakiBot) only when something is wrong.
  python backend/watchdog.py           # check + alert (env: ROOMKAKI_BOT_TOKEN, OWNER_CHAT_ID, ALERTS_JOB_SECRET, GITHUB_TOKEN)
  python backend/watchdog.py --check   # offline self-test of the rules
"""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_ENV = ROOT / "backend" / ".env.local"           # PC run: secrets from the gitignored env file + owner id file
if "ALERTS_JOB_SECRET" not in os.environ and _ENV.exists():
    for _l in _ENV.read_text(encoding="utf-8").splitlines():
        if "=" in _l and not _l.startswith("#"):
            _k, _v = _l.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())
    _oid = ROOT / "backend" / ".owner_tg_id"
    if _oid.exists():
        os.environ.setdefault("OWNER_CHAT_ID", _oid.read_text(encoding="utf-8").strip())
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
    tok, chat = os.environ.get("ROOMKAKI_BOT_TOKEN"), os.environ.get("OWNER_CHAT_ID")
    removed = check_found()
    if removed:
        print("found listings removed (source gone):", removed)
    # Monday owner to-do reminder, once per Monday even with two runners (PC + GitHub)
    now = datetime.now(timezone.utc)
    todo = json.loads((ROOT / "backend" / "owner_todo.json").read_text(encoding="utf-8")).get("items", [])
    monday_sgt = (now + timedelta(hours=8)).weekday() == 0
    if todo and ((monday_sgt and state("reminder_last") != now.date().isoformat()) or "--remind" in sys.argv):
        msg = "📋 RoomKaki — things only you can do this week:\n\n" + "\n\n".join(f"{i}. {t}" for i, t in enumerate(todo, 1))
        print(msg)
        if tok and chat:
            get(f"https://api.telegram.org/bot{tok}/sendMessage", data={"chat_id": chat, "text": msg, "disable_web_page_preview": True})
            state("reminder_last", now.date().isoformat())
    summary = (f"site {'ok' if f.get('site_ok') else 'DOWN'} · db {'ok' if f.get('db_ok') else 'DOWN'} · last guide "
               f"{f.get('last_release')} · queue {f.get('ready_guides')} · pending {f.get('pending', '?')} · "
               f"telegram job {('%.1f h ago' % f['tg_age_h']) if f.get('tg_age_h') is not None else '?'}")
    print(summary)
    if not found:
        print("watchdog OK")
        return 0
    text = "RoomKaki WATCHDOG — needs attention\n\n" + "\n".join(found) + "\n\n" + summary
    print(text)
    # same problems already reported in the last 6 h (by either runner) → don't repeat
    sig = "|".join(sorted(p.split(" ")[0] + p.split(" ")[2] for p in found))
    prev = state("alert_last") or ""
    try:
        recent = prev.startswith(sig + "@") and (now - datetime.fromisoformat(prev.split("@", 1)[1])) < timedelta(hours=6)
    except ValueError:
        recent = False
    if tok and chat and not recent:
        get(f"https://api.telegram.org/bot{tok}/sendMessage", data={"chat_id": chat, "text": text})
        state("alert_last", f"{sig}@{now.isoformat(timespec='seconds')}")
    return 1


def state(key, value=None):
    """Shared memory between the PC and GitHub runners (job_state, secret-guarded)."""
    sec = os.environ.get("ALERTS_JOB_SECRET")
    if not sec:
        return None
    try:
        fn, body = ("job_set_state", {"p_secret": sec, "p_key": key, "p_value": value}) if value is not None \
            else ("job_get_state", {"p_secret": sec, "p_key": key})
        _, b = get(f"{SB}/rest/v1/rpc/{fn}", {"apikey": ANON, "Authorization": f"Bearer {ANON}"}, body)
        return json.loads(b) if b else None
    except Exception:                                                # noqa: BLE001
        return None


def check_found():
    """Found listings link to someone else's post: if that post is gone (404/410), take ours down."""
    sec = os.environ.get("ALERTS_JOB_SECRET")
    if not sec:
        return []
    h = {"apikey": ANON, "Authorization": f"Bearer {ANON}"}
    try:
        _, b = get(f"{SB}/rest/v1/rpc/job_found_listings", h, {"p_secret": sec})
        rows = json.loads(b) or []
    except Exception:                                                # noqa: BLE001
        return []
    gone = []
    for r in rows:
        if source_gone(r["source_url"]):
            get(f"{SB}/rest/v1/rpc/job_remove_found", h, {"p_secret": sec, "p_id": r["id"]})
            gone.append(r["id"])
    return gone


SOFT_404 = ("not found", "no longer available", "has been removed", "does not exist", "expired", "404")


def source_gone(url):
    """True only when we're sure: 404/410, a redirect away from the listing's own page (99.co sends deleted rooms
    elsewhere with a 308), or a 'no longer available' page. Network errors / 5xx → keep (never remove on doubt)."""
    from urllib.parse import urlparse
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30)
        body = resp.read(200000).decode("utf-8", "replace").lower()
    except urllib.error.HTTPError as e:
        return e.code in (404, 410)
    except Exception:                                                # noqa: BLE001
        return False
    if urlparse(resp.geturl()).path.rstrip("/") != urlparse(url).path.rstrip("/"):
        return True
    # page title only (BurmaSpaces: "Room not found | Burma Spaces"); whole-body matching risks false removals
    import re
    m = re.search(r"<title[^>]*>(.*?)</title>", body, re.S)
    return bool(m) and any(s in m.group(1) for s in SOFT_404)


if __name__ == "__main__":
    sys.exit(main())
