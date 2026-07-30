# Setup Tahap 5: Implementasi Cache Service

## Ringkasan

Tahap 5 menambahkan service cache berbasis SQLite untuk menyimpan hasil pencarian Athena dan detail konsep.

File yang dibuat:

- `app/services/__init__.py`
- `app/services/cache_service.py`
- `scripts/smoke_cache.py`
- `setup_tahap_5.md`

File yang diperbarui:

- `app/routers/athena.py`
- `README.md`

## Fungsi Cache Service

`app/services/cache_service.py` menyediakan fungsi:

| Fungsi | Keterangan |
|---|---|
| `build_cache_key()` | Membuat SHA-256 key dari query, domain, page, dan filter |
| `get_search_cache()` | Mengambil cache pencarian dan status valid/stale |
| `save_search_cache()` | Menyimpan atau memperbarui cache pencarian |
| `get_concept_cache()` | Mengambil cache detail konsep dan status valid/stale |
| `save_concept_cache()` | Menyimpan atau memperbarui cache detail konsep |
| `get_cache_status()` | Menghitung total, valid, expired, dan update terakhir |
| `clear_cache()` | Menghapus semua cache search dan concept |

## Endpoint Aktif

Endpoint cache sekarang sudah aktif:

```http
GET /api/athena/cache
DELETE /api/athena/cache
```

Contoh response `GET /api/athena/cache`:

```json
{
  "search_cache": {
    "total": 0,
    "expired": 0,
    "valid": 0,
    "last_updated_at": null
  },
  "concept_cache": {
    "total": 0,
    "expired": 0,
    "valid": 0,
    "last_updated_at": null
  }
}
```

Contoh response `DELETE /api/athena/cache`:

```json
{
  "status": "ok",
  "deleted": {
    "search_cache_deleted": 0,
    "concept_cache_deleted": 0
  }
}
```

## Catatan

Endpoint berikut masih `501 Not Implemented` karena membutuhkan search service dan Playwright adapter:

```http
GET /api/athena/search
GET /api/athena/concepts/{concept_id}
```

Implementasi endpoint tersebut masuk Tahap 6 dan Tahap 7.

## Verifikasi

Jalankan dari folder `Riset/api-athena`:

```powershell
conda run -n cde-mapper-win python -c "from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); print(c.get('/api/athena/cache').json()); print(c.delete('/api/athena/cache').json())"
```

Output harus menunjukkan response JSON cache status dan clear cache dengan status `ok`.

Verifikasi round-trip service cache:

```powershell
conda run -n cde-mapper-win python -m scripts.smoke_cache
```

Output harus memuat potongan cache key, nilai `True`, dan payload dummy yang disimpan.

## Status

Tahap 5 selesai jika:

- cache service dapat diimport;
- `GET /api/athena/cache` mengembalikan status cache;
- `DELETE /api/athena/cache` menghapus cache tanpa error;
- fungsi save/get cache dapat melakukan round-trip data JSON.
