# Setup Tahap 4: Implementasi FastAPI

## Ringkasan

Tahap 4 menambahkan aplikasi FastAPI dasar dan router awal untuk API Athena lokal.

File yang dibuat:

- `app/main.py`
- `app/routers/__init__.py`
- `app/routers/athena.py`
- `setup_tahap_4.md`

## Endpoint yang Tersedia

### Health Check

```http
GET /health
```

Contoh response:

```json
{
  "status": "ok",
  "app": "Local Athena API",
  "version": "0.1.0"
}
```

### Athena Router

Endpoint berikut sudah terdaftar di OpenAPI, tetapi logika service-nya belum diimplementasikan pada tahap ini.

```http
GET /api/athena/search
GET /api/athena/concepts/{concept_id}
GET /api/athena/cache
DELETE /api/athena/cache
```

Untuk sementara endpoint Athena mengembalikan `501 Not Implemented`. Implementasi cache masuk Tahap 5, sedangkan adapter Playwright Athena masuk Tahap 6.

## Startup Behavior

Saat aplikasi FastAPI start:

1. Konfigurasi dibaca dari `.env` atau default.
2. Folder `data/` dibuat jika belum ada.
3. Database SQLite diinisialisasi menggunakan `init_db()`.

## Menjalankan Server

Jalankan dari folder `Riset/api-athena`:

```powershell
conda run -n cde-mapper-win python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Mode development:

```powershell
conda run -n cde-mapper-win python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Dokumentasi Swagger:

```text
http://127.0.0.1:8000/docs
```

OpenAPI JSON:

```text
http://127.0.0.1:8000/openapi.json
```

## Verifikasi Tanpa Menjalankan Server

Jalankan:

```powershell
conda run -n cde-mapper-win python -c "from app.main import app; print(app.title); print(len(app.routes))"
```

Output minimal:

```text
Local Athena API
8
```

## Status

Tahap 4 selesai jika:

- `app.main:app` dapat diimport.
- `/health` mengembalikan status `ok`.
- `/docs` dapat menampilkan endpoint health dan Athena router.
