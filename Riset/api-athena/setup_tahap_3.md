# Setup Tahap 3: Desain Database SQLite

## Ringkasan

Tahap 3 menambahkan desain dan inisialisasi database SQLite untuk cache pencarian Athena.

File yang dibuat:

- `app/models.py`
- `app/database.py`
- `scripts/__init__.py`
- `scripts/init_db.py`
- `setup_tahap_3.md`

## Tabel Database

### `search_cache`

Digunakan untuk menyimpan hasil pencarian konsep Athena berdasarkan query dan filter.

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id` | integer | Primary key |
| `cache_key` | string | Hash unik untuk query + filter |
| `query` | string | Kata kunci pencarian |
| `domain` | string/null | Domain OMOP |
| `page` | integer | Nomor halaman |
| `filters_json` | text | Filter tambahan dalam JSON |
| `response_json` | text | Response hasil pencarian dalam JSON |
| `created_at` | datetime | Waktu data dibuat |
| `updated_at` | datetime | Waktu data diperbarui |
| `expires_at` | datetime | Waktu cache kedaluwarsa |

Index:

- `cache_key` unik
- `query + domain + page`
- `expires_at`

### `concept_cache`

Digunakan untuk menyimpan detail konsep Athena berdasarkan `concept_id`.

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id` | integer | Primary key |
| `concept_id` | integer | OMOP concept ID unik |
| `response_json` | text | Response detail konsep dalam JSON |
| `created_at` | datetime | Waktu data dibuat |
| `updated_at` | datetime | Waktu data diperbarui |
| `expires_at` | datetime | Waktu cache kedaluwarsa |

Index:

- `concept_id` unik
- `expires_at`

## Inisialisasi Database

Jalankan dari folder `Riset/api-athena`:

```powershell
conda run -n cde-mapper-win python -m scripts.init_db
```

Database dibuat di:

```text
data/athena_cache.sqlite3
```

## Verifikasi Tabel

Jalankan:

```powershell
conda run -n cde-mapper-win python -c "import sqlite3; db='data/athena_cache.sqlite3'; con=sqlite3.connect(db); print([r[0] for r in con.execute(\"select name from sqlite_master where type='table' order by name\")]); con.close()"
```

Output minimal:

```text
['concept_cache', 'search_cache']
```

## Status

Tahap 3 selesai jika database SQLite terbentuk dan tabel `search_cache` serta `concept_cache` tersedia.
