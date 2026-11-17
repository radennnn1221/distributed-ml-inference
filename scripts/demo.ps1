param(
    [string]$BackendUrl = "http://localhost:8000",
    [string]$KeycloakUrl = "http://localhost:8080",
    [string]$Realm = "ml-inference",
    [string]$ClientId = "ml-backend",
    [string]$ClientSecret = "ml-backend-secret",
    [string]$Username = "demo",
    [string]$Password = "demo123"
)

$ErrorActionPreference = "Stop"

Write-Host "== 1. Mengambil token OIDC dari Keycloak ==" -ForegroundColor Cyan
$tokenResponse = Invoke-RestMethod -Method Post `
    -Uri "$KeycloakUrl/realms/$Realm/protocol/openid-connect/token" `
    -ContentType "application/x-www-form-urlencoded" `
    -Body @{
        grant_type    = "password"
        client_id     = $ClientId
        client_secret = $ClientSecret
        username      = $Username
        password      = $Password
    }

$headers = @{ Authorization = "Bearer $($tokenResponse.access_token)" }
Write-Host "Token diperoleh (expires_in=$($tokenResponse.expires_in) detik).`n"

Write-Host "== 2. GET /auth/me (validasi JWT mandiri) ==" -ForegroundColor Cyan
Invoke-RestMethod "$BackendUrl/auth/me" -Headers $headers | ConvertTo-Json -Depth 6

Write-Host "`n== 3. GET /mahasiswa (Read Replica) ==" -ForegroundColor Cyan
Invoke-RestMethod "$BackendUrl/mahasiswa" -Headers $headers | ConvertTo-Json -Depth 6

Write-Host "`n== 4. POST /mahasiswa (tulis ke Primary) ==" -ForegroundColor Cyan
Invoke-RestMethod -Method Post "$BackendUrl/mahasiswa" -Headers $headers `
    -ContentType "application/json" `
    -Body '{"nama":"Budi Santoso","jurusan":"Sistem Informasi"}' |
    ConvertTo-Json -Depth 6

Write-Host "`n== 5. POST /predict (inferensi + simpan terstruktur) ==" -ForegroundColor Cyan
Invoke-RestMethod -Method Post "$BackendUrl/predict" -Headers $headers `
    -ContentType "application/json" `
    -Body '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}' |
    ConvertTo-Json -Depth 6

Write-Host "`nMenunggu replikasi (3 detik)..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "`n== 6. GET /predictions (Read Replica) ==" -ForegroundColor Cyan
Invoke-RestMethod "$BackendUrl/predictions?limit=5" -Headers $headers | ConvertTo-Json -Depth 6

Write-Host "`nSelesai." -ForegroundColor Green
