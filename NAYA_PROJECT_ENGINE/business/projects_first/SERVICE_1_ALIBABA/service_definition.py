"""SERVICE_1_ALIBABA — service definition (deduplicated)."""

from NAYA_PROJECT_ENGINE.business.common.base_service_definition import BaseNayaService


class NayaService(BaseNayaService):
    """Alibaba-specific service implementation via shared base."""

    def __init__(self) -> None:
        super().__init__(class_label="SERVICE_1_ALIBABA.NayaService")

