"""
NAYA SUPREME V6 — Database Manager
Accès unifié à toutes les tables : 6 projets + pipeline + scheduler + revenue.
WAL mode, thread-safe, zero-downtime.
"""
import os, sqlite3, json, time, uuid, logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

log = logging.getLogger("NAYA.DB")


class DatabaseManager:
    def initialize(self):
        """Initialize database tables and connections."""
        self._init()
        return self


    def __init__(self, db_path=None):
        if db_path:
            self.db_path = db_path
        else:
            d = Path(__file__).parent.parent.parent / "data" / "db"
            d.mkdir(parents=True, exist_ok=True)
            self.db_path = str(d / "naya_supreme.db")
        self._conn: Optional[sqlite3.Connection] = None
        self._init()

    def _init(self):
        c = self._get()
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA cache_size=-32000")
        c.commit()

    def _get(self) -> sqlite3.Connection:
        if not self._conn:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def connect(self): return self._get()
    def get_connection(self): return self._get()

    @contextmanager
    def transaction(self):
        c = self._get()
        try: yield c; c.commit()
        except: c.rollback(); raise

    def execute(self, sql, params=()): return self._get().execute(sql, params)
    def fetch_one(self, sql, params=()) -> Optional[Dict]:
        r = self.execute(sql, params).fetchone()
        return dict(r) if r else None
    def fetch_all(self, sql, params=()) -> List[Dict]:
        return [dict(r) for r in self.execute(sql, params).fetchall()]

    # ── System State ─────────────────────────────────────────────────────────
    def upsert_state(self, key: str, value: Any):
        v = json.dumps(value) if not isinstance(value, str) else value
        with self.transaction() as c:
            c.execute("""INSERT INTO naya_system_state(key,value,updated_at) VALUES(?,?,?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at""",
                (key, v, time.time()))

    def get_state(self, key: str) -> Optional[Any]:
        r = self.fetch_one("SELECT value FROM naya_system_state WHERE key=?", (key,))
        if not r: return None
        try: return json.loads(r["value"])
        except: return r["value"]

    # ── Events ───────────────────────────────────────────────────────────────
    def log_event(self, event_type, payload, source="system", priority="NORMAL"):
        with self.transaction() as c:
            c.execute("""INSERT INTO naya_events(event_type,source,payload,priority,created_at)
                VALUES(?,?,?,?,?)""", (event_type, source, json.dumps(payload), priority, time.time()))

    def get_recent_events(self, n=100, event_type=None) -> List[Dict]:
        if event_type:
            return self.fetch_all("SELECT * FROM naya_events WHERE event_type=? ORDER BY created_at DESC LIMIT ?", (event_type, n))
        return self.fetch_all("SELECT * FROM naya_events ORDER BY created_at DESC LIMIT ?", (n,))

    # ── KPI ──────────────────────────────────────────────────────────────────
    def record_kpi(self, metric, value, unit=""):
        with self.transaction() as c:
            c.execute("INSERT INTO naya_kpi(metric_name,metric_value,unit,recorded_at) VALUES(?,?,?,?)",
                (metric, value, unit, time.time()))

    def get_kpi_series(self, metric, limit=100) -> List[Dict]:
        return self.fetch_all(
            "SELECT * FROM naya_kpi WHERE metric_name=? ORDER BY recorded_at DESC LIMIT ?", (metric, limit))

    # ── Businesses (legacy) ───────────────────────────────────────────────────
    def save_business(self, bp_dict: Dict):
        with self.transaction() as c:
            c.execute("""INSERT OR REPLACE INTO naya_businesses(id,name,category,status,price,plan,created_at)
                VALUES(?,?,?,?,?,?,?)""",
                (bp_dict["id"], bp_dict["name"], bp_dict.get("category",""),
                 bp_dict.get("status",""), bp_dict.get("price_recommended",0),
                 str(bp_dict.get("full_plan",""))[:5000], time.time()))

    def get_businesses(self, n=50) -> List[Dict]:
        return self.fetch_all("SELECT * FROM naya_businesses ORDER BY created_at DESC LIMIT ?", (n,))

    # ══════════════════════════════════════════════════════════════════════════
    # PROJECT_01 — CASH RAPIDE
    # ══════════════════════════════════════════════════════════════════════════
    def save_cash_rapide(self, pain_tier: str, service_id: str, service_name: str,
                          price_quoted: float, urgency_score: float = 0.7,
                          pain_score: float = 0.7, client_name: str = None,
                          client_sector: str = None, timeline_hours: int = 24,
                          deliverable: str = None, notes: str = None,
                          source_channel: str = "direct") -> str:
        rid = f"CR_{uuid.uuid4().hex[:10].upper()}"
        with self.transaction() as c:
            c.execute("""INSERT INTO proj_cash_rapide(
                id,pain_tier,client_name,client_sector,service_id,service_name,
                price_quoted,urgency_score,pain_score,timeline_hours,
                deliverable,notes,source_channel,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (rid, pain_tier, client_name, client_sector, service_id, service_name,
                 price_quoted, urgency_score, pain_score, timeline_hours,
                 deliverable, notes, source_channel, time.time()))
        log.info(f"[P01] Cash Rapide #{rid} — {service_name} — {price_quoted}€ — {pain_tier}")
        return rid

    def update_cash_rapide_status(self, rid: str, status: str, revenue: float = None):
        # Whitelist explicite — jamais de f-string avec des colonnes dynamiques
        TS_FIELDS = {"SIGNED": "signed_at", "DELIVERED": "delivered_at", "PAID": "paid_at"}
        VALID_STATUSES = {"NEW", "SIGNED", "DELIVERED", "PAID", "CANCELLED"}
        if status not in VALID_STATUSES:
            log.warning(f"[DB] update_cash_rapide_status: statut invalide '{status}' rejeté")
            return
        ts_field = TS_FIELDS.get(status)
        with self.transaction() as c:
            if ts_field:
                # ts_field vient d'une whitelist interne — sécurisé
                sql = f"UPDATE proj_cash_rapide SET status=?,{ts_field}=? WHERE id=?"  # nosec
                c.execute(sql, (status, time.time(), rid))
            else:
                c.execute("UPDATE proj_cash_rapide SET status=? WHERE id=?", (status, rid))
            if revenue is not None:
                c.execute("UPDATE proj_cash_rapide SET revenue=? WHERE id=?", (revenue, rid))

    def get_cash_rapide(self, status: str = None, limit: int = 50) -> List[Dict]:
        if status:
            return self.fetch_all("SELECT * FROM proj_cash_rapide WHERE status=? ORDER BY created_at DESC LIMIT ?", (status, limit))
        return self.fetch_all("SELECT * FROM proj_cash_rapide ORDER BY created_at DESC LIMIT ?", (limit,))

    # ══════════════════════════════════════════════════════════════════════════
    # PROJECT_02 — GOOGLE XR
    # ══════════════════════════════════════════════════════════════════════════
    def save_xr_deal(self, pain_id: str, client_name: str = None, client_sector: str = None,
                      client_size: str = "medium", use_case: str = None,
                      solution_type: str = None, price_quoted: float = None,
                      setup_fee: float = None, monthly_support: float = None,
                      contract_months: int = 12, team_size_client: int = None,
                      notes: str = None) -> str:
        rid = f"XR_{uuid.uuid4().hex[:10].upper()}"
        deal_total = (price_quoted or 0) + (setup_fee or 0) + (monthly_support or 0) * contract_months
        with self.transaction() as c:
            c.execute("""INSERT INTO proj_google_xr(
                id,pain_id,client_name,client_sector,client_size,use_case,solution_type,
                price_quoted,setup_fee,monthly_support,contract_months,team_size_client,
                deal_value_total,notes,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (rid, pain_id, client_name, client_sector, client_size, use_case, solution_type,
                 price_quoted, setup_fee, monthly_support, contract_months, team_size_client,
                 deal_total, notes, time.time()))
        log.info(f"[P02] XR Deal #{rid} — {client_name} — {deal_total:.0f}€ total")
        return rid

    def update_xr_pipeline_stage(self, rid: str, stage: str):
        TS_FIELDS = {"WON": "won_at", "DEMO": "demo_date", "PROPOSAL": "proposal_sent_at"}
        VALID_STAGES = {"LEAD", "DEMO", "PROPOSAL", "NEGOTIATION", "WON", "LOST"}
        if stage not in VALID_STAGES:
            log.warning(f"[DB] update_xr_pipeline_stage: stage invalide '{stage}' rejeté")
            return
        ts_field = TS_FIELDS.get(stage)
        with self.transaction() as c:
            if ts_field:
                sql = f"UPDATE proj_google_xr SET pipeline_stage=?,{ts_field}=? WHERE id=?"  # nosec — whitelist
                c.execute(sql, (stage, time.time(), rid))
            else:
                c.execute("UPDATE proj_google_xr SET pipeline_stage=? WHERE id=?", (stage, rid))

    def get_xr_pipeline(self, stage: str = None) -> List[Dict]:
        if stage:
            return self.fetch_all("SELECT * FROM proj_google_xr WHERE pipeline_stage=? ORDER BY deal_value_total DESC", (stage,))
        return self.fetch_all("SELECT * FROM proj_google_xr ORDER BY created_at DESC LIMIT 100")

    # ══════════════════════════════════════════════════════════════════════════
    # PROJECT_03 — NAYA BOTANICA
    # ══════════════════════════════════════════════════════════════════════════
    def init_botanica_catalog(self):
        """Insère les produits du catalogue si absents."""
        from NAYA_PROJECT_ENGINE.business.projects.PROJECT_03_NAYA_BOTANICA.PAINS.PAIN_01_SKIN_REPAIR import REPAIR_PRODUCTS
        try:
            from NAYA_PROJECT_ENGINE.business.projects.PROJECT_03_NAYA_BOTANICA.PAINS.PAIN_02_HYPERPIGMENTATION import HYPERPIG_PRODUCTS
        except: HYPERPIG_PRODUCTS = []
        try:
            from NAYA_PROJECT_ENGINE.business.projects.PROJECT_03_NAYA_BOTANICA.PAINS.PAIN_03_FIRMING_BODY import FIRMING_PRODUCTS
        except: FIRMING_PRODUCTS = []

        all_products = [
            (p, "SKIN_REPAIR") for p in REPAIR_PRODUCTS
        ] + [
            (p, "HYPERPIGMENTATION") for p in HYPERPIG_PRODUCTS
        ] + [
            (p, "FIRMING") for p in FIRMING_PRODUCTS
        ]
        with self.transaction() as c:
            for prod, cat in all_products:
                c.execute("""INSERT OR IGNORE INTO proj_botanica_products(
                    id,pain_category,name,price_eur,cost_eur,margin_pct,
                    volume_ml,key_actives,routine,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (prod["id"], cat, prod["name"], prod["price"], prod["cost"],
                     round((prod["price"]-prod["cost"])/prod["price"]*100, 1),
                     prod.get("volume", 0), json.dumps(prod.get("key_actives", [])),
                     prod.get("routine",""), time.time()))
        log.info(f"[P03] Botanica catalog initialized — {len(all_products)} products")

    def save_botanica_order(self, items: List[Dict], customer_email: str = None,
                             skin_type: str = "sensitive", channel: str = "dtc",
                             subscription: bool = False, shopify_order_id: str = None) -> str:
        oid = f"NB_{uuid.uuid4().hex[:10].upper()}"
        subtotal = sum(i["price"] * i.get("qty", 1) for i in items)
        total = subtotal
        with self.transaction() as c:
            c.execute("""INSERT INTO proj_botanica_orders(
                id,customer_email,skin_type,channel,items,subtotal,total,
                subscription,shopify_order_id,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (oid, customer_email, skin_type, channel, json.dumps(items),
                 subtotal, total, 1 if subscription else 0,
                 shopify_order_id, time.time()))
            # MAJ stock + units_sold
            for item in items:
                c.execute("""UPDATE proj_botanica_products
                    SET units_sold=units_sold+?, revenue_total=revenue_total+?
                    WHERE id=?""", (item.get("qty",1), item["price"]*item.get("qty",1), item["product_id"]))
        log.info(f"[P03] Botanica Order #{oid} — {total}€ — {channel}")
        return oid

    def get_botanica_stats(self) -> Dict:
        revenue = self.fetch_one("SELECT SUM(total) as rev, COUNT(*) as cnt FROM proj_botanica_orders WHERE status!='REFUNDED'")
        top = self.fetch_all("SELECT name, units_sold, revenue_total FROM proj_botanica_products ORDER BY revenue_total DESC LIMIT 5")
        return {"total_revenue": revenue["rev"] or 0, "total_orders": revenue["cnt"] or 0, "top_products": top}

    # ══════════════════════════════════════════════════════════════════════════
    # PROJECT_04 — TINY HOUSE
    # ══════════════════════════════════════════════════════════════════════════
    def save_tiny_house_quote(self, pain_id: str, package_type: str, price_quoted: float,
                               client_name: str = None, client_profile: str = "family",
                               customizations: list = None, location_region: str = None,
                               notes: str = None) -> str:
        rid = f"TH_{uuid.uuid4().hex[:10].upper()}"
        # Récupère les specs du package
        try:
            from NAYA_PROJECT_ENGINE.business.projects.PROJECT_04_TINY_HOUSE.PAINS.PAIN_01_OFF_GRID_LIVING import OFF_GRID_PACKAGES
            pkg = OFF_GRID_PACKAGES.get(package_type, {})
        except: pkg = {}

        with self.transaction() as c:
            c.execute("""INSERT INTO proj_tiny_house(
                id,pain_id,client_name,client_profile,package_type,customizations,
                price_quoted,surface_m2,solar_kwp,battery_kwh,autonomy_days,
                location_region,notes,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (rid, pain_id, client_name, client_profile, package_type,
                 json.dumps(customizations or []), price_quoted,
                 pkg.get("surface_m2"), pkg.get("solar_kwp"),
                 pkg.get("battery_kwh"), pkg.get("autonomy_days"),
                 location_region, notes, time.time()))
        log.info(f"[P04] Tiny House #{rid} — {package_type} — {price_quoted}€")
        return rid

    def update_tiny_house_status(self, rid: str, build_status: str, deposit_paid: float = None):
        with self.transaction() as c:
            c.execute("UPDATE proj_tiny_house SET build_status=? WHERE id=?", (build_status, rid))
            if deposit_paid is not None:
                c.execute("UPDATE proj_tiny_house SET deposit_paid=?,deposit_date=? WHERE id=?",
                    (deposit_paid, time.time(), rid))

    # ══════════════════════════════════════════════════════════════════════════
    # PROJECT_05 — MARCHÉS OUBLIÉS
    # ══════════════════════════════════════════════════════════════════════════
    def save_marches_member(self, pain_id: str, segment: str, subscription_tier: str,
                             price_monthly: float, member_name: str = None,
                             member_email: str = None, acquisition_channel: str = "direct",
                             languages: list = None, notes: str = None) -> str:
        rid = f"MO_{uuid.uuid4().hex[:10].upper()}"
        with self.transaction() as c:
            c.execute("""INSERT INTO proj_marches_oublies(
                id,pain_id,segment,member_name,member_email,subscription_tier,
                price_monthly,languages,acquisition_channel,notes,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (rid, pain_id, segment, member_name, member_email,
                 subscription_tier, price_monthly, json.dumps(languages or []),
                 acquisition_channel, notes, time.time()))
        log.info(f"[P05] Marchés Oubliés #{rid} — {segment} — {price_monthly}€/mois")
        return rid

    def tick_marches_monthly(self):
        """Incrémente months_active et revenue pour abonnés ACTIVE."""
        with self.transaction() as c:
            c.execute("""UPDATE proj_marches_oublies
                SET months_active=months_active+1,
                    revenue_total=revenue_total+price_monthly
                WHERE status='ACTIVE'""")
        log.info("[P05] Monthly tick applied")

    def get_marches_mrr(self) -> float:
        r = self.fetch_one("SELECT SUM(price_monthly) as mrr FROM proj_marches_oublies WHERE status='ACTIVE'")
        return r["mrr"] or 0.0

    # ══════════════════════════════════════════════════════════════════════════
    # PROJECT_06 — ACQUISITION IMMOBILIÈRE
    # ══════════════════════════════════════════════════════════════════════════
    def save_immo_mandate(self, pain_id: str, service_type: str, price_quoted: float,
                           client_name: str = None, client_type: str = "investisseur",
                           zone_geo: str = "IDF", property_value: float = None,
                           notes: str = None) -> str:
        rid = f"IM_{uuid.uuid4().hex[:10].upper()}"
        # Calcule gain espéré
        try:
            from NAYA_PROJECT_ENGINE.business.projects.PROJECT_06_ACQUISITION_IMMOBILIERE.PAINS.PAIN_01_UNDERVALUED_PROPERTY import get_investment_analysis
            analysis = get_investment_analysis(property_value or 300000, zone_geo)
        except: analysis = {}

        with self.transaction() as c:
            c.execute("""INSERT INTO proj_immo(
                id,pain_id,client_name,client_type,service_type,zone_geo,
                property_value,expected_discount_pct,expected_gain,
                price_quoted,notes,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (rid, pain_id, client_name, client_type, service_type, zone_geo,
                 property_value, analysis.get("expected_discount_pct"),
                 analysis.get("expected_gain"), price_quoted, notes, time.time()))
        log.info(f"[P06] Immo Mandate #{rid} — {service_type} — {price_quoted}€")
        return rid

    def update_immo_status(self, rid: str, status: str, properties_scanned: int = None,
                            off_market_found: int = None, deal_value_final: float = None):
        with self.transaction() as c:
            c.execute("UPDATE proj_immo SET status=? WHERE id=?", (status, rid))
            if status == "OPPORTUNITY_FOUND":
                c.execute("UPDATE proj_immo SET opportunity_found_at=? WHERE id=?", (time.time(), rid))
            if status == "CLOSED":
                c.execute("UPDATE proj_immo SET closed_at=? WHERE id=?", (time.time(), rid))
            if properties_scanned is not None:
                c.execute("UPDATE proj_immo SET properties_scanned=? WHERE id=?", (properties_scanned, rid))
            if off_market_found is not None:
                c.execute("UPDATE proj_immo SET off_market_found=? WHERE id=?", (off_market_found, rid))
            if deal_value_final is not None:
                c.execute("UPDATE proj_immo SET deal_value_final=? WHERE id=?", (deal_value_final, rid))

    # ══════════════════════════════════════════════════════════════════════════
    # PIPELINE — Opportunités cross-projets
    # ══════════════════════════════════════════════════════════════════════════
    def save_pipeline_signal(self, project_id: str, pain_id: str,
                              pain_score: float, solvability: float,
                              price_floor: float, price_target: float,
                              lead_name: str = None, lead_sector: str = None,
                              silence_type: str = None, source: str = "autonomous",
                              discretion_level: str = "DISCREET",
                              notes: str = None) -> str:
        pid = f"PL_{uuid.uuid4().hex[:10].upper()}"
        with self.transaction() as c:
            c.execute("""INSERT INTO naya_pipeline(
                id,project_id,pain_id,lead_name,lead_sector,silence_type,
                pain_score,solvability,price_floor,price_target,
                stage,discretion_level,source,notes,detected_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (pid, project_id, pain_id, lead_name, lead_sector, silence_type,
                 pain_score, solvability, price_floor, price_target,
                 "SIGNAL", discretion_level, source, notes, time.time()))
        return pid

    def advance_pipeline(self, pid: str, stage: str, notes: str = None):
        TS_MAP = {"QUALIFIED": "qualified_at", "CONTACTED": "contacted_at",
                  "WON": "won_at", "LOST": "lost_at"}
        VALID_STAGES = {"SIGNAL", "QUALIFIED", "CONTACTED", "MEETING",
                        "PROPOSAL", "NEGOTIATING", "WON", "LOST", "NURTURING"}
        if stage not in VALID_STAGES:
            log.warning(f"[DB] advance_pipeline: stage invalide '{stage}' rejeté")
            return
        with self.transaction() as c:
            c.execute("UPDATE naya_pipeline SET stage=?,last_action=? WHERE id=?",
                (stage, stage, pid))
            if stage in TS_MAP:
                ts_col = TS_MAP[stage]
                sql = f"UPDATE naya_pipeline SET {ts_col}=? WHERE id=?"  # nosec — whitelist interne
                c.execute(sql, (time.time(), pid))
            if notes:
                c.execute("UPDATE naya_pipeline SET notes=? WHERE id=?", (notes, pid))

    def get_pipeline_by_project(self, project_id: str, stage: str = None) -> List[Dict]:
        if stage:
            return self.fetch_all(
                "SELECT * FROM naya_pipeline WHERE project_id=? AND stage=? ORDER BY pain_score DESC",
                (project_id, stage))
        return self.fetch_all(
            "SELECT * FROM naya_pipeline WHERE project_id=? ORDER BY detected_at DESC LIMIT 100",
            (project_id,))

    def get_pipeline_summary(self) -> Dict:
        rows = self.fetch_all("""
            SELECT project_id, stage, COUNT(*) as cnt, SUM(price_target) as value
            FROM naya_pipeline GROUP BY project_id, stage""")
        summary = {}
        for r in rows:
            if r["project_id"] not in summary:
                summary[r["project_id"]] = {}
            summary[r["project_id"]][r["stage"]] = {
                "count": r["cnt"], "value": r["value"] or 0
            }
        return summary

    # ══════════════════════════════════════════════════════════════════════════
    # SCHEDULER
    # ══════════════════════════════════════════════════════════════════════════
    def register_job(self, job_name: str, job_type: str, interval_secs: int,
                      project_id: str = None, payload: dict = None) -> str:
        jid = f"JOB_{job_name.upper()}"
        next_run = time.time() + interval_secs
        with self.transaction() as c:
            c.execute("""INSERT OR REPLACE INTO naya_scheduler_jobs(
                id,job_name,job_type,project_id,interval_secs,payload,
                next_run_at,created_at)
                VALUES(?,?,?,?,?,?,?,?)""",
                (jid, job_name, job_type, project_id, interval_secs,
                 json.dumps(payload or {}), next_run, time.time()))
        return jid

    def get_due_jobs(self) -> List[Dict]:
        return self.fetch_all(
            "SELECT * FROM naya_scheduler_jobs WHERE enabled=1 AND next_run_at<=? ORDER BY next_run_at",
            (time.time(),))

    def record_job_run(self, job_id: str, status: str, result: dict = None, error: str = None):
        run_id = f"RUN_{uuid.uuid4().hex[:10].upper()}"
        now = time.time()
        with self.transaction() as c:
            c.execute("""INSERT INTO naya_scheduler_runs(id,job_id,status,started_at,ended_at,result,error)
                VALUES(?,?,?,?,?,?,?)""",
                (run_id, job_id, status, now, now, json.dumps(result or {}), error))
            # MAJ last_run
            c.execute("""UPDATE naya_scheduler_jobs SET
                last_run_at=?, last_run_status=?, run_count=run_count+1,
                fail_count=fail_count+(?),
                next_run_at=last_run_at+interval_secs
                WHERE id=?""",
                (now, status, 1 if status == "FAILED" else 0, job_id))

    # ══════════════════════════════════════════════════════════════════════════
    # CONTENT
    # ══════════════════════════════════════════════════════════════════════════
    def save_content(self, channel: str, content_type: str, body: str,
                      project_id: str = None, pipeline_id: str = None,
                      title: str = None, hashtags: list = None,
                      tone: str = "professional", target_audience: str = None,
                      media_prompt: str = None, scheduled_at: float = None) -> str:
        cid = f"CNT_{uuid.uuid4().hex[:10].upper()}"
        with self.transaction() as c:
            c.execute("""INSERT INTO naya_content(
                id,project_id,pipeline_id,channel,content_type,title,body,
                hashtags,tone,target_audience,media_prompt,scheduled_at,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (cid, project_id, pipeline_id, channel, content_type, title, body,
                 json.dumps(hashtags or []), tone, target_audience, media_prompt,
                 scheduled_at, time.time()))
        return cid

    def get_scheduled_content(self) -> List[Dict]:
        return self.fetch_all(
            "SELECT * FROM naya_content WHERE status='SCHEDULED' AND scheduled_at<=? ORDER BY scheduled_at",
            (time.time(),))

    def mark_content_published(self, cid: str, platform_post_id: str = None):
        with self.transaction() as c:
            c.execute("UPDATE naya_content SET status='PUBLISHED',published_at=?,platform_post_id=? WHERE id=?",
                (time.time(), platform_post_id, cid))

    # ══════════════════════════════════════════════════════════════════════════
    # REVENUE TRACKER
    # ══════════════════════════════════════════════════════════════════════════
    def record_revenue(self, project_id: str, source_table: str, source_id: str,
                        amount: float, revenue_type: str = "one_time",
                        payment_method: str = None, notes: str = None) -> str:
        rid = f"REV_{uuid.uuid4().hex[:10].upper()}"
        amount_ht = round(amount / 1.20, 2)
        with self.transaction() as c:
            c.execute("""INSERT INTO naya_revenue(
                id,project_id,source_table,source_id,amount,revenue_type,
                payment_method,amount_ht,recorded_at,notes)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (rid, project_id, source_table, source_id, amount, revenue_type,
                 payment_method, amount_ht, time.time(), notes))
        log.info(f"[REVENUE] {project_id} +{amount}€ ({revenue_type}) — {source_table}#{source_id}")
        return rid

    def get_revenue_summary(self) -> Dict:
        total = self.fetch_one("SELECT SUM(amount) as total, COUNT(*) as cnt FROM naya_revenue")
        by_project = self.fetch_all("""
            SELECT project_id, SUM(amount) as total, COUNT(*) as cnt
            FROM naya_revenue GROUP BY project_id ORDER BY total DESC""")
        mrr = self.fetch_one(
            "SELECT SUM(amount) as mrr FROM naya_revenue WHERE revenue_type='recurring' AND recorded_at>?",
            (time.time() - 2592000,))  # 30 jours
        return {
            "total_revenue": total["total"] or 0,
            "total_transactions": total["cnt"] or 0,
            "mrr": mrr["mrr"] or 0,
            "by_project": by_project,
        }

    def get_portfolio_dashboard(self) -> Dict:
        """Dashboard complet — toutes les métriques en un appel."""
        rev = self.get_revenue_summary()
        pipeline = self.get_pipeline_summary()
        missions = self.fetch_one("SELECT COUNT(*) as cnt FROM naya_missions WHERE status='COMPLETED'")
        content = self.fetch_one("SELECT COUNT(*) as cnt FROM naya_content WHERE status='PUBLISHED'")
        jobs = self.fetch_all("SELECT job_name,last_run_at,last_run_status,run_count FROM naya_scheduler_jobs WHERE enabled=1")
        botanica = self.get_botanica_stats()
        mrr_marches = self.get_marches_mrr()

        return {
            "revenue": rev,
            "pipeline": pipeline,
            "missions_completed": missions["cnt"] if missions else 0,
            "content_published": content["cnt"] if content else 0,
            "scheduler_jobs": jobs,
            "botanica": botanica,
            "marches_mrr": mrr_marches,
        }

    # ══════════════════════════════════════════════════════════════════════════
    # PARALLEL EXECUTION
    # ══════════════════════════════════════════════════════════════════════════
    def start_parallel_batch(self, batch_id: str, executions: List[Dict]) -> List[str]:
        ids = []
        with self.transaction() as c:
            for ex in executions:
                eid = f"EX_{uuid.uuid4().hex[:8].upper()}"
                c.execute("""INSERT INTO naya_parallel_executions(
                    id,batch_id,mission_type,project_id,worker_id,status,started_at)
                    VALUES(?,?,?,?,?,?,?)""",
                    (eid, batch_id, ex["mission_type"], ex.get("project_id"),
                     ex.get("worker_id"), "RUNNING", time.time()))
                ids.append(eid)
        return ids

    def complete_parallel_execution(self, eid: str, status: str,
                                     result_summary: str = None, error: str = None,
                                     resource_cost: float = 0):
        now = time.time()
        with self.transaction() as c:
            c.execute("""UPDATE naya_parallel_executions
                SET status=?,ended_at=?,duration_ms=((ended_at-started_at)*1000),
                    result_summary=?,error=?,resource_cost=?
                WHERE id=?""",
                (status, now, result_summary, error, resource_cost, eid))

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


_db: Optional[DatabaseManager] = None

def get_db() -> DatabaseManager:
    global _db
    if _db is None:
        _db = DatabaseManager()
    return _db
