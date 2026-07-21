# Crawler Alodokter

Folder ini berisi crawler standalone untuk mengambil daftar diskusi konsultasi publik Alodokter dari halaman kategori penyakit.

## File

- `crawler_alodokter.py`: crawler Python standalone tanpa dependency eksternal.

## Konfigurasi

Konstanta utama ada di bagian atas file:

- `URL`
- `START_PAGE`
- `JUMLAH_HALAMAN`
- `RANDOM_HALAMAN`
- `RANDOM_PAGE_SPAN`
- `OUTPUT_JSON`
- `OUTPUT_DATASET_JSON`
- `OUTPUT_QA_JSON`
- `MIN_DELAY_SECONDS`
- `MAX_DELAY_SECONDS`
- `PAGINATION_STYLE`

Contoh default saat ini:

```python
URL = "https://www.alodokter.com/komunitas/diskusi/penyakit"
START_PAGE = 4500
JUMLAH_HALAMAN = 10
RANDOM_HALAMAN = True
```

Jika `RANDOM_HALAMAN = True`, crawler mengambil sejumlah halaman dari rentang `START_PAGE` ke atas secara acak.

## Cara Menjalankan

```bash
python crawler_alodokter.py
```

Atau tentukan file output:

```bash
python crawler_alodokter.py --output hasil_crawl_alodokter.json
```

Atau tentukan dua output sekaligus:

```bash
python crawler_alodokter.py --output hasil_crawl_alodokter.json --dataset-output hasil_crawl_alodokter_dataset.json
```

## Output JSON

Secara default, output disimpan di folder crawler:

- `hasil_crawl_alodokter.json`: JSON lengkap dengan `crawl_metadata`, `listings`, `records`, dan `errors`.
- `hasil_crawl_alodokter_qa_pairs.json`: JSON langsung berupa array pasangan pertanyaan pasien dan jawaban dokter.
- `hasil_crawl_alodokter_dataset.json`: JSON dataset riset/anonymized.

Setiap item pada `records` dan `hasil_crawl_alodokter_qa_pairs.json` mengikuti struktur:

```json
{
  "source": "alodokter",
  "source_type": "public_health_consultation",
  "url": "https://www.alodokter.com/...",
  "listing_url": "https://www.alodokter.com/komunitas/diskusi/penyakit/page/2",
  "title": "...",
  "category": "penyakit",
  "question": {
    "raw_text": "...",
    "clean_text": "...",
    "asked_at": null
  },
  "answer": {
    "raw_text": "...",
    "clean_text": "...",
    "answered_at_date": "2025-12-12",
    "answered_at_time": "10:34",
    "doctor_name": "dr. ...",
    "doctor_role": "Dokter"
  },
  "metadata": {
    "related_links": [],
    "scraped_at": "2026-07-21T...",
    "language": "id",
    "raw_html_hash": "...",
    "parser_version": "alodokter_v1"
  }
}
```

Setiap item pada file dataset mengikuti struktur:

```json
{
  "document_id": "alodokter_000001",
  "input_text": "...",
  "source_type": "public_consultation",
  "category": "penyakit",
  "date": "2025-12-12",
  "doctor_present": true,
  "doctor_name_removed": true,
  "annotation_status": "raw"
}
```

## Catatan

Crawler ini hanya mengambil link diskusi dari halaman listing dan detail diskusi tersebut. Crawler tidak menelusuri link tambahan seperti artikel rujukan atau "Diskusi Terkait" di halaman detail.
