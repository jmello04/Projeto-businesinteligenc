from datetime import datetime, timezone


def montar_contexto(fonte: str, id_dado: str, atributos: dict) -> dict:
    # Monta o dicionário canônico inspirado no padrão NGSI-LD do FIWARE.
    # Todos os adapters devem retornar dados neste formato para garantir
    # que o restante do sistema não precise saber de qual órgão o dado veio.
    return {
        "id": f"urn:recife:{fonte.lower()}:{id_dado}",
        "type": "ContextData",
        "fonte": fonte,
        "atributos": atributos,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
