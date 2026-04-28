"""SERVICE_3_SAP_ARIBA — service definition (deduplicated)."""

from NAYA_PROJECT_ENGINE.business.common.base_service_definition import BaseNayaService


class NayaService(BaseNayaService):
    """SAP Ariba-specific service implementation via shared base."""

    def __init__(self) -> None:
        super().__init__(class_label="SERVICE_3_SAP_ARIBA.NayaService")


