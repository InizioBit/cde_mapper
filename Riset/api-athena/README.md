# Athena API Lokal

Athena API Lokal adalah service FastAPI untuk mencari konsep OMOP dari Athena OHDSI dan mengembalikan hasilnya sebagai JSON lokal.

Service ini dibuat sebagai adapter karena endpoint JSON internal Athena dapat mengembalikan `403 Forbidden`. Implementasi saat ini mengambil data dari endpoint CSV Athena yang masih dapat diakses dari halaman web Athena, lalu menyimpan hasil pencarian ke SQLite sebagai cache.

## Fitur Utama

- Search concept OMOP dari Athena OHDSI.
- Filter berdasarkan domain, vocabulary, concept class, dan standard concept.
- Cache hasil pencarian menggunakan SQLite.
- Fallback stale cache jika Athena gagal diakses.
- Error handling dengan status HTTP yang jelas.
- Logging request, cache, dan akses Athena.
- Dokumentasi API otomatis melalui Swagger UI.

## Requirement

Dependency utama:

```text
fastapi
uvicorn
playwright
pydantic
SQLAlchemy
aiosqlite
python-dotenv
```

Versi lengkap tersedia di:

```text
requirements.txt
```

Python yang direkomendasikan:

```text
Python 3.10+
```

## Instalasi

Jalankan dari folder `Riset/api-athena`:

```powershell
python -m pip install -r requirements.txt
```

Install browser Chromium untuk Playwright:

```powershell
python -m playwright install chromium
```

## Persiapan SQLite

API lokal menggunakan SQLite sebagai cache hasil pencarian Athena.

Database default:

```text
data/athena_cache.sqlite3
```

Tabel SQLite akan dibuat otomatis saat service API dijalankan karena aplikasi memanggil inisialisasi database pada startup.

Untuk inisialisasi manual, jalankan dari folder `Riset/api-athena`:

```powershell
python -m scripts.init_db
```

Folder `data/` akan dibuat otomatis jika belum ada.

Untuk melihat status cache:

```http
GET /api/athena/cache
```

Untuk menghapus isi cache:

```http
DELETE /api/athena/cache
```

## Konfigurasi

Salin file `.env.example` menjadi `.env` jika ingin mengubah konfigurasi lokal.

```powershell
copy .env.example .env
```

Nilai konfigurasi default:

```text
ATHENA_BASE_URL=https://athena.ohdsi.org
ATHENA_TIMEOUT_SECONDS=30
CACHE_TTL_DAYS=7
DATABASE_URL=sqlite+aiosqlite:///./data/athena_cache.sqlite3
PLAYWRIGHT_HEADLESS=true
LOG_LEVEL=INFO
LOG_FILE=./logs/athena_api.log
```

Keterangan:

| Variabel | Keterangan |
|---|---|
| `ATHENA_BASE_URL` | Base URL Athena OHDSI |
| `ATHENA_TIMEOUT_SECONDS` | Timeout akses Athena dalam detik |
| `CACHE_TTL_DAYS` | Masa berlaku cache pencarian |
| `DATABASE_URL` | Lokasi database SQLite cache |
| `PLAYWRIGHT_HEADLESS` | Mode headless browser Playwright |
| `LOG_LEVEL` | Level logging aplikasi |
| `LOG_FILE` | Lokasi file log |

## Menjalankan Service API

Jalankan dari folder `Riset/api-athena`:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Search Concept

Endpoint utama:

```http
GET /api/athena/search
```

Contoh request:

```text
http://127.0.0.1:8000/api/athena/search?query=diabetes&domain=Condition
```

Parameter:

| Parameter | Wajib | Default | Keterangan |
|---|---:|---|---|
| `query` | Ya | - | Kata kunci pencarian Athena |
| `domain` | Tidak | `null` | Filter domain OMOP, misalnya `Condition`, `Drug`, `Measurement`, atau `Procedure` |
| `page` | Tidak | `1` | Nomor halaman pencarian |
| `standard_concept` | Tidak | `null` | Filter standard concept |
| `vocabulary` | Tidak | `null` | Filter vocabulary, misalnya `SNOMED`, `LOINC`, atau `RxNorm` |
| `concept_class` | Tidak | `null` | Filter concept class |
| `refresh` | Tidak | `false` | Jika `true`, cache lokal dilewati dan data diambil ulang dari Athena |
| `pageSize` | Tidak | `null` | Jumlah item per halaman, kompatibel dengan parameter Athena lama |
| `standardConcept` | Tidak | `null` | Filter standard concept bergaya Athena lama |
| `conceptClass` | Tidak | `null` | Filter concept class bergaya Athena lama |
| `invalidReason` | Tidak | `null` | Filter validitas konsep, misalnya `Valid` |
| `format` | Tidak | `local` | Gunakan `athena` untuk output kompatibel pipeline lama |

Contoh dengan filter vocabulary:

```text
http://127.0.0.1:8000/api/athena/search?query=diabetes&domain=Condition&vocabulary=SNOMED
```

Contoh memaksa refresh cache:

```text
http://127.0.0.1:8000/api/athena/search?query=diabetes&domain=Condition&refresh=true
```

Contoh output kompatibel pipeline lama:

```text
http://127.0.0.1:8000/api/athena/search?query=diabetes&domain=Condition&page=1&pageSize=10&standardConcept=Standard&standardConcept=Classification&vocabulary=SNOMED&vocabulary=LOINC&invalidReason=Valid&format=athena
```

Contoh respons:

```json
{
  "query": "diabetes",
  "domain": "Condition",
  "page": 1,
  "source": "athena_csv_http",
  "result_count": 4348,
  "cached": false,
  "stale": false,
  "cache": {
    "hit": false,
    "stale": false,
    "key": "dad08e83cfe0dc30fa5ca5ff3155db59c848df79f87dcf322776268be4fa57c4"
  },
  "results": [
    {
      "concept_id": 28660,
      "concept_name": "Immune Dysregulation, Polyendocrinopathy, Enteropathy, X-Linked Syndrome",
      "domain_id": "Condition",
      "vocabulary_id": "MeSH",
      "concept_class_id": "Suppl Concept",
      "standard_concept": "Non-standard",
      "concept_code": "C580192",
      "valid_start_date": null,
      "valid_end_date": null,
      "invalid_reason": "Valid"
    }
  ]
}
```

Keterangan metadata:

| Field | Keterangan |
|---|---|
| `source` | Sumber hasil, misalnya `athena_csv_http` |
| `result_count` | Jumlah hasil yang dikembalikan |
| `cached` | `true` jika respons berasal dari cache |
| `stale` | `true` jika cache lama dipakai karena Athena gagal |
| `cache.hit` | Status cache hit/miss |
| `cache.key` | Hash cache berdasarkan query dan filter |

## Format Kompatibilitas Athena

Pipeline lama pada `rag/athena_api_retriever.py` mengharapkan respons bergaya Athena dengan key `content` dan field:

```text
id
code
name
domain
vocabulary
standardConcept
className
```

Gunakan query param berikut untuk mendapatkan format tersebut:

```text
format=athena
```

Contoh respons ringkas:

```json
{
  "content": [
    {
      "id": 192279,
      "code": "127013003",
      "name": "Disorder of kidney due to diabetes mellitus",
      "domain": "Condition",
      "vocabulary": "SNOMED",
      "standardConcept": "Standard",
      "className": "Disorder",
      "invalidReason": "Valid"
    }
  ],
  "result_count": 10,
  "total_result_count": 662
}
```

`pageSize` diterapkan di API lokal setelah CSV Athena diparse, sehingga `page=1&pageSize=10` mengembalikan 10 item pertama.

## Integrasi Pipeline

`rag/athena_api_retriever.py` diarahkan ke API lokal secara default:

```text
http://127.0.0.1:8000/api/athena/search
```

Endpoint dapat diganti dengan environment variable:

```text
ATHENA_API_URL=http://127.0.0.1:8000/api/athena/search
```

## Strategi Akses Athena

Urutan pengambilan data:

1. Mengambil CSV Athena langsung melalui HTTP.
2. Jika jalur langsung gagal, adapter dapat memakai Playwright untuk membuka halaman Athena.
3. Jika Athena gagal tetapi cache tersedia, API mengembalikan cache dengan `stale: true`.

Endpoint CSV Athena yang digunakan mengikuti pola:

```text
https://athena.ohdsi.org/api/v1/concepts/download/csv?query=diabetes&boosts=&page=1&domain=Condition
```

## Error Handling

| Kondisi | HTTP Status | Respons |
|---|---:|---|
| Query kosong setelah trimming | `400` | Request tidak valid |
| Athena timeout tanpa cache | `504` | Gateway timeout |
| Parsing hasil Athena gagal tanpa cache | `502` | Bad gateway |
| Athena gagal tanpa cache | `502` | Bad gateway |
| Athena gagal tetapi cache tersedia | `200` | Respons cache dengan `stale: true` |

## Logging

Log ditulis ke console dan file:

```text
logs/athena_api.log
```

Event penting yang dicatat:

- `request_complete`
- `cache_hit`
- `cache_miss`
- `cache_save`
- `athena_search_success`
- `athena_direct_csv_download`
- `athena_direct_csv_parsed`
- `athena_timeout_stale_cache`

## Cache

Cache disimpan di SQLite dan mengikuti konfigurasi:

```text
DATABASE_URL=sqlite+aiosqlite:///./data/athena_cache.sqlite3
```

Masa berlaku cache diatur oleh:

```text
CACHE_TTL_DAYS=7
```

## Verifikasi

Jalankan test suite:

```powershell
python -m unittest discover -s tests -v
```

Smoke test live Athena:

```powershell
python -m scripts.smoke_athena_adapter
```

Catatan: smoke test live Athena membutuhkan koneksi internet.
