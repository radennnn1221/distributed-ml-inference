import threading
import time

import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt

from backend.config import (
    KEYCLOAK_AUDIENCE,
    KEYCLOAK_ISSUER,
    KEYCLOAK_JWKS_URL,
    KEYCLOAK_REQUIRED_ROLE,
)

ALGORITHMS = ["RS256"]
JWKS_CACHE_SECONDS = 300

_bearer = HTTPBearer(auto_error=False)
_lock = threading.Lock()
_cache = {"keys": [], "fetched_at": 0.0}


def _fetch_jwks():
    response = requests.get(KEYCLOAK_JWKS_URL, timeout=5)
    response.raise_for_status()
    return response.json().get("keys", [])


def _get_keys():
    now = time.time()
    with _lock:
        if not _cache["keys"] or now - _cache["fetched_at"] > JWKS_CACHE_SECONDS:
            _cache["keys"] = _fetch_jwks()
            _cache["fetched_at"] = now
        return _cache["keys"]


def _resolve_signing_key(token: str):
    try:
        headers = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Header token tidak valid: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    kid = headers.get("kid")
    keys = _get_keys()

    for key in keys:
        if kid is None or key.get("kid") == kid:
            return jwk.construct(key, algorithm=key.get("alg", "RS256"))

    if keys and kid is None:
        return jwk.construct(keys[0], algorithm=keys[0].get("alg", "RS256"))

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Signing key tidak ditemukan pada JWKS Keycloak",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _roles_from_claims(claims: dict):
    roles = set(claims.get("realm_access", {}).get("roles", []))
    for client_access in claims.get("resource_access", {}).values():
        roles.update(client_access.get("roles", []))
    return roles


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Bearer wajib disertakan",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        signing_key = _resolve_signing_key(token)
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=ALGORITHMS,
            audience=KEYCLOAK_AUDIENCE or None,
            issuer=KEYCLOAK_ISSUER,
            options={"verify_aud": bool(KEYCLOAK_AUDIENCE)},
        )
    except HTTPException:
        raise
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token tidak valid: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Keycloak tidak dapat dihubungi: {exc}",
        )

    if KEYCLOAK_REQUIRED_ROLE:
        roles = _roles_from_claims(claims)
        if KEYCLOAK_REQUIRED_ROLE not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{KEYCLOAK_REQUIRED_ROLE}' dibutuhkan untuk mengakses endpoint ini",
            )

    return claims
