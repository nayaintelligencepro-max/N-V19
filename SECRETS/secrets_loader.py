"""
NAYA V19 — Secrets Loader
Charge TOUTES les clés depuis SECRETS/keys/ au boot.
JSON + .env racine + sous-dossiers .env — ordre: .env écrase JSON si défini.
Grok utilisé en fallback si Anthropic sans crédit.
"""
import os, json, logging
from pathlib import Path
from typing import Dict, Optional, Tuple

log = logging.getLogger("NAYA.SECRETS")
ROOT_DIR = Path(__file__).resolve().parent.parent
KEYS_DIR = Path(__file__).parent / "keys"
SA_DIR   = Path(__file__).parent / "service_accounts"

_STUBS = ("METS_TA_CLE","METS_TON","_ICI","tondomaine.com","ton.email",
          "ton-projet-gcp","YOUR_KEY","PLACEHOLDER","XXXX")

def _stub(v: str) -> bool:
    return any(s in v for s in _STUBS)

def _load_file(path: Path) -> int:
    if not path.is_file(): return 0
    n = 0
    try:
        for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k,_,v = line.partition("=")
            k=k.strip(); v=v.strip().strip('"').strip("'")
            if not k:
                continue
            existing = os.environ.get(k)
            # Injecter si : jamais défini, OU valeur existante est un placeholder stub
            if existing is None or _stub(existing):
                os.environ[k] = v
                n += 1
    except Exception as e:
        log.debug(f"[SECRETS] {path.name}: {e}")
    return n

# Mapping JSON → variables d'environnement
_JSON_MAP = {
    "anthropic.json":         [("api_key","ANTHROPIC_API_KEY")],
    "openai.json":            [("api_key","OPENAI_API_KEY")],
    "grok.json":              [("api_key","GROK_API_KEY"),("api_key","XAI_API_KEY"),("base_url","XAI_BASE_URL")],
    "telegram.json":          [("bot_token","TELEGRAM_BOT_TOKEN"),("chat_id","TELEGRAM_CHAT_ID")],
    "notion.json":            [("token","NOTION_TOKEN")],
    "shopify.json":           [("shop","SHOPIFY_SHOP_NAME"),("access_token","SHOPIFY_ACCESS_TOKEN")],
    "shopify.autopilot.json": [("shop","SHOPIFY_SHOP_NAME"),("token","SHOPIFY_ACCESS_TOKEN")],
    "shopify_webhooks.json":  [("webhook_secret","SHOPIFY_WEBHOOK_SECRET")],
    "tiktok_business.json":   [("credentials.access_token","TIKTOK_ACCESS_TOKEN"),
                                ("account.business_id","TIKTOK_BUSINESS_ID")],
    "paypal.json":            [("payment_url","PAYPAL_ME_URL")],
    "groq.json":              [("api_key","GROQ_API_KEY")],
    "huggingface.json":       [],   # Géré via _inject_real_keys (tableau de clés)
    "sendgrid.json":          [("api_key","SENDGRID_API_KEY"),("from_email","EMAIL_FROM"),("from_name","EMAIL_FROM_NAME")],
    "serper.json":            [],   # Géré via _inject_real_keys (tableau de clés)
    "supabase.json":          [("url","SUPABASE_URL"),("anon_public_key","SUPABASE_ANON_KEY"),("service_role_key","SUPABASE_SERVICE_KEY"),("project_ref","SUPABASE_PROJECT_REF")],
    "deepseek.json":          [("api_key","DEEPSEEK_API_KEY"),("base_url","DEEPSEEK_BASE_URL")],
    "openai.json":            [("api_key","OPENAI_API_KEY")],
    "anthropic.json":         [("api_key","ANTHROPIC_API_KEY")],
    "google_service_account.json":[("project_id","GOOGLE_CLOUD_PROJECT"),
                                    ("client_email","GCP_SERVICE_ACCOUNT")],
    "instagram.json":         [("account.instagram_id","INSTAGRAM_ID"),
                                ("account.name","INSTAGRAM_USERNAME")],
    "facebook.json":          [("raw.page.page_id","FACEBOOK_PAGE_ID"),
                                ("raw.page.phone_number","CONTACT_PHONE")],
    "whatsapp.json":          [("account.phone_number","WHATSAPP_PHONE"),
                                ("ids.whatsapp_id","WHATSAPP_ID")],
}

def _get_nested(d, key):
    parts = key.split(".")
    val = d
    for p in parts:
        val = val.get(p,"") if isinstance(val, dict) else ""
    return val or ""

def _load_json_keys() -> int:
    n = 0
    for fname, mappings in _JSON_MAP.items():
        f = KEYS_DIR / fname
        if not f.exists(): continue
        try:
            d = json.loads(f.read_text(encoding="utf-8-sig", errors="replace"))
            for jk, ek in mappings:
                val = _get_nested(d,jk) if "." in jk else d.get(jk,"")
                if val and not _stub(str(val)) and ek not in os.environ:
                    os.environ[ek]=str(val); n+=1
        except Exception as e:
            log.debug(f"[SECRETS] JSON {fname}: {e}")
    return n

def _load_sa() -> bool:
    for j in (SA_DIR/"gcp-service-account.json", KEYS_DIR/"google_service_account.json"):
        if not j.exists(): continue
        try:
            d = json.loads(j.read_text(encoding="utf-8-sig"))
            if d.get("type")=="service_account":
                if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=str(j.resolve())
                if "GOOGLE_CLOUD_PROJECT" not in os.environ and d.get("project_id"):
                    os.environ["GOOGLE_CLOUD_PROJECT"]=d["project_id"]
                return True
        except Exception as e: log.debug(f"[SECRETS] Google credentials: {e}")
    return False


def _inject_v10_keys():
    """Injecte les clés V10 supplémentaires depuis les fichiers secrets."""
    # Groq API (ultra-rapide, gratuit)
    for key in ['GROQ_API_KEY']:
        if not os.environ.get(key):
            val = os.environ.get('GROK_API_KEY', '')  # Fallback sur Grok si Groq manquant
            if val and 'xai-' in val.lower():
                log.debug("[SECRETS] GROK key detected (xAI format), not reused as GROQ_API_KEY")
    
    # HuggingFace — distribuer les clés
    hf_keys = [
        os.environ.get('HF_API_KEY_1', ''),
        os.environ.get('HF_API_KEY_2', ''),
        os.environ.get('HF_API_KEY_3', ''),
        os.environ.get('HF_API_KEY_4', ''),
    ]
    # Prendre la première clé valide comme HUGGINGFACE_API_KEY principale
    if not os.environ.get('HUGGINGFACE_API_KEY') and not os.environ.get('HF_API_KEY'):
        for k in hf_keys:
            if k and k.startswith('hf_'):
                os.environ['HUGGINGFACE_API_KEY'] = k
                os.environ['HF_API_KEY'] = k
                break
    
    # Serper — clé principale
    if not os.environ.get('SERPER_API_KEY') or 'METS' in os.environ.get('SERPER_API_KEY', ''):
        default = os.environ.get('SERPER_API_KEY_DEFAULT', '')
        if default:
            os.environ['SERPER_API_KEY'] = default



def _inject_real_keys() -> int:
    """Injecte les cles reelles depuis les fichiers JSON — complement de _JSON_MAP."""
    import json
    n = 0
    KEYS = Path(__file__).parent / "keys"

    def _set(key: str, val: str):
        nonlocal n
        if val and not _stub(val) and key not in os.environ:
            os.environ[key] = val; n += 1

    # Google OAuth — Gmail envoie depuis nayaintelligencepro@gmail.com
    try:
        d = json.loads((KEYS/"google_token.json").read_text())
        _set("GOOGLE_OAUTH_CLIENT_ID",     d.get("client_id",""))
        _set("GOOGLE_OAUTH_CLIENT_SECRET", d.get("client_secret",""))
        _set("GOOGLE_OAUTH_REFRESH_TOKEN", d.get("refresh_token",""))
        _set("GMAIL_OAUTH_USER",           "nayaintelligencepro@gmail.com")
    except Exception as exc:
        log.debug("[SECRETS] google_token.json skipped: %s", exc)

    # Shopify
    try:
        d = json.loads((KEYS/"shopify.json").read_text())
        shop = d.get("shop", "")
        token = d.get("access_token", "")
        _set("SHOPIFY_SHOP_NAME",    shop)
        _set("SHOPIFY_ACCESS_TOKEN", token)
        # Construire l'URL complete obligatoire pour ShopifyIntegration
        if shop and not shop.startswith("http"):
            _set("SHOPIFY_SHOP_URL", f"https://{shop}")
        elif shop:
            _set("SHOPIFY_SHOP_URL", shop)
    except Exception as exc:
        log.debug("[SECRETS] shopify.json skipped: %s", exc)

    try:
        d = json.loads((KEYS/"shopify.autopilot.json").read_text())
        _set("SHOPIFY_SHOP_NAME",    d.get("shop",""))
        _set("SHOPIFY_ACCESS_TOKEN", d.get("token",""))
    except Exception as exc:
        log.debug("[SECRETS] shopify.autopilot.json skipped: %s", exc)

    try:
        d = json.loads((KEYS/"shopify_webhooks.json").read_text())
        _set("SHOPIFY_WEBHOOK_SECRET", d.get("webhook_secret",""))
    except Exception as exc:
        log.debug("[SECRETS] shopify_webhooks.json skipped: %s", exc)

    # TikTok
    try:
        d = json.loads((KEYS/"tiktok_business.json").read_text())
        _set("TIKTOK_ACCESS_TOKEN", d.get("credentials",{}).get("access_token",""))
        _set("TIKTOK_BUSINESS_ID",  str(d.get("account",{}).get("business_id","") or
                                       d.get("account",{}).get("open_id","")))
        _set("TIKTOK_USERNAME",     d.get("account",{}).get("name",""))
    except Exception as exc:
        log.debug("[SECRETS] tiktok_business.json skipped: %s", exc)

    # Instagram / Facebook
    try:
        d = json.loads((KEYS/"insta.json").read_text())
        _set("INSTAGRAM_USERNAME", d.get("username",""))
        _set("INSTAGRAM_URL",      d.get("profile_url",""))
    except Exception as exc:
        log.debug("[SECRETS] insta.json skipped: %s", exc)

    try:
        d = json.loads((KEYS/"facebook.json").read_text())
        _set("FACEBOOK_PAGE_URL",  d.get("page_url",""))
        _set("FACEBOOK_PAGE_NAME", d.get("page_name",""))
    except Exception as exc:
        log.debug("[SECRETS] facebook.json skipped: %s", exc)

    # WhatsApp
    try:
        d = json.loads((KEYS/"whatsapp.json").read_text())
        _set("WHATSAPP_PHONE", d.get("account",{}).get("phone_number","") or "+68989559088")
        _set("WHATSAPP_ID",    str(d.get("ids",{}).get("whatsapp_id","") or
                                  d.get("ids",{}).get("phone_number_id","")))
    except Exception as exc:
        log.debug("[SECRETS] whatsapp.json skipped: %s", exc)

    # PayPal / Revolut
    try:
        d = json.loads((KEYS/"paypal.json").read_text())
        _set("PAYPAL_ME_URL", d.get("payment_url",""))
    except Exception as exc:
        log.debug("[SECRETS] paypal.json skipped: %s", exc)

    try:
        d = json.loads((KEYS/"revolut_payment.json").read_text())
        _set("REVOLUT_ME_URL", d.get("link",""))
    except Exception as exc:
        log.debug("[SECRETS] revolut_payment.json skipped: %s", exc)

    # HuggingFace — tableau de clés
    try:
        d = json.loads((KEYS/"huggingface.json").read_text())
        keys = d.get("keys", [])
        for i, k in enumerate(keys):
            if k and not _stub(k):
                _set(f"HF_API_KEY_{i+1}", k)
                if i == 0:
                    _set("HUGGINGFACE_API_KEY", k)
                    _set("HF_API_KEY", k)
    except Exception as exc:
        log.debug("[SECRETS] huggingface.json skipped: %s", exc)

    # Serper — tableau de clés
    try:
        d = json.loads((KEYS/"serper.json").read_text())
        keys = d.get("keys", [])
        for i, k in enumerate(keys):
            if k and not _stub(k):
                if i == 0: _set("SERPER_API_KEY", k)
                _set(f"SERPER_API_KEY_{i+1}", k)
    except Exception as exc:
        log.debug("[SECRETS] serper.json skipped: %s", exc)

    # Supabase
    try:
        d = json.loads((KEYS/"supabase.json").read_text())
        _set("SUPABASE_URL", d.get("url", ""))
        _set("SUPABASE_ANON_KEY", d.get("anon_public_key", ""))
        _set("SUPABASE_SERVICE_KEY", d.get("service_role_key", ""))
        _set("SUPABASE_PROJECT_REF", d.get("project_ref", ""))
    except Exception as exc:
        log.debug("[SECRETS] supabase.json skipped: %s", exc)

    # Groq
    try:
        d = json.loads((KEYS/"groq.json").read_text())
        _set("GROQ_API_KEY", d.get("api_key", ""))
    except Exception as exc:
        log.debug("[SECRETS] groq.json skipped: %s", exc)

    # DeepSeek
    try:
        d = json.loads((KEYS/"deepseek.json").read_text())
        _set("DEEPSEEK_API_KEY", d.get("api_key", ""))
        _set("DEEPSEEK_BASE_URL", d.get("base_url", "https://api.deepseek.com/v1"))
    except Exception as exc:
        log.debug("[SECRETS] deepseek.json skipped: %s", exc)

    # SendGrid
    try:
        d = json.loads((KEYS/"sendgrid.json").read_text())
        _set("SENDGRID_API_KEY", d.get("api_key", ""))
        _set("EMAIL_FROM", d.get("from_email", ""))
        _set("EMAIL_FROM_NAME", d.get("from_name", "NAYA SUPREME"))
    except Exception as exc:
        log.debug("[SECRETS] sendgrid.json skipped: %s", exc)

    # Domains
    try:
        d = json.loads((KEYS/"domains_emails.json").read_text())
        ci = d.get("central_identity",{})
        _set("EMAIL_FROM",      ci.get("email",""))
        _set("NAYA_MAIN_EMAIL", ci.get("email",""))
        _set("NAYA_MAIN_DOMAIN", d.get("domains",[{}])[0].get("domain","") if d.get("domains") else "")
    except Exception as exc:
        log.debug("[SECRETS] domains_emails.json skipped: %s", exc)

    # Google Service Account
    try:
        d = json.loads((KEYS/"google_service_account.json").read_text())
        if d.get("type") == "service_account":
            sa_path = str((KEYS/"google_service_account.json").resolve())
            _set("GOOGLE_APPLICATION_CREDENTIALS", sa_path)
            _set("GOOGLE_CLOUD_PROJECT", d.get("project_id",""))
            _set("GCP_SERVICE_ACCOUNT",  d.get("client_email",""))
    except Exception as exc:
        log.debug("[SECRETS] google_service_account.json skipped: %s", exc)

    if n > 0:
        log.info(f"[SECRETS] _inject_real_keys: {n} cles injectees")
    return n


def _load_txt_keys(keys_dir: Path) -> int:
    """Charge les fichiers NOM_CLE.txt : filename (sans extension) = clé, contenu = valeur.
    Gère aussi les fichiers avec noms lisibles comme 'lien révolut.me' ou 'PAYPAL_ME_URL.txt'.
    Si le contenu est une URL revolut.me/paypal.me/deblock.me, injecte la clé correspondante."""
    n = 0

    # Détection par contenu URL → clé automatique
    URL_PATTERNS = {
        "revolut.me":  "REVOLUT_ME_URL",
        "paypal.me":   "PAYPAL_ME_URL",
        "deblock.me":  "DEBLOCK_ME_URL",
        "deblock.com": "DEBLOCK_ME_URL",
    }

    try:
        for f in keys_dir.iterdir():
            if not f.is_file():
                continue
            # Lire tous les fichiers texte (txt, sans extension, ou extension non-standard)
            if f.suffix.lower() not in (".txt", ".env", ".json", ".py", ".md", ".sh", ".csv", ".log"):
                # Fichier sans extension reconnue — tenter lecture
                try:
                    val = f.read_text(encoding="utf-8-sig", errors="replace").strip()
                except Exception:
                    continue
            elif f.suffix.lower() == ".txt":
                try:
                    val = f.read_text(encoding="utf-8-sig", errors="replace").strip()
                except Exception:
                    continue
            else:
                continue

            if not val:
                continue

            # 1. Détecter par contenu URL (priorité)
            detected_key = None
            for pattern, env_key in URL_PATTERNS.items():
                if pattern in val:
                    detected_key = env_key
                    break

            if detected_key:
                if detected_key not in os.environ and not _stub(val):
                    os.environ[detected_key] = val
                    log.debug(f"[SECRETS] URL détectée: {detected_key} ← {f.name}")
                    n += 1
                continue

            # 2. Dériver la clé depuis le nom de fichier (ex: PAYPAL_ME_URL.txt)
            stem = f.stem.strip()
            if not stem:
                continue
            # Normaliser : accents → ASCII approximatif, espaces/tirets → _
            import unicodedata
            try:
                stem_ascii = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode()
            except Exception:
                stem_ascii = stem
            key = stem_ascii.upper().replace(" ", "_").replace("-", "_").replace(".", "_")
            # Filtrer les noms de fichiers non-clés (trop longs ou contenant des caractères invalides)
            if not key or len(key) > 60:
                continue
            if key not in os.environ and not _stub(val):
                os.environ[key] = val
                n += 1
    except Exception as e:
        log.debug(f"[SECRETS] _load_txt_keys {keys_dir}: {e}")
    return n


def _load_raw_dump_keys(keys_dir: Path) -> int:
    """Parse naya_raw_dump.env narratif et injecte les variables critiques reconnues.

    Le fichier peut contenir du texte libre, des labels et des tokens sur lignes séparées.
    On extrait uniquement les patterns connus sans jamais logger les valeurs.
    """
    import re

    raw_file = keys_dir / "naya_raw_dump.env"
    if not raw_file.exists():
        return 0

    try:
        text = raw_file.read_text(encoding="utf-8-sig", errors="replace")
    except Exception as exc:
        log.debug("[SECRETS] raw dump read skipped: %s", exc)
        return 0

    n = 0

    def _set(key: str, val: str):
        nonlocal n
        if not val:
            return
        existing = os.environ.get(key)
        if (existing is None or _stub(existing)) and not _stub(val):
            os.environ[key] = val
            n += 1

    # Tokens/API keys (formats usuels)
    patterns = {
        "SENDGRID_API_KEY": r"\bSG\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\b",
        "HUGGINGFACE_API_KEY": r"\bhf_[A-Za-z0-9]{20,}\b",
        "OPENAI_API_KEY": r"\bsk-[A-Za-z0-9_-]{20,}\b",
        "DEEPSEEK_API_KEY": r"\bsk-[A-Za-z0-9]{20,}\b",
        "GROQ_API_KEY": r"\bgsk_[A-Za-z0-9]{20,}\b",
        "SERPER_API_KEY": r"\b[a-f0-9]{32,40}\b",
        "NOTION_TOKEN": r"\bntn_[A-Za-z0-9]{20,}\b",
    }

    # Extraction ciblée: on prend la première occurrence plausible par clé
    for env_key, pat in patterns.items():
        if env_key in os.environ and not _stub(os.environ.get(env_key, "")):
            continue
        m = re.search(pat, text)
        if m:
            _set(env_key, m.group(0))

    # URLs paiement
    for env_key, pat in {
        "PAYPAL_ME_URL": r"https?://(?:www\.)?paypal\.me/[A-Za-z0-9_\-/.]+",
        "REVOLUT_ME_URL": r"https?://(?:www\.)?revolut\.me/[A-Za-z0-9_\-/.]+",
        "DEBLOCK_ME_URL": r"https?://(?:www\.)?deblock\.(?:me|com)/[A-Za-z0-9_\-/.]+",
    }.items():
        if env_key in os.environ and not _stub(os.environ.get(env_key, "")):
            continue
        m = re.search(pat, text)
        if m:
            _set(env_key, m.group(0))

    # Telegram token heuristique (bot token format: digits:token)
    if not is_configured("TELEGRAM_BOT_TOKEN"):
        m = re.search(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b", text)
        if m:
            _set("TELEGRAM_BOT_TOKEN", m.group(0))

    if n > 0:
        log.info("[SECRETS] raw dump parser: %d vars injectées", n)
    return n
def load_all_secrets(verbose: bool = False) -> Dict:
    """
    Charge TOUTES les clés depuis SECRETS/keys/ — ordre:
    1. JSON clés (via _JSON_MAP + _inject_real_keys)
    2. .env racine dans keys/
    3. Sous-dossiers .env + .env.template
    4. Fichiers .txt (NOM_CLE.txt → NOM_CLE env var)
    5. naya_raw_dump.env (format narratif)
    6. Service accounts Google
    7. .env projet racine (override final)

    Returns:
        Dict avec stats de chargement + validation
    """
    total = 0
    files = []
    loaded_keys = set()

    if KEYS_DIR.exists():
        # 1. Charger JSON (via mapping)
        n = _load_json_keys()
        total += n
        if n > 0 and verbose:
            log.info(f"[SECRETS] JSON keys: {n} vars")

        # 2. Charger tous les .env à la racine de keys/
        for f in sorted(KEYS_DIR.glob("*.env")):
            n = _load_file(f)
            total += n
            if n:
                files.append(f"keys/{f.name}")
                if verbose:
                    log.info(f"[SECRETS] {f.name}: {n} vars")

        # 3. Charger tous les sous-dossiers (.env ou .env.template)
        for sub in sorted(d for d in KEYS_DIR.iterdir() if d.is_dir()):
            # Préférer .env, fallback sur .env.template
            target = sub/".env" if (sub/".env").exists() else sub/".env.template"
            if target.exists():
                n = _load_file(target)
                total += n
                if n:
                    files.append(f"keys/{sub.name}/{target.name}")
                    if verbose:
                        log.info(f"[SECRETS] {sub.name}/{target.name}: {n} vars")

        # 4. Charger fichiers .txt (NOM_CLE.txt)
        n = _load_txt_keys(KEYS_DIR)
        total += n
        if n > 0 and verbose:
            log.info(f"[SECRETS] TXT keys: {n} vars")

        # 5. Parser raw dump narratif (si présent)
        n = _load_raw_dump_keys(KEYS_DIR)
        total += n
        if n > 0 and verbose:
            log.info(f"[SECRETS] RAW keys: {n} vars")

    # 6. Service accounts Google
    sa_loaded = _load_sa()
    if sa_loaded and verbose:
        log.info("[SECRETS] Google Service Account loaded")

    # 6. Injection clés spécifiques (HuggingFace multi-keys, etc.)
    n = _inject_real_keys()
    total += n
    if n > 0 and verbose:
        log.info(f"[SECRETS] Real keys injected: {n} vars")

    # 7. Injection V10 (Groq, HuggingFace distribution, Serper)
    _inject_v10_keys()

    # 8. .env projet racine (override final)
    root_env = ROOT_DIR/".env"
    if root_env.exists():
        n = _load_file(root_env)
        total += n
        if n > 0 and verbose:
            log.info(f"[SECRETS] Root .env: {n} vars")

    # Compter clés réellement configurées (non-stub)
    real = sum(1 for k in _CRITICAL_KEYS if is_configured(k))

    # Collecter toutes les clés chargées (pour diagnostic)
    for key in _CRITICAL_KEYS:
        if is_configured(key):
            loaded_keys.add(key)

    log.info(f"[SECRETS] 🔐 {total} vars chargées — {real}/{len(_CRITICAL_KEYS)} clés critiques actives")

    if verbose:
        # Afficher clés manquantes
        missing = [k for k in _CRITICAL_KEYS if not is_configured(k)]
        if missing:
            log.warning(f"[SECRETS] ⚠️  Clés manquantes: {', '.join(missing[:5])}")

    return {
        "loaded": total,
        "files": files,
        "real_keys": real,
        "critical_keys_total": len(_CRITICAL_KEYS),
        "loaded_keys": list(loaded_keys),
        "missing_keys": [k for k in _CRITICAL_KEYS if not is_configured(k)]
    }

_CRITICAL_KEYS = [
    # === LLM / IA ===
    "ANTHROPIC_API_KEY","OPENAI_API_KEY","GROK_API_KEY","XAI_API_KEY",
    "GROQ_API_KEY","DEEPSEEK_API_KEY","HUGGINGFACE_API_KEY",
    "MISTRAL_API_KEY",
    # === Communication ===
    "TELEGRAM_BOT_TOKEN","TELEGRAM_CHAT_ID",
    "SENDGRID_API_KEY","EMAIL_FROM","EMAIL_FROM_NAME",
    "TWILIO_ACCOUNT_SID","TWILIO_AUTH_TOKEN",
    # === Paiements ===
    "PAYPAL_ME_URL","REVOLUT_ME_URL","DEBLOCK_ME_URL",
    "PAYPAL_ME_URL","PAYPAL_CLIENT_ID",
    # === Intégrations Business ===
    "NOTION_TOKEN","SHOPIFY_ACCESS_TOKEN","SHOPIFY_SHOP_NAME",
    "TIKTOK_ACCESS_TOKEN","INSTAGRAM_ID","FACEBOOK_PAGE_ID",
    "WHATSAPP_PHONE","WHATSAPP_ID",
    # === Data & Recherche ===
    "SERPER_API_KEY","APOLLO_API_KEY","HUNTER_API_KEY",
    # === Cloud / Infrastructure ===
    "GOOGLE_CLOUD_PROJECT","GOOGLE_APPLICATION_CREDENTIALS",
    "SUPABASE_URL","SUPABASE_ANON_KEY",
]

# Clés optionnelles (non critiques mais utiles)
_OPTIONAL_KEYS = [
    "LINKEDIN_CLIENT_ID","LINKEDIN_ACCESS_TOKEN",
    "CALENDLY_API_KEY","INSTANTLY_API_KEY",
    "SLACK_BOT_TOKEN","GMAIL_OAUTH_USER",
    "SENTRY_DSN","MIXPANEL_TOKEN",
]

def get_secret(key: str, default: Optional[str]=None) -> Optional[str]:
    v = os.environ.get(key)
    if v is None: return default
    if _stub(v): return default
    return v

def is_configured(key: str) -> bool:
    return get_secret(key) is not None

def get_llm_key() -> Tuple[str, str]:
    """Retourne (provider, api_key) — Anthropic en priorité, Grok en fallback."""
    ant = get_secret("ANTHROPIC_API_KEY")
    if ant: return ("anthropic", ant)
    grok = get_secret("GROK_API_KEY") or get_secret("XAI_API_KEY")
    if grok: return ("grok", grok)
    oai = get_secret("OPENAI_API_KEY")
    if oai: return ("openai", oai)
    return ("none", "")

def get_status() -> Dict:
    groups = {
        "llm":    {"claude": is_configured("ANTHROPIC_API_KEY"),
                   "openai": is_configured("OPENAI_API_KEY"),
                   "grok":   is_configured("GROK_API_KEY")},
        "alerts": {"telegram": is_configured("TELEGRAM_BOT_TOKEN") and is_configured("TELEGRAM_CHAT_ID"),
                   "sendgrid": is_configured("SENDGRID_API_KEY")},
        "payment":{"paypal":   is_configured("PAYPAL_ME_URL"),
                   "deblock":  is_configured("DEBLOCK_ME_URL")},
        "prospect":{"apollo":  is_configured("APOLLO_API_KEY"),
                    "serper":  is_configured("SERPER_API_KEY")},
        "social":  {"tiktok":  is_configured("TIKTOK_ACCESS_TOKEN"),
                    "instagram":is_configured("INSTAGRAM_ID"),
                    "facebook":is_configured("FACEBOOK_PAGE_ID")},
        "storage": {"notion":  is_configured("NOTION_TOKEN"),
                    "shopify": is_configured("SHOPIFY_ACCESS_TOKEN"),
                    "gcp":     is_configured("GOOGLE_CLOUD_PROJECT")},
    }
    flat=[v for g in groups.values() for v in g.values()]
    n=sum(flat)
    llm_provider, _ = get_llm_key()
    return {
        "groups": groups, "configured": n, "total": len(flat),
        "score": f"{n}/{len(flat)}",
        "active_llm": llm_provider,
        "minimum_viable": {
            "llm":     llm_provider != "none",
            "telegram":groups["alerts"]["telegram"],
            "email":   groups["alerts"]["sendgrid"],
            "payment": groups["payment"]["paypal"],
        }
    }

def validate_all_keys(strict: bool = False) -> Dict:
    """
    Valide que toutes les clés critiques sont présentes.

    Args:
        strict: Si True, lève une exception si clés critiques manquantes

    Returns:
        Rapport de validation complet
    """
    result = load_all_secrets(verbose=False)
    missing = result.get("missing_keys", [])
    loaded = result.get("loaded_keys", [])

    report = {
        "status": "PASS" if len(missing) == 0 else ("PARTIAL" if len(loaded) > 0 else "FAIL"),
        "total_critical": len(_CRITICAL_KEYS),
        "loaded_critical": len(loaded),
        "missing_critical": len(missing),
        "missing_keys": missing,
        "loaded_keys": loaded,
        "total_vars_loaded": result.get("loaded", 0),
        "files_loaded": result.get("files", []),
    }

    if strict and missing:
        raise RuntimeError(
            f"❌ VALIDATION ÉCHOUÉE: {len(missing)} clés critiques manquantes\n"
            f"Manquantes: {', '.join(missing[:10])}\n"
            f"Vérifier SECRETS/keys/"
        )

    return report


def print_diagnostic_report() -> None:
    """Affiche un rapport de diagnostic complet des clés API."""
    import sys

    print("="*80)
    print("🔐 NAYA V19 — DIAGNOSTIC SECRETS & API KEYS")
    print("="*80)

    # Charger et valider
    report = validate_all_keys(strict=False)

    print(f"\n📊 STATUT GLOBAL: {report['status']}")
    print(f"   • Total vars chargées: {report['total_vars_loaded']}")
    print(f"   • Clés critiques: {report['loaded_critical']}/{report['total_critical']}")
    print(f"   • Fichiers sources: {len(report['files_loaded'])}")

    # Détails par groupe
    st = get_status()
    print(f"\n🤖 LLM ACTIF: {st['active_llm'].upper()}")

    print("\n📋 DÉTAILS PAR GROUPE:")
    for group, keys in st['groups'].items():
        print(f"\n  {group.upper()}:")
        for key, ok in keys.items():
            status = "✅" if ok else "❌"
            print(f"    {status} {key}")

    # Clés manquantes
    if report['missing_keys']:
        print(f"\n⚠️  CLÉS CRITIQUES MANQUANTES ({len(report['missing_keys'])}):")
        for key in report['missing_keys'][:15]:
            print(f"    ❌ {key}")
        if len(report['missing_keys']) > 15:
            print(f"    ... et {len(report['missing_keys']) - 15} autres")

    # Fichiers chargés
    if report['files_loaded']:
        print(f"\n📁 FICHIERS CHARGÉS ({len(report['files_loaded'])}):")
        for f in report['files_loaded'][:10]:
            print(f"    • {f}")
        if len(report['files_loaded']) > 10:
            print(f"    ... et {len(report['files_loaded']) - 10} autres")

    # Minimum viable
    mv = st['minimum_viable']
    print("\n🎯 CONFIGURATION MINIMALE VIABLE:")
    for key, ok in mv.items():
        status = "✅" if ok else "❌"
        print(f"    {status} {key}")

    viable = all(mv.values())
    print(f"\n{'✅ SYSTÈME OPÉRATIONNEL' if viable else '⚠️  CONFIGURATION INCOMPLÈTE'}")
    print("="*80)

    return report


_WEAK_DEFAULTS: dict[str, str] = {
    "SECRET_KEY":       "naya-supreme-v19-production-key",
    "JWT_SECRET":       "naya-jwt-secret-key-2024",
    "ENCRYPTION_KEY":   "naya-encryption-key-2024",
    "GRAFANA_PASSWORD": "admin",
    "DB_PASSWORD":      "naya_secure_password_production",
    "RABBITMQ_PASSWORD":"naya_rabbitmq_password",
    "VAULT_KEY":        "naya",
}

def validate_production_secrets(raise_on_weak: bool = False) -> list[str]:
    """
    Détecte les secrets par défaut (placeholders) encore actifs.

    En mode production (ENVIRONMENT=production), ces valeurs DOIVENT avoir été
    remplacées. Utilisez ``scripts/generate_secrets.py`` pour générer des valeurs fortes.

    Args:
        raise_on_weak: Si True, lève RuntimeError si des secrets faibles sont détectés.

    Returns:
        Liste des noms de variables avec des valeurs faibles/par défaut.
    """
    env = os.environ.get("ENVIRONMENT", "development").lower()
    weak: list[str] = []

    for var, weak_prefix in _WEAK_DEFAULTS.items():
        val = os.environ.get(var, "")
        if val and val.startswith(weak_prefix):
            weak.append(var)

    if weak:
        msg = (
            f"[SECRETS] ⚠️  {len(weak)} secret(s) par défaut détecté(s): "
            f"{', '.join(weak)}. "
            f"Générer des valeurs fortes: py scripts/generate_secrets.py"
        )
        if env == "production":
            log.critical(msg)
            if raise_on_weak:
                raise RuntimeError(
                    f"SECRETS FAIBLES EN PRODUCTION: {', '.join(weak)}\n"
                    "Exécuter: py scripts/generate_secrets.py --apply"
                )
        else:
            log.warning(msg)

    return weak


def auto_load_on_import():
    """
    Charge automatiquement tous les secrets dès l'import du module.
    Appelé automatiquement par SECRETS/__init__.py
    """
    try:
        result = load_all_secrets(verbose=False)
        if result.get("real_keys", 0) > 0:
            log.debug(f"[SECRETS] Auto-loaded: {result['real_keys']} clés actives")
        # Vérifier les secrets faibles (avertissement seulement, pas de blocage)
        validate_production_secrets(raise_on_weak=False)
        return result
    except RuntimeError:
        raise
    except Exception as e:
        log.error(f"[SECRETS] Auto-load failed: {e}")
        return None


# Auto-chargement au boot si importé directement
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Mode diagnostic complet
    if "--diagnostic" in sys.argv or "-d" in sys.argv:
        print_diagnostic_report()
    # Mode validation stricte
    elif "--validate" in sys.argv or "-v" in sys.argv:
        try:
            report = validate_all_keys(strict=True)
            print(f"✅ VALIDATION RÉUSSIE: {report['loaded_critical']}/{report['total_critical']} clés")
            sys.exit(0)
        except RuntimeError as e:
            print(str(e))
            sys.exit(1)
    # Mode standard
    else:
        load_all_secrets(verbose=True)
        st = get_status()
        print(f"\nScore: {st['score']} | LLM actif: {st['active_llm']}")
        for g, keys in st['groups'].items():
            for k, ok in keys.items():
                print(f"  {'✅' if ok else '❌'} {g}.{k}")
        mv = st['minimum_viable']
        print(f"\nMinimum viable: {', '.join(k+'='+ ('✅' if v else '❌') for k,v in mv.items())}")



