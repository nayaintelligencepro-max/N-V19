"""
NAYA SUPREME V6 — Database Migration Runner
Schéma complet : 6 projets business + scheduler + pipeline + parallel orchestration
"""
import sqlite3, time, logging, json
from pathlib import Path
from typing import Optional

log = logging.getLogger("NAYA.DB.MIGRATIONS")

MIGRATIONS = [
    (1, "naya_events", """CREATE TABLE IF NOT EXISTS naya_events(
        id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL,
        source TEXT DEFAULT 'system', payload TEXT, priority TEXT DEFAULT 'NORMAL',
        processed INTEGER DEFAULT 0, created_at REAL NOT NULL, processed_at REAL)"""),
    (2, "naya_decisions", """CREATE TABLE IF NOT EXISTS naya_decisions(
        id TEXT PRIMARY KEY, decision_type TEXT NOT NULL, target TEXT,
        rationale TEXT, parameters TEXT, status TEXT DEFAULT 'PENDING', created_at REAL NOT NULL)"""),
    (3, "naya_opportunities", """CREATE TABLE IF NOT EXISTS naya_opportunities(
        id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT,
        business_type TEXT, value REAL, confidence REAL,
        status TEXT DEFAULT 'IDENTIFIED', created_at REAL NOT NULL)"""),
    (4, "naya_system_state", """CREATE TABLE IF NOT EXISTS naya_system_state(
        key TEXT PRIMARY KEY, value TEXT, updated_at REAL NOT NULL)"""),
    (5, "naya_kpi", """CREATE TABLE IF NOT EXISTS naya_kpi(
        id INTEGER PRIMARY KEY AUTOINCREMENT, metric_name TEXT NOT NULL,
        metric_value REAL, unit TEXT, recorded_at REAL NOT NULL)"""),
    (6, "naya_missions", """CREATE TABLE IF NOT EXISTS naya_missions(
        id TEXT PRIMARY KEY, mission_type TEXT NOT NULL, status TEXT DEFAULT 'QUEUED',
        payload TEXT, result TEXT, created_at REAL NOT NULL, completed_at REAL)"""),
    (7, "naya_businesses", """CREATE TABLE IF NOT EXISTS naya_businesses(
        id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT,
        status TEXT DEFAULT 'IDENTIFIED', price REAL, plan TEXT,
        created_at REAL NOT NULL, launched_at REAL, revenue REAL DEFAULT 0)"""),
    (8, "schema_migrations", """CREATE TABLE IF NOT EXISTS schema_migrations(
        version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at REAL NOT NULL)"""),

    # ── PROJECT_01 CASH RAPIDE ────────────────────────────────────────────────
    (9, "proj_cash_rapide", """CREATE TABLE IF NOT EXISTS proj_cash_rapide(
        id TEXT PRIMARY KEY,
        pain_tier TEXT NOT NULL,
        client_name TEXT, client_sector TEXT,
        service_id TEXT NOT NULL, service_name TEXT NOT NULL,
        price_quoted REAL NOT NULL, price_floor REAL DEFAULT 1000,
        urgency_score REAL DEFAULT 0.5, pain_score REAL DEFAULT 0.5,
        status TEXT DEFAULT 'QUOTED',
        timeline_hours INTEGER, deliverable TEXT, notes TEXT,
        created_at REAL NOT NULL, signed_at REAL, delivered_at REAL,
        paid_at REAL, revenue REAL DEFAULT 0, source_channel TEXT DEFAULT 'direct')"""),
    (10, "idx_cash_rapide_status", """CREATE INDEX IF NOT EXISTS idx_cash_rapide_status
        ON proj_cash_rapide(status, created_at DESC)"""),

    # ── PROJECT_02 GOOGLE XR ──────────────────────────────────────────────────
    (11, "proj_google_xr", """CREATE TABLE IF NOT EXISTS proj_google_xr(
        id TEXT PRIMARY KEY,
        pain_id TEXT NOT NULL,
        client_name TEXT, client_sector TEXT,
        client_size TEXT DEFAULT 'medium',
        use_case TEXT, solution_type TEXT,
        price_quoted REAL, setup_fee REAL, monthly_support REAL,
        contract_months INTEGER DEFAULT 12, team_size_client INTEGER,
        status TEXT DEFAULT 'PROSPECTING',
        pipeline_stage TEXT DEFAULT 'DISCOVERY',
        deal_value_total REAL, google_partner_ref TEXT, notes TEXT,
        created_at REAL NOT NULL, demo_date REAL, proposal_sent_at REAL,
        won_at REAL, revenue REAL DEFAULT 0)"""),
    (12, "idx_xr_pipeline", """CREATE INDEX IF NOT EXISTS idx_xr_pipeline
        ON proj_google_xr(pipeline_stage, deal_value_total DESC)"""),

    # ── PROJECT_03 NAYA BOTANICA ──────────────────────────────────────────────
    (13, "proj_botanica_products", """CREATE TABLE IF NOT EXISTS proj_botanica_products(
        id TEXT PRIMARY KEY,
        pain_category TEXT NOT NULL,
        name TEXT NOT NULL, price_eur REAL NOT NULL, cost_eur REAL NOT NULL,
        margin_pct REAL, volume_ml INTEGER, key_actives TEXT, routine TEXT,
        in_stock INTEGER DEFAULT 1, stock_units INTEGER DEFAULT 0,
        units_sold INTEGER DEFAULT 0, revenue_total REAL DEFAULT 0,
        created_at REAL NOT NULL)"""),
    (14, "proj_botanica_orders", """CREATE TABLE IF NOT EXISTS proj_botanica_orders(
        id TEXT PRIMARY KEY,
        customer_id TEXT, customer_email TEXT, skin_type TEXT,
        channel TEXT DEFAULT 'dtc',
        items TEXT NOT NULL,
        subtotal REAL NOT NULL, shipping REAL DEFAULT 0, total REAL NOT NULL,
        status TEXT DEFAULT 'PENDING',
        subscription INTEGER DEFAULT 0, subscription_cycle INTEGER DEFAULT 0,
        shopify_order_id TEXT,
        created_at REAL NOT NULL, shipped_at REAL, delivered_at REAL, refunded_at REAL)"""),
    (15, "idx_botanica_orders_status", """CREATE INDEX IF NOT EXISTS idx_botanica_orders_status
        ON proj_botanica_orders(status, created_at DESC)"""),

    # ── PROJECT_04 TINY HOUSE ─────────────────────────────────────────────────
    (16, "proj_tiny_house", """CREATE TABLE IF NOT EXISTS proj_tiny_house(
        id TEXT PRIMARY KEY,
        pain_id TEXT NOT NULL,
        client_name TEXT, client_profile TEXT,
        package_type TEXT NOT NULL,
        customizations TEXT,
        price_quoted REAL NOT NULL,
        deposit_pct REAL DEFAULT 30.0, deposit_paid REAL DEFAULT 0,
        surface_m2 INTEGER, solar_kwp REAL, battery_kwh REAL, autonomy_days INTEGER,
        location_region TEXT,
        permit_status TEXT DEFAULT 'NOT_STARTED',
        build_status TEXT DEFAULT 'QUOTED',
        supplier_ref TEXT, notes TEXT,
        created_at REAL NOT NULL, deposit_date REAL, build_start_date REAL,
        delivery_date REAL, revenue REAL DEFAULT 0)"""),
    (17, "idx_tiny_house_build_status", """CREATE INDEX IF NOT EXISTS idx_tiny_house_build_status
        ON proj_tiny_house(build_status, created_at DESC)"""),

    # ── PROJECT_05 MARCHÉS OUBLIÉS ────────────────────────────────────────────
    (18, "proj_marches_oublies", """CREATE TABLE IF NOT EXISTS proj_marches_oublies(
        id TEXT PRIMARY KEY,
        pain_id TEXT NOT NULL,
        segment TEXT NOT NULL,
        member_name TEXT, member_email TEXT, member_phone TEXT,
        subscription_tier TEXT NOT NULL,
        price_monthly REAL NOT NULL,
        languages TEXT, services_included TEXT,
        status TEXT DEFAULT 'TRIAL',
        acquisition_channel TEXT,
        acquisition_cost REAL DEFAULT 35,
        ltv_estimated REAL DEFAULT 1200,
        months_active INTEGER DEFAULT 0, revenue_total REAL DEFAULT 0,
        nps_score INTEGER, notes TEXT,
        created_at REAL NOT NULL, activated_at REAL, churned_at REAL)"""),
    (19, "idx_marches_status", """CREATE INDEX IF NOT EXISTS idx_marches_status
        ON proj_marches_oublies(status, segment)"""),

    # ── PROJECT_06 ACQUISITION IMMOBILIÈRE ───────────────────────────────────
    (20, "proj_immo", """CREATE TABLE IF NOT EXISTS proj_immo(
        id TEXT PRIMARY KEY,
        pain_id TEXT NOT NULL,
        client_name TEXT, client_type TEXT,
        service_type TEXT NOT NULL,
        zone_geo TEXT,
        property_value REAL, expected_discount_pct REAL, expected_gain REAL,
        price_quoted REAL NOT NULL,
        success_fee_pct REAL DEFAULT 2.0,
        status TEXT DEFAULT 'PROSPECTING',
        properties_scanned INTEGER DEFAULT 0,
        off_market_found INTEGER DEFAULT 0,
        best_discount_pct REAL DEFAULT 0,
        deal_value_final REAL, net_roi_client REAL,
        notaire_partner TEXT, notes TEXT,
        created_at REAL NOT NULL, mandate_date REAL,
        opportunity_found_at REAL, closed_at REAL, revenue REAL DEFAULT 0)"""),
    (21, "idx_immo_status", """CREATE INDEX IF NOT EXISTS idx_immo_status
        ON proj_immo(status, property_value DESC)"""),

    # ── SCHEDULER ────────────────────────────────────────────────────────────
    (22, "naya_scheduler_jobs", """CREATE TABLE IF NOT EXISTS naya_scheduler_jobs(
        id TEXT PRIMARY KEY,
        job_name TEXT NOT NULL,
        job_type TEXT NOT NULL,
        project_id TEXT,
        interval_secs INTEGER,
        payload TEXT,
        enabled INTEGER DEFAULT 1,
        last_run_at REAL, last_run_status TEXT,
        next_run_at REAL,
        run_count INTEGER DEFAULT 0, fail_count INTEGER DEFAULT 0,
        created_at REAL NOT NULL)"""),
    (23, "naya_scheduler_runs", """CREATE TABLE IF NOT EXISTS naya_scheduler_runs(
        id TEXT PRIMARY KEY,
        job_id TEXT NOT NULL,
        status TEXT NOT NULL,
        started_at REAL NOT NULL, ended_at REAL, duration_s REAL,
        result TEXT, error TEXT)"""),

    # ── PIPELINE ─────────────────────────────────────────────────────────────
    (24, "naya_pipeline", """CREATE TABLE IF NOT EXISTS naya_pipeline(
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        pain_id TEXT NOT NULL,
        lead_name TEXT, lead_contact TEXT, lead_sector TEXT,
        silence_type TEXT,
        pain_score REAL NOT NULL, solvability REAL NOT NULL,
        price_floor REAL NOT NULL, price_target REAL NOT NULL, price_ceiling REAL,
        stage TEXT DEFAULT 'SIGNAL',
        discretion_level TEXT DEFAULT 'DISCREET',
        source TEXT,
        content_generated INTEGER DEFAULT 0, proposal_sent INTEGER DEFAULT 0,
        last_action TEXT, notes TEXT,
        detected_at REAL NOT NULL, qualified_at REAL, contacted_at REAL,
        won_at REAL, lost_at REAL, revenue REAL DEFAULT 0)"""),
    (25, "idx_pipeline_project_stage", """CREATE INDEX IF NOT EXISTS idx_pipeline_project_stage
        ON naya_pipeline(project_id, stage, pain_score DESC)"""),

    # ── CONTENU ──────────────────────────────────────────────────────────────
    (26, "naya_content", """CREATE TABLE IF NOT EXISTS naya_content(
        id TEXT PRIMARY KEY,
        project_id TEXT, pipeline_id TEXT,
        channel TEXT NOT NULL,
        content_type TEXT NOT NULL,
        title TEXT, body TEXT NOT NULL,
        hashtags TEXT, media_prompt TEXT, tone TEXT, target_audience TEXT,
        status TEXT DEFAULT 'DRAFT',
        scheduled_at REAL, published_at REAL, platform_post_id TEXT,
        engagement_likes INTEGER DEFAULT 0, engagement_reach INTEGER DEFAULT 0,
        created_at REAL NOT NULL, created_by TEXT DEFAULT 'naya_autonomous')"""),
    (27, "idx_content_status_channel", """CREATE INDEX IF NOT EXISTS idx_content_status_channel
        ON naya_content(status, channel, scheduled_at)"""),

    # ── REVENUE TRACKER ───────────────────────────────────────────────────────
    (28, "naya_revenue", """CREATE TABLE IF NOT EXISTS naya_revenue(
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        source_table TEXT NOT NULL, source_id TEXT NOT NULL,
        amount REAL NOT NULL, currency TEXT DEFAULT 'EUR',
        revenue_type TEXT NOT NULL,
        payment_method TEXT, invoice_ref TEXT,
        vat_rate REAL DEFAULT 20.0, amount_ht REAL,
        recorded_at REAL NOT NULL, notes TEXT)"""),
    (29, "idx_revenue_project_date", """CREATE INDEX IF NOT EXISTS idx_revenue_project_date
        ON naya_revenue(project_id, recorded_at DESC)"""),

    # ── PARALLEL EXECUTION LOG ────────────────────────────────────────────────
    (30, "naya_parallel_executions", """CREATE TABLE IF NOT EXISTS naya_parallel_executions(
        id TEXT PRIMARY KEY,
        batch_id TEXT NOT NULL,
        mission_type TEXT NOT NULL, project_id TEXT, worker_id TEXT,
        status TEXT DEFAULT 'RUNNING',
        started_at REAL NOT NULL, ended_at REAL, duration_ms REAL,
        result_summary TEXT, error TEXT, resource_cost REAL DEFAULT 0)"""),
    (31, "idx_parallel_batch", """CREATE INDEX IF NOT EXISTS idx_parallel_batch
        ON naya_parallel_executions(batch_id, status)"""),
]


class MigrationRunner:
    def __init__(self, db_path=None):
        if db_path:
            self.db_path = db_path
        else:
            d = Path(__file__).parent.parent.parent / "data" / "db"
            d.mkdir(parents=True, exist_ok=True)
            self.db_path = str(d / "naya_supreme.db")
        self._conn: Optional[sqlite3.Connection] = None

    def conn(self) -> sqlite3.Connection:
        if not self._conn:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.execute("PRAGMA cache_size=-32000")
        return self._conn

    def run(self) -> int:
        c = self.conn()
        c.execute("""CREATE TABLE IF NOT EXISTS schema_migrations(
            version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at REAL NOT NULL)""")
        c.commit()
        applied = {row[0] for row in c.execute("SELECT version FROM schema_migrations")}
        count = 0
        for v, name, sql in MIGRATIONS:
            if v not in applied:
                try:
                    c.execute(sql)
                    c.execute("INSERT INTO schema_migrations VALUES(?,?,?)", (v, name, time.time()))
                    c.commit()
                    count += 1
                except Exception as e:
                    log.error(f"Migration v{v} '{name}' failed: {e}")
                    c.rollback()
                    raise
        if count:
            log.info(f"✅ Applied {count} migrations — schema v{self.get_version()}")
        return count

    def get_version(self) -> int:
        try:
            r = self.conn().execute("SELECT MAX(version) FROM schema_migrations").fetchone()
            return r[0] or 0
        except:
            return 0

    def get_table_stats(self) -> dict:
        tables = [
            "proj_cash_rapide", "proj_google_xr", "proj_botanica_orders",
            "proj_tiny_house", "proj_marches_oublies", "proj_immo",
            "naya_pipeline", "naya_content", "naya_revenue",
            "naya_scheduler_jobs", "naya_missions",
        ]
        # Tables hardcodées en interne — pas d'entrée utilisateur ici
        ALLOWED_TABLES = {
            "naya_state", "naya_events", "naya_kpis", "naya_businesses",
            "proj_cash_rapide", "proj_google_xr", "proj_botanica_orders",
            "proj_tiny_house", "proj_marches_members", "proj_immobilier_deals",
            "naya_pipeline", "naya_scheduler_jobs", "naya_missions",
            "proj_marches_oublies", "proj_immo", "naya_content", "naya_revenue",
            "naya_parallel_executions", "naya_scheduler_runs", "naya_decisions",
            "naya_opportunities", "naya_system_state", "naya_kpi",
        }
        stats = {}
        c = self.conn()
        for t in tables:
            if t not in ALLOWED_TABLES:
                log.warning(f"[MIGRATION] Table non autorisée ignorée: {t}")
                continue
            try:
                r = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()  # nosec — whitelist
                stats[t] = r[0] if r else 0
            except Exception:
                stats[t] = -1
        return stats

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


def run_migrations(db_path=None) -> MigrationRunner:
    r = MigrationRunner(db_path)
    r.run()
    return r
