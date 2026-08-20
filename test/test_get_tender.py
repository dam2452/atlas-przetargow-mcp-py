from typing import Any, Dict
from unittest.mock import MagicMock, patch

from atlas_przetargow_mcp_py import server


def _detail() -> Dict[str, Any]:
    return {
        "id": "2026/BZP 00276746",
        "title": "Dostawa",
        "htmlBody": "<p>body</p>",
        "estimatedValue": 443107.5,
    }


class TestGetTender:
    @patch.object(server, "_client")
    def test_strips_html_body_by_default(self, client_factory: MagicMock) -> None:
        client_factory.return_value.get_tender.return_value = _detail()

        result = server.get_tender("2026/BZP 00276746")

        assert "htmlBody" not in result
        assert result["estimatedValue"] == 443107.5

    @patch.object(server, "_client")
    def test_full_keeps_html_body(self, client_factory: MagicMock) -> None:
        client_factory.return_value.get_tender.return_value = _detail()

        result = server.get_tender("2026/BZP 00276746", full=True)

        assert result["htmlBody"] == "<p>body</p>"

    @patch.object(server, "_client")
    def test_timeline(self, client_factory: MagicMock) -> None:
        client_factory.return_value.get_tender.return_value = {
            "title": "T",
            "timeline": [{"id": "a"}, {"id": "b"}],
        }

        result = server.get_tender_timeline("X")

        assert result["timeline"] == [{"id": "a"}, {"id": "b"}]
