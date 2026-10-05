@echo off
rem One outbound tick: inbox sync, follow-ups, stop rules, sends. Schedule every 15 min.
cd /d D:\velarqo
call scripts\wait_for_db.cmd || exit /b 1
.venv\Scripts\python.exe -m pipelines.outbound run >> data\outbound.log 2>&1
