#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
REALM="${REALM:-ml-inference}"
CLIENT_ID="${CLIENT_ID:-ml-backend}"
CLIENT_SECRET="${CLIENT_SECRET:-ml-backend-secret}"
USERNAME="${USERNAME:-demo}"
PASSWORD="${PASSWORD:-demo123}"

echo "== 1. Mengambil token OIDC dari Keycloak =="
TOKEN=$(curl -sS -X POST \
  "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "username=$USERNAME" \
  -d "password=$PASSWORD" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

AUTH="Authorization: Bearer $TOKEN"

echo "== 2. GET /auth/me =="
curl -sS "$BACKEND_URL/auth/me" -H "$AUTH"; echo

echo "== 3. GET /mahasiswa (Read Replica) =="
curl -sS "$BACKEND_URL/mahasiswa" -H "$AUTH"; echo

echo "== 4. POST /mahasiswa (Primary) =="
curl -sS -X POST "$BACKEND_URL/mahasiswa" -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{"nama":"Budi Santoso","jurusan":"Sistem Informasi"}'; echo

echo "== 5. POST /predict =="
curl -sS -X POST "$BACKEND_URL/predict" -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'; echo

echo "Menunggu replikasi (3 detik)..."
sleep 3

echo "== 6. GET /predictions (Read Replica) =="
curl -sS "$BACKEND_URL/predictions?limit=5" -H "$AUTH"; echo
