import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    api_base: str
    api_key: str
    timeout_seconds: float

    @staticmethod
    def from_env() -> "Settings":
        api_key = os.environ.get("ATLAS_PRZETARGOW_MCP_PY_API_KEY", "")
        return Settings(
            api_base=os.environ.get(
                "ATLAS_PRZETARGOW_MCP_PY_API_BASE", "https://atlasprzetargow.pl"
            ).rstrip("/"),
            api_key=api_key,
            timeout_seconds=float(
                os.environ.get("ATLAS_PRZETARGOW_MCP_PY_TIMEOUT", "20")
            ),
        )
