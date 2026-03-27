"""Adapter that converts CTTU JSON traffic data to the canonical format."""

from typing import Any

from models.canonical import montar_contexto


def converter_json_cttu(payload: dict[str, Any]) -> dict[str, Any]:
    """Parse a CTTU JSON payload and return a canonical context object.

    Expects a dictionary in the following shape::

        {
            "id": "CTTU-889",
            "via": "Av. Agamenon Magalhães",
            "status": "CONGESTIONADO",
            "velocidade_media": 12.5
        }

    Args:
        payload: Parsed JSON dictionary received from the CTTU data source.

    Returns:
        Canonical NGSI-LD-inspired dictionary produced by
        :func:`models.canonical.montar_contexto`.

    Raises:
        ValueError: If any required field (``via``, ``status``,
                    ``velocidade_media``) is absent from the payload.
    """
    obrigatorios = ("via", "status", "velocidade_media")
    faltando = [c for c in obrigatorios if c not in payload]
    if faltando:
        raise ValueError(f"Campos obrigatórios ausentes no JSON da CTTU: {faltando}")

    id_ocorrencia = payload.get("id", "sem-id")

    atributos = {
        "via": payload["via"],
        "status": payload["status"],
        "velocidade_media": float(payload["velocidade_media"]),
    }

    return montar_contexto(fonte="CTTU", id_dado=id_ocorrencia, atributos=atributos)
