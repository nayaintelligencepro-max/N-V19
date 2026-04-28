"""NAYA — Activation Queue"""
from .SERVICE_1_ALIBABA.service_entry import run as run_alibaba
from .SERVICE_2_SAMSUNG.service_entry import run as run_samsung
from .SERVICE_3_SAP_ARIBA.service_entry import run as run_sap_ariba

SERVICE_QUEUE = ["SERVICE_1_ALIBABA", "SERVICE_2_SAMSUNG", "SERVICE_3_SAP_ARIBA"]
__all__ = ["run_alibaba", "run_samsung", "run_sap_ariba", "SERVICE_QUEUE"]
