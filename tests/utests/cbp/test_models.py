from max_core.misc.utils import load_jwk

from .fixtures import create_cbp_client


class PublicKey:
    pass


def test_cbp_client_serializes_jwk_pubkey() -> None:
    public_key = load_jwk("secrets/clients/test_client/test_client.pub")
    client = create_cbp_client(public_key=public_key)
    client_dict = client.model_dump()

    assert "public_key" in client_dict
    assert "kty" in client_dict["public_key"]
    assert "kid" in client_dict["public_key"]
    assert "n" in client_dict["public_key"]
    assert "e" in client_dict["public_key"]


def test_cbp_client_returns_empty_dict_if_public_key_not_jwk() -> None:
    client = create_cbp_client(public_key=PublicKey())
    client_dict = client.model_dump()

    assert "public_key" in client_dict
    assert client_dict["public_key"] == {}
