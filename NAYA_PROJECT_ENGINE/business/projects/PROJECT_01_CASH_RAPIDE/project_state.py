"""PROJECT_01_CASH_RAPIDE — shared project state."""

from NAYA_PROJECT_ENGINE.business.projects.common.base_project_state import BaseProjectState


class ProjectState(BaseProjectState):
    def __init__(self) -> None:
        super().__init__(class_label="PROJECT_01_CASH_RAPIDE.ProjectState")
