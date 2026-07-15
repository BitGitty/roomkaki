#!/usr/bin/env python3
"""Apply a .sql file to the RoomKaki Supabase Postgres (session pooler, IPv4, SSL).
Usage: python run_sql.py rls.sql   |   python run_sql.py -c "SQL text"
Reads DB creds from backend/.env.local. Never commit .env.local.
"""
import os, sys, ssl, pathlib, psycopg2

env = {}
for line in (pathlib.Path(__file__).parent / ".env.local").read_text().splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, _, v = line.partition("="); env[k.strip()] = v.strip()

REF = env["SUPABASE_PROJECT_REF"]
PW = env["SUPABASE_DB_PASSWORD"]
# Session-mode pooler is IPv4-reachable; try aws-0 then aws-1 for the region.
HOSTS = ["aws-0-ap-southeast-1.pooler.supabase.com", "aws-1-ap-southeast-1.pooler.supabase.com",
         f"db.{REF}.supabase.co"]

if len(sys.argv) >= 3 and sys.argv[1] == "-c":
    sql = sys.argv[2]
else:
    sql = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")

last = None
for host in HOSTS:
    try:
        user = "postgres" if host.startswith("db.") else f"postgres.{REF}"
        conn = psycopg2.connect(host=host, port=5432, user=user, password=PW,
                                dbname="postgres", sslmode="require", connect_timeout=10)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql)
            print(f"OK via {host}  (statusmessage: {cur.statusmessage})")
        conn.close()
        sys.exit(0)
    except Exception as e:
        last = e
        print(f"  {host}: {type(e).__name__}: {str(e).splitlines()[0]}")
print("FAILED on all hosts:", last)
sys.exit(1)
