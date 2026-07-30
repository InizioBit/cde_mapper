# Setup Tahap 9: Logging

## Ringkasan

Tahap 9 menambahkan logging aplikasi untuk memantau request API, status cache, akses Athena, durasi scraping, jumlah hasil, dan error upstream.

File yang dibuat atau diperbarui:

- `app/logging_config.py`
- `app/config.py`
- `app/main.py`
- `app/services/search_service.py`
- `app/services/athena_browser_adapter.py`
- `app/routers/athena.py`
- `scripts/smoke_logging.py`
- `.env.example`
- `.gitignore`
- `setup_tahap_9.md`
- `README.md`

## Konfigurasi

Variabel environment:

```text
LOG_LEVEL=INFO
LOG_FILE=./logs/athena_api.log
```

Jika `LOG_FILE` memakai path relatif, path dihitung dari folder project `Riset/api-athena`.

## Output Logging

Logging dikirim ke:

- console;
- file `logs/athena_api.log`.

Format:

```text
timestamp level logger message
```

Contoh:

```text
2026-07-30 10:30:00,123 INFO app.services.search_service cache_miss query='diabetes' domain='Condition' page=1 refresh=False cache_key=...
```

## Event yang Dicatat

### Request API

- `request_complete`
- `request_error`

Field:

- method;
- path;
- status code;
- durasi request dalam milidetik.

### Search Service

- `search_validation_error`
- `cache_hit`
- `cache_miss`
- `athena_search_success`
- `cache_save`
- `athena_timeout`
- `athena_timeout_stale_cache`
- `athena_parse_error`
- `athena_parse_error_stale_cache`
- `athena_upstream_error`
- `athena_upstream_error_stale_cache`

### Athena Browser Adapter

- `athena_browser_open`
- `athena_browser_results`
- `athena_direct_csv_download`
- `athena_direct_csv_parsed`
- `athena_csv_download`
- `athena_csv_parsed`
- `athena_parse_failed`
- `athena_concept_open`

### Cache Endpoint

- `cache_status`
- `cache_clear`

## Smoke Test

Jalankan dari folder `Riset/api-athena`:

```powershell
conda run -n cde-mapper-win python -m scripts.smoke_logging
```

Smoke test memakai fake adapter sehingga tidak membutuhkan akses Athena live.

Output menampilkan lokasi file log dan beberapa baris terakhir, misalnya:

```text
D:\Program\cde_mapper\Riset\api-athena\logs\athena_api.log
2026-07-30 10:30:00,123 INFO app.services.search_service cache_miss ...
2026-07-30 10:30:00,234 INFO app.services.search_service athena_search_success ...
2026-07-30 10:30:00,345 INFO app.services.search_service cache_hit ...
```

## Catatan

Stack trace penuh hanya ditulis ke log untuk exception yang tidak tertangani atau error CSV internal. Respons API tetap memakai pesan ringkas dari Tahap 8.
