from unittest.mock import MagicMock, patch

import pytest

from atlas_przetargow_mcp_py import server


class TestStats:
    @patch.object(server, "_client")
    def test_category_stats_passes_window(self, client_factory: MagicMock) -> None:
        client_factory.return_value.get.return_value = {"days": 90}

        result = server.get_category_stats("302", window="year")

        client_factory.return_value.get.assert_called_once_with(
            "/api/tenders/agg/category-stats", params={"cpv": "302", "window": "year"}
        )
        assert result == {"days": 90}

    @patch.object(server, "_client")
    def test_province_filters_by_value_field(self, client_factory: MagicMock) -> None:
        client_factory.return_value.get.return_value = {
            "data": [{"total": 327072, "value": "PL12"}, {"total": 652370, "value": "PL14"}]
        }

        result = server.get_province_stats(province="PL12")

        assert result["stats"] == [{"total": 327072, "value": "PL12"}]

    @patch.object(server, "_client")
    def test_unknown_province_raises(self, client_factory: MagicMock) -> None:
        client_factory.return_value.get.return_value = {"data": []}

        with pytest.raises(ValueError, match="PL99|province"):
            server.get_province_stats(province="PL12")

    @patch.object(server, "_client")
    def test_city_stats(self, client_factory: MagicMock) -> None:
        client = client_factory.return_value
        client.get.side_effect = [
            {"city": "Kraków", "topBuyers": []},
            {"city": "Kraków", "topCpv": []},
        ]

        result = server.get_province_stats(city="Kraków")

        assert result["topBuyers"] == []
        assert result["top_cpv"] == {"city": "Kraków", "topCpv": []}

    @patch.object(server, "_client")
    def test_search_cpv(self, client_factory: MagicMock) -> None:
        client_factory.return_value.get.return_value = []

        server.search_cpv("komputer", limit=5)

        client_factory.return_value.get.assert_called_once_with(
            "/api/cpv/search", params={"q": "komputer", "limit": 5}
        )
