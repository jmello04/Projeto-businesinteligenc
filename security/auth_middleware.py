"""Request authentication middleware based on the X-Sistema-Token header."""

from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import get_settings

# Rotas publicas que dispensam autenticacao (ex.: healthcheck).
_PUBLIC_PATHS: frozenset[str] = frozenset({"/status", "/"})


class AutenticacaoMiddleware(BaseHTTPMiddleware):
    """Middleware de autenticacao baseado em token de cabecalho.

    Implementa o principio Zero Trust: nenhuma requisicao e automaticamente
    confiavel, mesmo oriunda da rede interna. Todo acesso precisa de
    autenticacao explicita via X-Sistema-Token.

    Rotas listadas em _PUBLIC_PATHS ficam isentas para permitir
    healthchecks sem credenciais.
    """

    def __init__(self, app: ASGIApp) -> None:
        """Inicializa o middleware carregando a configuracao de API key.

        Args:
            app: Aplicacao ASGI que recebera as requisicoes autenticadas.
        """
        super().__init__(app)
        self._api_key: str = get_settings().api_key

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Verifica o token antes de encaminhar a requisicao.

        Args:
            request: Objeto de requisicao HTTP recebido.
            call_next: Proximo handler na cadeia de middlewares.

        Returns:
            JSONResponse 403 se o token estiver ausente ou invalido;
            caso contrario, a resposta do handler downstream.
        """
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        token: str | None = request.headers.get("X-Sistema-Token")

        if token != self._api_key:
            return JSONResponse(
                status_code=403,
                content={
                    "erro": "Acesso negado.",
                    "detalhe": "Header X-Sistema-Token ausente ou invalido.",
                },
            )

        return await call_next(request)
