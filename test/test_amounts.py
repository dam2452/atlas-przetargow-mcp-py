from unittest.mock import MagicMock, patch

from atlas_przetargow_mcp_py import server


_BODY = (
    "<p>4) Wartość umowy: 443107,50 PLN 5) Łączna wartość wynagrodzenia "
    "wypłacona z tytułu zrealizowanej umowy: 443107,50 PLN</p>"
    "<p>Cena lub koszt oferty z najniższą ceną: 97883,4 PLN "
    "Cena lub koszt oferty wykonawcy, któremu udzielono zamówienia: 120991,52 PLN</p>"
)


class TestAmountExtraction:
    @patch.object(server, "_client")
    def test_extract_contract_value(self, client_factory: MagicMock) -> None:
        client_factory.return_value.get_tender.return_value = {
            "title": "T",
            "noticeType": "ContractPerformingNotice",
            "estimatedValue": None,
            "htmlBody": _BODY,
        }

        result = server.extract_contract_value("X")

        assert result["amounts_pln"]["contract_value"] == ["443107,50"]
        assert result["amounts_pln"]["total_paid"] == ["443107,50"]
        assert result["amounts_pln"]["lowest_offer"] == ["97883,4"]
        assert result["amounts_pln"]["winning_offer"] == ["120991,52"]

    @patch.object(server, "_client")
    def test_get_tender_offers(self, client_factory: MagicMock) -> None:
        client_factory.return_value.get_tender.return_value = {
            "noticeType": "TenderResultNotice",
            "offersCount": 4,
            "procedureResult": "zawarcieUmowy",
            "htmlBody": "<p>Liczba ofert: 4</p>",
        }

        result = server.get_tender_offers("X")

        assert result["offers_count_field"] == 4
        assert result["offers_count_text"] == ["4"]
