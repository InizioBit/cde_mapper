# Contoh Input dan Output Tahap 1

Folder ini berisi contoh minimal untuk menjalankan implementasi Tahap 1 — Normalisasi Bahasa Indonesia.

## Struktur

```text
Riset/Tahap_1/
├── README.md
├── input/
│   └── contoh_input_alodokter.json
└── output/
    ├── contoh_output_normalisasi_tahap_1.json
    └── contoh_output_normalisasi_tahap_1.jsonl
```

## Input

File:

```text
input/contoh_input_alodokter.json
```

Input mengikuti struktur dasar hasil crawler Alodokter:

```json
{
  "source": "alodokter",
  "url": "...",
  "title": "...",
  "question": {
    "raw_text": "...",
    "clean_text": "..."
  },
  "answer": {
    "raw_text": "...",
    "clean_text": "..."
  }
}
```

Contoh dipilih untuk menunjukkan:

- singkatan informal;
- singkatan medis;
- typo dan tanda baca menempel;
- angka dan satuan;
- negasi;
- temporalitas;
- boilerplate jawaban;
- singkatan ambigu seperti `TB`;
- disambiguasi `BB` dan `TB` menggunakan konteks satuan.

## Menjalankan

Jalankan dari root repositori:

```bash
python scripts/preprocess_alodokter.py \
  --input-file Riset/Tahap_1/input/contoh_input_alodokter.json \
  --output-file Riset/Tahap_1/output/contoh_output_normalisasi_tahap_1.jsonl \
  --resource-dir data/input
```

Untuk PowerShell:

```powershell
python scripts/preprocess_alodokter.py `
  --input-file Riset/Tahap_1/input/contoh_input_alodokter.json `
  --output-file Riset/Tahap_1/output/contoh_output_normalisasi_tahap_1.jsonl `
  --resource-dir data/input
```

Untuk menghasilkan satu array JSON yang dapat dibuka langsung oleh parser
JSON atau JSON5:

```powershell
python scripts/preprocess_alodokter.py `
  --input-file Riset/Tahap_1/input/contoh_input_alodokter.json `
  --output-file Riset/Tahap_1/output/contoh_output_normalisasi_tahap_1.json `
  --resource-dir data/input
```

## Output

File:

```text
output/contoh_output_normalisasi_tahap_1.jsonl
```

Setiap baris merupakan satu objek JSON:

```json
{
  "record_id": "...",
  "source": "alodokter",
  "url": "...",
  "title": "...",
  "question": {
    "raw_text": "...",
    "normalized_text": "...",
    "content_text": "...",
    "sentences": [],
    "normalization_changes": [],
    "warnings": [],
    "boilerplate": [],
    "replacements": {},
    "profile": "question",
    "normalizer_version": "1.0.0",
    "resource_version": "1.0.0"
  },
  "answer": {
    "raw_text": "...",
    "normalized_text": "...",
    "content_text": "...",
    "sentences": [],
    "normalization_changes": [],
    "warnings": [],
    "boilerplate": [],
    "replacements": {},
    "profile": "answer",
    "normalizer_version": "1.0.0",
    "resource_version": "1.0.0"
  }
}
```

Versi array JSON:

```text
output/contoh_output_normalisasi_tahap_1.json
```

Perbedaan format:

| Ekstensi | Struktur | Kegunaan |
|---|---|---|
| `.jsonl` | Satu objek JSON per baris | Streaming dan pipeline data |
| `.json` | Satu array berisi seluruh record | Editor dan parser JSON/JSON5 |

File `.jsonl` bukan satu dokumen JSON tunggal. File tersebut harus dibaca per
baris. Gunakan file `.json` jika aplikasi mengharapkan satu dokumen JSON atau
JSON5.

## Perbedaan Profil

### `question`

- normalisasi bentuk informal aktif;
- ekspansi singkatan medis aktif;
- koreksi typo aktif;
- nilai dan satuan dipertahankan.

### `answer`

- normalisasi lebih konservatif;
- bentuk informal tidak diperluas melalui lapisan percakapan;
- sapaan dan penutup dideteksi sebagai boilerplate;
- teks lengkap tetap tersedia pada `normalized_text`;
- isi tanpa boilerplate yang terdeteksi tersedia pada `content_text`.

## Reproducibility

File output dalam folder ini dihasilkan oleh:

```text
scripts/preprocess_alodokter.py
```

dengan resource:

```text
data/input/id_abbreviations_layered.json
data/input/id_typos.json
data/input/id_units.json
```

Jika resource atau versi normalizer berubah, output dapat berubah. Versi normalizer dan resource disimpan pada setiap hasil.
