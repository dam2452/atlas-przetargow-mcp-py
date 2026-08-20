# atlas-przetargow-mcp-py

[English](README.md)

Serwer MCP do API Atlas Przetargów (polskie zamówienia publiczne, BZP + TED). Przepisana na Python/FastMCP wersja oficjalnego serwera TypeScript — z naprawionymi bugami upstream i nowymi narzędziami analitycznymi.

## Spis treści

- [Toole](#toole)
- [Naprawione bugi vs upstream TS](#naprawione-bugi-vs-upstream-ts)
- [Zmienne środowiskowe](#zmienne-środowiskowe)
- [Podpięcie](#podpięcie)
- [Uruchomienie lokalne](#uruchomienie-lokalne)

## Toole

| Tool | Parametry | Opis |
|------|-----------|------|
| `search_tenders` | `search?, buyer_nip?, cpv?, city?, province?, notice_type?, order_kind?, date_from?, date_to?, value_min?, value_max?, sort?, page=1, limit=20` | Wyszukiwanie przetargów BZP + TED z filtrami |
| `get_tender` | `tender_id: str, full: bool = False` | Szczegóły przetargu; `full=True` dołącza pełną treść ogłoszenia |
| `get_tender_timeline` | `tender_id: str` | Pełny łańcuch ogłoszeń postępowania (ogłoszenie, zmiany, wynik, wykonanie) |
| `get_tender_offers` | `tender_id: str` | Liczba ofert oraz ceny najniższa/najwyższa/wybrana z ogłoszeń wynikowych |
| `extract_contract_value` | `tender_id: str` | Kwoty umów/zamówień wyciągnięte z treści ogłoszenia |
| `get_buyer` | `nip: str, include_winning_contractors: bool = True` | Profil zamawiającego + wykonawcy najczęściej wygrywający jego przetargi |
| `get_contractor` | `nip: str, include_winning_buyers: bool = True` | Profil wykonawcy z geografią wygranych + top zamawiający |
| `search_entities` | `query: str, entity_type?, limit=10` | Szukanie zamawiających/wykonawców po nazwie (zwraca NIP) |
| `search_cpv` | `query: str, limit=10` | Kody CPV po polskim słowie kluczowym |
| `get_category_stats` | `cpv: str, window="year"` | Statystyki kategorii: liczba, mediana wartości, średnia ofert, termin |
| `get_province_stats` | `province?, city?` | Ranking województw, jedno województwo lub drill-down miasta |
| `raw_request` | `path: str, params_json?` | Wentyl: GET dowolny endpoint `/api/*` |

## Naprawione bugi vs upstream TS

Bugi znalezione przy testowaniu `@atlasprzetargow/mcp` v0.1.1:

1. Filtrowanie po zamawiającym wysyłane jako `buyerNip`, a API oczekuje `buyer_nip` — filtr ignorowany. Naprawione.
2. `get_buyer` czytał wykonawców z `winners.contractors`, a API zwraca `{"data": [...]}` — sekcja nigdy się nie pojawiała. Naprawione.
3. Statystyki miast zwracały pusty nagłówek, mimo że `/api/stats/city/{miasto}/top-buyers` zwraca dane. Naprawione.
4. `get_category_stats` — API potrafi ignorować żądane okno czasowe (prośba o rok, odpowiedź 90 dni) — ten serwer zwraca faktyczne `days`, żeby rozbieżność była widoczna.
5. `get_contractor` zwracał 3 linijki; ten serwer zwraca pełny profil (geografia wygranych, udziały) plus top zamawiających.

Nowe narzędzia nieobecne w upstream: `get_tender_timeline`, `get_tender_offers`, `extract_contract_value`, `raw_request`.

## Zmienne środowiskowe

| Zmienna | Wymagana | Opis |
|---------|----------|------|
| `ATLAS_PRZETARGOW_MCP_PY_API_BASE` | nie | Baza API (default `https://atlasprzetargow.pl`) |
| `ATLAS_PRZETARGOW_MCP_PY_API_KEY` | nie | Klucz do endpointów AI `/api/llm/*` |
| `ATLAS_PRZETARGOW_MCP_PY_TIMEOUT` | nie | Timeout zapytań w sekundach (default 20) |

## Podpięcie

Wymagany tylko `uv` (https://docs.astral.sh/uv/). Nic więcej nie trzeba instalować.

### Claude Code

```
claude mcp add atlas-przetargow-mcp-py -- uvx --from git+https://github.com/dam2452/atlas-przetargow-mcp-py.git atlas-przetargow-mcp-py
```

### Claude Desktop / inny klient MCP

```json
{
  "mcpServers": {
    "atlas-przetargow-mcp-py": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/dam2452/atlas-przetargow-mcp-py.git", "atlas-przetargow-mcp-py"]
    }
  }
}
```

Po pushu nowej wersji: `uv cache clean` i restart klienta.

## Uruchomienie lokalne

```
uv run --directory . atlas-przetargow-mcp-py
```

Testy (ręcznie):

```
uv run --directory . --with pytest pytest test/
```
