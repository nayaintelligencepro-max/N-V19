"""
NAYA PROJECT ENGINE V19
Core-Level Industrial Engine — Autonome, Souverain, Productif.
"""
# Execution guard instantiation (pas d'import de fonction standalone)
try:
    from .industrial.execution_guard import ExecutionGuard as _EG
    _EG().enforce_entrypoint_execution()
except Exception:
    pass  # Boot gracieux — ne jamais bloquer le démarrage
