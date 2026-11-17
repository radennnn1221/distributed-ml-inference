from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

from backend.auth import get_current_user
from backend.config import AUTO_INIT_DB, KEYCLOAK_ISSUER
from backend.database import ensure_schema, read_data, write_data
from ml.predict import predict_flower


@asynccontextmanager
async def lifespan(app: FastAPI):
    if AUTO_INIT_DB:
        try:
            ensure_schema()
            print("[startup] Skema tabel mahasiswa & inference_results siap.")
        except Exception as exc:
            print(f"[startup] Peringatan: gagal menyiapkan skema database: {exc}")
    yield


app = FastAPI(
    title="Distributed ML Inference System",
    description=(
        "API dengan PostgreSQL Primary, Read Replica, Keycloak SSO (OIDC), "
        "dan Machine Learning Random Forest."
    ),
    version="2.0.0",
    lifespan=lifespan,
)


class Mahasiswa(BaseModel):
    nama: str
    jurusan: str


class PrediksiRequest(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float


@app.get("/")
def home():
    return {
        "message": "Distributed ML Inference System is running!",
        "status": "success",
        "auth": "Keycloak OIDC (Bearer JWT)",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "FastAPI Backend",
    }


@app.get("/auth/me")
def auth_me(claims: dict = Depends(get_current_user)):
    roles = set(claims.get("realm_access", {}).get("roles", []))
    for client_access in claims.get("resource_access", {}).values():
        roles.update(client_access.get("roles", []))

    return {
        "message": "Token JWT valid dan tervalidasi mandiri oleh backend",
        "issuer": claims.get("iss"),
        "expected_issuer": KEYCLOAK_ISSUER,
        "subject": claims.get("sub"),
        "username": claims.get("preferred_username"),
        "email": claims.get("email"),
        "roles": sorted(roles),
        "expires_at": claims.get("exp"),
    }


@app.post("/mahasiswa")
def tambah_mahasiswa(
    data: Mahasiswa,
    claims: dict = Depends(get_current_user),
):
    try:
        result = write_data(
            """
            INSERT INTO mahasiswa (nama, jurusan)
            VALUES (%s, %s)
            RETURNING id, nama, jurusan
            """,
            (data.nama, data.jurusan),
        )

        return {
            "message": "Data berhasil disimpan ke Primary",
            "saved_by": claims.get("preferred_username"),
            "target": "PostgreSQL Primary",
            "data": result[0] if result else None,
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/mahasiswa")
def daftar_mahasiswa(claims: dict = Depends(get_current_user)):
    try:
        result = read_data("SELECT id, nama, jurusan FROM mahasiswa ORDER BY id")

        return {
            "source": "PostgreSQL Read Replica",
            "requested_by": claims.get("preferred_username"),
            "total": len(result),
            "data": result,
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/predict")
def prediksi_bunga(
    data: PrediksiRequest,
    claims: dict = Depends(get_current_user),
):
    try:
        result = predict_flower(
            sepal_length=data.sepal_length,
            sepal_width=data.sepal_width,
            petal_length=data.petal_length,
            petal_width=data.petal_width,
        )

        stored = write_data(
            """
            INSERT INTO inference_results (
                sepal_length, sepal_width, petal_length, petal_width,
                prediction, confidence, subject, model_name
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, prediction, confidence, created_at
            """,
            (
                data.sepal_length,
                data.sepal_width,
                data.petal_length,
                data.petal_width,
                result["prediction"],
                result["confidence"],
                claims.get("sub"),
                "Random Forest",
            ),
        )

        record = stored[0] if stored else {}

        return {
            "message": "Prediksi berhasil dan tersimpan ke Primary",
            "model": "Random Forest",
            "prediction": result["prediction"],
            "confidence": result["confidence"],
            "record_id": record.get("id"),
            "stored_in": "PostgreSQL Primary (tabel inference_results)",
            "created_at": record.get("created_at"),
            "requested_by": claims.get("preferred_username"),
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/predictions")
def riwayat_prediksi(
    limit: int = Query(default=20, ge=1, le=100),
    claims: dict = Depends(get_current_user),
):
    try:
        result = read_data(
            """
            SELECT id, sepal_length, sepal_width, petal_length, petal_width,
                   prediction, confidence, model_name, subject, created_at
            FROM inference_results
            ORDER BY id DESC
            LIMIT %s
            """,
            (limit,),
        )

        return {
            "source": "PostgreSQL Read Replica",
            "requested_by": claims.get("preferred_username"),
            "total": len(result),
            "data": result,
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
