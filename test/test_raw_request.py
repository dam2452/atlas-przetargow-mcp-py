from unittest.mock import MagicMock, patch

import pytest

from atlas_przetargow_mcp_py import server


class TestRawRequest:
    @patch.object(server, "_client")
    def test_gets_api_path(self, client_factory: MagicMock) -> None:
        client_factory.return_value.get.return_value = {"ok": True}

        result = server.raw_request("/api/tenders/agg/provinces")

        assert result == {"ok": True}
        client_factory.return_value.get.assert_called_once_with(
            "/api/tenders/agg/provinces", params=None
        )

    @patch.object(server, "_client")
    def test_rejects_non_api_path(self, client_factory: MagicMock) -> None:
        with pytest.raises(ValueError, match="/api/"):
            server.raw_request("/etc/passwd")

    @patch.object(server, "_client")
    def test_parses_params_json(self, client_factory: MagicMock) -> None:
        client_factory.return_value.get.return_value = {}

        server.raw_request("/api/entities/search", params_json='{"q": "gddkia"}')

        client_factory.return_value.get.assert_called_once_with(
            "/api/entities/search", params={"q": "gddkia"}
        )
