from __future__ import annotations

import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from api import app
from core.auth import get_current_user

FAKE_USER = SimpleNamespace(id="test-user-id", email="test@example.com")


def _fake_auth():
    return FAKE_USER


def _make_supabase_mock() -> MagicMock:
    """Return a mock that satisfies the chained Supabase query pattern."""
    m = MagicMock()
    chain = m.table.return_value
    chain.select.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    chain.ilike.return_value = chain
    chain.eq.return_value = chain
    chain.single.return_value = chain
    chain.execute.return_value = MagicMock(data=[])
    return m


@pytest.fixture
def client():
    mock_supa = _make_supabase_mock()
    app.dependency_overrides[get_current_user] = _fake_auth
    with (
        patch("api.supabase", mock_supa),
        patch("core.db.supabase", mock_supa),
        patch("api._run_job"),
        patch("api._run_regenerate_job"),
        patch("core.analytics.supabase", mock_supa),
    ):
        yield TestClient(app)
    app.dependency_overrides.clear()
