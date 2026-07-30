# Setup Tahap 8: Error Handling

## Ringkasan

Tahap 8 menambahkan penanganan error yang lebih eksplisit untuk endpoint pencarian Athena.

File yang dibuat atau diperbarui:

- `app/services/athena_browser_adapter.py`
- `app/services/search_service.py`
- `app/routers/athena.py`
- `scripts/smoke_error_handling.py`
- `setup_tahap_8.md`
- `README.md`

## Mapping Error

| Kondisi | HTTP Status | Perilaku |
|---|---:|---|
| Query kosong setelah `strip()` | `400` | Request ditolak sebagai parameter tidak valid |
| Athena timeout tanpa cache | `504` | API mengembalikan gateway timeout |
| Parsing Athena gagal tanpa cache | `502` | API mengembalikan bad gateway |
| Athena gagal tanpa cache | `502` | API mengembalikan bad gateway |
| Athena gagal tetapi cache tersedia | `200` | API mengembalikan cache dengan `stale: true` |

## Kelas Error

Adapter:

- `AthenaAdapterError`
- `AthenaTimeoutError`
- `AthenaRenderError`

Search Service:

- `AthenaSearchServiceError`
- `AthenaSearchValidationError`
- `AthenaSearchTimeoutError`
- `AthenaSearchParsingError`
- `AthenaSearchUpstreamError`

## Metadata Respons Cache

Respons pencarian sekarang menyertakan metadata kompatibel untuk cache:

```json
{
  "cached": true,
  "stale": true,
  "cache": {
    "hit": true,
    "stale": true,
    "key": "...",
    "upstream_error": "Timed out opening Athena URL: ..."
  }
}
```

Keterangan:

- `cached`: data berasal dari cache.
- `stale`: data cache dipakai sebagai fallback karena Athena gagal atau cache sudah kedaluwarsa.
- `cache.upstream_error`: ringkasan error upstream, tanpa stack trace.

## Smoke Test

Jalankan dari folder `Riset/api-athena`:

```powershell
conda run -n cde-mapper-win python -m scripts.smoke_error_handling
```

Output yang diharapkan:

```text
AthenaSearchValidationError Query must not be empty.
AthenaSearchTimeoutError Simulated Athena timeout.
True True
Simulated Athena timeout.
```

Smoke test ini memverifikasi:

- query berisi spasi saja ditolak;
- timeout tanpa cache menghasilkan error service;
- cache kedaluwarsa tetap dikembalikan saat Athena timeout.

## Catatan

Detail error internal dan stack trace tidak dikirim ke client. Logging penuh akan ditambahkan pada Tahap 9.
