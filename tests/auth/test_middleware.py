import os
import sys
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from hermes.auth.middleware import JWTAuthMiddleware
from hermes.auth.jwt_handler import JWTHandler


def setup_app():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_key = private_key.public_key()
    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    handler = JWTHandler(private_key=priv_pem, public_key=pub_pem)
    app = FastAPI()
    app.add_middleware(JWTAuthMiddleware, jwt_handler=handler)

    @app.get("/protected")
    async def protected(request: Request):
        return {"tenant": request.state.tenant_id}

    return app, handler


def test_requires_auth():
    app, handler = setup_app()
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/protected")
    assert resp.status_code == 401


def test_allows_authenticated_request():
    app, handler = setup_app()
    client = TestClient(app)
    pair = handler.create_token_pair("user1", "tenant1")
    resp = client.get("/protected", headers={"Authorization": f"Bearer {pair.access_token}"})
    assert resp.status_code == 200
    assert resp.json()["tenant"] == "tenant1"
