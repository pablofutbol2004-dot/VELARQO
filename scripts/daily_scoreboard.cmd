@echo off
rem The 20:00 scoreboard: print, save data\scoreboard_<day>.csv, push/email it (once a day).
rem Schedule daily at 20:05 UK in Task Scheduler. The 15-minute outbound tick also
rem sends it if it runs after 20:00, so this is the belt and braces.
cd /d D:\velarqo
call scripts\wait_for_db.cmd || exit /b 1
.venv\Scripts\python.exe -m pipelines.outbound scoreboard --csv --notify >> data\outbound.log 2>&1
