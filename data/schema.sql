-- WASTE Master Brain Database Schema
-- Extended schema for waste intelligence platform

-- Properties table (core entity)
CREATE TABLE IF NOT EXISTS properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    property_type TEXT CHECK(property_type IN ('garden', 'mid-rise', 'high-rise', 'townhome', 'mixed')),
    unit_count INTEGER,
    region TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Vector storage for semantic search
CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL CHECK(source_type IN ('email', 'invoice', 'contract', 'note')),
    source_id TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding BLOB NOT NULL,    -- Gemini embedding (768 dims, stored as binary)
    metadata TEXT,              -- JSON metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_embeddings_source ON embeddings(source_type, source_id);

-- Rate history (for pricing trends KPI)
CREATE TABLE IF NOT EXISTS rate_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER REFERENCES properties(id),
    vendor TEXT NOT NULL,
    service_type TEXT NOT NULL CHECK(service_type IN ('compactor', 'dumpster', 'recycling', 'organics', 'bulky')),
    rate_type TEXT NOT NULL CHECK(rate_type IN ('haul_fee', 'disposal_per_ton', 'rental', 'fuel_surcharge', 'environmental_fee', 'admin_fee', 'contamination_fee')),
    rate_value DECIMAL(10,2) NOT NULL,
    effective_date DATE NOT NULL,
    region TEXT,
    source_document TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_rate_history_vendor ON rate_history(vendor);
CREATE INDEX IF NOT EXISTS idx_rate_history_property ON rate_history(property_id);
CREATE INDEX IF NOT EXISTS idx_rate_history_date ON rate_history(effective_date);

-- KPI history (for trend tracking)
CREATE TABLE IF NOT EXISTS kpi_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL REFERENCES properties(id),
    period TEXT NOT NULL,       -- YYYY-MM
    cost_per_door DECIMAL(10,2),
    yards_per_door DECIMAL(10,2),
    contamination_rate DECIMAL(5,4),
    fee_burden_pct DECIMAL(5,2),
    tons_per_haul DECIMAL(10,2),
    hauls_per_month INTEGER,
    total_cost DECIMAL(10,2),
    source_invoice_id TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(property_id, period)
);
CREATE INDEX IF NOT EXISTS idx_kpi_history_period ON kpi_history(period);

-- Hauler intelligence (from emails)
CREATE TABLE IF NOT EXISTS hauler_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_name TEXT NOT NULL UNIQUE,
    avg_response_days DECIMAL(5,2),
    dispute_rate DECIMAL(5,4),
    negotiation_notes TEXT,
    contact_info TEXT,          -- JSON: [{name, email, phone, role}]
    service_regions TEXT,       -- JSON: ["region1", "region2"]
    strengths TEXT,
    weaknesses TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Invoices table (extraction results)
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER REFERENCES properties(id),
    vendor TEXT NOT NULL,
    invoice_number TEXT,
    invoice_date DATE,
    service_period_start DATE,
    service_period_end DATE,
    total_amount DECIMAL(10,2),
    haul_count INTEGER,
    tons_total DECIMAL(10,2),
    base_service_cost DECIMAL(10,2),
    disposal_cost DECIMAL(10,2),
    fees_total DECIMAL(10,2),
    fees_breakdown TEXT,        -- JSON breakdown
    source_file TEXT,
    extraction_json TEXT,       -- Full WasteWise extraction
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_invoices_property ON invoices(property_id);
CREATE INDEX IF NOT EXISTS idx_invoices_vendor ON invoices(vendor);
CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date);

-- Contracts table
CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER REFERENCES properties(id),
    vendor TEXT NOT NULL,
    contract_type TEXT CHECK(contract_type IN ('waste', 'recycling', 'combined', 'special')),
    start_date DATE,
    end_date DATE,
    auto_renewal BOOLEAN DEFAULT 0,
    renewal_notice_days INTEGER,
    termination_notice_days INTEGER,
    rate_increase_cap DECIMAL(5,2),
    key_terms TEXT,             -- JSON: important clauses
    risk_factors TEXT,          -- JSON: identified risks
    source_file TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Email knowledge index
CREATE TABLE IF NOT EXISTS email_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id TEXT NOT NULL UNIQUE,
    date_sent DATETIME,
    subject TEXT,
    sender TEXT,
    recipients TEXT,            -- JSON array
    body_preview TEXT,
    thread_id TEXT,
    vendors_mentioned TEXT,     -- JSON array
    properties_mentioned TEXT,  -- JSON array
    issue_types TEXT,           -- JSON array: ["contamination", "billing", "service"]
    sentiment TEXT CHECK(sentiment IN ('positive', 'negative', 'neutral')),
    action_required BOOLEAN DEFAULT 0,
    source_file TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_email_date ON email_index(date_sent);
CREATE INDEX IF NOT EXISTS idx_email_thread ON email_index(thread_id);

-- Analytics cache (pre-computed metrics)
CREATE TABLE IF NOT EXISTS analytics_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_type TEXT NOT NULL,
    dimension TEXT,             -- e.g., "vendor:WM", "region:Sacramento"
    period TEXT,                -- YYYY-MM or YYYY
    value DECIMAL(10,4),
    metadata TEXT,              -- JSON additional context
    computed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(metric_type, dimension, period)
);

-- Views for common queries
CREATE VIEW IF NOT EXISTS v_property_kpis AS
SELECT
    p.id as property_id,
    p.name as property_name,
    p.property_type,
    p.unit_count,
    p.region,
    k.period,
    k.cost_per_door,
    k.yards_per_door,
    k.contamination_rate,
    k.fee_burden_pct,
    k.total_cost
FROM properties p
LEFT JOIN kpi_history k ON p.id = k.property_id
ORDER BY p.name, k.period DESC;

CREATE VIEW IF NOT EXISTS v_rate_trends AS
SELECT
    vendor,
    service_type,
    rate_type,
    region,
    strftime('%Y-%m', effective_date) as period,
    AVG(rate_value) as avg_rate,
    MIN(rate_value) as min_rate,
    MAX(rate_value) as max_rate,
    COUNT(*) as sample_count
FROM rate_history
GROUP BY vendor, service_type, rate_type, region, strftime('%Y-%m', effective_date)
ORDER BY vendor, period DESC;

-- Metadata table for tracking
CREATE TABLE IF NOT EXISTS _metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT OR REPLACE INTO _metadata (key, value) VALUES ('schema_version', '1.0.0');
INSERT OR REPLACE INTO _metadata (key, value) VALUES ('created_at', datetime('now'));
