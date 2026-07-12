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

### 3.3 Dampak atribut yang tidak tersedia

Atribut kosong tidak selalu menurunkan kualitas mapping. Dampaknya bergantung pada jenis entitas dan tujuan pemrosesan. Pada BC5CDR-Disease, `categorical`, `units`, `formula`, dan `visits` umumnya memang tidak berlaku karena setiap record adalah mention penyakit. Sebaliknya, atribut yang sama dapat sangat menentukan untuk measurement, obat, atau observation.

| Atribut yang tidak tersedia | Dampak umum | Kapan signifikan |
|---|---|---|
| `variablelabel` | Sangat tinggi | Selalu; merupakan query utama |
| `domain` | Tinggi | Filtering domain dan vocabulary |
| `gold_concept_ids` | Sangat tinggi untuk evaluasi | Perhitungan Accuracy@k, Recall@k, MRR, dan NDCG |
| `units` | Tinggi | Laboratorium, measurement, dan dosis obat |
| `categorical` | Sedang–tinggi | Pertanyaan ordinal atau nilai positif/negatif |
| `formula` | Sedang–tinggi | Variabel turunan seperti BMI atau eGFR |
| `visits` | Rendah–sedang | Konteks baseline, follow-up, dan analisis longitudinal |
| `target_vocabularies` | Tinggi | Pemetaan multi-terminologi |

#### Label, domain, dan gold ID

`variablelabel` wajib tersedia karena menjadi input query, base entity awal, dan sumber pembuatan embedding. Record tanpa label seharusnya ditolak atau dilewati.

Domain membatasi ruang pencarian:

```text
condition    → SNOMED CT
measurement  → LOINC/SNOMED CT
unit         → UCUM
drug         → RxNorm/ATC
```

Jika domain tidak tersedia, pipeline masih dapat memakai `domain="all"`, tetapi kandidat salah domain dapat meningkat sehingga precision dan Accuracy@1 menurun. Hal ini penting pada implementasi saat ini karena `custom_data_loader` masih menetapkan domain menjadi `all`, meskipun CSV mempunyai kolom `domain`. Loader perlu diperluas sebelum eksperimen multi-domain.

`gold_concept_ids` tidak diperlukan untuk menjalankan inference, tetapi wajib untuk evaluasi kuantitatif:

```text
Inference       → gold ID opsional
Evaluasi riset  → gold ID wajib
```

Tanpa gold ID, hasil hanya dapat diperiksa secara manual dan kontribusi setiap komponen tidak dapat dibuktikan melalui metrik retrieval.

#### Unit, category, formula, dan visit

Unit membantu membedakan measurement serta memetakan unit UCUM. Sebagai contoh, query `glucose` tanpa konteks dapat merujuk glukosa darah, urine, puasa, sewaktu, atau postprandial. Informasi `mg/dL`, `mmol/L`, specimen, dan waktu pemeriksaan membantu memilih konsep yang lebih spesifik.

Category diperlukan untuk memetakan answer concept seperti:

```text
yes|no
positive|negative
never|former|current
mild|moderate|severe
```

Formula membantu membedakan nilai yang diukur langsung dan nilai turunan, misalnya BMI atau eGFR. Visit umumnya tidak mengubah konsep klinis utama, tetapi diperlukan untuk provenance dan analisis longitudinal seperti baseline dibanding follow-up.

#### Dampak khusus untuk BC5CDR-Disease

Untuk record berikut:

```csv
bc5cdr_000001,torsade de pointes,,,,,D016171,condition,combined_test_queries
```

nilai kosong pada `categorical`, `units`, `formula`, dan `visits` tidak berdampak signifikan karena atribut tersebut memang tidak berlaku pada mention penyakit. Atribut yang harus dipertahankan adalah:

```text
variablelabel
gold_concept_ids
domain=condition
source_dataset
```

Kondisinya berbeda untuk data Indonesia multi-domain. Jika `GDP 126 mg/dL` hanya disimpan sebagai `gula darah`, pipeline kehilangan konteks `puasa`, unit `mg/dL`, dan domain `measurement`. Kandidat glukosa sewaktu, postprandial, urine, atau konsep zat dapat muncul dan menurunkan ketepatan mapping.

#### Status missing value

Dataset penelitian sebaiknya membedakan tiga alasan nilai kosong:

```text
not_applicable → atribut memang tidak berlaku
unknown        → atribut mungkin berlaku, tetapi nilainya tidak diketahui
not_annotated  → atribut belum dianotasi
```

Contoh penyimpanan:

```csv
units,units_status
,not_applicable
,unknown
,not_annotated
mg/dL,available
```

Perbedaan ini mencegah sistem menyamakan unit yang tidak berlaku pada diagnosis dengan unit laboratorium yang hilang atau belum dianotasi.

#### Kelengkapan yang disarankan per domain

| Domain | Label | Unit | Category | Formula | Visit | Gold ID untuk evaluasi |
|---|---:|---:|---:|---:|---:|---:|
| Condition | Wajib | Tidak berlaku | Opsional | Tidak berlaku | Opsional | Wajib |
| Measurement | Wajib | Dianjurkan | Opsional | Opsional | Opsional | Wajib |
| Drug | Wajib | Dosis/unit dianjurkan | Tidak berlaku | Tidak berlaku | Opsional | Wajib |
| Procedure | Wajib | Tidak berlaku | Tidak berlaku | Tidak berlaku | Opsional | Wajib |
| Survey/Observation | Wajib | Opsional | Dianjurkan | Opsional | Opsional | Wajib |
| Unit | Wajib | Menjadi mention utama | Tidak berlaku | Tidak berlaku | Tidak berlaku | Wajib |

Prinsip yang digunakan adalah: **jangan mengarang atribut yang tidak tersedia, tetapi catat apakah atribut tersebut tidak berlaku, tidak diketahui, atau belum dianotasi**.

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

## 9. Rekomendasi Dataset Publik OMOP

Tidak ada dataset publik OMOP yang secara native menyediakan seluruh atribut Tahap 1a. OMOP CDM menyimpan kejadian klinis pasien, sedangkan Tahap 1a adalah format data dictionary untuk terminology mapping. Label, kategori, unit, visit, domain, dan gold concept dapat direkonstruksi melalui beberapa tabel, tetapi `formula` tidak mempunyai kolom generik dalam OMOP CDM.

### 9.1 Perbandingan dataset

| Dataset | Condition | Measurement dan unit | Observation/category | Visit | Vocabulary | Formula | Kesesuaian |
|---|---:|---:|---:|---:|---:|---:|---|
| MIMIC-IV Demo OMOP | Ya | Ya | Ya | Ya | Parsial | Tidak | Paling mendekati Tahap 1a |
| Eunomia | Ya | Ya | Ya | Ya | Subset | Tidak | Terbaik untuk smoke/integration test |
| Synthea → OMOP | Ya | Ya | Ya | Ya | Memerlukan ETL dan vocabulary | Tidak | Data sintetis skala besar |
| MIMIC-BR | Ya | Ya | Ya | Ya | Tergantung rilis | Tidak | Alternatif data rumah sakit/ICU |
| CMS Synthetic PUF | Claims | Terbatas | Terbatas | Claims encounter | Bukan OMOP native | Tidak | Kurang cocok untuk Tahap 1a |

### 9.2 MIMIC-IV Demo OMOP

[MIMIC-IV Demo OMOP](https://physionet.org/content/mimic-iv-demo-omop/0.9/) merupakan pilihan publik yang paling mendekati kebutuhan Tahap 1a. Dataset demo mencakup 100 pasien dan menyediakan tabel seperti:

```text
condition_occurrence
measurement
observation
drug_exposure
procedure_occurrence
visit_occurrence
visit_detail
specimen
```

Pemetaan atributnya:

| Tahap 1a | Sumber OMOP |
|---|---|
| `variablelabel` | `*_source_value` atau nama konsep hasil join |
| `categorical` | `value_as_concept_id` atau `value_source_value` |
| `units` | `unit_concept_id` dan `unit_source_value` |
| `formula` | Tidak tersedia secara generik |
| `visits` | `visit_occurrence_id` → `visit_occurrence` |
| `domain` | Tabel sumber atau `CONCEPT.domain_id` |
| `method` | `measurement.method_concept_id` |
| `gold_concept_ids` | Standard `*_concept_id` |
| `target_vocabularies` | `CONCEPT.vocabulary_id` |

Daftar file resminya mencakup `measurement.csv`, `observation.csv`, `condition_occurrence.csv`, dan `visit_occurrence.csv`. [Daftar file MIMIC-IV Demo OMOP](https://physionet.org/content/mimic-iv-demo-omop/0.9/1_omop_data_csv/)

Keterbatasannya:

- hanya local concepts tertentu yang disertakan dalam vocabulary files;
- standard vocabulary lengkap harus diperoleh secara terpisah;
- beberapa source concept belum dipetakan secara memadai;
- free-text note tidak dipopulasi;
- formula data dictionary tidak tersedia.

### 9.3 Eunomia

[Eunomia](https://ohdsi.github.io/Eunomia/) adalah sample dataset resmi ekosistem OHDSI untuk testing dan demonstrasi. Dataset ini mengikuti OMOP CDM, dapat berjalan dengan SQLite, dan menyertakan subset Standardized Vocabularies.

Eunomia direkomendasikan untuk:

- menguji join antar-tabel OMOP;
- integration test loader;
- menguji condition, measurement, drug, dan visit;
- membuat sampel CSV Tahap 1a tanpa menyiapkan server database.

Eunomia tidak disarankan sebagai benchmark mapping final karena merupakan sample/synthetic data, vocabulary-nya hanya subset, dan tidak dirancang sebagai gold standard terminology mapping.

### 9.4 Synthea, MIMIC-BR, dan CMS synthetic data

- [Synthea](https://github.com/synthetichealth/synthea) dapat menghasilkan populasi pasien sintetis dalam jumlah yang ditentukan, kemudian dikonversi ke OMOP dengan ETL. Pilihan ini cocok untuk stress test dan skalabilitas, tetapi kualitas mapping bergantung pada ETL dan ketersediaan vocabulary.
- [MIMIC-BR](https://physionet.org/content/mimic-br/1.0.0/) diturunkan dari OMOP CDM dan menyediakan data rumah sakit/ICU, termasuk visit dan measurement. Dataset ini tetap memerlukan adapter dan bukan data Bahasa Indonesia.
- [CMS Synthetic Public Use Files](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files) lebih berorientasi claims dan bukan OMOP native. Dataset ini kurang sesuai untuk measurement, unit, formula, serta konteks klinis kaya atribut.

### 9.5 Rekonstruksi Tahap 1a dari OMOP

Untuk `MEASUREMENT`, bentuk CSV Tahap 1a dengan prinsip:

```text
input label       = measurement_source_value
categorical       = value_as_concept_id/value_source_value
unit              = unit_source_value/unit_concept_id
visit             = join visit_occurrence_id
domain            = measurement
gold concept ID   = measurement_concept_id
target vocabulary = vocabulary dari standard concept
formula           = kosong + status not_available
```

Contoh SQL konseptual:

```sql
SELECT
    CONCAT('measurement_', m.measurement_id) AS variablename,
    COALESCE(NULLIF(m.measurement_source_value, ''), c.concept_name)
        AS variablelabel,
    value_concept.concept_name AS categorical,
    COALESCE(NULLIF(m.unit_source_value, ''), unit_concept.concept_name)
        AS units,
    '' AS formula,
    visit_concept.concept_name AS visits,
    c.domain_id AS domain,
    c.concept_id AS gold_concept_ids,
    c.vocabulary_id AS target_vocabularies
FROM measurement m
LEFT JOIN concept c
    ON c.concept_id = m.measurement_concept_id
LEFT JOIN concept value_concept
    ON value_concept.concept_id = m.value_as_concept_id
LEFT JOIN concept unit_concept
    ON unit_concept.concept_id = m.unit_concept_id
LEFT JOIN visit_occurrence v
    ON v.visit_occurrence_id = m.visit_occurrence_id
LEFT JOIN concept visit_concept
    ON visit_concept.concept_id = v.visit_concept_id;
```

Untuk condition, gunakan `condition_source_value` sebagai input dan `condition_concept_id` sebagai gold. Pola yang sama dapat diterapkan pada drug, procedure, dan observation.

### 9.6 Risiko data leakage

Jangan membentuk benchmark utama dengan pasangan berikut:

```text
input = standard CONCEPT.concept_name
gold  = concept_id dari standard concept yang sama
```

Kasus tersebut terlalu mudah karena query identik dengan label dalam knowledge base. Bentuk yang lebih valid adalah:

```text
input = *_source_value atau label lokal asli
gold  = standard *_concept_id
```

Lebih baik lagi, gunakan label sumber rumah sakit dan gold mapping yang telah diverifikasi ahli. Pastikan source value bukan hanya kode tanpa label; jika berupa kode, simpan kode dan label sumber sebagai field terpisah.

### 9.7 Rekomendasi pemilihan

```text
Uji teknis/loader        → Eunomia
Dataset Tahap 1a kaya    → MIMIC-IV Demo OMOP
Uji skalabilitas         → Synthea → OMOP
Eksperimen Indonesia     → dataset baru tervalidasi ahli
```

MIMIC-IV Demo OMOP dapat menyediakan struktur dan variasi domain untuk baseline, tetapi tidak menggantikan dataset Bahasa Indonesia. Formula, singkatan lokal, variasi ejaan, dan gold mapping Indonesia tetap harus disiapkan secara terpisah.

### 9.8 Tahapan teknis menggunakan repo MIMIC-IV Demo OMOP

Repo [MIT-LCP/mimic-iv-demo-omop](https://github.com/MIT-LCP/mimic-iv-demo-omop/tree/master) berisi kode ETL, schema, crosswalk, custom mapping, vocabulary refresh, dan quality assurance. Repo tersebut tidak memuat seluruh output patient-level OMOP. Pemanfaatannya dibagi menjadi dua jalur:

```text
Jalur A: custom mapping/crosswalk → benchmark terminology mapping ringan
Jalur B: output OMOP PhysioNet   → dataset patient-event multi-atribut
```

#### Tahap 1 — Tetapkan versi dan provenance

Clone dan pin commit sumber:

```bash
git clone https://github.com/MIT-LCP/mimic-iv-demo-omop.git \
  external/mimic-iv-demo-omop
cd external/mimic-iv-demo-omop
git rev-parse HEAD
```

Manifest harus menyimpan commit SHA, versi MIMIC, versi OMOP CDM, versi vocabulary, dan tanggal ekstraksi. Repo menggunakan DDL OMOP CDM 5.3.1, sedangkan proyek ini mengarah ke OMOP v5.4; perbedaan schema dan status concept harus diaudit.

#### Tahap 2 — Pilih jalur sumber

Untuk Jalur A, gunakan:

```text
crosswalk_csv/d_items_to_concept.csv
custom_mapping_csv/gcpt_meas_lab_loinc_mod.csv
custom_mapping_csv/gcpt_meas_chartevents_main_mod.csv
custom_mapping_csv/gcpt_meas_chartevents_value.csv
custom_mapping_csv/gcpt_meas_unit.csv
custom_mapping_csv/gcpt_proc_itemid.csv
custom_mapping_csv/gcpt_vis_admission.csv
```

Untuk Jalur B, unduh output demo dari [PhysioNet](https://physionet.org/content/mimic-iv-demo-omop/0.9/1_omop_data_csv/), terutama `measurement.csv`, `condition_occurrence.csv`, `observation.csv`, `drug_exposure.csv`, `procedure_occurrence.csv`, dan `visit_occurrence.csv`.

#### Tahap 3A — Bentuk CSV dari crosswalk/custom mapping

Pemetaan `d_items_to_concept.csv`:

| Field sumber | Field Tahap 1a |
|---|---|
| `linksto` + `itemid` | `variablename` |
| `label`/`source_concept_name` | `variablelabel` |
| `source_domain_id` | `domain` |
| `target_vocabulary_id` | `target_vocabularies` |
| `target_concept_id` | `gold_concept_ids` |
| `source_code` | `source_code` |
| `source_vocabulary_id` | `source_vocabulary` |
| `target_concept_name` | `standard_label` |
| `target_standard_concept` | `standard_concept` |

Target schema:

```csv
variablename,variablelabel,categorical,units,formula,visits,domain,target_vocabularies,gold_concept_ids,source_code,source_vocabulary,standard_label,mapping_status,source_dataset
```

Contoh:

```csv
chartevents_220045,Heart Rate,,,,,measurement,LOINC,3027018,Heart Rate,mimiciv_meas_chart,Heart rate,mapped,mimic_d_items_crosswalk
```

Prosedur pembersihan:

1. normalisasi nama kolom dan whitespace;
2. pertahankan source label, jangan menggantinya dengan standard label;
3. normalisasi domain secara konsisten;
4. validasi `target_concept_id`;
5. deduplikasi pasangan source–target concept;
6. simpan file dan nomor baris sumber sebagai provenance;
7. pisahkan mapped dan unmapped.

Baris tanpa target tidak boleh diubah menjadi gold `0`. Tandai sebagai `mapping_status=unmapped`; gunakan untuk coverage analysis atau antrean validasi, bukan accuracy mapping berlabel.

#### Tahap 3B — Bentuk CSV dari patient-event

Rekonstruksi per domain:

```text
Measurement:
  label       ← measurement_source_value
  categorical ← value_source_value/value_as_concept_id
  unit        ← unit_source_value/unit_concept_id
  visit       ← visit_occurrence_id
  gold        ← measurement_concept_id

Condition:
  label       ← condition_source_value
  visit       ← visit_occurrence_id
  gold        ← condition_concept_id

Observation:
  label       ← observation_source_value
  categorical ← value_as_concept_id/value_as_string
  visit       ← visit_occurrence_id
  gold        ← observation_concept_id
```

Join visit melalui `visit_occurrence_id`, lalu gunakan jenis/source value visit sebagai konteks. `formula` tetap kosong dengan `formula_status=not_available`.

#### Tahap 4 — Verifikasi metadata target

Lengkapi setiap target concept dengan standard label, vocabulary, domain, standard status, validity date, dan `invalid_reason`. Urutan sumber:

1. snapshot vocabulary OMOP lokal yang versioned;
2. metadata collection Qdrant sebagai fallback read-only;
3. mapping repo untuk field yang tersedia.

Karena Athena tidak dapat diakses, persiapan data tidak boleh bergantung pada Athena. Record yang belum dapat diverifikasi diberi `target_metadata_unverified` dan tidak langsung masuk test set utama.

#### Tahap 5 — Selaraskan loader

Perluas `custom_data_loader` agar membaca:

```text
domain
target_vocabularies
gold_concept_ids
source_code
source_vocabulary
source_dataset
```

Gold ID harus menjadi evaluation metadata terpisah dan tidak boleh masuk `full_query`. Dengan demikian model tidak melihat jawaban saat inference.

#### Tahap 6 — Cegah data leakage

Pasangan test tidak boleh dimasukkan ke `mapping_templates.json`, reservoir, sinonim target, atau few-shot prompt. Split berdasarkan `source_concept_id`/`itemid`, bukan hanya baris acak:

```text
train 70% | dev 15% | test 15%
```

Semua variasi satu source concept harus berada pada split yang sama. Knowledge base hanya berisi standard label dan sinonim resmi, sedangkan input evaluasi menggunakan source label MIMIC.

#### Tahap 7 — Validasi kualitas

Audit minimal:

```text
schema dan missing-label check
duplicate source-target check
domain/vocabulary consistency
target concept existence dan validity
mapped/unmapped count
train-test overlap
```

Ambil sampel per domain untuk validasi manual/ahli, khususnya mapping ambigu, one-to-many, unit, serta measurement yang berbeda specimen atau timing.

#### Tahap 8 — Jalankan baseline dan ablation

| Eksperimen | Tujuan |
|---|---|
| Lexical only | Baseline kecocokan source label |
| Dense only | Kontribusi semantic retrieval |
| Dense + sparse | Kontribusi hybrid retrieval |
| + domain filter | Pengaruh domain |
| + unit/category | Pengaruh atribut tambahan |
| + Gemma reranking | Pengaruh reranker |

Laporkan metrik per domain dan agregat. Measurement biasanya lebih kompleks karena unit, specimen, method, dan timing membedakan konsep.

#### Tahap 9 — Simpan artefak reproducible

```text
data/raw/mimic_iv_demo_omop/
data/processed/mimic_stage_1a.csv
data/gold/mimic_stage_1a_train.csv
data/gold/mimic_stage_1a_dev.csv
data/gold/mimic_stage_1a_test.csv
configs/mimic_stage_1a.yaml
Riset/mimic_stage_1a_manifest.json
Riset/LAPORAN_DATA_MIMIC_TAHAP_1A.md
```

Manifest menyimpan checksum sumber, commit repo, versi data/CDM/vocabulary, aturan transformasi, dan seed split.

#### Urutan implementasi yang disarankan

```text
1. Pin commit dan versi data
2. Pilot dengan d_items_to_concept.csv
3. Bentuk CSV source-label → gold-concept
4. Verifikasi target concept
5. Perluas loader domain/evaluation metadata
6. Split anti-leakage
7. Jalankan lexical/dense/hybrid baseline
8. Tambahkan unit dan categorical value
9. Lanjutkan ke patient-event PhysioNet
10. Validasi ahli dan dokumentasikan provenance
```

Pilot dimulai dari `crosswalk_csv/d_items_to_concept.csv` karena satu tabel sudah memuat source label, domain, target vocabulary, target ID, target label, dan standard status. Setelah converter dan evaluator stabil, perluas ke lab, unit, procedure, visit, lalu patient-event.

## 10. Rekomendasi Pemakaian

| Tujuan | Dataset |
|---|---|
| Smoke test loader | `baseline_smoke.csv` |
| Baseline retrieval dengan gold | `combined_test_queries.txt` |
| Evaluasi multi-gold | `test_queries.txt` |
| Knowledge base lokal | `test_dictionary_docs.jsonl` |
| Evaluasi normalisasi Indonesia | `id_normalization_gold.jsonl` |
| Uji struktur dan join OMOP | Eunomia |
| Pembentukan Tahap 1a publik multi-domain | MIMIC-IV Demo OMOP |
| Uji skalabilitas data sintetis | Synthea → OMOP |
| Evaluasi mapping Indonesia final | Dataset baru tervalidasi ahli |

Urutan praktis:

1. konversi `combined_test_queries.txt` menjadi `bc5cdr_stage_1a.csv`;
2. validasi hasil dengan `custom_data_loader`;
3. jalankan retrieval dan simpan kandidat Top-k;
4. samakan namespace identifier sebelum menghitung metrik;
5. gunakan hasil sebagai baseline disease retrieval berbahasa Inggris;
6. susun dataset Bahasa Indonesia terpisah untuk eksperimen utama.

## 11. Kesimpulan

Repositori mempunyai dataset yang lebih layak daripada `baseline_smoke.csv` untuk evaluasi retrieval, terutama `combined_test_queries.txt` dan `test_queries.txt`. Namun, tidak ada dataset lain yang langsung mempunyai seluruh atribut Tahap 1a.

Konversi file query ke CSV mempertahankan mention sebagai `variablelabel` dan identifier sumber sebagai `gold_concept_ids`, sedangkan atribut yang tidak tersedia dibiarkan kosong. CSV tersebut cocok untuk baseline mention-to-concept, tetapi bukan pengganti dataset klinis Bahasa Indonesia yang kaya konteks dan tervalidasi ahli.
