from models.canonical import montar_contexto


def converter_json_cttu(payload: dict) -> dict:
    # Recebe um dicionário JSON da CTTU com dados de trânsito e converte
    # para o padrão canônico interno do sistema.
    #
    # Exemplo de JSON esperado:
    # {
    #   "id": "CTTU-889",
    #   "via": "Av. Agamenon Magalhães",
    #   "status": "CONGESTIONADO",
    #   "velocidade_media": 12.5
    # }

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
