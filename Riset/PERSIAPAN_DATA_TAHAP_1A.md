# Persiapan Data Tahap 1a dari Dataset Repositori

## 1. Tujuan dan Posisi Data

Tahap 1a pada diagram framework adalah **data klinis atau data dictionary yang akan dipetakan**, dengan atribut:

```text
Label | Categorical | Unit | Formula | Visit
```

Implementasi baseline merepresentasikannya melalui CSV:

```csv
variablename,variablelabel,categorical,units,formula,visits
```

`data/input/baseline_smoke.csv` hanya dibuat untuk membuktikan bahwa `custom_data_loader` bekerja. File tersebut bukan dataset penelitian utama.

Tiga jenis data berikut harus dibedakan:

| Jenis data | Fungsi | Contoh dalam repositori |
|---|---|---|
| Input/query | Istilah yang akan dipetakan | `combined_test_queries.txt` |
| Gold standard | Identifier konsep yang dianggap benar | Bagian kiri setiap baris query |
| Knowledge base | Daftar konsep tempat pencarian | `test_dictionary_docs.jsonl` |

```text
query → retrieval pada knowledge base → kandidat Top-k → dibandingkan dengan gold ID
```

## 2. Dataset yang Tersedia

### 2.1 `combined_test_queries.txt`

Lokasi:

```text
data/eval_datasets/original_bc5cdr-disease/combined_test_queries.txt
```

Contoh:

```text
D016171||torsade de pointes
D017180||ventricular tachycardia
D002311||dilated cardiomyopathy
D065008||scorpionism
```

Formatnya:

```text
gold concept ID || mention
```

File ini merupakan pilihan terbaik dalam repo untuk baseline retrieval karena mention dan gold ID tersedia dalam satu baris. Loader `.txt` pada `rag/data_loader.py` juga dapat membacanya langsung.

Keterbatasannya:

- berbahasa Inggris;
- hanya berfokus pada penyakit/condition;
- tidak mempunyai category, unit, formula, atau visit;
- bukan teks klinis panjang Indonesia.

### 2.2 `test_queries.txt`

Contoh:

```text
c565162|121210||torsade de pointes
```

Bagian kiri dapat berisi beberapa gold ID yang dipisahkan `|`. File ini dapat digunakan untuk evaluasi multi-gold apabila evaluator memperlakukan seluruh ID tersebut sebagai himpunan konsep yang sah.

### 2.3 Dictionary dan document index

File berikut adalah sumber konsep, bukan input Tahap 1a:

```text
train_dictionary.txt
dev_dictionary.txt
test_dictionary.txt
test_dictionary_docs.jsonl
```

`test_dictionary_docs.jsonl` memiliki metadata konsep seperti label, `sid`, domain, vocabulary, dan status standard. Posisinya adalah knowledge base atau vector index. Menggunakan label dictionary sebagai query terhadap indeks yang sama dapat membuat evaluasi terlalu mudah.

### 2.4 Dataset pendukung lain

| Dataset | Fungsi | Langsung cocok sebagai Tahap 1a? |
|---|---|---:|
| `baseline_smoke.csv` | Smoke test data dictionary | Ya, tetapi sintetis dan sangat kecil |
| `baseline_retrieval_gold.jsonl` | Benchmark internal Tahap 0 | Perlu adapter dan berisiko leakage |
| `id_normalization_gold.jsonl` | Evaluasi normalisasi Indonesia | Perlu anotasi entitas dan gold mapping |
| `umls_abbreviations.csv` | Kamus singkatan | Tidak |
| `mapping_templates.json` | Rules, examples, dan seed reservoir | Tidak |

Kesimpulannya, repo memiliki dataset retrieval yang lebih nyata daripada smoke CSV, tetapi belum memiliki dataset lain dengan seluruh atribut Tahap 1a.

## 3. Format CSV Tahap 1a

### 3.1 Kolom minimum baseline

```csv
variablename,variablelabel,categorical,units,formula,visits
```

| Kolom | Makna |
|---|---|
| `variablename` | Identifier unik record |
| `variablelabel` | Mention yang akan dipetakan |
| `categorical` | Nilai kategori, dipisahkan `|` |
| `units` | Unit pengukuran |
| `formula` | Formula turunan jika ada |
| `visits` | Konteks kunjungan atau waktu |

### 3.2 Kolom evaluasi tambahan

Format yang direkomendasikan:

```csv
variablename,variablelabel,categorical,units,formula,visits,gold_concept_ids,domain,source_dataset
```

Kolom tambahan mempertahankan gold ID, domain, dan provenance. `custom_data_loader` saat ini mengabaikan kolom tambahan sehingga CSV tetap dapat digunakan untuk inference. Namun, loader masih menetapkan `domain="all"`; kolom `domain` baru memengaruhi retrieval jika loader diperluas.

## 4. Konversi File Query Teks

### 4.1 Aturan pemetaan

Baris sumber:

```text
D016171||torsade de pointes
```

Diubah menjadi:

```csv
bc5cdr_000001,torsade de pointes,,,,,D016171,condition,combined_test_queries
```

| Sumber | Target CSV |
|---|---|
| Nomor urut | `variablename` |
| Teks setelah `||` | `variablelabel` |
| Tidak tersedia | category, unit, formula, dan visit dikosongkan |
| Teks sebelum `||` | `gold_concept_ids` |
| Karakteristik BC5CDR-Disease | `domain=condition` |
| Nama file | `source_dataset` |

Atribut yang tidak tersedia tidak boleh diisi dengan nilai tebakan.

### 4.2 Skrip konversi

Skrip berikut hanya menggunakan library standar Python:

```python
from __future__ import annotations

import csv
from pathlib import Path

source = Path(
    "data/eval_datasets/original_bc5cdr-disease/combined_test_queries.txt"
)
target = Path("data/input/bc5cdr_stage_1a.csv")

fieldnames = [
    "variablename",
    "variablelabel",
    "categorical",
    "units",
    "formula",
    "visits",
    "gold_concept_ids",
    "domain",
    "source_dataset",
]

rows = []
seen = set()

for line_number, raw_line in enumerate(
    source.read_text(encoding="utf-8").splitlines(), start=1
):
    line = raw_line.strip()
    if not line:
        continue
    if "||" not in line:
        raise ValueError(f"Baris {line_number} tidak memiliki separator ||: {line}")

    gold_ids, mention = line.split("||", maxsplit=1)
    gold_ids = gold_ids.strip()
    mention = mention.strip()
    if not gold_ids or not mention:
        raise ValueError(f"Baris {line_number} tidak lengkap: {line}")

    # Deduplicate berdasarkan pasangan gold dan mention.
    identity = (gold_ids.casefold(), mention.casefold())
    if identity in seen:
        continue
    seen.add(identity)

    rows.append(
        {
            "variablename": f"bc5cdr_{len(rows) + 1:06d}",
            "variablelabel": mention,
            "categorical": "",
            "units": "",
            "formula": "",
            "visits": "",
            "gold_concept_ids": gold_ids,
            "domain": "condition",
            "source_dataset": "combined_test_queries",
        }
    )

target.parent.mkdir(parents=True, exist_ok=True)
with target.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Menulis {len(rows)} query ke {target}")
```

## 5. Validasi CSV

Periksa header dan sampel:

```bash
head -5 data/input/bc5cdr_stage_1a.csv
```

Periksa jumlah baris:

```bash
wc -l \
  data/eval_datasets/original_bc5cdr-disease/combined_test_queries.txt \
  data/input/bc5cdr_stage_1a.csv
```

CSV mempunyai satu baris tambahan untuk header dan dapat memiliki lebih sedikit baris jika terdapat duplikasi pasangan gold–mention.

Validasi dengan loader:

```bash
conda run --no-capture-output -n cde-mapper python -c \
  "from rag.data_loader import load_data; q, mapped = load_data('data/input/bc5cdr_stage_1a.csv', load_custom=True); print(len(q), mapped)"
```

Hasil yang diharapkan:

```text
jumlah query > 0
mapped = False
```

## 6. Menjalankan Inference

```bash
conda run --no-capture-output -n cde-mapper python run.py \
  --flag inference \
  --input_file data/input/bc5cdr_stage_1a.csv \
  --custom_data \
  --is_omop_data \
  --collection_name concept_mapping_1 \
  --llm_id google/gemma-3n-E4B-it \
  --topk 10 \
  --output_file data/output/bc5cdr_stage_1a_mapped.csv
```

Catatan:

- CSV ini adalah mention-level disease dataset, bukan data dictionary kaya atribut.
- Athena yang gagal tidak menghentikan Qdrant retrieval, tetapi eksperimen harus dilaporkan sebagai Qdrant dense-sparse tanpa kontribusi Athena.
- Top-k kandidat harus disimpan agar metrik retrieval dapat dihitung.

## 7. Gold ID dan Namespace

Kolom `gold_concept_ids` tidak otomatis digunakan oleh `map_data`. Evaluator harus membandingkannya dengan identifier kandidat.

Parsing multi-gold:

```python
gold_set = {
    value.strip().casefold()
    for value in row["gold_concept_ids"].split("|")
    if value.strip()
}
```

Kandidat dinilai benar jika:

```text
candidate identifiers ∩ gold_set tidak kosong
```

Sebelum menghitung metrik, pastikan gold dan kandidat menggunakan namespace yang sama. `D016171` adalah identifier sumber yang berbeda dari OMOP numeric concept ID. Perbandingan string langsung hanya valid apabila kandidat juga membawa identifier itu atau tersedia crosswalk terverifikasi.

## 8. Pengembangan menuju Dataset Indonesia

CSV BC5CDR cocok untuk baseline retrieval, tetapi belum menguji kontribusi utama riset Bahasa Indonesia. Dataset Tahap 1a Indonesia sebaiknya mempunyai minimal:

```csv
document_id,variablename,variablelabel,categorical,units,formula,visits,domain,target_vocabularies,gold_concept_ids
```

Untuk teks panjang, simpan pula:

```text
original_text
normalized_text
mention
assertion
temporal
method
```

Contoh:

```csv
document_id,variablename,variablelabel,categorical,units,formula,visits,domain,target_vocabularies,gold_concept_ids
doc_001,ent_001,diabetes melitus tipe 2,,,,,condition,SNOMED|ICD-10,
doc_001,ent_002,gula darah puasa,,mg/dL,,,measurement,LOINC,
doc_001,ent_003,tekanan darah,,mmHg,,,measurement,LOINC,
```

Gold ID tidak boleh berasal dari tebakan sistem yang sedang dievaluasi. Nilainya harus ditentukan melalui anotasi ahli atau sumber mapping independen.

## 9. Rekomendasi Pemakaian

| Tujuan | Dataset |
|---|---|
| Smoke test loader | `baseline_smoke.csv` |
| Baseline retrieval dengan gold | `combined_test_queries.txt` |
| Evaluasi multi-gold | `test_queries.txt` |
| Knowledge base lokal | `test_dictionary_docs.jsonl` |
| Evaluasi normalisasi Indonesia | `id_normalization_gold.jsonl` |
| Evaluasi mapping Indonesia final | Dataset baru tervalidasi ahli |

Urutan praktis:

1. konversi `combined_test_queries.txt` menjadi `bc5cdr_stage_1a.csv`;
2. validasi hasil dengan `custom_data_loader`;
3. jalankan retrieval dan simpan kandidat Top-k;
4. samakan namespace identifier sebelum menghitung metrik;
5. gunakan hasil sebagai baseline disease retrieval berbahasa Inggris;
6. susun dataset Bahasa Indonesia terpisah untuk eksperimen utama.

## 10. Kesimpulan

Repositori mempunyai dataset yang lebih layak daripada `baseline_smoke.csv` untuk evaluasi retrieval, terutama `combined_test_queries.txt` dan `test_queries.txt`. Namun, tidak ada dataset lain yang langsung mempunyai seluruh atribut Tahap 1a.

Konversi file query ke CSV mempertahankan mention sebagai `variablelabel` dan identifier sumber sebagai `gold_concept_ids`, sedangkan atribut yang tidak tersedia dibiarkan kosong. CSV tersebut cocok untuk baseline mention-to-concept, tetapi bukan pengganti dataset klinis Bahasa Indonesia yang kaya konteks dan tervalidasi ahli.
