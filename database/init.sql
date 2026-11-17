-- ============================================================
-- Inisialisasi PostgreSQL Primary
-- Dijalankan sekali saat volume data masih kosong
-- (docker-entrypoint-initdb.d / ConfigMap init.sql)
-- ============================================================

-- 1. Role untuk streaming replication (dipakai pg_basebackup di replica)
--    Password default: repl123. Samakan dengan REPLICATION_PASSWORD
--    pada docker-compose / Secret Kubernetes jika diubah.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'replicator') THEN
        CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'repl123';
    END IF;
END
$$;

-- 2. Tabel operasional
CREATE TABLE IF NOT EXISTS mahasiswa (
    id SERIAL PRIMARY KEY,
    nama TEXT NOT NULL,
    jurusan TEXT NOT NULL
);

-- 3. Tabel penyimpanan hasil inferensi model secara terstruktur
CREATE TABLE IF NOT EXISTS inference_results (
    id BIGSERIAL PRIMARY KEY,
    sepal_length DOUBLE PRECISION NOT NULL,
    sepal_width DOUBLE PRECISION NOT NULL,
    petal_length DOUBLE PRECISION NOT NULL,
    petal_width DOUBLE PRECISION NOT NULL,
    prediction TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    subject TEXT,
    model_name TEXT NOT NULL DEFAULT 'Random Forest',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Data awal (id 1..6), sehingga POST /mahasiswa berikutnya menjadi id 7
INSERT INTO mahasiswa (nama, jurusan) VALUES
    ('Andi Pratama', 'Teknik Informatika'),
    ('Citra Lestari', 'Sistem Informasi'),
    ('Dewi Anggraini', 'Teknik Informatika'),
    ('Eko Nugroho', 'Sistem Informasi'),
    ('Fajar Ramadhan', 'Teknik Komputer'),
    ('Gita Permata', 'Teknik Informatika');
