from unittest.mock import MagicMock, patch

from atlas_przetargow_mcp_py import server


class TestBuyer:
    @patch.object(server, "_client")
    def test_winning_contractors_from_data_key(self, client_factory: MagicMock) -> None:
        client = client_factory.return_value
        client.get.side_effect = [
            {"name": "Szpital"},
            {"data": [{"name": "Urtica", "wins": 12}]},
        ]

        result = server.get_buyer("6751199459")

        assert result["winning_contractors"] == [{"name": "Urtica", "wins": 12}]

    @patch.object(server, "_client")
    def test_contractor_winning_buyers(self, client_factory: MagicMock) -> None:
        client = client_factory.return_value
        client.get.side_effect = [
            {"displayName": "Blue Energy"},
            {"data": [{"name": "ZUOP"}]},
        ]

        result = server.get_contractor("7781473428")

        assert result["contractor"]["displayName"] == "Blue Energy"
        assert result["winning_buyers"] == [{"name": "ZUOP"}]

    @patch.object(server, "_client")
    def test_search_entities_q_param(self, client_factory: MagicMock) -> None:
        client_factory.return_value.get.return_value = []

        server.search_entities("szpital dziecięcy", entity_type="buyer")

        client_factory.return_value.get.assert_called_once_with(
            "/api/entities/search",
            params={"q": "szpital dziecięcy", "type": "buyer", "limit": 10},
        )
