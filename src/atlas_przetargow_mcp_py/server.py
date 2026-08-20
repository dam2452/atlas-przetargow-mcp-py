import html
import re
from typing import Any, Dict, List, Literal, Optional

from fastmcp import FastMCP

from atlas_przetargow_mcp_py.client import ApiClient
from atlas_przetargow_mcp_py.settings import Settings

mcp = FastMCP("atlas-przetargow-mcp-py")


def _client() -> ApiClient:
    return ApiClient(Settings.from_env())


def _notice_text(detail: Dict[str, Any]) -> str:
    body = html.unescape(re.sub(r"<[^>]+>", " ", str(detail.get("htmlBody", ""))))
    return re.sub(r"\s+", " ", body)


def _amounts(text: str) -> Dict[str, List[str]]:
    patterns = {
        "contract_value": r"Warto[sś][cć][^:.]{0,15}umowy:\s*([\d\s,.]+)\s*(?:PLN|z[łl])",
        "total_paid": r"[Łł][aą]czna warto[sś][cć][^:.]{0,60}:\s*([\d\s,.]+)\s*(?:PLN|z[łl])",
        "estimated_value": r"Warto[sś][cć][^:.]{0,25}zam[óo]wienia[^:.]*:\s*([\d\s,.]+)\s*(?:PLN|z[łl])",
        "lowest_offer": r"(?:najni[sżz]sz[aą][^:.]{0,30}):\s*([\d\s,.]+)\s*(?:PLN|z[łl])",
        "highest_offer": r"(?:najwy[sżz]sz[aą][^:.]{0,30}):\s*([\d\s,.]+)\s*(?:PLN|z[łl])",
        "winning_offer": r"(?:wykonawcy, kt[óo]remu udzielono[^:.]{0,30}):\s*([\d\s,.]+)\s*(?:PLN|z[łl])",
        "part_value": r"Warto[sś][cć][^:.]{0,5}cz[eę][sś]ci:\s*([\d\s,.]+)\s*(?:PLN|z[łl])",
    }
    return {
        key: [match.strip() for match in re.findall(pattern, text)]
        for key, pattern in patterns.items()
    }


@mcp.tool()
def search_tenders(
    search: Optional[str] = None,
    buyer_nip: Optional[str] = None,
    cpv: Optional[str] = None,
    city: Optional[str] = None,
    province: Optional[
        Literal[
            "PL02", "PL04", "PL06", "PL08", "PL10", "PL12", "PL14", "PL16",
            "PL18", "PL20", "PL22", "PL24", "PL26", "PL28", "PL30", "PL32",
        ]
    ] = None,
    notice_type: Optional[
        Literal[
            "ContractNotice", "TenderResultNotice", "ContractAwardNotice",
            "CompetitionNotice", "ConcessionNotice",
        ]
    ] = None,
    order_kind: Optional[Literal["works", "supplies", "services"]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    value_min: Optional[int] = None,
    value_max: Optional[int] = None,
    sort: Optional[
        Literal["newest", "oldest", "deadline", "value_desc", "value_asc"]
    ] = None,
    page: int = 1,
    limit: int = 20,
) -> Dict[str, Any]:
    """Search Polish public tenders (BZP + TED) with filters.

    Note: value_min/value_max filter on the estimated value and are known to be
    leaky at the API side (results slightly outside the range can appear).

    Examples:
      search_tenders(search="komputer", city="Kraków", notice_type="ContractNotice")
      search_tenders(buyer_nip="6751199459", cpv="302", sort="newest")
      search_tenders(cpv="45", province="PL12", value_min=1000000, sort="value_desc")
    """
    return _client().get(
        "/api/tenders",
        params={
            "search": search,
            "buyer_nip": buyer_nip,
            "cpv": cpv,
            "city": city,
            "province": province,
            "noticeType": notice_type,
            "orderKind": order_kind,
            "dateFrom": date_from,
            "dateTo": date_to,
            "valueMin": value_min,
            "valueMax": value_max,
            "sort": sort,
            "page": page,
            "per_page": min(max(limit, 1), 50),
        },
    )


@mcp.tool()
def get_tender(tender_id: str, full: bool = False) -> Dict[str, Any]:
    """Get full details of a tender by ID ('2026/BZP 00202613' or 'TED-123456-2026').

    Set full=True to include the complete notice text (htmlBody) - it can be
    very large (tens of KB); default response excludes it.

    Examples:
      get_tender("2026/BZP 00276746")
      get_tender("TED-279585-2026", full=True)
    """
    detail = _client().get_tender(tender_id)
    if not full:
        detail.pop("htmlBody", None)
    return detail


@mcp.tool()
def get_tender_timeline(tender_id: str) -> Dict[str, Any]:
    """Get the full notice chain of a procurement procedure (announcement,
    revisions, result, contract performance) with dates and notice types.

    Examples:
      get_tender_timeline("2023/BZP 00510245")
    """
    detail = _client().get_tender(tender_id)
    return {
        "requested_id": tender_id,
        "title": detail.get("title"),
        "timeline": detail.get("timeline", []),
    }


@mcp.tool()
def get_tender_offers(tender_id: str) -> Dict[str, Any]:
    """Get offer statistics for a tender: number of offers, lowest/highest/
    winning prices, extracted from the result notice text (SEKCJA V).

    Works best on TenderResultNotice / can-standard / ContractPerformingNotice
    IDs - use get_tender_timeline first to find the result notice of a procedure.

    Examples:
      get_tender_offers("2023/BZP 00559582")
    """
    detail = _client().get_tender(tender_id)
    text = _notice_text(detail)
    amounts = _amounts(text)
    offers_matches = re.findall(r"[Ll]iczba ofert[^:.]{0,20}:\s*(\d+)", text)
    return {
        "id": tender_id,
        "notice_type": detail.get("noticeType"),
        "offers_count_field": detail.get("offersCount"),
        "offers_count_text": offers_matches[:1],
        "amounts_pln": {k: v for k, v in amounts.items() if v},
        "procedure_result": detail.get("procedureResult"),
    }


@mcp.tool()
def extract_contract_value(tender_id: str) -> Dict[str, Any]:
    """Extract contract/order money amounts from a tender notice full text.

    Finds contract value, total paid, estimated value, part values and offer
    prices that the structured API fields do not expose. Amounts are returned
    as raw strings exactly as published (usually PLN).

    Examples:
      extract_contract_value("2026/BZP 00278142")
    """
    detail = _client().get_tender(tender_id)
    text = _notice_text(detail)
    amounts = _amounts(text)
    return {
        "id": tender_id,
        "title": detail.get("title"),
        "notice_type": detail.get("noticeType"),
        "estimated_value_field": detail.get("estimatedValue"),
        "amounts_pln": amounts,
    }


@mcp.tool()
def get_buyer(
    nip: str,
    include_winning_contractors: bool = True,
) -> Dict[str, Any]:
    """Get a procuring entity (zamawiający) profile by NIP, optionally with
    the contractors that most frequently win its tenders.

    Examples:
      get_buyer("6751199459")
      get_buyer("5252248481", include_winning_contractors=False)
    """
    client = _client()
    buyer = client.get(f"/api/buyers/{nip}")
    result: Dict[str, Any] = {"buyer": buyer}
    if include_winning_contractors:
        winners = client.get(f"/api/buyers/{nip}/winning-contractors", params={"limit": 10})
        result["winning_contractors"] = winners.get("data", [])
    return result


@mcp.tool()
def get_contractor(
    nip: str,
    include_winning_buyers: bool = True,
) -> Dict[str, Any]:
    """Get a contractor (wykonawca) profile by NIP with win geography and,
    optionally, the buyers they most frequently win tenders from.

    Examples:
      get_contractor("7781473428")
    """
    client = _client()
    contractor = client.get(f"/api/contractors/{nip}")
    result: Dict[str, Any] = {"contractor": contractor}
    if include_winning_buyers:
        buyers = client.get(f"/api/contractors/{nip}/winning-buyers")
        result["winning_buyers"] = buyers.get("data", [])
    return result


@mcp.tool()
def search_entities(
    query: str,
    entity_type: Optional[Literal["buyer", "contractor"]] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Search buyers (zamawiający) and contractors (wykonawcy) by name to find
    their NIP for get_buyer / get_contractor / search_tenders(buyer_nip=...).

    Examples:
      search_entities("szpital dziecięcy")
      search_entities("budimex", entity_type="contractor")
    """
    return _client().get(
        "/api/entities/search",
        params={"q": query, "type": entity_type, "limit": min(max(limit, 1), 30)},
    )


@mcp.tool()
def search_cpv(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Look up CPV (procurement category) codes by Polish keyword.

    Examples:
      search_cpv("komputer")
      search_cpv("budowa drogi", limit=5)
    """
    return _client().get(
        "/api/cpv/search", params={"q": query, "limit": min(max(limit, 1), 30)}
    )


@mcp.tool()
def get_category_stats(
    cpv: str,
    window: Literal["month", "quarter", "year"] = "year",
) -> Dict[str, Any]:
    """Get aggregate statistics for a CPV category: tender count, average and
    median value, average offers count, average deadline length.

    The response includes the actual `days` window the API applied - the
    upstream API sometimes ignores the requested window, so verify it.

    Examples:
      get_category_stats("302")
      get_category_stats("45240000-1", window="quarter")
    """
    return _client().get(
        "/api/tenders/agg/category-stats", params={"cpv": cpv, "window": window}
    )


@mcp.tool()
def get_province_stats(
    province: Optional[
        Literal[
            "PL02", "PL04", "PL06", "PL08", "PL10", "PL12", "PL14", "PL16",
            "PL18", "PL20", "PL22", "PL24", "PL26", "PL28", "PL30", "PL32",
        ]
    ] = None,
    city: Optional[str] = None,
) -> Dict[str, Any]:
    """Get tender statistics: full province ranking (no args), one province,
    or a city drill-down with top buyers and top CPV categories.

    Examples:
      get_province_stats()
      get_province_stats(province="PL12")
      get_province_stats(city="Kraków")
    """
    client = _client()
    if city:
        result: Dict[str, Any] = client.get(
            f"/api/stats/city/{city}/top-buyers"
        )
        try:
            result["top_cpv"] = client.get(f"/api/stats/city/{city}/top-cpv")
        except Exception:
            result["top_cpv"] = None
        return result
    response = client.get("/api/tenders/agg/provinces")
    if province:
        rows = response.get("data", response) if isinstance(response, dict) else response
        if isinstance(rows, dict):
            rows = rows.get("data", [])
        matching = [row for row in rows if isinstance(row, dict) and row.get("value") == province]
        if not matching:
            raise ValueError(
                f"No stats found for province {province}. "
                "Valid codes: PL02, PL04, PL06, PL08, PL10, PL12, PL14, PL16, "
                "PL18, PL20, PL22, PL24, PL26, PL28, PL30, PL32."
            )
        return {"province": province, "stats": matching}
    return response


@mcp.tool()
def raw_request(
    path: str,
    params_json: Optional[str] = None,
) -> Any:
    """Escape hatch: GET any Atlas Przetargów API endpoint (path must start
    with /api/). Use for endpoints not covered by dedicated tools.

    Examples:
      raw_request("/api/tenders/agg/provinces")
      raw_request("/api/entities/search", params_json='{"q": "gddkia"}')
    """
    import json as _json

    if not path.startswith("/api/"):
        raise ValueError("path must start with /api/")
    params = _json.loads(params_json) if params_json else None
    return _client().get(path, params=params)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
