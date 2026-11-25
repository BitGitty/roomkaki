"""Adds the weekly RoomKaki DB backup to the PC's headless task runner (D:/shared-tools/taskrun/tasks.json).
The scheduled task itself is created by register_backup_task.ps1 (conhost --headless + taskrun.py)."""
import io
import json

P = r"D:\shared-tools\taskrun\tasks.json"
t = json.load(io.open(P, encoding="utf-8"))
t["RoomKakiDbBackup"] = {"cmdline": r"C:\Python314\python.exe D:\roomkaki\backend\backup_db.py",
                         "cwd": r"D:\roomkaki\backend", "path": "\\", "limit_s": 600}
# GitHub runs "every 30 min" schedules only ~every 10 h on small repos (seen 11-24): PC is the primary runner
t["RoomKakiTelegramJob"] = {"cmdline": r"C:\Python314\python.exe D:\roomkaki\backend\telegram_job.py",
                            "cwd": r"D:\roomkaki\backend", "path": "\\", "limit_s": 240}
# watchdog on the PC too (GitHub stays as the PC-independent backup); alerts are de-duplicated via job_state
t["RoomKakiWatchdog"] = {"cmdline": r"C:\Python314\python.exe D:\roomkaki\backend\watchdog.py",
                         "cwd": r"D:\roomkaki\backend", "path": "\\", "limit_s": 300}
io.open(P, "w", encoding="utf-8").write(json.dumps(t, indent=1, ensure_ascii=False))
print("tasks.json entries:", json.dumps({k: t[k] for k in ("RoomKakiDbBackup", "RoomKakiTelegramJob", "RoomKakiWatchdog")}))
