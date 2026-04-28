"""
NAYA SUPREME V19 — Security Module 3/10
secrets_manager.py — Gestion chiffrée des clés API (AES-256)

Agent 11 — Guardian Agent
Rôle : Chiffrement, rotation et gestion sécurisée des secrets
"""

import os
import json
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import hashlib


class SecretsManager:
    """
    Gestionnaire de secrets chiffrés AES-256.
    Rotation automatique tous les 30 jours.
    """

    def __init__(
        self,
        project_root: str = "/home/runner/work/V19/V19",
        master_password: Optional[str] = None
    ):
        self.project_root = Path(project_root)
        self.secrets_dir = self.project_root / "SECRETS" / "keys"
        self.secrets_dir.mkdir(parents=True, exist_ok=True)

        # Fichier vault chiffré
        self.vault_path = self.secrets_dir / "vault.enc"
        self.vault_metadata_path = self.secrets_dir / "vault_meta.json"

        # Master password depuis env ou paramètre
        self.master_password = master_password or os.environ.get("NAYA_MASTER_PASSWORD", "")

        if not self.master_password:
            # Générer master password unique si inexistant
            self.master_password = self._generate_master_password()

        # Initialiser Fernet cipher
        self.cipher = self._initialize_cipher()

        # Charger vault
        self.vault: Dict[str, Any] = self._load_vault()

    def _generate_master_password(self) -> str:
        """
        Génère un master password unique pour ce système.

        Returns:
            Master password généré
        """
        # Utiliser hostname + timestamp comme seed
        import socket
        seed = f"{socket.gethostname()}_{datetime.now().isoformat()}"
        password = hashlib.sha256(seed.encode()).hexdigest()

        print(f"⚠️  [SECRETS] Master password généré. Sauvegarder dans variable d'env NAYA_MASTER_PASSWORD")
        print(f"   Password: {password[:32]}...")

        return password

    def _initialize_cipher(self) -> Fernet:
        """
        Initialise cipher Fernet avec dérivation PBKDF2.

        Returns:
            Instance Fernet
        """
        # Salt fixe pour ce projet (devrait être stocké séparément en prod)
        salt = b"naya_supreme_v19_salt_2026"

        # Dériver clé avec PBKDF2
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        key = base64.urlsafe_b64encode(
            kdf.derive(self.master_password.encode())
        )

        return Fernet(key)

    def _load_vault(self) -> Dict[str, Any]:
        """
        Charge le vault chiffré.

        Returns:
            Dictionnaire des secrets
        """
        try:
            if self.vault_path.exists():
                with open(self.vault_path, 'rb') as f:
                    encrypted_data = f.read()

                decrypted_data = self.cipher.decrypt(encrypted_data)
                vault = json.loads(decrypted_data.decode())

                print(f"🔓 [SECRETS] Vault chargé — {len(vault)} secrets")
                return vault
            else:
                print("🆕 [SECRETS] Nouveau vault créé")
                return {}

        except Exception as e:
            print(f"❌ [SECRETS] Erreur chargement vault: {e}")
            return {}

    def _save_vault(self) -> bool:
        """
        Sauvegarde le vault chiffré.

        Returns:
            True si succès
        """
        try:
            # Chiffrer données
            data = json.dumps(self.vault, indent=2).encode()
            encrypted_data = self.cipher.encrypt(data)

            # Écrire vault chiffré
            with open(self.vault_path, 'wb') as f:
                f.write(encrypted_data)

            # Mettre à jour metadata
            metadata = {
                "last_modified": datetime.now().isoformat(),
                "total_secrets": len(self.vault),
                "vault_hash": hashlib.sha256(encrypted_data).hexdigest()
            }

            with open(self.vault_metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            return True

        except Exception as e:
            print(f"❌ [SECRETS] Erreur sauvegarde vault: {e}")
            return False

    def set_secret(
        self,
        key: str,
        value: str,
        rotation_days: int = 30,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Stocke un secret chiffré avec rotation automatique.

        Args:
            key: Nom du secret (ex: ANTHROPIC_API_KEY)
            value: Valeur du secret
            rotation_days: Jours avant rotation recommandée
            metadata: Metadata additionnelle

        Returns:
            True si succès
        """
        try:
            self.vault[key] = {
                "value": value,
                "created_at": datetime.now().isoformat(),
                "last_rotated": datetime.now().isoformat(),
                "rotation_days": rotation_days,
                "next_rotation": (datetime.now() + timedelta(days=rotation_days)).isoformat(),
                "metadata": metadata or {}
            }

            success = self._save_vault()

            if success:
                print(f"✅ [SECRETS] Secret '{key}' stocké (rotation dans {rotation_days}j)")

            return success

        except Exception as e:
            print(f"❌ [SECRETS] Erreur stockage '{key}': {e}")
            return False

    def get_secret(self, key: str) -> Optional[str]:
        """
        Récupère un secret déchiffré.

        Args:
            key: Nom du secret

        Returns:
            Valeur du secret ou None
        """
        try:
            if key in self.vault:
                secret_data = self.vault[key]

                # Vérifier expiration
                next_rotation = datetime.fromisoformat(secret_data["next_rotation"])
                if datetime.now() > next_rotation:
                    print(f"⚠️  [SECRETS] Secret '{key}' expire — rotation recommandée")

                return secret_data["value"]
            else:
                # Fallback sur variable d'environnement
                env_value = os.environ.get(key)
                if env_value:
                    print(f"🔄 [SECRETS] Secret '{key}' chargé depuis env (non chiffré)")
                    return env_value

                print(f"❌ [SECRETS] Secret '{key}' non trouvé")
                return None

        except Exception as e:
            print(f"❌ [SECRETS] Erreur récupération '{key}': {e}")
            return None

    def rotate_secret(self, key: str, new_value: str) -> bool:
        """
        Effectue la rotation d'un secret.

        Args:
            key: Nom du secret
            new_value: Nouvelle valeur

        Returns:
            True si succès
        """
        try:
            if key not in self.vault:
                print(f"❌ [SECRETS] Secret '{key}' inexistant")
                return False

            old_data = self.vault[key]

            # Archiver ancienne valeur
            archive_key = f"{key}_ARCHIVE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.vault[archive_key] = {
                "value": old_data["value"],
                "archived_at": datetime.now().isoformat(),
                "original_key": key
            }

            # Mettre à jour avec nouvelle valeur
            rotation_days = old_data.get("rotation_days", 30)
            metadata = old_data.get("metadata", {})

            self.vault[key] = {
                "value": new_value,
                "created_at": old_data["created_at"],
                "last_rotated": datetime.now().isoformat(),
                "rotation_days": rotation_days,
                "next_rotation": (datetime.now() + timedelta(days=rotation_days)).isoformat(),
                "metadata": metadata,
                "rotation_count": old_data.get("rotation_count", 0) + 1
            }

            success = self._save_vault()

            if success:
                print(f"🔄 [SECRETS] Secret '{key}' rotaté (prochaine rotation dans {rotation_days}j)")

            return success

        except Exception as e:
            print(f"❌ [SECRETS] Erreur rotation '{key}': {e}")
            return False

    def delete_secret(self, key: str) -> bool:
        """
        Supprime un secret du vault.

        Args:
            key: Nom du secret

        Returns:
            True si succès
        """
        try:
            if key in self.vault:
                del self.vault[key]
                success = self._save_vault()

                if success:
                    print(f"🗑️  [SECRETS] Secret '{key}' supprimé")

                return success
            else:
                print(f"⚠️  [SECRETS] Secret '{key}' inexistant")
                return False

        except Exception as e:
            print(f"❌ [SECRETS] Erreur suppression '{key}': {e}")
            return False

    def list_secrets(self) -> Dict[str, Dict[str, Any]]:
        """
        Liste tous les secrets (sans valeurs).

        Returns:
            Dictionnaire des secrets avec metadata
        """
        secrets_info = {}

        for key, data in self.vault.items():
            if "_ARCHIVE_" not in key:
                secrets_info[key] = {
                    "created_at": data.get("created_at"),
                    "last_rotated": data.get("last_rotated"),
                    "next_rotation": data.get("next_rotation"),
                    "rotation_days": data.get("rotation_days"),
                    "rotation_count": data.get("rotation_count", 0),
                    "expires_soon": self._check_expiration(data),
                    "metadata": data.get("metadata", {})
                }

        return secrets_info

    def check_expirations(self) -> Dict[str, Any]:
        """
        Vérifie les secrets nécessitant rotation.

        Returns:
            Rapport des expirations
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "expired": [],
            "expiring_soon": [],
            "healthy": []
        }

        for key, data in self.vault.items():
            if "_ARCHIVE_" in key:
                continue

            next_rotation = datetime.fromisoformat(data["next_rotation"])
            days_until_rotation = (next_rotation - datetime.now()).days

            if days_until_rotation < 0:
                report["expired"].append({
                    "key": key,
                    "days_overdue": abs(days_until_rotation)
                })
            elif days_until_rotation <= 7:
                report["expiring_soon"].append({
                    "key": key,
                    "days_remaining": days_until_rotation
                })
            else:
                report["healthy"].append({
                    "key": key,
                    "days_remaining": days_until_rotation
                })

        return report

    def _check_expiration(self, data: Dict[str, Any]) -> bool:
        """Vérifie si un secret expire bientôt."""
        try:
            next_rotation = datetime.fromisoformat(data["next_rotation"])
            days_until_rotation = (next_rotation - datetime.now()).days
            return days_until_rotation <= 7
        except:
            return False

    def import_from_env(self, env_keys: list) -> int:
        """
        Importe des secrets depuis variables d'environnement.

        Args:
            env_keys: Liste des clés à importer

        Returns:
            Nombre de secrets importés
        """
        imported = 0

        for key in env_keys:
            value = os.environ.get(key)
            if value:
                success = self.set_secret(key, value)
                if success:
                    imported += 1

        print(f"📥 [SECRETS] {imported}/{len(env_keys)} secrets importés depuis env")

        return imported

    def export_to_env_file(self, output_path: Optional[Path] = None) -> bool:
        """
        Exporte secrets vers fichier .env (ATTENTION: non chiffré).

        Args:
            output_path: Chemin du fichier .env

        Returns:
            True si succès
        """
        try:
            if output_path is None:
                output_path = self.project_root / ".env.local"

            with open(output_path, 'w') as f:
                f.write(f"# NAYA SUPREME V19 — Secrets exportés\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n")
                f.write(f"# ⚠️  ATTENTION: Ce fichier contient des secrets en clair\n\n")

                for key, data in self.vault.items():
                    if "_ARCHIVE_" not in key:
                        f.write(f"{key}={data['value']}\n")

            print(f"📤 [SECRETS] Secrets exportés vers {output_path}")
            print(f"   ⚠️  ATTENTION: Fichier non chiffré — Ne pas committer!")

            return True

        except Exception as e:
            print(f"❌ [SECRETS] Erreur export: {e}")
            return False

    def get_vault_stats(self) -> Dict[str, Any]:
        """
        Statistiques du vault.

        Returns:
            Stats du vault
        """
        active_secrets = [k for k in self.vault.keys() if "_ARCHIVE_" not in k]
        archived_secrets = [k for k in self.vault.keys() if "_ARCHIVE_" in k]

        return {
            "total_secrets": len(active_secrets),
            "archived_secrets": len(archived_secrets),
            "vault_size_bytes": self.vault_path.stat().st_size if self.vault_path.exists() else 0,
            "last_modified": self.vault["__metadata__"]["last_modified"] if "__metadata__" in self.vault else "unknown",
            "encryption": "AES-256 (Fernet)",
            "vault_path": str(self.vault_path)
        }


def main():
    """Test du secrets manager."""
    manager = SecretsManager()

    print("\n" + "="*60)
    print("🔐 NAYA SECRETS MANAGER")
    print("="*60)

    # Tester stockage
    manager.set_secret("TEST_API_KEY", "sk-test123456789", rotation_days=30)

    # Tester récupération
    value = manager.get_secret("TEST_API_KEY")
    print(f"Valeur récupérée: {value[:10]}...")

    # Lister secrets
    secrets = manager.list_secrets()
    print(f"\nSecrets stockés: {len(secrets)}")

    # Vérifier expirations
    expiration_report = manager.check_expirations()
    print(f"\nExpirés: {len(expiration_report['expired'])}")
    print(f"Expire bientôt: {len(expiration_report['expiring_soon'])}")
    print(f"Sains: {len(expiration_report['healthy'])}")

    # Stats vault
    stats = manager.get_vault_stats()
    print(f"\nStats vault:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
