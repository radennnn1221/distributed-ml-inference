import os


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value not in (None, "") else default


PRIMARY_CONFIG = {
    "host": _env("DB_PRIMARY_HOST", "localhost"),
    "port": _env("DB_PRIMARY_PORT", "5432"),
    "database": _env("POSTGRES_DB", "ml_database"),
    "user": _env("POSTGRES_USER", "admin"),
    "password": _env("POSTGRES_PASSWORD", "admin123"),
}

REPLICA_CONFIG = {
    "host": _env("DB_REPLICA_HOST", "localhost"),
    "port": _env("DB_REPLICA_PORT", "5433"),
    "database": _env("POSTGRES_DB", "ml_database"),
    "user": _env("POSTGRES_USER", "admin"),
    "password": _env("POSTGRES_PASSWORD", "admin123"),
}

AUTO_INIT_DB = _env("AUTO_INIT_DB", "true").lower() in ("1", "true", "yes", "on")

KEYCLOAK_ISSUER = _env(
    "KEYCLOAK_ISSUER", "http://localhost:8080/realms/ml-inference"
)
KEYCLOAK_JWKS_URL = _env(
    "KEYCLOAK_JWKS_URL", f"{KEYCLOAK_ISSUER}/protocol/openid-connect/certs"
)
KEYCLOAK_AUDIENCE = _env("KEYCLOAK_AUDIENCE", "ml-backend")
KEYCLOAK_REQUIRED_ROLE = _env("KEYCLOAK_REQUIRED_ROLE", "user")
