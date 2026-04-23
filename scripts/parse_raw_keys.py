#!/usr/bin/env python3
"""
NAYA V19 — Parse Raw Keys Dump
Extrait toutes les clés API du fichier naya_raw_dump.env et crée un .env propre
"""
import re
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_FILE = ROOT / "SECRETS/keys/naya_raw_dump.env"
OUTPUT_FILE = ROOT / ".env"

def parse_raw_dump():
    """Parse le fichier raw dump et extrait toutes les clés."""
    if not RAW_FILE.exists():
        print(f"❌ Fichier {RAW_FILE} introuvable")
        return {}

    content = RAW_FILE.read_text(encoding="utf-8", errors="replace")
    keys = {}

    # === SENDGRID ===
    match = re.search(r'clé api sendgrid\s*\n(SG\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)', content, re.I)
    if match:
        keys['SENDGRID_API_KEY'] = match.group(1).strip()

    # === HUGGINGFACE (multiple keys) ===
    hf_keys = re.findall(r'hf_[A-Za-z0-9]{34}', content)
    if hf_keys:
        keys['HUGGINGFACE_API_KEY'] = hf_keys[0]
        for i, key in enumerate(hf_keys[:4], 1):
            keys[f'HF_API_KEY_{i}'] = key

    # === GROQ (note: it's "grok" in the file but should be GROQ) ===
    match = re.search(r'clé grok\s*\n(gsk_[A-Za-z0-9_-]+)', content, re.I)
    if match:
        keys['GROQ_API_KEY'] = match.group(1).strip()

    # === SERPER ===
    match = re.search(r'clé API SERPER par default\s*\n([a-f0-9]{40})', content, re.I)
    if match:
        keys['SERPER_API_KEY'] = match.group(1).strip()
        keys['SERPER_API_KEY_DEFAULT'] = match.group(1).strip()

    match = re.search(r'clé API SERPER KEY\s*\n([a-f0-9]{40})', content, re.I)
    if match:
        keys['SERPER_API_KEY_1'] = match.group(1).strip()

    # === SUPABASE ===
    match = re.search(r'anon public key\s*\n(eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)', content, re.I)
    if match:
        keys['SUPABASE_ANON_KEY'] = match.group(1).strip()

    match = re.search(r'service role key\s*\n(eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)', content, re.I)
    if match:
        keys['SUPABASE_SERVICE_KEY'] = match.group(1).strip()

    # Extraire URL Supabase du project ref dans le token
    if 'SUPABASE_ANON_KEY' in keys:
        try:
            import base64
            import json
            # Decoder le JWT pour extraire le ref
            parts = keys['SUPABASE_ANON_KEY'].split('.')
            if len(parts) >= 2:
                payload = base64.b64decode(parts[1] + '==').decode()
                data = json.loads(payload)
                ref = data.get('ref', '')
                if ref:
                    keys['SUPABASE_URL'] = f'https://{ref}.supabase.co'
                    keys['SUPABASE_PROJECT_REF'] = ref
        except Exception:
            pass

    # === DEEPSEEK ===
    match = re.search(r'clé deepseek\s*\n(sk-[a-f0-9]{32})', content, re.I)
    if match:
        keys['DEEPSEEK_API_KEY'] = match.group(1).strip()
        keys['DEEPSEEK_BASE_URL'] = 'https://api.deepseek.com/v1'

    # === OPENAI ===
    match = re.search(r'clé openai\s*\n(sk-[A-Za-z0-9_-]{100,})', content, re.I)
    if match:
        keys['OPENAI_API_KEY'] = match.group(1).strip()

    # === ANTHROPIC (multi-line key) ===
    # La clé anthropic est sur plusieurs lignes dans le fichier
    match = re.search(r'clé anthropic[^\n]*\n(sk-ant-api03-[^\n]+)\n([^\n]+)\n([^\n]+)', content, re.I)
    if match:
        # Combiner les 3 lignes (enlever les caractères cyrilliques/étrangers)
        line1 = match.group(1).strip()
        line2 = match.group(2).strip()
        line3 = match.group(3).strip()
        # Nettoyer et recombiner
        full_key = (line1 + line2 + line3).replace('г', 'r').replace('ó', 'o').replace('ń', 'n').replace('а', 'a')
        # Garder seulement les caractères valides pour une API key
        full_key = re.sub(r'[^A-Za-z0-9_-]', '', full_key)
        if len(full_key) > 50:  # Clé anthropic devrait être longue
            keys['ANTHROPIC_API_KEY'] = full_key

    # === N8N ===
    match = re.search(r'clé API n8n[^\n]*\n(eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)', content, re.I)
    if match:
        keys['N8N_API_KEY'] = match.group(1).strip()

    # === NOTION ===
    match = re.search(r'notion token:\s*\n(ntn_[A-Za-z0-9]+)', content, re.I)
    if match:
        keys['NOTION_TOKEN'] = match.group(1).strip()

    # === SHOPIFY ===
    match = re.search(r'shopify webhook secret[^\n]*\n([a-f0-9]{64})', content, re.I)
    if match:
        keys['SHOPIFY_WEBHOOK_SECRET'] = match.group(1).strip()

    match = re.search(r'https://([a-zA-Z0-9-]+\.com)', content)
    if match and 'shop' in match.group(1):
        keys['SHOPIFY_SHOP_URL'] = match.group(0)
        keys['SHOPIFY_SHOP_NAME'] = match.group(1)

    # === GOOGLE CLOUD ===
    match = re.search(r'GOOGLE_PROJECT_ID=\s*([a-z0-9-]+)', content, re.I)
    if match:
        keys['GOOGLE_CLOUD_PROJECT'] = match.group(1).strip()

    match = re.search(r'GOOGLE PROJECT NUMERO\s*:\s*(\d+)', content, re.I)
    if match:
        keys['GOOGLE_PROJECT_NUMBER'] = match.group(1).strip()

    # === WHATSAPP ===
    match = re.search(r'https://wa\.me/message/([A-Z0-9]+)', content, re.I)
    if match:
        keys['WHATSAPP_LINK'] = match.group(0)
        keys['WHATSAPP_ID'] = match.group(1)

    # === DEBLOCK ===
    match = re.search(r'https://deblock\.com/([a-z0-9-]+)', content, re.I)
    if match:
        keys['DEBLOCK_ME_URL'] = match.group(0)

    # === TELEGRAM (from other sources if not found) ===
    # Will be loaded from existing files

    # === RENDER ===
    match = re.search(r'Render clé[^\n]*:(rnd_[A-Za-z0-9]+)', content, re.I)
    if match:
        keys['RENDER_API_KEY'] = match.group(1).strip()

    # === VERCEL ===
    match = re.search(r'AI GATEAWAY API KEY[^\n]*:(vck_[A-Za-z0-9]+)', content, re.I)
    if match:
        keys['VERCEL_AI_KEY'] = match.group(1).strip()

    match = re.search(r'VERCEL TOKEN[^\n]*:(vcp_[A-Za-z0-9]+)', content, re.I)
    if match:
        keys['VERCEL_TOKEN'] = match.group(1).strip()

    # === DOCKER ===
    match = re.search(r'Token CLI\s*:(dckr_pat_[A-Za-z0-9]+)', content, re.I)
    if match:
        keys['DOCKER_TOKEN'] = match.group(1).strip()

    match = re.search(r'Username\s*:([a-z0-9]+)', content, re.I)
    if match and 'naya' in match.group(1).lower():
        keys['DOCKER_USERNAME'] = match.group(1).strip()

    # === OLLAMA ===
    match = re.search(r'Ollama key\s*:\s*([a-f0-9]{32}\.[A-Za-z0-9]+)', content, re.I)
    if match:
        keys['OLLAMA_API_KEY'] = match.group(1).strip()

    # === GEMINI ===
    match = re.search(r'clé gemini\s*:\s*(AQ\.[A-Za-z0-9_-]+)', content, re.I)
    if match:
        keys['GEMINI_API_KEY'] = match.group(1).strip()
        keys['GOOGLE_GEMINI_API_KEY'] = match.group(1).strip()

    # === HUGGINGFACE GEMMA4 (separate named key) ===
    match = re.search(r'Gemma4\s+hugging\s+face\s*:\s*(hf_[A-Za-z0-9]{32,})', content, re.I)
    if match:
        keys['HF_GEMMA4_KEY'] = match.group(1).strip()

    # === TELEGRAM BOT (primary extraction from JSON block) ===
    match = re.search(r'"bot_token"\s*:\s*"(\d+:[A-Za-z0-9_-]+)"', content)
    if not match:
        match = re.search(r'(\d{10}:AA[A-Za-z0-9_-]{30,})', content)
    if match:
        keys['TELEGRAM_BOT_TOKEN'] = match.group(1).strip()
    match = re.search(r'"chat_id"\s*:\s*"?(\d{6,})"?', content)
    if match:
        keys['TELEGRAM_CHAT_ID'] = match.group(1).strip()
        keys['TELEGRAM_OWNER_CHAT_ID'] = match.group(1).strip()

    # === STRIPE (test mode keys — publishable + secret) ===
    match = re.search(r'(pk_test_[A-Za-z0-9_]+)', content)
    if match:
        keys['STRIPE_PUBLISHABLE_KEY'] = match.group(1).strip()
    match = re.search(r'(sk_test_[A-Za-z0-9_]+)', content)
    if match:
        keys['STRIPE_SECRET_KEY'] = match.group(1).strip()

    # === SHOPIFY ACCESS TOKEN ===
    match = re.search(r'"access_token"\s*:\s*"(shpat_[A-Za-z0-9]+)"', content)
    if not match:
        match = re.search(r'(shpat_[A-Za-z0-9]{32,})', content)
    if match:
        keys['SHOPIFY_ACCESS_TOKEN'] = match.group(1).strip()
    match = re.search(r'"shop"\s*:\s*"([a-z0-9-]+\.myshopify\.com)"', content)
    if match:
        keys['SHOPIFY_SHOP_DOMAIN'] = match.group(1).strip()

    # === PAYPAL ME URL ===
    match = re.search(r'PAYPAL\s*ME\s*:\s*(https://[\w./]+)', content, re.I)
    if match:
        keys['PAYPAL_ME_URL'] = match.group(1).strip()

    # === TIKTOK ===
    match = re.search(r'"tiktok_token"\s*:\s*"([A-Za-z0-9_-]+)"', content)
    if not match:
        match = re.search(r'tiktok_token\s*"?\s*:\s*"?([A-Za-z0-9_-]{20,})', content, re.I)
    if match:
        keys['TIKTOK_ACCESS_TOKEN'] = match.group(1).strip()
    match = re.search(r'TIK\s*TOK\s*BUSINESS\s*nom\s*:\s*(\w+)', content, re.I)
    if match:
        keys['TIKTOK_USERNAME'] = match.group(1).strip()
    match = re.search(r'id\s*tik\s*tok\s*:\s*(\d+)', content, re.I)
    if match:
        keys['TIKTOK_BUSINESS_ID'] = match.group(1).strip()

    # === GOOGLE OAUTH 2 (from installed JSON block) ===
    match = re.search(r'"client_id"\s*:\s*"([^"]+\.apps\.googleusercontent\.com)"', content)
    if match:
        keys['GOOGLE_OAUTH_CLIENT_ID'] = match.group(1).strip()
    match = re.search(r'"client_secret"\s*:\s*"(GOCSPX-[^"]+)"', content)
    if match:
        keys['GOOGLE_OAUTH_CLIENT_SECRET'] = match.group(1).strip()

    # === GOOGLE OAUTH TOKEN (refresh/access) ===
    match = re.search(r'"refresh_token"\s*:\s*"(1//[^"]+)"', content)
    if match:
        keys['GOOGLE_OAUTH_REFRESH_TOKEN'] = match.group(1).strip()
    match = re.search(r'"token"\s*:\s*"(ya29\.[^"]+)"', content)
    if match:
        keys['GOOGLE_OAUTH_ACCESS_TOKEN'] = match.group(1).strip()

    # === INSTAGRAM ===
    match = re.search(r'"instagram_id"\s*:\s*"(\d+)"', content)
    if match:
        keys['INSTAGRAM_ID'] = match.group(1).strip()
    match = re.search(r'"username"\s*:\s*"(nayaservice\w*)"', content, re.I)
    if match:
        keys['INSTAGRAM_USERNAME'] = match.group(1).strip()

    # === FACEBOOK ===
    match = re.search(r'"page_id"\s*:\s*"(\d+)"', content)
    if match:
        keys['FACEBOOK_PAGE_ID'] = match.group(1).strip()

    # === WHATSAPP BUSINESS ===
    match = re.search(r'"whatsapp_id"\s*:\s*"(\d+)"', content)
    if match:
        keys['WHATSAPP_BUSINESS_ID'] = match.group(1).strip()
    match = re.search(r'"phone_number"\s*:\s*"(\+\d+)"', content)
    if match:
        keys['WHATSAPP_PHONE'] = match.group(1).strip()
        keys['OWNER_PHONE'] = match.group(1).strip()

    # === EMAIL (Central identity) ===
    match = re.search(r'"email"\s*:\s*"(nayaintelligencepro@gmail\.com)"', content)
    if match:
        keys['EMAIL_FROM'] = match.group(1).strip()
        keys['OWNER_EMAIL'] = match.group(1).strip()
        keys['EMAIL_FROM_NAME'] = 'Naya Intelligence Pro'

    # === GOOGLE SERVICE ACCOUNT (full JSON extraction) ===
    # We detect the SA JSON block and save it to SECRETS/service_accounts/
    sa_match = re.search(
        r'(\{[^{]*"type"\s*:\s*"service_account"[^}]*"universe_domain"\s*:\s*"googleapis\.com"[^}]*\})',
        content, re.DOTALL
    )
    if sa_match:
        keys['_GOOGLE_SERVICE_ACCOUNT_JSON'] = sa_match.group(1)
        keys['GOOGLE_APPLICATION_CREDENTIALS'] = 'SECRETS/service_accounts/gcp-service-account.json'

    # === DASHBOARD / SPREADSHEET ===
    match = re.search(r'"sheet_url"\s*:\s*"(https://docs\.google\.com/spreadsheets/d/[^"]+)"', content)
    if match:
        keys['DASHBOARD_SHEET_URL'] = match.group(1).strip()

    return keys


def merge_with_existing_env():
    """Merge avec le .env existant si présent."""
    existing = {}
    if OUTPUT_FILE.exists():
        for line in OUTPUT_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, val = line.partition('=')
                existing[key.strip()] = val.strip().strip('"').strip("'")
    return existing


def write_service_account_file(keys: dict):
    """Écrit le service account Google dans SECRETS/service_accounts/."""
    if '_GOOGLE_SERVICE_ACCOUNT_JSON' not in keys:
        return None
    sa_dir = ROOT / 'SECRETS' / 'service_accounts'
    sa_dir.mkdir(parents=True, exist_ok=True)
    sa_path = sa_dir / 'gcp-service-account.json'
    try:
        import json as _json
        parsed = _json.loads(keys['_GOOGLE_SERVICE_ACCOUNT_JSON'])
        sa_path.write_text(_json.dumps(parsed, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"   ↳ Service Account JSON → {sa_path}")
        return str(sa_path)
    except Exception as exc:
        print(f"   ⚠ SA JSON non écrit (parse error): {exc}")
        return None


def write_env_file(keys: dict):
    """Écrit le fichier .env avec toutes les clés."""
    # Écrit le SA JSON si présent (hors .env)
    sa_path = write_service_account_file(keys)
    if sa_path:
        keys['GOOGLE_APPLICATION_CREDENTIALS'] = sa_path
    keys.pop('_GOOGLE_SERVICE_ACCOUNT_JSON', None)

    # Merger avec existant
    existing = merge_with_existing_env()

    # Ajouter les nouvelles clés (sans écraser les existantes)
    all_keys = {**keys, **existing}

    # Organiser par catégorie
    categories = {
        'LLM & AI': ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'GROQ_API_KEY', 'DEEPSEEK_API_KEY',
                      'HUGGINGFACE_API_KEY', 'HF_API_KEY_1', 'HF_API_KEY_2', 'HF_API_KEY_3', 'HF_API_KEY_4',
                      'HF_GEMMA4_KEY', 'GEMINI_API_KEY', 'GOOGLE_GEMINI_API_KEY',
                      'MISTRAL_API_KEY', 'DEEPSEEK_BASE_URL'],
        'COMMUNICATION': ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'TELEGRAM_OWNER_CHAT_ID',
                          'SENDGRID_API_KEY', 'EMAIL_FROM', 'EMAIL_FROM_NAME', 'OWNER_EMAIL', 'OWNER_PHONE'],
        'PROSPECTION': ['SERPER_API_KEY', 'SERPER_API_KEY_DEFAULT', 'SERPER_API_KEY_1',
                        'APOLLO_API_KEY', 'HUNTER_API_KEY'],
        'PAYMENT': ['PAYPAL_ME_URL', 'PAYPAL_CLIENT_ID', 'PAYPAL_CLIENT_SECRET',
                    'PAYPAL_WEBHOOK_SECRET',
                    'STRIPE_PUBLISHABLE_KEY', 'STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET',
                    'DEBLOCK_ME_URL', 'REVOLUT_ME_URL'],
        'ECOMMERCE & SOCIAL': ['SHOPIFY_SHOP_NAME', 'SHOPIFY_SHOP_URL', 'SHOPIFY_SHOP_DOMAIN',
                                'SHOPIFY_ACCESS_TOKEN', 'SHOPIFY_WEBHOOK_SECRET',
                                'TIKTOK_ACCESS_TOKEN', 'TIKTOK_USERNAME', 'TIKTOK_BUSINESS_ID',
                                'INSTAGRAM_ID', 'INSTAGRAM_USERNAME', 'FACEBOOK_PAGE_ID',
                                'WHATSAPP_PHONE', 'WHATSAPP_ID', 'WHATSAPP_LINK', 'WHATSAPP_BUSINESS_ID'],
        'INFRASTRUCTURE': ['NOTION_TOKEN', 'N8N_API_KEY', 'DASHBOARD_SHEET_URL',
                           'GOOGLE_CLOUD_PROJECT', 'GOOGLE_PROJECT_NUMBER', 'GOOGLE_APPLICATION_CREDENTIALS',
                           'GOOGLE_OAUTH_CLIENT_ID', 'GOOGLE_OAUTH_CLIENT_SECRET',
                           'GOOGLE_OAUTH_REFRESH_TOKEN', 'GOOGLE_OAUTH_ACCESS_TOKEN',
                           'SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_SERVICE_KEY', 'SUPABASE_PROJECT_REF'],
        'DEPLOYMENT': ['RENDER_API_KEY', 'VERCEL_TOKEN', 'VERCEL_AI_KEY',
                       'DOCKER_USERNAME', 'DOCKER_TOKEN',
                       'OLLAMA_API_KEY'],
        'SYSTEM': ['ENVIRONMENT', 'DEBUG', 'LOG_LEVEL', 'SECRET_KEY', 'ENCRYPTION_KEY', 'JWT_SECRET'],
    }

    lines = [
        "# ==================== NAYA V19 — CONFIGURATION ====================",
        "# Auto-généré par scripts/parse_raw_keys.py",
        "# NE PAS COMMITTER CE FICHIER",
        "",
    ]

    for category, keys_list in categories.items():
        found_any = any(k in all_keys for k in keys_list)
        if not found_any:
            continue

        lines.append(f"# === {category} ===")
        for key in keys_list:
            if key in all_keys:
                val = all_keys[key]
                # Échapper les valeurs avec espaces ou caractères spéciaux
                if ' ' in val or any(c in val for c in ['#', '$', '"', "'"]):
                    val = f'"{val}"'
                lines.append(f"{key}={val}")
        lines.append("")

    # Ajouter toutes les autres clés non catégorisées
    categorized = set(k for keys in categories.values() for k in keys)
    others = {k: v for k, v in all_keys.items() if k not in categorized}

    if others:
        lines.append("# === AUTRES ===")
        for key, val in sorted(others.items()):
            if ' ' in val or any(c in val for c in ['#', '$', '"', "'"]):
                val = f'"{val}"'
            lines.append(f"{key}={val}")
        lines.append("")

    # Écrire le fichier
    OUTPUT_FILE.write_text('\n'.join(lines), encoding='utf-8')
    print(f"✅ Fichier .env créé: {OUTPUT_FILE}")
    print(f"   {len(all_keys)} variables au total")
    print(f"   {len(keys)} nouvelles clés extraites du raw dump")


def main():
    print("="*70)
    print("🔐 NAYA V19 — PARSE RAW KEYS DUMP")
    print("="*70)

    print(f"\n📂 Lecture: {RAW_FILE}")
    keys = parse_raw_dump()

    print(f"\n✅ {len(keys)} clés extraites:")
    for key in sorted(keys.keys()):
        val = keys[key]
        # Masquer la clé (afficher seulement début/fin)
        if len(val) > 20:
            display = f"{val[:10]}...{val[-8:]}"
        else:
            display = f"{val[:4]}...{val[-2:]}"
        print(f"   • {key}: {display}")

    print(f"\n📝 Écriture: {OUTPUT_FILE}")
    write_env_file(keys)

    print("\n✅ TERMINÉ")
    print("   Vous pouvez maintenant lancer:")
    print("   python scripts/check_api_keys.py --diagnostic")


if __name__ == "__main__":
    main()
