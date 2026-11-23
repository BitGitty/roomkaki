"""Weekly backup of RoomKaki's own tables to D:/roomkaki-backups (NOT in the public repo).
Supabase free plan has no downloadable backups — this is the restore point if the database is wiped or abused.
Keeps the newest 12 backups.  python backend/backup_db.py"""
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import psycopg2

OUT = Path(r"D:\roomkaki-backups")


def connect():
    """Same credentials and pooler fallbacks as run_sql.py (backend/.env.local, never committed)."""
    env = dict(l.split("=", 1) for l in (Path(__file__).resolve().parent / ".env.local").read_text(encoding="utf-8").splitlines()
               if "=" in l and not l.startswith("#"))
    ref, pw = env["SUPABASE_PROJECT_REF"].strip(), env["SUPABASE_DB_PASSWORD"].strip()
    last = None
    for host in ["aws-0-ap-southeast-1.pooler.supabase.com", "aws-1-ap-southeast-1.pooler.supabase.com", f"db.{ref}.supabase.co"]:
        try:
            return psycopg2.connect(host=host, port=5432, user="postgres" if host.startswith("db.") else f"postgres.{ref}",
                                    password=pw, dbname="postgres", sslmode="require", connect_timeout=10)
        except psycopg2.Error as e:
            last = e
    raise SystemExit(f"backup: could not connect ({type(last).__name__})")
TABLES = ["listings", "listing_photos", "profiles", "reports", "favorites", "contact_reveals",
          "room_alerts", "markets", "job_state", "site_suggestions"]


def enc(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if isinstance(o, Decimal):
        return float(o)
    return str(o)


def main():
    OUT.mkdir(exist_ok=True)
    conn = connect()
    dump, counts = {}, {}
    with conn, conn.cursor() as cur:
        for t in TABLES:
            try:
                cur.execute(f"select * from {t}" + (" where site = 'roomkaki'" if t == "site_suggestions" else ""))
                cols = [d[0] for d in cur.description]
                dump[t] = [dict(zip(cols, r)) for r in cur.fetchall()]
                counts[t] = len(dump[t])
            except psycopg2.Error as e:
                conn.rollback()
                counts[t] = f"skipped ({e.pgcode})"
    f = OUT / f"roomkaki_{date.today().isoformat()}.json"
    f.write_text(json.dumps({"made": datetime.now().isoformat(), "counts": counts, "tables": dump},
                            default=enc, ensure_ascii=False), encoding="utf-8")
    for old in sorted(OUT.glob("roomkaki_*.json"))[:-12]:
        old.unlink()
    line = f"{datetime.now().isoformat(timespec='seconds')} backup written: {f.name} ({f.stat().st_size // 1024} KB) {counts}"
    print(line)
    with open(OUT / "backup.log", "a", encoding="utf-8") as lg:   # scheduled runs are windowless: the log is the proof
        lg.write(line + "\n")


if __name__ == "__main__":
    main()
