from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


def pytest_configure(config):
    config.addinivalue_line("markers", "anyio: run async tests with anyio")


@pytest.fixture
def anyio_backend():
    return "asyncio"
