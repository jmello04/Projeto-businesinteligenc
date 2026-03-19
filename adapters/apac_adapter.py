import xml.etree.ElementTree as ET

from models.canonical import montar_contexto


def converter_xml_apac(xml_str: str) -> dict:
    # Recebe uma string XML da APAC com dados climáticos e converte
    # para o padrão canônico interno do sistema.
    #
    # Exemplo de XML esperado:
    # <medicao id="APAC-001">
    #   <temperatura>28.5</temperatura>
    #   <chuva_mm>12.3</chuva_mm>
    #   <nivel_rio>1.8</nivel_rio>
    # </medicao>

    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError as e:
        raise ValueError(f"XML inválido recebido da APAC: {e}")

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
