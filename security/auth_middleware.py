from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Token fixo que representa o "segredo compartilhado" entre os sistemas.
# Em produção, viria de variável de ambiente ou cofre de segredos.
TOKEN_VALIDO = "recife-secret-2025"


class AutenticacaoMiddleware(BaseHTTPMiddleware):
    # Zero Trust significa: nunca confiar automaticamente em nenhuma requisição,
    # mesmo que venha de dentro da rede interna. Todo acesso precisa ser
    # autenticado explicitamente. Aqui simulamos isso exigindo um token
    # no header de TODAS as requisições, sem exceção para IPs internos.

    async def dispatch(self, request: Request, call_next):
        # A rota /status é pública para permitir healthcheck sem token.
        if request.url.path in ("/status", "/"):
            return await call_next(request)

        token = request.headers.get("X-Sistema-Token")

        if token != TOKEN_VALIDO:
            return JSONResponse(
                status_code=403,
                content={
                    "erro": "Acesso negado.",
                    "detalhe": "Header X-Sistema-Token ausente ou inválido.",
                },
            )

        return await call_next(request)
