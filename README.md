# atlas-przetargow-mcp-py

[Polski](README.pl.md)

Atlas Przetargow Polish public procurement API MCP server. A Python/FastMCP rewrite of the official TypeScript server with several upstream bugs fixed and new tender-analysis tools added.

## Table of contents

- [Tools](#tools)
- [Fixed vs upstream TS server](#fixed-vs-upstream-ts-server)
- [Environment variables](#environment-variables)
- [Wiring it up](#wiring-it-up)
- [Local run](#local-run)

## Tools

| Tool | Parameters | Description |
|------|-----------|------|
| `search_tenders` | `search?, buyer_nip?, cpv?, city?, province?, notice_type?, order_kind?, date_from?, date_to?, value_min?, value_max?, sort?, page=1, limit=20` | Search BZP + TED tenders with filters |
| `get_tender` | `tender_id: str, full: bool = False` | Tender details; `full=True` includes complete notice text |
| `get_tender_timeline` | `tender_id: str` | Full notice chain of a procedure (announcement, revisions, result, performance) |
| `get_tender_offers` | `tender_id: str` | Offers count and lowest/highest/winning prices from result notices |
| `extract_contract_value` | `tender_id: str` | Contract/order money amounts extracted from notice text |
| `get_buyer` | `nip: str, include_winning_contractors: bool = True` | Buyer profile + contractors that most often win its tenders |
| `get_contractor` | `nip: str, include_winning_buyers: bool = True` | Contractor profile with win geography + top buyers |
| `search_entities` | `query: str, entity_type?, limit=10` | Find buyers/contractors by name (returns NIP) |
| `search_cpv` | `query: str, limit=10` | Look up CPV codes by Polish keyword |
| `get_category_stats` | `cpv: str, window="year"` | Category stats: count, median value, avg offers, avg deadline |
| `get_province_stats` | `province?, city?` | Province ranking, single province, or city drill-down |
| `raw_request` | `path: str, params_json?` | Escape hatch: GET any `/api/*` endpoint |

## Fixed vs upstream TS server

Bugs found while testing `@atlasprzetargow/mcp` v0.1.1:

1. `buyerNip` filter sent as `buyerNip` while the API expects `buyer_nip` — filter silently ignored. Fixed here.
2. `get_buyer` winning contractors read from `winners.contractors` while the API returns `{"data": [...]}` — section never rendered. Fixed here.
3. City stats returned an empty header although `/api/stats/city/{city}/top-buyers` returns data. Fixed here.
4. `get_category_stats` requested window can be ignored by the API (asks for year, returns 90 days) — this server returns the actual `days` value so the discrepancy is visible.
5. `get_contractor` returned 3 lines; this server returns the full profile (win geography, shares) plus winning buyers.

New tools not present upstream: `get_tender_timeline`, `get_tender_offers`, `extract_contract_value`, `raw_request`.

## Environment variables

| Variable | Required | Description |
|---------|----------|------|
| `ATLAS_PRZETARGOW_MCP_PY_API_BASE` | no | API base (default `https://atlasprzetargow.pl`) |
| `ATLAS_PRZETARGOW_MCP_PY_API_KEY` | no | Key for `/api/llm/*` AI summary endpoints |
| `ATLAS_PRZETARGOW_MCP_PY_TIMEOUT` | no | Request timeout in seconds (default 20) |

## Wiring it up

Only requirement: `uv` (https://docs.astral.sh/uv/). Nothing else to install.

### Claude Code

```
claude mcp add atlas-przetargow-mcp-py -- uvx --from git+https://github.com/dam2452/atlas-przetargow-mcp-py.git atlas-przetargow-mcp-py
```

### Claude Desktop / other MCP client

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

After pushing a new version: `uv cache clean` and restart the client.

## Local run

```
uv run --directory . atlas-przetargow-mcp-py
```

Tests (manual):

```
uv run --directory . --with pytest pytest test/
```
