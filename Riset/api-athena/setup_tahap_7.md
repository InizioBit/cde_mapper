# Setup Tahap 7: Implementasi Search Service

## Ringkasan

Tahap 7 menambahkan lapisan `SearchService` untuk menghubungkan endpoint FastAPI, cache SQLite, dan Athena Browser Adapter.

File yang dibuat atau diperbarui:

- `app/services/search_service.py`
- `app/routers/athena.py`
- `scripts/smoke_search_service.py`
- `setup_tahap_7.md`
- `README.md`

## Komponen Utama

### `AthenaSearchService`

Service ini bertanggung jawab untuk:

- membersihkan parameter pencarian;
- membentuk cache key;
- membaca cache SQLite;
- memanggil `AthenaBrowserAdapter` jika cache kosong, kedaluwarsa, atau `refresh=true`;
- menyimpan hasil pencarian Athena ke cache;
- mengembalikan respons pencarian ke endpoint API.

### Endpoint Aktif

Endpoint `/api/athena/search` sekarang aktif.

```text
GET /api/athena/search
```

Parameter:

| Parameter | Keterangan |
|---|---|
| `query` | Kata kunci pencarian Athena |
| `domain` | Filter domain OMOP, misalnya `Condition` |
| `page` | Nomor halaman pencarian |
| `standard_concept` | Filter standard concept |
| `vocabulary` | Filter vocabulary |
| `concept_class` | Filter concept class |
| `refresh` | Jika `true`, cache dilewati dan data diambil ulang dari Athena |

Contoh:

```powershell
conda run -n cde-mapper-win python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```text
http://127.0.0.1:8000/api/athena/search?query=diabetes&domain=Condition
```

## Struktur Respons

Respons pencarian mengikuti format adapter Athena dan ditambah metadata cache:

```json
{
  "query": "diabetes",
  "domain": "Condition",
  "page": 1,
  "source": "athena_csv",
  "result_count": 4348,
  "results": [],
  "cache": {
    "hit": false,
    "key": "..."
  }
}
```

Nilai `cache.hit`:

- `false`: data baru diambil dari Athena dan disimpan ke SQLite.
- `true`: data dikembalikan dari cache SQLite.

## Smoke Test Service

Smoke test service memakai adapter palsu agar cepat dan tidak bergantung jaringan:

```powershell
conda run -n cde-mapper-win python -m scripts.smoke_search_service
```

Output yang diharapkan:

```text
False fake_adapter 1
True fake_adapter 1
adapter_calls=1
```

Artinya:

- panggilan pertama mengambil data dari adapter dan menyimpan cache;
- panggilan kedua membaca data dari cache;
- adapter hanya dipanggil satu kali.

## Catatan

Endpoint detail konsep `/api/athena/concepts/{concept_id}` masih disiapkan untuk tahap berikutnya.
