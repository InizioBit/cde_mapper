# Setup Tahap 6: Implementasi Athena Browser Adapter

## Ringkasan

Tahap 6 menambahkan adapter Playwright untuk membuka halaman Athena OHDSI dan mengambil hasil pencarian konsep OMOP.

File yang dibuat:

- `app/services/athena_browser_adapter.py`
- `scripts/smoke_athena_adapter.py`
- `setup_tahap_6.md`

## Komponen Utama

### `AthenaSearchParams`

Dataclass untuk parameter pencarian:

- `query`
- `domain`
- `page`
- `standard_concept`
- `vocabulary`
- `concept_class`

### `AthenaBrowserAdapter`

Fungsi utama:

| Fungsi | Keterangan |
|---|---|
| `build_search_url()` | Membentuk URL pencarian Athena |
| `build_download_csv_url()` | Membentuk URL download CSV Athena |
| `build_concept_url()` | Membentuk URL detail konsep Athena |
| `search()` | Membuka halaman pencarian Athena dan mengambil hasil |
| `get_concept_detail()` | Membuka halaman detail konsep Athena |

## Strategi Ekstraksi

Adapter mencoba tiga strategi:

1. Menangkap response JSON internal yang muncul saat halaman Athena dirender browser.
2. Fallback membaca DOM, terutama tabel dan link konsep.
3. Fallback download CSV dari endpoint Athena yang masih dapat diakses dari halaman web.

Adapter juga mencoba menekan tombol `Accept` jika license agreement modal Athena muncul. Jika Athena menampilkan `No data available`, adapter mengembalikan `results: []` dengan `result_count: 0`.

Fallback CSV dipakai karena endpoint JSON internal Athena dapat mengembalikan `403`, sementara URL download CSV seperti berikut masih mengembalikan data:

```text
https://athena.ohdsi.org/api/v1/concepts/download/csv?query=diabetes&boosts=&page=1&domain=Condition
```

Kolom CSV Athena dinormalisasi ke struktur respons lokal:

| CSV Athena | Respons lokal |
|---|---|
| `Id` | `concept_id` |
| `Code` | `concept_code` |
| `Name` | `concept_name` |
| `Standard Class` | `concept_class_id` |
| `Domain` | `domain_id` |
| `Vocab` | `vocabulary_id` |
| `Validity` | `invalid_reason` |
| `Concept` | `standard_concept` |

Jika keduanya gagal, adapter menyimpan HTML debug ke folder:

```text
debug/
```

## Verifikasi URL Builder

Jalankan dari folder `Riset/api-athena`:

```powershell
conda run -n cde-mapper-win python -c "from app.services.athena_browser_adapter import AthenaBrowserAdapter, AthenaSearchParams; a=AthenaBrowserAdapter(); print(a.build_search_url(AthenaSearchParams(query='heart rate', domain='Condition', page=1)))"
```

Output:

```text
https://athena.ohdsi.org/search-terms/terms?query=heart+rate&boosts=&page=1&domain=Condition
```

## Smoke Test Live Athena

Jalankan:

```powershell
conda run -n cde-mapper-win python -m scripts.smoke_athena_adapter
```

Catatan:

- Test ini membutuhkan akses internet.
- Athena dapat lambat atau mengubah struktur halaman.
- Jika parsing gagal, cek file HTML di folder `debug/`.

## Status

Tahap 6 selesai jika:

- adapter dapat diimport;
- URL Athena dapat dibentuk;
- Playwright dapat membuka browser;
- adapter dapat membaca hasil dari CSV Athena;
- adapter memiliki fallback debug HTML saat halaman Athena tidak dapat diparse.

Hasil smoke test live untuk `query=diabetes` dan `domain=Condition`:

```text
source: athena_csv_http
result_count: 4348
```

Integrasi adapter ke endpoint `/api/athena/search` dilakukan pada Tahap 7 bersama search service.
