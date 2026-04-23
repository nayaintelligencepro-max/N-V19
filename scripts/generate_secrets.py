"""
NAYA V19 — Générateur de secrets forts
Génère des valeurs cryptographiquement sûres pour toutes les variables sensibles.

Usage:
    py scripts/generate_secrets.py           # Afficher les nouvelles valeurs
    py scripts/generate_secrets.py --apply   # Mettre à jour .env directement
    py scripts/generate_secrets.py --check   # Vérifier les secrets faibles actuels
"""
import secrets
import string
import os
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"

# Variables à générer avec leur longueur cible
SECRET_SPECS: dict[str, int] = {
    "SECRET_KEY":        64,
    "JWT_SECRET":        64,
    "ENCRYPTION_KEY":    32,
    "VAULT_KEY":         32,
}

# Variables avec valeurs fixes à remplacer si faibles
FIXED_REPLACEMENTS: dict[str, str] = {
    "GRAFANA_PASSWORD":  None,   # Générer automatiquement (16 chars alphanum)
    "DB_PASSWORD":       None,
    "RABBITMQ_PASSWORD": None,
}


def generate_token(length: int = 64) -> str:
    """Génère un token hexadécimal cryptographiquement sûr."""
    return secrets.token_hex(length // 2)


def generate_password(length: int = 16) -> str:
    """Génère un mot de passe alphanumérique sûr (sans caractères spéciaux problématiques)."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def check_weak_secrets() -> list[str]:
    """Retourne la liste des variables faibles dans .env."""
    sys.path.insert(0, str(ROOT))
    try:
        from SECRETS.secrets_loader import _WEAK_DEFAULTS, validate_production_secrets
        # Charger .env temporairement
        if ENV_FILE.exists():
            for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
        return validate_production_secrets(raise_on_weak=False)
    except ImportError:
        # Fallback si module non importable
        weak = []
        weak_prefixes = {
            "SECRET_KEY": "naya-supreme-v19-production-key",
            "JWT_SECRET": "naya-jwt-secret-key-2024",
            "ENCRYPTION_KEY": "naya-encryption-key-2024",
            "GRAFANA_PASSWORD": "admin",
            "DB_PASSWORD": "naya_secure_password",
            "RABBITMQ_PASSWORD": "naya_rabbitmq",
            "GRAFANA_USER": "admin",
            "VAULT_KEY": "naya",
        }
        if ENV_FILE.exists():
            content = ENV_FILE.read_text(encoding="utf-8")
            for var, prefix in weak_prefixes.items():
                m = re.search(rf"^{re.escape(var)}=(.+)$", content, re.MULTILINE)
                if m and m.group(1).strip().startswith(prefix):
                    weak.append(var)
        return weak


def generate_all() -> dict[str, str]:
    """Génère toutes les nouvelles valeurs."""
    new_vals: dict[str, str] = {}
    for var, length in SECRET_SPECS.items():
        new_vals[var] = generate_token(length)
    for var in FIXED_REPLACEMENTS:
        new_vals[var] = generate_password(20)
    return new_vals


def apply_to_env(new_vals: dict[str, str], env_path: Path) -> int:
    """Applique les nouvelles valeurs dans .env. Retourne le nombre de mises à jour."""
    if not env_path.exists():
        print(f"[ERREUR] Fichier introuvable: {env_path}")
        return 0

    content = env_path.read_text(encoding="utf-8")
    updated = 0

    for var, new_val in new_vals.items():
        pattern = rf"^({re.escape(var)}=).*$"
        replacement = rf"\g<1>{new_val}"
        new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
        if count > 0:
            content = new_content
            updated += 1
        else:
            # Variable absente — l'ajouter à la fin
            content += f"\n{var}={new_val}\n"
            updated += 1

    env_path.write_text(content, encoding="utf-8")
    return updated


def main():
    args = sys.argv[1:]

    if "--check" in args:
        print("Vérification des secrets faibles...")
        weak = check_weak_secrets()
        if weak:
            print(f"\n⚠️  {len(weak)} secret(s) faible(s) détecté(s):")
            for v in weak:
                print(f"  ❌ {v}")
            print("\nPour les corriger: py scripts/generate_secrets.py --apply")
        else:
            print("✅ Aucun secret faible détecté.")
        sys.exit(1 if weak else 0)

    new_vals = generate_all()

    if "--apply" in args:
        if not ENV_FILE.exists():
            print(f"[ERREUR] .env introuvable: {ENV_FILE}")
            sys.exit(1)
        # Sauvegarder une copie
        backup = ENV_FILE.with_suffix(".env.bak")
        backup.write_text(ENV_FILE.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Sauvegarde: {backup}")

        n = apply_to_env(new_vals, ENV_FILE)
        print(f"\n✅ {n} secret(s) mis à jour dans {ENV_FILE}")
        for var, val in new_vals.items():
            print(f"  {var}={val[:8]}...{val[-4:]}")
    else:
        print("Nouveaux secrets (copier-coller dans .env) :\n")
        for var, val in new_vals.items():
            print(f"{var}={val}")
        print("\nPour appliquer automatiquement: py scripts/generate_secrets.py --apply")


if __name__ == "__main__":
    main()
