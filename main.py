from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from adapters.apac_adapter import converter_xml_apac
from adapters.cttu_adapter import converter_json_cttu
from cache.fallback_cache import buscar_dados_apac
from database.geo_repository import criar_tabelas, salvar_ponto_alagamento
from security.auth_middleware import AutenticacaoMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gerencia o ciclo de vida da aplicacao.

    Na inicializacao, garante que todas as tabelas do banco de dados existam.
    """
    criar_tabelas()
    yield


app = FastAPI(title="Recife Data Hub", version="1.0.0", lifespan=lifespan)
app.add_middleware(AutenticacaoMiddleware)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/status")
def status() -> dict:
    """Retorna o status operacional da aplicacao.

    Returns:
        Dicionario com campos status, versao e sistema.

    Note:
        Rota publica -- nao requer autenticacao (usada como healthcheck).
    """
    return {"status": "ok", "versao": "1.0.0", "sistema": "Recife Data Hub"}


@app.post("/ingest/apac")
async def ingest_apac(request: Request) -> dict:
    """Recebe XML da APAC e retorna o dado no formato canonico NGSI-LD.

    O corpo da requisicao deve conter um XML valido com os campos
    temperatura, chuva_mm e nivel_rio.

    Args:
        request: Requisicao HTTP com o XML da APAC no corpo.

    Returns:
        Dicionario no formato canonico NGSI-LD com os dados normalizados.

    Raises:
        HTTPException(422): Corpo vazio ou XML malformado / campos ausentes.
    """
    xml_str: str = (await request.body()).decode("utf-8")
    if not xml_str.strip():
        raise HTTPException(
            status_code=422,
            detail="Body vazio. Envie o XML no corpo da requisicao.",
        )
    try:
        return converter_xml_apac(xml_str)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/ingest/cttu")
async def ingest_cttu(request: Request) -> dict:
    """Recebe JSON da CTTU e retorna o dado no formato canonico NGSI-LD.

    O corpo da requisicao deve ser um JSON com os campos via, status
    e velocidade_media.

    Args:
        request: Requisicao HTTP com o payload JSON da CTTU.

    Returns:
        Dicionario no formato canonico NGSI-LD com os dados normalizados.

    Raises:
        HTTPException(422): JSON invalido ou campos obrigatorios ausentes.
    """
    try:
        payload: dict = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="JSON invalido.") from exc
    try:
        return converter_json_cttu(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/cache/apac/{sensor_id}")
def cache_apac(sensor_id: str, forcar_falha: bool = False) -> dict:
    """Busca dado de um sensor APAC com fallback automatico para cache.

    Args:
        sensor_id: Identificador do sensor (ex.: APAC-001).
        forcar_falha: Se True, simula o sensor offline e forca o uso do cache.

    Returns:
        Dicionario com dado (formato canonico) e fonte (ao_vivo ou cache).

    Raises:
        HTTPException(503): Sensor indisponivel e sem dados em cache.
    """
    try:
        dado, fonte = buscar_dados_apac(sensor_id, forcar_falha=forcar_falha)
        return {"dado": dado, "fonte": fonte}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/alagamento")
async def registrar_alagamento(request: Request) -> dict:
    """Registra um ponto de alagamento no banco de dados.

    O corpo da requisicao deve ser um JSON com os campos obrigatorios
    latitude, longitude e descricao.

    Args:
        request: Requisicao HTTP com o payload JSON do ponto de alagamento.

    Returns:
        Dicionario com mensagem de confirmacao e dados do registro salvo.

    Raises:
        HTTPException(422): JSON invalido ou campos obrigatorios ausentes.
        HTTPException(500): Erro de persistencia no banco de dados.
    """
    try:
        payload: dict = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="JSON invalido.") from exc

    obrigatorios: tuple[str, ...] = ("latitude", "longitude", "descricao")
    faltando: list[str] = [c for c in obrigatorios if c not in payload]
    if faltando:
        raise HTTPException(
            status_code=422,
            detail=f"Campos obrigatorios ausentes: {faltando}",
        )

    try:
        salvo: dict = salvar_ponto_alagamento(
            lat=float(payload["latitude"]),
            lon=float(payload["longitude"]),
            descricao=payload["descricao"],
        )
        return {"mensagem": "Ponto de alagamento registrado.", "registro": salvo}
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Valores de coordenadas invalidos: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao salvar: {exc}",
        ) from exc


@app.get("/")
def interface() -> FileResponse:
    """Serve a interface web estatica do Recife Data Hub.

    Returns:
        FileResponse com o arquivo static/index.html.
    """
    return FileResponse("static/index.html")
