"""SERVICE_2_SAMSUNG — service definition (deduplicated)."""

from NAYA_PROJECT_ENGINE.business.common.base_service_definition import BaseNayaService


class NayaService(BaseNayaService):
    """Samsung-specific service implementation via shared base."""

    def __init__(self) -> None:
        super().__init__(class_label="SERVICE_2_SAMSUNG.NayaService")


