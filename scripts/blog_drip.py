"""RoomKaki daily blog drip (pattern copied from rightsatlas/scripts/drip_publish.py).

blog/pending/ holds finished posts; this moves the OLDEST one into blog/posts/ once per
day so the blog grows daily. Run by the nightly workflow before blog_build.py.

  python scripts/blog_drip.py        # release today's post (if any pending)
"""
import json
import shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PENDING = ROOT / "blog" / "pending"
POSTS = ROOT / "blog" / "posts"
STATE = ROOT / "blog" / "drip_state.json"


def release_one(today: str) -> str | None:
    st = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    if st.get("last_release") == today:
        return None
    pend = sorted(PENDING.glob("*.json"))
    if not pend:
        return None
    pick = pend[0]
    post = json.loads(pick.read_text(encoding="utf-8"))
    post["date"] = today
    (POSTS / pick.name).write_text(json.dumps(post, ensure_ascii=False, indent=1), encoding="utf-8")
    pick.unlink()
    st["last_release"] = today
    st.setdefault("log", []).append({"date": today, "post": pick.stem})
    STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")
    return pick.stem


def main() -> int:
    PENDING.mkdir(parents=True, exist_ok=True)
    POSTS.mkdir(parents=True, exist_ok=True)
    released = release_one(date.today().isoformat())
    left = len(list(PENDING.glob("*.json")))
    print(f"blog drip: released {released} ({left} pending left)" if released
          else f"blog drip: nothing today (already dripped or queue empty; {left} pending)")
    if left <= 2:
        print("blog drip: WARNING queue low — write more posts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
