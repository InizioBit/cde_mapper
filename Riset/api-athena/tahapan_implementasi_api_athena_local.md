# Tahapan Implementasi API Athena Lokal

## Tujuan

Dokumen ini menjelaskan tahapan implementasi API lokal untuk pencarian konsep OMOP dari Athena OHDSI menggunakan stack:

- Python
- FastAPI
- Playwright
- SQLite

API lokal ini bertindak sebagai adapter/proxy. Karena endpoint internal Athena saat ini tidak dapat dipanggil langsung dan mengembalikan `403 Forbidden`, pendekatan awal yang disarankan adalah membuka halaman Athena menggunakan browser headless, mengambil hasil pencarian dari halaman, lalu menormalkan hasilnya menjadi JSON lokal.

## Arsitektur

```text
Client / aplikasi lokal
        |
        v
FastAPI Local Athena API
        |
        +-- SQLite Cache
        |
        +-- Athena Search Service
                |
                +-- Playwright Headless Browser
                        |
                        v
                Athena OHDSI Web
```

## Target Endpoint Lokal

### 1. Search Concept

```http
GET /api/athena/search
```

Parameter:

| Parameter | Wajib | Contoh | Keterangan |
|---|---|---|---|
| `query` | Ya | `heart rate` | Kata kunci pencarian |
| `domain` | Tidak | `Condition` | Domain OMOP |
| `page` | Tidak | `1` | Nomor halaman |
| `standard_concept` | Tidak | `S` | Filter standard concept |
| `vocabulary` | Tidak | `SNOMED` | Filter vocabulary |
| `concept_class` | Tidak | `Clinical Finding` | Filter concept class |

Contoh request:

```http
GET /api/athena/search?domain=Condition&query=heart%20rate&page=1
```

Contoh response:

```json
{
  "query": "heart rate",
  "domain": "Condition",
  "page": 1,
  "source": "athena",
  "cached": false,
  "stale": false,
  "results": [
    {
      "concept_id": 123456,
      "concept_name": "Example concept",
      "domain_id": "Condition",
      "vocabulary_id": "SNOMED",
      "concept_class_id": "Clinical Finding",
      "standard_concept": "S",
      "concept_code": "123456",
      "valid_start_date": "2020-01-01",
      "valid_end_date": "2099-12-31",
      "invalid_reason": null
    }
  ]
}
```

### 2. Get Concept Detail

```http
GET /api/athena/concepts/{concept_id}
```

Endpoint ini digunakan untuk membuka halaman detail konsep Athena dan mengambil informasi detail konsep.

### 3. Cache Status

```http
GET /api/athena/cache
```

Endpoint ini menampilkan jumlah cache, waktu update terakhir, dan daftar query yang pernah disimpan.

### 4. Clear Cache

```http
DELETE /api/athena/cache
```

Endpoint ini menghapus cache lokal. Gunakan hanya untuk kebutuhan pengembangan atau reset data.

## Struktur Proyek

Struktur awal yang disarankan:

```text
Riset/api-athena/
  app/
    main.py
    config.py
    database.py
    models.py
    schemas.py
    services/
      athena_search_service.py
      athena_browser_adapter.py
      cache_service.py
    routers/
      athena.py
  tests/
    test_search_api.py
    test_cache_service.py
  data/
    athena_cache.sqlite3
  requirements.txt
  README.md
  tahapan_implementasi_api_athena_local.md
```

## Tahap 1: Persiapan Environment

### 1.1 Buat virtual environment

```bash
python -m venv .venv
```

Aktivasi di Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 1.2 Install dependency

```bash
pip install fastapi uvicorn playwright pydantic sqlalchemy aiosqlite python-dotenv
```

### 1.3 Install browser Playwright

```bash
playwright install chromium
```

### 1.4 Simpan dependency

```bash
pip freeze > requirements.txt
```

## Tahap 2: Konfigurasi Aplikasi

Buat konfigurasi utama di `app/config.py`.

Konfigurasi minimal:

```text
ATHENA_BASE_URL=https://athena.ohdsi.org
ATHENA_TIMEOUT_SECONDS=30
CACHE_TTL_DAYS=7
DATABASE_URL=sqlite+aiosqlite:///./data/athena_cache.sqlite3
PLAYWRIGHT_HEADLESS=true
```

Tujuannya agar perubahan URL, timeout, TTL cache, dan mode browser tidak tersebar di banyak file.

## Tahap 3: Desain Database SQLite

Gunakan SQLite sebagai cache hasil pencarian. Tabel awal:

### 3.1 Tabel `search_cache`

Kolom:

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id` | integer | Primary key |
| `cache_key` | text | Hash dari query dan filter |
| `query` | text | Kata kunci pencarian |
| `domain` | text | Domain OMOP |
| `page` | integer | Nomor halaman |
| `filters_json` | text | Filter tambahan dalam JSON |
| `response_json` | text | Hasil normalisasi |
| `created_at` | datetime | Waktu cache dibuat |
| `updated_at` | datetime | Waktu cache diperbarui |
| `expires_at` | datetime | Waktu cache kedaluwarsa |

### 3.2 Tabel `concept_cache`

Kolom:

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id` | integer | Primary key |
| `concept_id` | integer | OMOP concept ID |
| `response_json` | text | Detail konsep |
| `created_at` | datetime | Waktu cache dibuat |
| `updated_at` | datetime | Waktu cache diperbarui |
| `expires_at` | datetime | Waktu cache kedaluwarsa |

## Tahap 4: Implementasi FastAPI

### 4.1 Buat `app/main.py`

Isi utama:

- Inisialisasi FastAPI.
- Register router Athena.
- Tambahkan health check.

Endpoint health check:

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

### 4.2 Buat router `app/routers/athena.py`

Router bertanggung jawab menerima HTTP request, validasi parameter, lalu memanggil service.

Endpoint minimal:

```text
GET /api/athena/search
GET /api/athena/concepts/{concept_id}
GET /api/athena/cache
DELETE /api/athena/cache
```

## Tahap 5: Implementasi Cache Service

Buat `app/services/cache_service.py`.

Fungsi utama:

```text
build_cache_key(query, domain, page, filters)
get_search_cache(cache_key)
save_search_cache(cache_key, payload)
is_cache_valid(cache_row)
clear_cache()
```

Aturan:

- Jika cache valid, langsung kembalikan hasil dari SQLite.
- Jika cache kedaluwarsa tetapi Athena gagal diakses, kembalikan cache lama dengan flag `stale: true`.
- Jika tidak ada cache dan Athena gagal, kembalikan error `502 Bad Gateway`.

## Tahap 6: Implementasi Athena Browser Adapter

Buat `app/services/athena_browser_adapter.py`.

Tanggung jawab:

1. Membentuk URL Athena dari parameter lokal.
2. Membuka URL menggunakan Playwright Chromium headless.
3. Menunggu halaman selesai render.
4. Mengambil hasil tabel dari DOM.
5. Mengubah hasil DOM menjadi struktur Python.

Contoh URL Athena:

```text
https://athena.ohdsi.org/search-terms/terms?domain=Condition&query=heart+rate&boosts&page=1
```

Strategi scraping:

- Gunakan selector tabel hasil pencarian.
- Jika selector belum stabil, fallback ke pencarian teks/kolom yang mengandung `Concept ID`, `Concept Name`, `Domain`, `Vocabulary`, dan `Concept Class`.
- Simpan HTML debug saat parsing gagal agar mudah dianalisis.

Output adapter harus sudah berbentuk list dictionary:

```json
[
  {
    "concept_id": 123456,
    "concept_name": "Example concept",
    "domain_id": "Condition",
    "vocabulary_id": "SNOMED",
    "concept_class_id": "Clinical Finding",
    "standard_concept": "S",
    "concept_code": "123456",
    "valid_start_date": null,
    "valid_end_date": null,
    "invalid_reason": null
  }
]
```

## Tahap 7: Implementasi Search Service

Buat `app/services/athena_search_service.py`.

Alur kerja:

```text
1. Terima query dari router.
2. Bangun cache_key.
3. Cek SQLite cache.
4. Jika cache valid, return cached result.
5. Jika tidak valid, panggil Athena Browser Adapter.
6. Normalisasi hasil.
7. Simpan hasil ke SQLite.
8. Return response ke client.
```

Response harus selalu menyertakan metadata:

```json
{
  "query": "heart rate",
  "domain": "Condition",
  "page": 1,
  "source": "athena",
  "cached": false,
  "stale": false,
  "result_count": 15,
  "results": []
}
```

## Tahap 8: Error Handling

Gunakan status HTTP yang jelas:

| Kondisi | HTTP Status | Keterangan |
|---|---:|---|
| Query kosong | 400 | Parameter tidak valid |
| Athena timeout | 504 | Gateway timeout |
| Athena gagal dan tidak ada cache | 502 | Bad gateway |
| Athena gagal tetapi ada stale cache | 200 | Response tetap diberikan dengan `stale: true` |
| Parsing gagal | 502 | Struktur halaman berubah atau selector salah |

Simpan detail error di log, tetapi jangan semua stack trace dikirim ke client.

## Tahap 9: Logging

Log minimal:

- URL Athena yang dipanggil.
- Waktu request.
- Durasi scraping.
- Status cache: hit, miss, stale.
- Jumlah hasil.
- Error Playwright atau parsing.

Contoh log:

```text
2026-07-30 15:00:00 INFO cache_miss query="heart rate" domain="Condition" page=1
2026-07-30 15:00:04 INFO athena_scrape_success result_count=15 duration_ms=4200
```

## Tahap 10: Testing

### 10.1 Unit Test

Prioritas:

- `build_cache_key`
- validasi TTL cache
- normalisasi parameter
- parsing hasil HTML fixture

### 10.2 Integration Test

Test endpoint:

```text
GET /health
GET /api/athena/search?query=heart%20rate&domain=Condition&page=1
```

### 10.3 Fixture HTML

Simpan HTML hasil render Athena sebagai fixture agar parsing bisa dites tanpa selalu membuka Athena.

Contoh:

```text
tests/fixtures/athena_search_heart_rate.html
```

## Tahap 11: Menjalankan API Lokal

Jalankan server:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Buka dokumentasi Swagger:

```text
http://127.0.0.1:8000/docs
```

Contoh request:

```text
http://127.0.0.1:8000/api/athena/search?domain=Condition&query=heart%20rate&page=1
```

## Tahap 12: Validasi Manual

Setelah API berjalan, lakukan validasi:

1. Bandingkan hasil API lokal dengan tampilan Athena untuk query yang sama.
2. Cek apakah jumlah hasil per halaman sama.
3. Cek apakah `concept_id`, `concept_name`, `domain_id`, `vocabulary_id`, dan `standard_concept` terbaca benar.
4. Cek apakah cache digunakan pada request kedua.
5. Matikan koneksi Athena atau paksa timeout, lalu pastikan stale cache tetap bisa dikembalikan.

## Tahap 13: Hardening

Setelah MVP stabil, tambahkan:

- Rate limiting.
- Retry dengan exponential backoff.
- Background refresh cache.
- Admin endpoint untuk melihat query populer.
- Export hasil pencarian ke CSV.
- Dockerfile dan Docker Compose.
- Opsi migrasi SQLite ke PostgreSQL.

## Tahap 14: Roadmap Produksi

Untuk penggunaan serius, API lokal sebaiknya tidak bergantung penuh pada scraping halaman Athena. Roadmap yang lebih stabil:

1. Gunakan Playwright adapter hanya sebagai solusi awal.
2. Tambahkan cache agresif untuk mengurangi akses ke Athena.
3. Bangun local OMOP vocabulary mirror dari file vocabulary resmi Athena.
4. Pindahkan pencarian utama ke database lokal.
5. Jadikan Athena hanya sebagai sumber sinkronisasi atau validasi manual.

## Risiko Teknis

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Struktur HTML Athena berubah | Parser gagal | Simpan fixture HTML dan buat selector fallback |
| Athena lambat atau down | API ikut lambat | Gunakan cache dan timeout |
| Endpoint internal tetap `403` | Tidak bisa pakai request HTTP langsung | Gunakan Playwright headless |
| Vocabulary berlisensi | Risiko kepatuhan | Hormati license Athena, SNOMED, dan HemOnc |
| Scraping terlalu sering | Membebani Athena | Rate limit dan cache TTL |

## Kesimpulan

Implementasi yang paling realistis untuk kondisi saat ini adalah:

```text
FastAPI + Playwright + SQLite
```

FastAPI menyediakan API lokal yang bersih dan mudah diintegrasikan. Playwright digunakan karena Athena berbentuk aplikasi web dinamis dan endpoint internalnya tidak dapat dipanggil langsung. SQLite digunakan sebagai cache agar pencarian lebih cepat, lebih stabil, dan tidak selalu bergantung pada akses real-time ke Athena.

Setelah MVP berjalan, arah pengembangan terbaik adalah membuat local OMOP vocabulary mirror agar sistem lebih cepat, stabil, dan tidak bergantung pada perubahan halaman Athena.
