"""Save a secret (API key, token) into D:/velarqo/.env without it appearing
on screen or in chat.

    .venv\\Scripts\\python.exe scripts\\set_secret.py INSTANTLY_API_KEY
"""

import sys
from getpass import getpass
from pathlib import Path

from dotenv import set_key

ENV_PATH = Path(__file__).parents[1] / ".env"

if len(sys.argv) != 2:
    raise SystemExit("usage: set_secret.py NAME")

name = sys.argv[1]
value = getpass(f"Paste {name} (hidden) and press Enter: ").strip()
if not value:
    raise SystemExit("Nothing pasted, nothing saved.")
set_key(str(ENV_PATH), name, value)
print(f"Saved {name} to .env ({len(value)} characters).")
