import json
import sys

sys.path.insert(0, "src")

from atlas_przetargow_mcp_py import server

results = []


def check(name, fn, expect):
    try:
        out = fn()
        detail = expect(out)
        results.append((name, "PASS" if detail is True else f"FAIL: {detail}"))
    except Exception as exc:
        results.append((name, f"ERROR: {type(exc).__name__}: {str(exc)[:120]}"))


check("search_tenders: buyer_nip filtruje",
      lambda: server.search_tenders(buyer_nip="6751199459", limit=5),
      lambda r: True if r["total"] < 1000 else f"total={r['total']} (filtr nie dziala!)")

check("search_tenders: cpv+city+notice_type",
      lambda: server.search_tenders(cpv="302", city="Kraków", notice_type="ContractNotice", limit=5),
      lambda r: True if r["total"] > 0 and all(t.get("noticeType") == "ContractNotice" for t in r["data"]) else r["total"])

check("search_tenders: zakres dat",
      lambda: server.search_tenders(search="komputer", date_from="2026-01-01", date_to="2026-01-31", limit=10, sort="oldest"),
      lambda r: True if all((t.get("date") or "")[:7] == "2026-01" for t in r["data"]) else [t.get("date") for t in r["data"][:3]])

check("search_tenders: sort value_desc",
      lambda: server.search_tenders(cpv="45", sort="value_desc", limit=5),
      lambda r: True if (r["data"][0].get("estimatedValue") or 0) >= (r["data"][-1].get("estimatedValue") or 0) else "nieposortowane")

check("search_tenders: pusty wynik",
      lambda: server.search_tenders(search="zzzzqqqqxxxx", limit=5),
      lambda r: True if r["total"] == 0 else r["total"])

check("get_tender: BZP bez full",
      lambda: server.get_tender("2026/BZP 00276746"),
      lambda r: True if r.get("id") and "htmlBody" not in r else "brak id lub htmlBody obecny")

check("get_tender: TED z full",
      lambda: server.get_tender("TED-279585-2026", full=True),
      lambda r: True if len(str(r.get("htmlBody", ""))) > 5000 else f"htmlBody za krotki: {len(str(r.get('htmlBody','')))}")

check("get_tender: 404",
      lambda: server.get_tender("2099/BZP 99999999"),
      lambda r: "FAIL: powinien byc wyjatek" if r else "FAIL")

check("get_tender_timeline: lancuch",
      lambda: server.get_tender_timeline("2023/BZP 00510245"),
      lambda r: True if len(r["timeline"]) >= 3 else f"timeline={len(r['timeline'])}")

check("get_tender_offers: statystyki ofert",
      lambda: server.get_tender_offers("2023/BZP 00559582"),
      lambda r: True if r["offers_count_field"] == 4 and r["amounts_pln"].get("winning_offer") else r)

check("extract_contract_value: kwota umowy",
      lambda: server.extract_contract_value("2026/BZP 00278142"),
      lambda r: True if r["amounts_pln"]["contract_value"] == ["1356690,00"] else r["amounts_pln"]["contract_value"])

check("extract_contract_value: brak kwot",
      lambda: server.extract_contract_value("2023/BZP 00510245"),
      lambda r: True if isinstance(r["amounts_pln"], dict) else "brak slownika")

check("get_buyer: profil+wykonawcy",
      lambda: server.get_buyer("6751199459"),
      lambda r: True if r["buyer"].get("name") and len(r["winning_contractors"]) >= 3 else f"contractors={len(r.get('winning_contractors', []))}")

check("get_buyer: bez wykonawcow",
      lambda: server.get_buyer("6751199459", include_winning_contractors=False),
      lambda r: True if "winning_contractors" not in r else "sekcja powinna byc nieobecna")

check("get_contractor: pelny profil",
      lambda: server.get_contractor("7781473428"),
      lambda r: True if r["contractor"].get("displayName") and len(r.get("winning_buyers", [])) >= 1 else list(r.keys()))

check("search_entities: buyer",
      lambda: server.search_entities("szpital dziecięcy", entity_type="buyer", limit=3),
      lambda r: True if len(r) >= 1 and all(x.get("nip") for x in r) else r)

check("search_entities: gibberish",
      lambda: server.search_entities("zzqqxx"),
      lambda r: True if r == [] else r)

check("search_cpv: trafienie",
      lambda: server.search_cpv("komputer", limit=3),
      lambda r: True if any("302" in str(x.get("code", "")) for x in r["data"]) else r)

check("search_cpv: pudlo",
      lambda: server.search_cpv("zzqqxxww"),
      lambda r: True if r["data"] == [] else r)

check("get_category_stats: window month vs year",
      lambda: (server.get_category_stats("302", window="month"), server.get_category_stats("302", window="year")),
      lambda pair: True if pair[0]["days"] != pair[1]["days"] else f"UWAGA: identyczne days={pair[0]['days']} (API upstream ignoruje window - ograniczenie API, nie toola)")

check("get_province_stats: ranking",
      lambda: server.get_province_stats(),
      lambda r: True if len(r["data"]) >= 16 else len(r["data"]))

check("get_province_stats: PL12",
      lambda: server.get_province_stats(province="PL12"),
      lambda r: True if r["stats"][0]["total"] > 300000 else r)

check("get_province_stats: miasto",
      lambda: server.get_province_stats(city="Kraków"),
      lambda r: True if r.get("topBuyers") and "Akademia" in str(r["topBuyers"][0].get("name", "")) else r.get("topBuyers", [])[:1])

check("get_province_stats: wirtualne wojewodztwo",
      lambda: server.get_province_stats(province="PL99"),
      lambda r: "FAIL: mial byc ValueError" if r else "FAIL")

check("raw_request: endpoint",
      lambda: server.raw_request("/api/entities/search", params_json='{"q": "gddkia", "limit": 2}'),
      lambda r: True if len(r) >= 1 else r)

check("raw_request: zla sciezka",
      lambda: server.raw_request("/etc/passwd"),
      lambda r: "FAIL: mial byc ValueError" if r else "FAIL")

EXPECTED_ERRORS = ("404", "wirtualne", "zla sciezka")

for name, status in results:
    expected_error = any(tag in name for tag in EXPECTED_ERRORS) and status.startswith("ERROR")
    if status == "PASS" or expected_error:
        marker = "PASS"
    elif status.startswith(("FAIL", "ERROR")):
        marker = "FAIL"
    else:
        marker = "WARN"
    print(f"[{marker:5}] {name:45} {'' if marker == 'PASS' else status}")

fails = [r for r in results if r[1].startswith(("FAIL", "ERROR")) and not any(t in r[0] for t in EXPECTED_ERRORS)]
print(f"\n=== {len(results) - len(fails)}/{len(results)} OK, {len(fails)} problemow ===")
