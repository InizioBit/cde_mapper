# Setup Tahap 10: Testing

## Ringkasan

Tahap 10 menambahkan test suite otomatis untuk API Athena lokal. Test dibuat dengan `unittest` bawaan Python agar tidak membutuhkan dependency baru.

File yang dibuat:

- `tests/__init__.py`
- `tests/test_api.py`
- `tests/test_athena_browser_adapter.py`
- `tests/test_cache_service.py`
- `tests/test_search_service.py`
- `setup_tahap_10.md`

## Cakupan Test

### API

File:

```text
tests/test_api.py
```

Cakupan:

- `GET /health` mengembalikan `200`;
- `GET /api/athena/cache` mengembalikan struktur cache;
- query kosong pada `/api/athena/search` mengembalikan `400`;
- endpoint detail konsep masih mengembalikan `501`.

### Athena Browser Adapter

File:

```text
tests/test_athena_browser_adapter.py
```

Cakupan:

- pembentukan URL halaman pencarian Athena;
- pembentukan URL download CSV Athena;
- parsing CSV tab-separated dari Athena;
- mapping baris DOM sesuai urutan kolom Athena.

### Cache Service

File:

```text
tests/test_cache_service.py
```

Cakupan:

- normalisasi cache key;
- perubahan cache key berdasarkan halaman;
- normalisasi filter;
- TTL cache;
- validasi cache kedaluwarsa.

### Search Service

File:

```text
tests/test_search_service.py
```

Cakupan:

- cache miss lalu cache hit;
- query kosong menghasilkan `AthenaSearchValidationError`;
- timeout tanpa cache menghasilkan `AthenaSearchTimeoutError`;
- timeout dengan cache kedaluwarsa mengembalikan stale cache.

## Menjalankan Test

Jalankan dari folder `Riset/api-athena`:

```powershell
conda run -n cde-mapper-win python -m unittest discover -s tests -v
```

Hasil verifikasi terakhir:

```text
Ran 17 tests in 0.529s

OK
```

## Catatan

- Test tidak melakukan network call ke Athena.
- Test tidak membuka Playwright browser.
- Search Service diuji menggunakan fake adapter.
- FastAPI TestClient saat ini menampilkan warning `StarletteDeprecationWarning` tentang `httpx2`; warning ini tidak menyebabkan test gagal.
