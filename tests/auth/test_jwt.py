import os
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from hermes.auth.jwt_handler import JWTHandler


def generate_keys():
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
    return priv_pem, pub_pem


def test_token_pair_roundtrip():
    priv, pub = generate_keys()
    handler = JWTHandler(private_key=priv, public_key=pub)
    pair = handler.create_token_pair("user1", "tenant1")
    payload = handler.decode(pair.access_token)
    assert payload.sub == "user1"
    assert payload.tenant_id == "tenant1"
