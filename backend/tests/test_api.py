"""Pruebas de la API con DynamoDB simulado (moto).

Ejecutar desde backend/:  pip install pytest httpx "moto[dynamodb]" && pytest
"""
import os
import uuid

os.environ.update(
    AWS_REGION="us-east-1",
    AWS_DEFAULT_REGION="us-east-1",
    AWS_ACCESS_KEY_ID="testing",
    AWS_SECRET_ACCESS_KEY="testing",
    TABLE_NAME="short_links",
    BASE_URL="http://1.2.3.4:8000",
    ALLOWED_ORIGINS="http://mi-bucket.s3-website-us-east-1.amazonaws.com",
)

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from app import db
from app.main import app

ORIGIN = "http://mi-bucket.s3-website-us-east-1.amazonaws.com"


@pytest.fixture
def client():
    with mock_aws():
        boto3.resource("dynamodb", region_name="us-east-1").create_table(
            TableName="short_links",
            KeySchema=[{"AttributeName": "short_code", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "short_code", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        db.get_table.cache_clear()
        yield TestClient(app, follow_redirects=False)
        db.get_table.cache_clear()


def test_flujo_completo(client):
    url = "https://www.example.com/articulos/arquitectura-cloud"
    r = client.post("/shorten", json={"original_url": url})
    assert r.status_code == 201
    data = r.json()
    uuid.UUID(data["short_code"])  # es un UUID válido
    assert data["original_url"] == url
    assert data["short_url"] == f"http://1.2.3.4:8000/{data['short_code']}"

    # Se guardó en DynamoDB
    item = db.get_table().get_item(Key={"short_code": data["short_code"]})["Item"]
    assert item["original_url"] == url and item["created_at"]

    # Redirección HTTP real
    r = client.get(f"/{data['short_code']}")
    assert r.status_code == 307
    assert r.headers["location"] == url

    # Información en JSON
    r = client.get(f"/urls/{data['short_code']}")
    assert r.status_code == 200
    assert set(r.json()) == {"short_code", "original_url", "created_at"}


def test_uuids_distintos(client):
    a = client.post("/shorten", json={"original_url": "https://a.com"}).json()
    b = client.post("/shorten", json={"original_url": "https://a.com"}).json()
    assert a["short_code"] != b["short_code"]


@pytest.mark.parametrize("path", [f"/{uuid.uuid4()}", "/no-es-uuid", f"/urls/{uuid.uuid4()}"])
def test_404(client, path):
    assert client.get(path).status_code == 404


@pytest.mark.parametrize("bad", ["hola", "ftp://x.com", ""])
def test_url_invalida(client, bad):
    assert client.post("/shorten", json={"original_url": bad}).status_code == 422


def test_cors(client):
    r = client.options(
        "/shorten",
        headers={"Origin": ORIGIN, "Access-Control-Request-Method": "POST",
                 "Access-Control-Request-Headers": "content-type"},
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == ORIGIN


def test_health_y_docs_no_capturados(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/docs").status_code == 200
