@echo off
rem Daily database backup (14 kept in dataackups). Copy the newest one off this PC regularly.
cd /d D:elarqo
call scripts\wait_for_db.cmd || exit /b 1
.venv\Scripts\python.exe scriptsackup_db.py >> dataackup.log 2>&1
