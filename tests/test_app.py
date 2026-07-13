"""Tests for src.app: the FastAPI sentiment API.

Currently covers the GET /version endpoint (story S-001). The TestClient is used
as a context manager so the FastAPI `lifespan` runs and trains/loads the model
before requests are made; this can take a few seconds on first run, so the
client is built once per module.
"""

import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.train import DEFAULT_MODEL


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# AC1: GET /version returns HTTP 200.
def test_version_returns_200(client):
    response = client.get("/version")
    assert response.status_code == 200


# AC2: response includes a "version" key whose value is a non-empty string.
def test_version_key_is_non_empty_string(client):
    body = client.get("/version").json()
    assert "version" in body
    assert isinstance(body["version"], str)
    assert body["version"] != ""


# AC3: response includes a "model_loaded" boolean that is True in the normal
# test case (lifespan trains/loads the model before serving requests).
def test_model_loaded_is_true(client):
    body = client.get("/version").json()
    assert "model_loaded" in body
    assert isinstance(body["model_loaded"], bool)
    assert body["model_loaded"] is True


# AC4: response includes a "model_path" string equal to the filename of the
# model artifact loaded (DEFAULT_MODEL.name from src/train.py).
def test_model_path_matches_default_model_name(client):
    body = client.get("/version").json()
    assert "model_path" in body
    assert isinstance(body["model_path"], str)
    assert body["model_path"] == DEFAULT_MODEL.name
