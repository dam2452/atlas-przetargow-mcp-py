from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx

from atlas_przetargow_mcp_py.settings import Settings


class ApiClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        cleaned = {k: v for k, v in (params or {}).items() if v is not None}
        response = httpx.get(
            f"{self._settings.api_base}{path}",
            params=cleaned,
            headers=self._auth_headers(path),
            timeout=self._settings.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def get_tender(self, tender_id: str) -> Dict[str, Any]:
        return self.get(f"/api/tenders/{quote(tender_id, safe='')}")

    def _auth_headers(self, path: str) -> Dict[str, str]:
        if self._settings.api_key and path.startswith("/api/llm/"):
            return {"Authorization": f"Bearer {self._settings.api_key}"}
        return {}
