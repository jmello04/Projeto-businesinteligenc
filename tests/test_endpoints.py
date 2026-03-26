"""Testes de integracao para os endpoints do Recife Data Hub."""

import pytest
from fastapi.testclient import TestClient

AUTH_HEADERS = {"X-Sistema-Token": "recife-secret-2025"}

VALID_ALAGAMENTO = {
    "latitude": -8.0539,
    "longitude": -34.8811,
    "descricao": "Alagamento na Av. Norte, altura do viaduto",
}


class TestStatus:
    """Testes para o endpoint GET /status."""

    def test_status_returns_200(self, client: TestClient) -> None:
        """GET /status deve retornar 200 sem necessidade de autenticacao."""
        response = client.get("/status")
        assert response.status_code == 200

    def test_status_body(self, client: TestClient) -> None:
        """GET /status deve retornar o campo status como ok."""
        response = client.get("/status")
        data = response.json()
        assert data["status"] == "ok"
        assert "versao" in data
        assert "sistema" in data


class TestIngestApac:
    """Testes para o endpoint POST /ingest/apac."""

    def test_empty_body_returns_422(self, client: TestClient) -> None:
        """POST /ingest/apac com body vazio deve retornar 422."""
        response = client.post("/ingest/apac", content="", headers=AUTH_HEADERS)
        assert response.status_code == 422

    def test_valid_xml_returns_200(self, client: TestClient) -> None:
        """POST /ingest/apac com XML valido deve retornar 200."""
        xml = (
            '<medicao id="APAC-001">'
            "<temperatura>28.5</temperatura>"
            "<chuva_mm>12.3</chuva_mm>"
            "<nivel_rio>1.8</nivel_rio>"
            "</medicao>"
        )
        response = client.post(
            "/ingest/apac",
            content=xml,
            headers={**AUTH_HEADERS, "Content-Type": "text/plain"},
        )
        assert response.status_code == 200

    def test_invalid_xml_returns_422(self, client: TestClient) -> None:
        """POST /ingest/apac com XML malformado deve retornar 422."""
        response = client.post(
            "/ingest/apac",
            content="<nao-e-xml-valido",
            headers={**AUTH_HEADERS, "Content-Type": "text/plain"},
        )
        assert response.status_code == 422


class TestIngestCttu:
    """Testes para o endpoint POST /ingest/cttu."""

    def test_invalid_json_returns_422(self, client: TestClient) -> None:
        """POST /ingest/cttu com JSON invalido deve retornar 422."""
        response = client.post(
            "/ingest/cttu",
            content="nao-e-json{",
            headers={**AUTH_HEADERS, "Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_missing_fields_returns_422(self, client: TestClient) -> None:
        """POST /ingest/cttu com campos obrigatorios ausentes deve retornar 422."""
        response = client.post(
            "/ingest/cttu",
            json={"id": "CTTU-001"},
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 422

    def test_valid_payload_returns_200(self, client: TestClient) -> None:
        """POST /ingest/cttu com payload valido deve retornar 200."""
        payload = {
            "id": "CTTU-889",
            "via": "Av. Agamenon Magalhaes",
            "status": "CONGESTIONADO",
            "velocidade_media": 12.5,
        }
        response = client.post("/ingest/cttu", json=payload, headers=AUTH_HEADERS)
        assert response.status_code == 200


class TestAlagamento:
    """Testes para o endpoint POST /alagamento."""

    def test_missing_fields_returns_422(self, client: TestClient) -> None:
        """POST /alagamento com campos faltando deve retornar 422."""
        response = client.post(
            "/alagamento",
            json={"latitude": -8.0539},
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 422

    def test_empty_body_returns_422(self, client: TestClient) -> None:
        """POST /alagamento com body vazio deve retornar 422."""
        response = client.post(
            "/alagamento",
            content="",
            headers={**AUTH_HEADERS, "Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_valid_payload_returns_200(self, client: TestClient) -> None:
        """POST /alagamento com dados validos deve retornar 200."""
        response = client.post(
            "/alagamento",
            json=VALID_ALAGAMENTO,
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert "registro" in data
        assert data["registro"]["latitude"] == VALID_ALAGAMENTO["latitude"]
        assert data["registro"]["longitude"] == VALID_ALAGAMENTO["longitude"]

    def test_valid_payload_has_id(self, client: TestClient) -> None:
        """Registro salvo deve conter id auto-incrementado."""
        response = client.post(
            "/alagamento",
            json=VALID_ALAGAMENTO,
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 200
        assert "id" in response.json()["registro"]


class TestInterface:
    """Testes para o endpoint GET /."""

    def test_root_returns_200(self, client: TestClient) -> None:
        """GET / deve retornar 200 sem autenticacao."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_html(self, client: TestClient) -> None:
        """GET / deve retornar conteudo HTML."""
        response = client.get("/")
        assert "text/html" in response.headers.get("content-type", "")
