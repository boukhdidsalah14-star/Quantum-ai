CREATE TABLE IF NOT EXISTS leads (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, company TEXT DEFAULT '', email TEXT DEFAULT '', source TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'New', notes TEXT DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at DESC);
CREATE TABLE IF NOT EXISTS campaigns (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, audience TEXT DEFAULT '', message TEXT DEFAULT '', approved INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS activity (
 id TEXT PRIMARY KEY, event TEXT NOT NULL, detail TEXT DEFAULT '', created_at TEXT NOT NULL
);