# Distributed ML Inference System

Proyek Sistem Basis Data Terdistribusi: PostgreSQL **Primary + Read Replica**,
backend **FastAPI**, **Keycloak SSO (OIDC/OAuth2)**, inferensi **Random Forest**,
serta deployment **Docker Compose** dan **Kubernetes** dengan penyimpanan persisten.

## 1. Arsitektur Singkat

```text
                         +-----------------------------+
                         |   Client / Swagger UI       |
                         +--------------+--------------+
                                        |
                         1. login (OIDC) |  4. Bearer JWT
                                        v
                         +-----------------------------+
                         |  Keycloak (Realm ml-inference)|
                         |  http://localhost:8080       |
                         +--------------+--------------+
                                        | JWKS
                                        v
                         +-----------------------------+
                         |     FastAPI Backend         |
                         |  - validasi JWT (RS256)     |
                         |  - inferensi Random Forest  |
                         +------+---------------+------+
                       tulis    |               |    baca
                                v               v
                  +-------------------+   +-------------------+
                  | PostgreSQL        |   | PostgreSQL        |
                  | Primary :5432     |-->| Read Replica :5433|
                  | (tabel mahasiswa, |WAL| (read-only,       |
                  |  inference_results)|   |  streaming)       |
                  +-------------------+   +-------------------+
                            |
                    volume persisten (Docker volume / PVC-PV)
```

## 2. Struktur Folder

```text
distributed-ml-inference/
├── backend/
│   ├── auth.py              # validasi JWT Keycloak (JWKS, issuer, audience, role)
│   ├── config.py            # konfigurasi dari environment (ConfigMap/Secret)
│   ├── database.py          # koneksi Primary (write) & Replica (read)
│   ├── main.py              # endpoint FastAPI
│   └── requirements.txt
├── database/
│   ├── init.sql             # role replicator, tabel, data awal
│   └── pg_hba.conf          # aturan autentikasi + replikasi
├── docker/
│   └── Dockerfile           # multi-stage build (builder + runtime)
├── keycloak/
│   └── realm-ml-inference.json
├── kubernetes/
│   ├── 00-namespace.yaml
│   ├── 01-secrets.yaml
│   ├── 02-configmaps.yaml
│   ├── 03-configmap-keycloak-realm.yaml
│   ├── 04-storage.yaml      # StorageClass + PV (PVC dibuat StatefulSet)
│   ├── 10-postgres-primary.yaml
│   ├── 11-postgres-replica.yaml
│   ├── 20-keycloak-db.yaml
│   ├── 21-keycloak.yaml
│   └── 30-backend.yaml
├── ml/
│   ├── train.py
│   ├── predict.py
│   └── model.pkl
├── scripts/
│   ├── demo.ps1
│   └── demo.sh
├── docker-compose.yml
├── .env.example
└── README.md
```

## 3. Prasyarat

- Docker Desktop (Docker Compose v2)
- Python 3.12 (untuk menjalankan backend di host, opsional)
- kubectl + kind/minikube (untuk bagian Kubernetes)

## 4. Menjalankan dengan Docker Compose

```bash
copy .env.example .env      # Windows (PowerShell: Copy-Item .env.example .env)
docker compose up -d --build
docker compose ps
```

Layanan:

| Layanan | URL / Port | Keterangan |
|---|---|---|
| Backend / Swagger | http://localhost:8000/docs | FastAPI |
| Keycloak | http://localhost:8080 | Admin console |
| PostgreSQL Primary | localhost:5432 | write |
| PostgreSQL Replica | localhost:5433 | read |

Akun demo Keycloak (realm `ml-inference`):

| Username | Password | Role |
|---|---|---|
| demo | demo123 | user |
| adminuser | admin123 | user, admin |
| admin (console) | admin | Administrator Keycloak |

Client OIDC: `ml-backend` (confidential, secret `ml-backend-secret`).

> Reset total (hapus semua data): `docker compose down -v`

## 5. Mendapatkan Token & Menguji Endpoint

Contoh PowerShell:

```powershell
$token = (Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8080/realms/ml-inference/protocol/openid-connect/token" `
  -ContentType "application/x-www-form-urlencoded" `
  -Body @{
    grant_type    = "password"
    client_id     = "ml-backend"
    client_secret = "ml-backend-secret"
    username      = "demo"
    password      = "demo123"
  }).access_token

$headers = @{ Authorization = "Bearer $token" }

Invoke-RestMethod http://localhost:8000/auth/me -Headers $headers
Invoke-RestMethod http://localhost:8000/mahasiswa -Headers $headers

Invoke-RestMethod -Method Post http://localhost:8000/mahasiswa -Headers $headers `
  -ContentType "application/json" -Body '{"nama":"Budi Santoso","jurusan":"Sistem Informasi"}'

Invoke-RestMethod -Method Post http://localhost:8000/predict -Headers $headers `
  -ContentType "application/json" `
  -Body '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'

Invoke-RestMethod "http://localhost:8000/predictions?limit=5" -Headers $headers
```

Atau jalankan skrip: `powershell -ExecutionPolicy Bypass -File scripts/demo.ps1`.

Tanpa token, endpoint terproteksi akan mengembalikan **HTTP 401**.

## 6. Endpoint

| Method | Endpoint | Auth | Sumber Data / Fungsi |
|---|---|---|---|
| GET | `/` | - | status layanan |
| GET | `/health` | - | health check |
| GET | `/auth/me` | Bearer JWT | menampilkan claims tervalidasi |
| GET | `/mahasiswa` | Bearer JWT | baca dari **Read Replica** |
| POST | `/mahasiswa` | Bearer JWT | tulis ke **Primary** |
| POST | `/predict` | Bearer JWT | inferensi + simpan ke `inference_results` (Primary) |
| GET | `/predictions` | Bearer JWT | riwayat inferensi dari **Read Replica** |

## 7. Deployment Kubernetes

### 7.1 Build & load image (kind)

```bash
docker build -t distributed-ml-inference/backend:2.0.0 -f docker/Dockerfile .
kind load docker-image distributed-ml-inference/backend:2.0.0
```

Untuk minikube: `minikube image load distributed-ml-inference/backend:2.0.0`.

Jika `kind load docker-image` gagal dengan error `content digest ... not found`
(kasus pada kind v0.34-alpha), gunakan impor ekuivalen berikut untuk setiap image
(`backend:2.0.0`, `postgres:16`, `quay.io/keycloak/keycloak:26.0`, `busybox:1.36`):

```bash
docker save postgres:16 -o postgres.tar
docker cp postgres.tar ml-inference-control-plane:/postgres.tar
docker exec ml-inference-control-plane \
  ctr -n k8s.io images import --snapshotter=overlayfs /postgres.tar
```

Prosedur di atas telah diuji pada kind v0.34.0 + Kubernetes v1.37.0: 6 Pod
Running/Ready, seluruh PVC Bound, dan data tetap ada setelah Pod Primary dihapus.


### 7.2 Apply manifest

```bash
kubectl apply -f kubernetes/00-namespace.yaml
kubectl apply -f kubernetes/01-secrets.yaml
kubectl apply -f kubernetes/02-configmaps.yaml
kubectl apply -f kubernetes/03-configmap-keycloak-realm.yaml
kubectl apply -f kubernetes/04-storage.yaml
kubectl apply -f kubernetes/10-postgres-primary.yaml
kubectl apply -f kubernetes/11-postgres-replica.yaml
kubectl apply -f kubernetes/20-keycloak-db.yaml
kubectl apply -f kubernetes/21-keycloak.yaml
kubectl apply -f kubernetes/30-backend.yaml
```

Atau sekaligus: `kubectl apply -f kubernetes/`

### 7.3 Cek status

```bash
kubectl -n ml-inference get pods,svc,pvc,pv
kubectl -n ml-inference rollout status statefulset/postgres-primary
kubectl -n ml-inference rollout status statefulset/postgres-replica
kubectl -n ml-inference rollout status deployment/backend
```

### 7.4 Akses dari laptop

```bash
kubectl -n ml-inference port-forward svc/backend 8000:8000
kubectl -n ml-inference port-forward svc/keycloak 8080:8080
```

(KC issuer dikonfigurasi `http://localhost:8080/realms/ml-inference`, jadi token
diambil lewat port-forward di atas.)

### 7.5 Uji persistensi (wajib untuk rubrik)

```bash
# 1. Tambah data lewat API (lihat bagian 5)
# 2. Hapus Pod database primary
kubectl -n ml-inference delete pod postgres-primary-0
# 3. Tunggu Pod dibuat ulang, lalu cek data masih ada
kubectl -n ml-inference exec postgres-primary-0 -- \
  psql -U admin -d ml_database -c "SELECT count(*) FROM mahasiswa;"
```

PVC akan terikat kembali ke PV yang sama sehingga data tetap ada.

## 8. Pemetaan Rubrik

| Komponen | Implementasi |
|---|---|
| Arsitektur & Docker Setup | `docker/Dockerfile` multi-stage (builder/runtime), layer dependency dipisah, `docker-compose.yml` menghubungkan backend–Postgres–Keycloak |
| Kubernetes & Storage | StatefulSet Primary/Replica/Keycloak-DB, `volumeClaimTemplates` + PV statis, Secret, ConfigMap, Service; uji hapus Pod |
| SSO | Keycloak OIDC, realm + client `ml-backend`, backend memvalidasi signature JWKS, `iss`, `aud`, `exp`, dan role secara mandiri (`backend/auth.py`) |
| Model & Replikasi | write→Primary, read→Replica; hasil inferensi disimpan terstruktur di tabel `inference_results` |
| Laporan & Git | README + diagram arsitektur, skrip demo, repo Git |

## 9. Catatan Keamanan

- Kredensial di `01-secrets.yaml`, `.env.example`, dan realm JSON adalah **nilai demo**.
  Ganti sebelum dipakai di lingkungan nyata dan jangan commit rahasia asli.
- Model `ml/model.pkl` dibuat dengan scikit-learn 1.9.1 (lihat `requirements.txt`).
