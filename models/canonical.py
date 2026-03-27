"""Canonical data model shared across all source adapters."""

from datetime import datetime, timezone
from typing import Any


def montar_contexto(fonte: str, id_dado: str, atributos: dict[str, Any]) -> dict[str, Any]:
    """Build a canonical NGSI-LD-inspired context object from adapter data.

    All source adapters (APAC, CTTU, etc.) must return data through this
    function so that downstream consumers remain decoupled from the
    idiosyncrasies of each external data source.

    Args:
        fonte: Short identifier for the data source (e.g. ``"APAC"``).
        id_dado: Source-specific record identifier (e.g. ``"APAC-001"``).
        atributos: Domain-specific attribute dictionary produced by the adapter.

    Returns:
        Canonical dictionary with the following keys:

        - ``id``: URN in the form ``urn:recife:<fonte>:<id_dado>``.
        - ``type``: Fixed string ``"ContextData"``.
        - ``fonte``: Echoed source identifier.
        - ``atributos``: The attribute payload passed in.
        - ``timestamp``: ISO-8601 UTC timestamp of ingestion.
    """
    return {
        "id": f"urn:recife:{fonte.lower()}:{id_dado}",
        "type": "ContextData",
        "fonte": fonte,
        "atributos": atributos,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
