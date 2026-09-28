import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

from config import Config


@pytest.fixture(autouse=True)
def offline_brain_only(monkeypatch):
    # backend/.env may hold a real GEMINI_API_KEY; tests must never call a paid, non-deterministic API.
    monkeypatch.setattr(Config, 'BRAIN_MODE', 'offline')
