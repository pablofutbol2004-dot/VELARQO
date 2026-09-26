import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "velarqo.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS lead (
    id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    website TEXT,
    email TEXT,
    phone TEXT,
    postcode TEXT,
    lead_source TEXT,
    created_at TEXT NOT NULL,
    last_contact TEXT,
    normalized INTEGER DEFAULT 0,
    enriched INTEGER DEFAULT 0,
    duplicate_of TEXT,
    icp_score REAL,
    research_summary TEXT,
    angle TEXT,
    campaign_id TEXT,
    ghl_contact_id TEXT
);

CREATE TABLE IF NOT EXISTS experiment_result (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    lead_id TEXT NOT NULL,
    company_name TEXT NOT NULL,
    vertical TEXT,
    segment TEXT,
    message_variant INTEGER,
    offer TEXT,
    send_time TEXT NOT NULL,
    send_day TEXT,
    opened INTEGER DEFAULT 0,
    reply INTEGER DEFAULT 0,
    reply_sentiment TEXT,
    appointment_booked INTEGER DEFAULT 0,
    appointment_date TEXT,
    quote_requested INTEGER DEFAULT 0,
    quote_value REAL,
    quote_date TEXT,
    sale_closed INTEGER DEFAULT 0,
    revenue REAL,
    revenue_date TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_experiment_campaign_variant
    ON experiment_result (campaign_id, message_variant);
CREATE INDEX IF NOT EXISTS idx_experiment_segment_sentiment
    ON experiment_result (segment, reply_sentiment);
CREATE INDEX IF NOT EXISTS idx_lead_company
    ON lead (company_name);
"""


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | None = None) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
