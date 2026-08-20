from unittest.mock import MagicMock, patch

from atlas_przetargow_mcp_py import server


class TestSearchTenders:
    @patch.object(server, "_client")
    def test_sends_buyer_nip_underscore_param(self, client_factory: MagicMock) -> None:
        client_factory.return_value.get.return_value = {"total": 0, "data": []}

        server.search_tenders(search="komputer", buyer_nip="6751199459")

        client_factory.return_value.get.assert_called_once_with(
            "/api/tenders",
            params={
                "search": "komputer",
                "buyer_nip": "6751199459",
                "cpv": None,
                "city": None,
                "province": None,
                "noticeType": None,
                "orderKind": None,
                "dateFrom": None,
                "dateTo": None,
                "valueMin": None,
                "valueMax": None,
                "sort": None,
                "page": 1,
                "per_page": 20,
            },
        )

    @patch.object(server, "_client")
    def test_clamps_limit(self, client_factory: MagicMock) -> None:
        client_factory.return_value.get.return_value = {"total": 0, "data": []}

        server.search_tenders(limit=500)

        assert client_factory.return_value.get.call_args.kwargs["params"]["per_page"] == 50
