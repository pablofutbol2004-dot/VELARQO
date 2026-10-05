@echo off
rem Waits up to ~5 minutes for the velarqo-postgres container (Docker Desktop starts at login, the DB a bit later).
for /l %%i in (1,1,60) do (
  docker exec velarqo-postgres pg_isready -U postgres -d velarqo >nul 2>&1 && exit /b 0
  timeout /t 5 /nobreak >nul
)
echo velarqo-postgres not ready after 5 minutes
exit /b 1
