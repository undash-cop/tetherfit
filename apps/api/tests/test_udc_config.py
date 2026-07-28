from app.core.config import Settings


def test_udc_jwt_issuer_overrides_token_issuer_not_jwks() -> None:
    settings = Settings(
        keycloak_server_url="http://keycloak:8080",
        keycloak_realm="undash",
        udc_jwt_issuer="https://secure.undash-cop.com/realms/undash",
    )
    assert settings.keycloak_issuer == "https://secure.undash-cop.com/realms/undash"
    assert settings.keycloak_jwks_url.startswith("http://keycloak:8080/")
