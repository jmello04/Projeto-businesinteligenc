"""Adapter that converts APAC XML climate measurements to the canonical format."""

import xml.etree.ElementTree as ET
from typing import Any

from models.canonical import montar_contexto


def converter_xml_apac(xml_str: str) -> dict[str, Any]:
    """Parse an APAC XML measurement and return a canonical context object.

    Expects an XML document in the following shape::

        <medicao id="APAC-001">
          <temperatura>28.5</temperatura>
          <chuva_mm>12.3</chuva_mm>
          <nivel_rio>1.8</nivel_rio>
        </medicao>

    Args:
        xml_str: Raw XML string received from the APAC data source.

    Returns:
        Canonical NGSI-LD-inspired dictionary produced by
        :func:`models.canonical.montar_contexto`.

    Raises:
        ValueError: If the XML is malformed or any required field is missing.
    """
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError as exc:
        raise ValueError(f"XML inválido recebido da APAC: {exc}") from exc

    def campo(tag: str) -> str:
        el = root.find(tag)
        if el is None or el.text is None:
            raise ValueError(f"Campo obrigatório ausente no XML: <{tag}>")
        return el.text.strip()

    id_medicao = root.get("id", "sem-id")

    atributos = {
        "temperatura": float(campo("temperatura")),
        "chuva_mm": float(campo("chuva_mm")),
        "nivel_rio": float(campo("nivel_rio")),
    }

    return montar_contexto(fonte="APAC", id_dado=id_medicao, atributos=atributos)
