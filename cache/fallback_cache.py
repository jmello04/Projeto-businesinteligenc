from adapters.apac_adapter import converter_xml_apac

# Cache em memória: guarda o último dado bem-sucedido por sensor_id.
# Em produção, seria substituído por Redis ou Memcached.
_cache: dict[str, dict] = {}

# XML de exemplo usado para simular a busca ao vivo.
_XML_EXEMPLO = """
<medicao id="{sensor_id}">
  <temperatura>29.1</temperatura>
  <chuva_mm>8.5</chuva_mm>
  <nivel_rio>1.2</nivel_rio>
</medicao>
"""


def buscar_dados_apac(sensor_id: str, forcar_falha: bool = False) -> tuple[dict, str]:
    # Tenta buscar dados ao vivo da APAC.
    # Se forcar_falha=True ou ocorrer qualquer exceção, usa o cache.
    # Se não houver cache, lança exceção.

    if not forcar_falha:
        try:
            xml = _XML_EXEMPLO.format(sensor_id=sensor_id)
            dado = converter_xml_apac(xml)
            _cache[sensor_id] = dado
            return dado, "ao_vivo"
        except Exception:
            pass

    # Falha ocorreu — tenta retornar o último valor salvo no cache.
    if sensor_id in _cache:
        return _cache[sensor_id], "cache"

    raise RuntimeError(
        f"Sensor '{sensor_id}' indisponível e não há dados em cache."
    )
