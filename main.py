from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse

from adapters.apac_adapter import converter_xml_apac
from adapters.cttu_adapter import converter_json_cttu
from cache.fallback_cache import buscar_dados_apac
from database.geo_repository import criar_tabelas, salvar_ponto_alagamento
from security.auth_middleware import AutenticacaoMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    criar_tabelas()
    yield


app = FastAPI(title="Recife Data Hub", version="1.0.0", lifespan=lifespan)
app.add_middleware(AutenticacaoMiddleware)


@app.get("/status")
def status():
    return {"status": "ok", "versao": "1.0.0", "sistema": "Recife Data Hub"}


@app.post("/ingest/apac")
async def ingest_apac(request: Request):
    xml_str = (await request.body()).decode("utf-8")
    if not xml_str.strip():
        raise HTTPException(status_code=422, detail="Body vazio. Envie o XML no corpo da requisição.")
    try:
        return converter_xml_apac(xml_str)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/ingest/cttu")
async def ingest_cttu(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=422, detail="JSON inválido.")
    try:
        return converter_json_cttu(payload)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/cache/apac/{sensor_id}")
def cache_apac(sensor_id: str, forcar_falha: bool = False):
    try:
        dado, fonte = buscar_dados_apac(sensor_id, forcar_falha=forcar_falha)
        return {"dado": dado, "fonte": fonte}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/alagamento")
async def registrar_alagamento(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=422, detail="JSON inválido.")

    obrigatorios = ("latitude", "longitude", "descricao")
    faltando = [c for c in obrigatorios if c not in payload]
    if faltando:
        raise HTTPException(status_code=422, detail=f"Campos obrigatórios ausentes: {faltando}")

    try:
        salvo = salvar_ponto_alagamento(
            lat=float(payload["latitude"]),
            lon=float(payload["longitude"]),
            descricao=payload["descricao"],
        )
        return {"mensagem": "Ponto de alagamento registrado.", "registro": salvo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar: {e}")


@app.get("/", response_class=HTMLResponse)
def interface():
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Recife Data Hub</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: #060d1a;
      color: #e2e8f0;
      min-height: 100vh;
      padding: 32px 16px 60px;
    }

    header {
      text-align: center;
      margin-bottom: 36px;
    }

    .logo {
      font-size: 0.75rem;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: #38bdf8;
      margin-bottom: 10px;
      opacity: 0.8;
    }

    header h1 {
      font-size: 2.2rem;
      font-weight: 800;
      background: linear-gradient(90deg, #38bdf8, #818cf8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 8px;
    }

    header p {
      color: #64748b;
      font-size: 0.9rem;
    }

    .server-status {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin-top: 16px;
      font-size: 0.82rem;
      color: #64748b;
    }

    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #334155;
      transition: background 0.3s;
    }
    .dot.online  { background: #22c55e; box-shadow: 0 0 6px #22c55e; }
    .dot.offline { background: #ef4444; }

    .token-section {
      max-width: 640px;
      margin: 0 auto 40px;
      background: #0f1f35;
      border: 1px solid #1e3a5f;
      border-radius: 14px;
      padding: 20px;
    }

    .token-section label {
      display: block;
      font-size: 0.75rem;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      margin-bottom: 8px;
    }

    .token-row {
      display: flex;
      gap: 10px;
    }

    .token-row input {
      flex: 1;
      padding: 10px 14px;
      border-radius: 8px;
      border: 1px solid #1e3a5f;
      background: #060d1a;
      color: #e2e8f0;
      font-size: 0.88rem;
      outline: none;
      transition: border-color 0.2s;
    }

    .token-row input:focus { border-color: #38bdf8; }

    .btn-status {
      padding: 10px 20px;
      background: #0ea5e9;
      color: #fff;
      border: none;
      border-radius: 8px;
      font-weight: 700;
      font-size: 0.85rem;
      cursor: pointer;
      white-space: nowrap;
      transition: background 0.2s;
    }
    .btn-status:hover { background: #38bdf8; }

    .status-result {
      margin-top: 12px;
      font-size: 0.8rem;
      font-family: 'Courier New', monospace;
      color: #94a3b8;
      min-height: 20px;
    }

    .section-title {
      max-width: 1200px;
      margin: 0 auto 16px;
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.15em;
      color: #475569;
      padding-left: 4px;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
      gap: 20px;
      max-width: 1200px;
      margin: 0 auto 40px;
    }

    .card {
      background: #0d1b2e;
      border: 1px solid #1e3a5f;
      border-radius: 14px;
      padding: 22px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      transition: border-color 0.2s;
    }

    .card:hover { border-color: #334155; }

    .card-header {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .method {
      font-size: 0.68rem;
      font-weight: 800;
      padding: 3px 9px;
      border-radius: 6px;
      letter-spacing: 0.05em;
    }

    .method.get  { background: #052e16; color: #4ade80; border: 1px solid #166534; }
    .method.post { background: #1e1b4b; color: #a5b4fc; border: 1px solid #3730a3; }

    .card-header h2 {
      font-size: 0.95rem;
      color: #cbd5e1;
      font-family: 'Courier New', monospace;
    }

    .card-desc {
      font-size: 0.82rem;
      color: #475569;
      line-height: 1.5;
    }

    textarea {
      width: 100%;
      min-height: 120px;
      background: #060d1a;
      border: 1px solid #1e3a5f;
      border-radius: 8px;
      color: #7dd3fc;
      font-family: 'Courier New', monospace;
      font-size: 0.78rem;
      padding: 10px 12px;
      resize: vertical;
      outline: none;
      transition: border-color 0.2s;
    }

    textarea:focus { border-color: #38bdf8; }

    .card-input-row {
      display: flex;
      gap: 8px;
    }

    .card-input-row input {
      flex: 1;
      padding: 8px 12px;
      border-radius: 8px;
      border: 1px solid #1e3a5f;
      background: #060d1a;
      color: #e2e8f0;
      font-size: 0.84rem;
      outline: none;
    }

    .card-input-row input:focus { border-color: #38bdf8; }

    .card-input-row label {
      font-size: 0.75rem;
      color: #475569;
      margin-bottom: 4px;
      display: block;
    }

    .input-group { flex: 1; }

    .checkbox-row {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.82rem;
      color: #64748b;
    }

    .checkbox-row input[type=checkbox] { accent-color: #f87171; }

    .btn-send {
      width: 100%;
      padding: 10px;
      background: #4f46e5;
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 0.88rem;
      font-weight: 700;
      cursor: pointer;
      transition: background 0.2s;
    }

    .btn-send:hover    { background: #6366f1; }
    .btn-send:disabled { background: #1e293b; color: #475569; cursor: not-allowed; }

    .response-box {
      background: #060d1a;
      border: 1px solid #1e3a5f;
      border-radius: 8px;
      padding: 12px;
      font-family: 'Courier New', monospace;
      font-size: 0.78rem;
      min-height: 56px;
      white-space: pre-wrap;
      word-break: break-word;
      color: #94a3b8;
      position: relative;
    }

    .response-box.success { border-color: #166534; color: #86efac; }
    .response-box.failure { border-color: #7f1d1d; color: #fca5a5; }

    .response-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }

    .http-badge {
      font-size: 0.7rem;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 6px;
    }

    .http-badge.ok   { background: #052e16; color: #4ade80; }
    .http-badge.err  { background: #450a0a; color: #fca5a5; }

    .copy-btn {
      font-size: 0.7rem;
      padding: 2px 8px;
      background: #1e293b;
      color: #94a3b8;
      border: 1px solid #334155;
      border-radius: 6px;
      cursor: pointer;
    }

    .copy-btn:hover { background: #334155; }

    .spinner {
      display: inline-block;
      width: 14px;
      height: 14px;
      border: 2px solid #334155;
      border-top-color: #38bdf8;
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
      vertical-align: middle;
      margin-right: 6px;
    }

    @keyframes spin { to { transform: rotate(360deg); } }

    footer {
      text-align: center;
      margin-top: 20px;
      font-size: 0.75rem;
      color: #334155;
    }
  </style>
</head>
<body>

<header>
  <div class="logo">Smart City Recife</div>
  <h1>Recife Data Hub</h1>
  <p>Middleware de Interoperabilidade — APAC · CTTU · Grande Recife</p>
  <div class="server-status">
    <div class="dot" id="dot"></div>
    <span id="server-label">Verificando conexão...</span>
  </div>
</header>

<div class="token-section">
  <label>Token de Autenticação (X-Sistema-Token)</label>
  <div class="token-row">
    <input id="token" type="text" value="recife-secret-2025" placeholder="recife-secret-2025">
    <button class="btn-status" onclick="testarStatus()">Testar Status</button>
  </div>
  <div class="status-result" id="status-result">—</div>
</div>

<div class="section-title">Ingestão de Dados</div>
<div class="grid">

  <div class="card">
    <div class="card-header">
      <span class="method post">POST</span>
      <h2>/ingest/apac</h2>
    </div>
    <p class="card-desc">Envia XML da APAC com dados climáticos e retorna o dado no formato canônico NGSI-LD.</p>
    <textarea id="body-apac"><medicao id="APAC-001">
  <temperatura>28.5</temperatura>
  <chuva_mm>12.3</chuva_mm>
  <nivel_rio>1.8</nivel_rio>
</medicao></textarea>
    <button class="btn-send" onclick="enviar('apac')">Enviar</button>
    <div class="response-box" id="resp-apac">Aguardando envio...</div>
  </div>

  <div class="card">
    <div class="card-header">
      <span class="method post">POST</span>
      <h2>/ingest/cttu</h2>
    </div>
    <p class="card-desc">Envia JSON da CTTU com ocorrência de trânsito e retorna o dado no formato canônico NGSI-LD.</p>
    <textarea id="body-cttu">{
  "id": "CTTU-889",
  "via": "Av. Agamenon Magalhães",
  "status": "CONGESTIONADO",
  "velocidade_media": 12.5
}</textarea>
    <button class="btn-send" onclick="enviar('cttu')">Enviar</button>
    <div class="response-box" id="resp-cttu">Aguardando envio...</div>
  </div>

</div>

<div class="section-title">Cache & Resiliência</div>
<div class="grid">

  <div class="card">
    <div class="card-header">
      <span class="method get">GET</span>
      <h2>/cache/apac/{sensor_id}</h2>
    </div>
    <p class="card-desc">Busca dado da APAC com fallback automático para cache em memória. Ative "forçar falha" para simular o sensor offline.</p>
    <div class="card-input-row">
      <div class="input-group">
        <label>sensor_id</label>
        <input id="cache-sensor" type="text" value="APAC-001">
      </div>
    </div>
    <div class="checkbox-row">
      <input type="checkbox" id="forcar-falha">
      <label for="forcar-falha" style="color:#f87171;font-size:0.82rem">Forçar falha do sensor (testa o cache)</label>
    </div>
    <button class="btn-send" onclick="enviarCache()">Buscar</button>
    <div class="response-box" id="resp-cache">Aguardando envio...</div>
  </div>

  <div class="card">
    <div class="card-header">
      <span class="method post">POST</span>
      <h2>/alagamento</h2>
    </div>
    <p class="card-desc">Registra um ponto de alagamento no banco de dados com latitude, longitude e descrição.</p>
    <textarea id="body-alagamento">{
  "latitude": -8.0539,
  "longitude": -34.8811,
  "descricao": "Alagamento na Av. Norte, altura do viaduto"
}</textarea>
    <button class="btn-send" onclick="enviar('alagamento')">Registrar</button>
    <div class="response-box" id="resp-alagamento">Aguardando envio...</div>
  </div>

</div>

<footer>Recife Data Hub v1.0.0 — Smart City Recife</footer>

<script>
  const TOKEN = () => document.getElementById("token").value.trim();

  function mostrar(id, status, data) {
    const box = document.getElementById(id);
    const ok  = status >= 200 && status < 300;
    box.className = "response-box " + (ok ? "success" : "failure");
    const badge = `<div class="response-header">
      <span class="http-badge ${ok ? "ok" : "err"}">HTTP ${status}</span>
      <button class="copy-btn" onclick="copiar('${id}')">copiar</button>
    </div>`;
    box.innerHTML = badge + JSON.stringify(data, null, 2);
  }

  function carregando(id) {
    const box = document.getElementById(id);
    box.className = "response-box";
    box.innerHTML = '<span class="spinner"></span>Enviando...';
  }

  function copiar(id) {
    const box = document.getElementById(id);
    const texto = box.innerText.replace(/^HTTP \d+\n/, "");
    navigator.clipboard.writeText(texto);
  }

  async function testarStatus() {
    document.getElementById("status-result").textContent = "Verificando...";
    try {
      const r = await fetch("/status");
      const d = await r.json();
      const dot = document.getElementById("dot");
      const lbl = document.getElementById("server-label");
      dot.className = "dot online";
      lbl.textContent = "Servidor online — " + d.sistema;
      document.getElementById("status-result").textContent =
        "✓ " + JSON.stringify(d);
    } catch(e) {
      document.getElementById("dot").className = "dot offline";
      document.getElementById("server-label").textContent = "Servidor offline";
      document.getElementById("status-result").textContent = "✗ Sem conexão";
    }
  }

  async function enviar(tipo) {
    const mapa = {
      apac:       { id: "resp-apac",       url: "/ingest/apac",  ct: "text/plain",       body: () => document.getElementById("body-apac").value },
      cttu:       { id: "resp-cttu",       url: "/ingest/cttu",  ct: "application/json", body: () => document.getElementById("body-cttu").value },
      alagamento: { id: "resp-alagamento", url: "/alagamento",   ct: "application/json", body: () => document.getElementById("body-alagamento").value },
    };
    const cfg = mapa[tipo];
    carregando(cfg.id);
    try {
      const r = await fetch(cfg.url, {
        method: "POST",
        headers: { "X-Sistema-Token": TOKEN(), "Content-Type": cfg.ct },
        body: cfg.body(),
      });
      const d = await r.json();
      mostrar(cfg.id, r.status, d);
    } catch(e) {
      mostrar(cfg.id, 0, { erro: e.message });
    }
  }

  async function enviarCache() {
    const id     = "resp-cache";
    const sensor = document.getElementById("cache-sensor").value.trim() || "APAC-001";
    const falha  = document.getElementById("forcar-falha").checked;
    carregando(id);
    try {
      const url = `/cache/apac/${encodeURIComponent(sensor)}?forcar_falha=${falha}`;
      const r   = await fetch(url, { headers: { "X-Sistema-Token": TOKEN() } });
      const d   = await r.json();
      mostrar(id, r.status, d);
    } catch(e) {
      mostrar(id, 0, { erro: e.message });
    }
  }

  // Verifica o status automaticamente ao carregar a página
  window.addEventListener("load", testarStatus);
</script>

</body>
</html>"""


