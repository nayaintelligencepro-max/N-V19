"""Tests for core NAYA modules - kernel, memory, pipeline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_kernel_contract_validator():
    from KERNEL.contract_validator import ContractValidator
    cv = ContractValidator()
    assert hasattr(cv, "validate")


def test_kernel_activation_controller():
    from KERNEL.activation_controller import ActivationController
    ac = ActivationController()
    assert hasattr(ac, "activate")


def test_version_manager():
    from VERSION_CONTROL.version_manager import VersionManager
    vm = VersionManager()
    assert hasattr(vm, "get_version")


def test_event_bus():
    from EVENT_STREAMING.event_bus import EventBus
    eb = EventBus()
    assert hasattr(eb, "publish")
    assert hasattr(eb, "subscribe")


def test_pipeline_tracker():
    from NAYA_REVENUE_ENGINE.pipeline_tracker import PipelineTracker
    pt = PipelineTracker()
    kpis = pt.get_kpis()
    assert isinstance(kpis, dict)


def test_zero_waste_recycler():
    from ZERO_WASTE.zero_waste_recycler import ZeroWasteRecycler
    zw = ZeroWasteRecycler()
    assert hasattr(zw, "recycle")


def test_secrets_loader():
    from SECRETS.secrets_loader import load_all_secrets
    result = load_all_secrets(verbose=False)
    assert "real_keys" in result


def test_system_identity():
    import configparser
    config = configparser.ConfigParser()
    config.read(str(Path(__file__).parent.parent / "SYSTEM_IDENTITY.ini"))
    assert config.get("SYSTEM", "name") == "NAYA SUPREME"
    assert config.get("SYSTEM", "version") == "19.0.0"
    assert config.get("SYSTEM", "status") == "production"


def test_env_example_exists():
    env_example = Path(__file__).parent.parent / ".env.example"
    assert env_example.exists()
    content = env_example.read_text()
    assert "OPENAI_API_KEY" in content
    assert "SENDGRID_API_KEY" in content
    assert "TELEGRAM_BOT_TOKEN" in content


def test_dockerfile_exists():
    dockerfile = Path(__file__).parent.parent / "Dockerfile"
    assert dockerfile.exists()
    content = dockerfile.read_text()
    assert "python:3.11" in content
    assert "uvicorn" in content


def test_docker_compose_exists():
    dc = Path(__file__).parent.parent / "docker-compose.yml"
    assert dc.exists()
    content = dc.read_text()
    assert "postgres" in content
    assert "redis" in content


def test_gitignore_covers_secrets():
    gitignore = Path(__file__).parent.parent / ".gitignore"
    assert gitignore.exists()
    content = gitignore.read_text()
    assert ".env" in content


def test_schema_sql_exists():
    schema = Path(__file__).parent.parent / "PERSISTENCE" / "database" / "schema.sql"
    assert schema.exists()
    content = schema.read_text()
    assert "CREATE TABLE" in content
    assert "prospects" in content
    assert "deals" in content
    assert "payments" in content
