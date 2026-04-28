"""NAYA SUPREME V19 — Workflows LangGraph.

Les imports sont volontairement protégés pour éviter les échecs au chargement du
package lorsqu'un sous-module est partiellement indisponible.
"""

import logging

log = logging.getLogger("NAYA.WORKFLOWS")

__all__ = []

try:
    from .prospection_workflow import ProspectionWorkflow
    __all__.append("ProspectionWorkflow")
except Exception as exc:
    log.debug("Workflow import skipped: prospection_workflow (%s)", exc)

try:
    from .audit_workflow import run_audit, AuditState
    __all__.extend(["run_audit", "AuditState"])
except Exception as exc:
    log.debug("Workflow import skipped: audit_workflow (%s)", exc)

try:
    from .closing_workflow import run_closing, ClosingState
    __all__.extend(["run_closing", "ClosingState"])
except Exception as exc:
    log.debug("Workflow import skipped: closing_workflow (%s)", exc)

try:
    from .content_workflow import content_workflow, run_content_workflow
    __all__.extend(["content_workflow", "run_content_workflow"])
except Exception as exc:
    log.debug("Workflow import skipped: content_workflow (%s)", exc)

try:
    from .node_registry import node_registry, NodeCategory
    __all__.extend(["node_registry", "NodeCategory"])
except Exception as exc:
    log.debug("Workflow import skipped: node_registry (%s)", exc)
