"""Compatibilité workflows CLAUDE.md -> NAYA_CORE.workflows.

Le package reste volontairement léger pour éviter les imports transitifs lourds.
Importer les sous-modules explicitement: ``workflows.prospection_workflow`` etc.
"""

__all__ = [
	"prospection_workflow",
	"audit_workflow",
	"content_workflow",
	"closing_workflow",
	"node_registry",
]
