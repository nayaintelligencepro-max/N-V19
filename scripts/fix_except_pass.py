"""
NAYA V19 — Migration : except:pass → except as _e: log.debug(...)
Transforme les silences d'exception en logs debug explicites.

Usage:
    py scripts/fix_except_pass.py --dry-run   # Preview des changements
    py scripts/fix_except_pass.py --apply     # Appliquer les changements
    py scripts/fix_except_pass.py --report    # Rapport seul (aucune modification)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Patterns à transformer
# Cas 1 : except Exception:  (suivi de pass sur la ligne suivante, indenté)
# Cas 2 : except Exception: pass  (inline)
# Cas 3 : except:  (bare, suivi de pass)
# Cas 4 : except: pass  (bare inline)

PATTERN_INLINE = re.compile(
    r'^(?P<indent>[ \t]*)except(?P<exc>\s+\w[\w.]*(?:\s+as\s+\w+)?)?:\s+pass\s*$',
    re.MULTILINE
)
PATTERN_BLOCK_HEADER = re.compile(
    r'^(?P<indent>[ \t]*)except(?P<exc>\s+\w[\w.]*(?:\s+as\s+\w+)?)?\s*:\s*$',
    re.MULTILINE
)

# Répertoires à traiter
TARGET_DIRS = [
    ROOT / "NAYA_CORE",
]

# Fichiers à exclure (déjà corrigés manuellement)
EXCLUDE_FILES = {
    "api/main.py",
}


def needs_log_import(content: str) -> bool:
    """Vérifie si le module a déjà un logger `log` ou `logger`."""
    return bool(re.search(r'\blog\s*=\s*logging\.getLogger\b', content) or
                re.search(r'\blogger\s*=\s*logging\.getLogger\b', content))


def transform_content(content: str, filepath: Path) -> tuple[str, int]:
    """
    Transforme les `except: pass` en `except as _e: log.debug(...)`.
    Retourne (nouveau_contenu, nombre_de_remplacements).
    """
    lines = content.splitlines(keepends=True)
    new_lines = list(lines)
    changes = 0
    log_var = "log" if re.search(r'\blog\s*=\s*logging', content) else \
              "logger" if re.search(r'\blogger\s*=\s*logging', content) else None

    i = 0
    while i < len(new_lines):
        line = new_lines[i]
        stripped = line.rstrip('\n\r')

        # Cas 1 : except Something: pass  (inline)
        m_inline = re.match(r'^(?P<indent>[ \t]*)except(?P<exc>[^:]*)?:\s+pass\s*$', stripped)
        if m_inline:
            indent = m_inline.group('indent')
            exc_part = m_inline.group('exc').strip() if m_inline.group('exc') else ''
            # Construire le nouveau handler
            if exc_part and 'as ' not in exc_part:
                new_except = f"{indent}except {exc_part} as _e:"
            elif not exc_part:
                new_except = f"{indent}except Exception as _e:"
            else:
                new_except = f"{indent}except {exc_part}:"

            if log_var:
                new_body = f"{indent}    {log_var}.debug(\"[suppressed] %s: %s\", type(_e).__name__, _e)"
            else:
                new_body = f"{indent}    pass  # suppressed: use log = logging.getLogger(__name__) to enable logging"

            new_lines[i] = new_except + '\n'
            new_lines.insert(i + 1, new_body + '\n')
            changes += 1
            i += 2
            continue

        # Cas 2 : except Something:  (header only)
        #         pass  (next non-empty line is just pass)
        m_header = re.match(r'^(?P<indent>[ \t]*)except(?P<exc>[^:]*)?:\s*$', stripped)
        if m_header and i + 1 < len(new_lines):
            next_line = new_lines[i + 1].rstrip('\n\r')
            header_indent = m_header.group('indent')
            m_pass = re.match(r'^(?P<indent>[ \t]*)pass\s*$', next_line)
            if m_pass and m_pass.group('indent') == header_indent + '    ':
                exc_part = m_header.group('exc').strip() if m_header.group('exc') else ''
                # Rebuild header with 'as _e'
                if exc_part and 'as ' not in exc_part:
                    new_header = f"{header_indent}except {exc_part} as _e:"
                elif not exc_part:
                    new_header = f"{header_indent}except Exception as _e:"
                else:
                    new_header = f"{header_indent}except {exc_part}:"

                if log_var:
                    new_body = f"{header_indent}    {log_var}.debug(\"[suppressed] %s: %s\", type(_e).__name__, _e)"
                else:
                    new_body = f"{header_indent}    pass  # suppressed: {exc_part or 'Exception'}"

                new_lines[i] = new_header + '\n'
                new_lines[i + 1] = new_body + '\n'
                changes += 1
                i += 2
                continue

        i += 1

    return ''.join(new_lines), changes


def run(apply: bool = False, dry_run: bool = True) -> None:
    total_files = 0
    total_changes = 0
    report_lines = []

    for target_dir in TARGET_DIRS:
        for py_file in sorted(target_dir.rglob("*.py")):
            # Check exclusions
            rel = py_file.relative_to(target_dir)
            if str(rel).replace("\\", "/") in EXCLUDE_FILES:
                continue

            try:
                original = py_file.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                print(f"[SKIP] {py_file}: {e}")
                continue

            new_content, n = transform_content(original, py_file)

            if n > 0:
                total_files += 1
                total_changes += n
                rel_path = py_file.relative_to(ROOT)
                report_lines.append(f"  {rel_path}: {n} fix(es)")

                if apply and not dry_run:
                    # Backup
                    backup = py_file.with_suffix(".py.bak")
                    backup.write_text(original, encoding="utf-8")
                    py_file.write_text(new_content, encoding="utf-8")

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Résultat:")
    print(f"  Fichiers affectés : {total_files}")
    print(f"  Remplacements     : {total_changes}")

    if report_lines:
        print("\nDétail:")
        for line in report_lines:
            print(line)

    if dry_run and total_changes > 0:
        print("\nPour appliquer: py scripts/fix_except_pass.py --apply")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--apply" in args:
        print("Application des corrections...")
        run(apply=True, dry_run=False)
    elif "--report" in args:
        run(apply=False, dry_run=True)
    else:
        # Default: dry-run
        run(apply=False, dry_run=True)
