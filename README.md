# Recife Data Hub

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

Middleware de interoperabilidade para dados geoespaciais urbanos da cidade do Recife — integra fontes APAC e CTTU em um formato canonico unificado.

---

## Visao Geral

### Problema

Os orgaos da cidade do Recife produzem dados de sensores urbanos em formatos heterogeneos:

- **APAC** (Agencia Pernambucana de Aguas e Clima): dados climaticos em XML (temperatura, chuva, nivel de rios).
- **CTTU** (Autarquia de Transito e Transporte Urbano): ocorrencias de transito em JSON (via, status, velocidade media).

Consumir essas fontes diretamente exige que cada cliente conheca e trate cada formato individualmente, gerando acoplamento e retrabalho.

### Solucao

O Recife Data Hub atua como camada de normalizacao: recebe os dados brutos de cada fonte, converte-os para um formato canonico inspirado no padrao **NGSI-LD (FIWARE)** e os expoe via API REST unificada. Um mecanismo de **fallback com cache em memoria** garante resiliencia quando sensores ficam temporariamente indisponiveis.

---

## Funcionalidades

- **Ingestao APAC (XML)** — recebe XML climatico e retorna dado canonico NGSI-LD.
- **Ingestao CTTU (JSON)** — recebe JSON de transito e retorna dado canonico NGSI-LD.
- **Cache com fallback** — armazena o ultimo dado bem-sucedido por sensor; retorna do cache automaticamente em caso de falha.
- **Registro de pontos de alagamento** — persiste coordenadas e descricao no banco de dados.
- **Interface web** — painel interativo para testar todos os endpoints diretamente no navegador.
- **Autenticacao por token** — middleware Zero Trust via header `X-Sistema-Token`.

---

## Arquitetura

```
adapters/          # Normalizacao de cada fonte para o formato canonico
  apac_adapter.py  #   XML APAC -> NGSI-LD
  cttu_adapter.py  #   JSON CTTU -> NGSI-LD

cache/             # Fallback em memoria por sensor_id
  fallback_cache.py

database/          # Persistencia com SQLAlchemy
  geo_repository.py

security/          # Autenticacao Zero Trust (header token)
  auth_middleware.py

app/core/          # Configuracao centralizada (Pydantic Settings)
  config.py

static/            # Interface web estatica
  index.html

main.py            # Ponto de entrada FastAPI
tests/             # Suite de testes com pytest + httpx
```

Fluxo: **adapters** (normalizacao) -> **cache** (fallback) -> **database** (persistencia) -> **security** (autenticacao em todas as rotas protegidas).

---

## Stack

| Tecnologia | Motivo |
|---|---|
| **FastAPI** | Alta performance, validacao automatica via Pydantic, documentacao OpenAPI gerada automaticamente |
| **SQLAlchemy 2.x** | ORM maduro com suporte a multiplos bancos; facilita migracao futura para PostgreSQL/PostGIS |
| **Pydantic Settings** | Configuracao tipada a partir de variaveis de ambiente e arquivo `.env`, sem acoplamento a strings hardcoded |
| **SQLite** | Zero configuracao para desenvolvimento; a URL do banco e configuravel para PostgreSQL em producao |
| **pytest + httpx** | Testes de integracao com TestClient sincrono, sem necessidade de subir servidor real |
| **Docker multi-stage** | Imagem de producao enxuta: dependencias compiladas no builder nao chegam ao runner |

---

## Como Rodar

### Com Docker (recomendado)

```bash
# 1. Copie e ajuste as variaveis de ambiente
cp .env.example .env

# 2. Suba o servico
docker compose up --build

# A API estara disponivel em http://localhost:8000
```

### Sem Docker

```bash
# 1. Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows

# 2. Instale as dependencias
pip install -r requirements.txt

# 3. Copie e ajuste as variaveis de ambiente
cp .env.example .env

# 4. Inicie o servidor
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Acesse:
- **Interface web**: http://localhost:8000/
- **Documentacao interativa**: http://localhost:8000/docs
- **Healthcheck**: http://localhost:8000/status

---

## Variaveis de Ambiente

| Variavel | Padrao | Descricao |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./recife_geo.db` | URL de conexao SQLAlchemy |
| `API_KEY` | `recife-secret-2025` | Token de autenticacao (header `X-Sistema-Token`) |
| `APP_HOST` | `0.0.0.0` | Host de escuta do servidor |
| `APP_PORT` | `8000` | Porta de escuta do servidor |
| `DEBUG` | `false` | Modo debug da aplicacao |

Consulte `.env.example` para o template completo.

---

## Testes

```bash
pytest tests/ -v
```

A suite cobre:

- `GET /status` -> 200 sem autenticacao
- `POST /ingest/apac` com body vazio -> 422
- `POST /ingest/apac` com XML valido -> 200
- `POST /ingest/cttu` com JSON invalido -> 422
- `POST /ingest/cttu` com campos ausentes -> 422
- `POST /alagamento` com campos faltando -> 422
- `POST /alagamento` com dados validos -> 200
- `GET /` -> 200, conteudo HTML

---

## Estrutura de Pastas

```
Projeto-businesinteligenc/
├── adapters/
│   ├── apac_adapter.py
│   └── cttu_adapter.py
├── app/
│   └── core/
│       └── config.py
├── cache/
│   └── fallback_cache.py
├── database/
│   └── geo_repository.py
├── models/
│   └── canonical.py
├── security/
│   └── auth_middleware.py
├── static/
│   └── index.html
├── tests/
│   ├── conftest.py
│   └── test_endpoints.py
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── main.py
├── README.md
└── requirements.txt
```

---

## Licenca

Distribuido sob a licenca MIT. Veja [LICENSE](LICENSE) para mais detalhes.
