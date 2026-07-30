# Setup Tahap 2: Konfigurasi Aplikasi

## Ringkasan

Tahap 2 menambahkan struktur package awal dan modul konfigurasi aplikasi.

File yang dibuat:

- `app/__init__.py`
- `app/config.py`
- `data/`
- `setup_tahap_2.md`

## Sumber Konfigurasi

Konfigurasi dibaca dari file `.env` di root project `Riset/api-athena`. Jika `.env` tidak ada, aplikasi memakai nilai default yang sama dengan `.env.example`.

Nilai konfigurasi:

| Nama | Default | Keterangan |
|---|---|---|
| `ATHENA_BASE_URL` | `https://athena.ohdsi.org` | Base URL Athena |
| `ATHENA_TIMEOUT_SECONDS` | `30` | Timeout request/browser action |
| `CACHE_TTL_DAYS` | `7` | Masa berlaku cache |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/athena_cache.sqlite3` | Lokasi database SQLite |
| `PLAYWRIGHT_HEADLESS` | `true` | Mode browser Playwright |

## Validasi

`app/config.py` melakukan validasi:

- `ATHENA_BASE_URL` wajib diawali `http://` atau `https://`.
- `DATABASE_URL` pada tahap ini wajib menggunakan `sqlite+aiosqlite:///`.
- `ATHENA_TIMEOUT_SECONDS` minimal `1`.
- `CACHE_TTL_DAYS` minimal `1`.
- `PLAYWRIGHT_HEADLESS` menerima nilai boolean seperti `true`, `false`, `1`, `0`, `yes`, dan `no`.

## Verifikasi

Jalankan dari folder `Riset/api-athena`:

```powershell
conda run -n cde-mapper-win python -c "from app.config import get_settings; s=get_settings(); print(s.athena_base_url); print(s.database_url); print(s.playwright_headless)"
```

Output yang diharapkan:

```text
https://athena.ohdsi.org
sqlite+aiosqlite:///./data/athena_cache.sqlite3
True
```

## Status

Tahap 2 selesai jika modul `app.config` dapat diimport dan fungsi `get_settings()` mengembalikan konfigurasi tanpa error.
