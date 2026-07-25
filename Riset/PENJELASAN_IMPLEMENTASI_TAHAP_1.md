# Penjelasan Implementasi Tahap 1 — Normalisasi Bahasa Indonesia

## 1. Tujuan Dokumen

Dokumen ini menjelaskan implementasi aktual Tahap 1 berdasarkan kode yang tersedia di repositori. Tahap 1 bertugas mengubah teks konsultasi klinis Bahasa Indonesia menjadi teks yang lebih bersih, konsisten, tersegmentasi, dan dapat diaudit sebelum diproses oleh ekstraksi entitas klinis pada Tahap 2.

Implementasi dirancang dengan prinsip:

- deterministik;
- konservatif terhadap informasi klinis;
- idempotent;
- dapat diaudit;
- tidak bergantung pada LLM;
- tidak bergantung pada Qdrant atau komponen retrieval;
- dapat digunakan secara opsional tanpa mengubah perilaku baseline.

---

## 2. Artefak Implementasi

### 2.1 Modul utama

```text
rag/id_preprocess.py
```

Berisi:

- struktur data hasil normalisasi;
- pemuatan kamus;
- normalisasi Unicode;
- cleaning teks;
- koreksi typo;
- ekspansi singkatan;
- disambiguasi berbasis konteks;
- normalisasi angka dan satuan;
- segmentasi kalimat;
- penandaan boilerplate;
- audit trail;
- normalisasi objek query baseline.

### 2.2 Resource

```text
data/input/id_abbreviations.json
data/input/id_abbreviations_layered.json
data/input/id_typos.json
data/input/id_units.json
```

### 2.3 Runner data Alodokter

```text
scripts/preprocess_alodokter.py
```

### 2.4 Audit intrinsik

```text
scripts/audit_id_preprocess.py
scripts/audit_id_preprocess_wsl.sh
```

### 2.5 Gold set dan unit test

```text
data/gold/id_normalization_gold.jsonl
tests/test_id_preprocess.py
```

### 2.6 Notebook

```text
Riset/Tahap_1_Normalisasi_Alodokter.ipynb
```

### 2.7 Output

```text
Riset/crawler_alodokter/hasil_normalisasi_tahap_1.jsonl
Riset/id_preprocess_audit_result.json
```

---

## 3. Arsitektur Implementasi

Alur aktual pada fungsi `IndonesianClinicalNormalizer.normalize`:

```text
raw_text
   ↓
Unicode NFKC, translasi karakter, dan casefold
   ↓
Cleaning karakter kontrol dan spasi
   ↓
Normalisasi tanda baca
   ↓
Koreksi typo berbasis kamus
   ↓
Ekspansi singkatan dan bentuk informal
   ↓
Normalisasi angka dan satuan
   ↓
Final spacing
   ↓
Segmentasi kalimat
   ↓
Penandaan boilerplate untuk profil answer
   ↓
NormalizationResult
```

Implementasi tidak melakukan stemming dan tidak melakukan fuzzy replacement otomatis.

---

## 4. Struktur Data

### 4.1 `NormalizationStep`

Mencatat perubahan pada tingkat tahap:

```python
NormalizationStep(
    name="unit_normalization",
    before="dosis 500mg",
    after="dosis 500 mg"
)
```

Field:

- `name`;
- `before`;
- `after`.

### 4.2 `NormalizationChange`

Mencatat perubahan token atau ekspresi:

```python
NormalizationChange(
    kind="abbreviation",
    source="isk",
    target="infeksi saluran kemih",
    count=1,
    status="automatic",
    rule="medical_clinical"
)
```

Field:

- `kind`;
- `source`;
- `target`;
- `count`;
- `status`;
- `rule`.

### 4.3 `NormalizationResult`

Hasil utama normalisasi:

```json
{
  "original_text": "...",
  "normalized_text": "...",
  "sentences": [],
  "steps": [],
  "changes": [],
  "replacements": {},
  "warnings": [],
  "boilerplate": [],
  "content_text": "...",
  "profile": "question",
  "normalizer_version": "1.0.0",
  "resource_version": "1.0.0"
}
```

Penjelasan:

| Field | Fungsi |
|---|---|
| `original_text` | Teks sebelum normalisasi |
| `normalized_text` | Teks lengkap hasil normalisasi |
| `sentences` | Hasil segmentasi kalimat |
| `steps` | Perubahan per tahap |
| `changes` | Perubahan token/ekspresi |
| `replacements` | Jumlah typo, singkatan, dan unit yang diubah |
| `warnings` | Peringatan singkatan ambigu |
| `boilerplate` | Sapaan atau penutup yang terdeteksi |
| `content_text` | Isi jawaban tanpa boilerplate yang terdeteksi |
| `profile` | `clinical`, `question`, atau `answer` |
| `normalizer_version` | Versi algoritma |
| `resource_version` | Versi kamus master |

### 4.4 `AbbreviationEntry`

Representasi internal entri kamus:

```text
abbreviation
expansion
status
contexts
warning
layer
```

---

## 5. Pemuatan Resource

Normalizer dibuat menggunakan:

```python
normalizer = IndonesianClinicalNormalizer.from_resource_dir("data/input")
```

Proses pemuatan:

1. mencari `id_abbreviations_layered.json`;
2. jika tersedia, menggunakan kamus master berlapis;
3. jika tidak tersedia, menggunakan `id_abbreviations.json`;
4. memuat `id_typos.json`;
5. memuat `id_units.json`;
6. menyimpan versi resource pada hasil.

Entri pada lapisan `ambiguous_not_automatic` tidak dimasukkan sebagai ekspansi biasa.

---

## 6. Profil Normalisasi

Normalizer mendukung tiga profil.

### 6.1 Profil `clinical`

Digunakan untuk:

- query CDE;
- data dictionary;
- teks klinis umum;
- integrasi dengan `run.py`.

Semua lapisan singkatan yang memenuhi aturan dapat digunakan.

### 6.2 Profil `question`

Digunakan untuk pertanyaan pasien.

Karakteristik:

- ekspansi bahasa informal aktif;
- ekspansi singkatan medis aktif;
- koreksi typo aktif;
- informasi angka, unit, negasi, dan temporal dipertahankan.

Contoh:

```text
Sy skrg ISK, tp blm minum obat 500mg.
```

menjadi:

```text
saya sekarang infeksi saluran kemih,
tetapi belum minum obat 500 mg.
```

### 6.3 Profil `answer`

Digunakan untuk jawaban dokter.

Karakteristik:

- lebih konservatif;
- lapisan `informal_conversation` tidak diterapkan;
- singkatan klinis tetap dapat diproses;
- sapaan dan penutup dicatat sebagai boilerplate;
- `normalized_text` tetap menyimpan teks lengkap;
- `content_text` menyimpan isi setelah boilerplate yang terdeteksi dipisahkan.

---

## 7. Normalisasi Unicode dan Casing

Fungsi internal:

```text
_unicode_and_case
```

Operasi:

1. normalisasi Unicode menggunakan NFKC;
2. pemisahan camel-case tertentu, misalnya `mlmSy`;
3. standardisasi en dash dan em dash menjadi `-`;
4. standardisasi tanda kutip tipografi;
5. penggantian non-breaking space;
6. konversi ke lowercase menggunakan `casefold`;
7. penghapusan spasi pada awal dan akhir teks.

Contoh:

```text
mlmSy → mlm sy → malam saya
```

Pemecahan camel-case dibatasi agar tidak merusak satuan seperti:

```text
mg/dL
```

---

## 8. Cleaning Karakter Kontrol dan Spasi

Fungsi:

```text
_clean_controls_and_spacing
```

Operasi:

- menghapus karakter kontrol;
- mempertahankan newline dan tab sebelum dirapikan;
- menggabungkan spasi atau tab berulang;
- merapikan spasi di sekitar newline;
- mempertahankan struktur paragraf.

Cleaning dibuat konservatif dan tidak menghapus angka, simbol klinis, atau isi teks.

---

## 9. Normalisasi Tanda Baca

Fungsi:

```text
_normalize_punctuation
_normalize_commas
```

Operasi:

- menggabungkan tanda `??` atau `!!`;
- merapikan titik berulang;
- menambahkan spasi pada batas kalimat yang menempel;
- merapikan spasi sebelum tanda kurung;
- menghapus spasi di sekitar `/`;
- menghapus spasi di sekitar `%`;
- merapikan koma dan titik koma.

Desimal koma dipertahankan:

```text
2,5mg → 2,5 mg
```

Koma sebagai tanda baca diberi spasi:

```text
demam,batuk → demam, batuk
```

---

## 10. Koreksi Typo

Resource:

```text
data/input/id_typos.json
```

Contoh:

```json
{
  "demem": "demam",
  "diabetis": "diabetes",
  "mellitus": "melitus",
  "pasiem": "pasien"
}
```

Koreksi menggunakan exact dictionary replacement berdasarkan batas token.

Karakteristik:

- deterministik;
- tidak menggunakan fuzzy matching otomatis;
- entri diproses dari frasa terpanjang;
- jumlah penggantian dicatat;
- perubahan dapat diaudit.

Keputusan tidak menggunakan fuzzy matching dimaksudkan untuk mengurangi risiko perubahan keliru pada istilah klinis dan nama obat.

---

## 11. Kamus Singkatan Berlapis

Resource master:

```text
data/input/id_abbreviations_layered.json
```

Lapisan:

- `medical_clinical`;
- `maternal_child_health`;
- `body_function_and_measurement`;
- `clinical_documentation`;
- `informal_conversation`;
- `ambiguous_not_automatic`.

Status:

### `automatic`

Langsung diperluas jika cocok sebagai token.

Contoh:

```text
ISK → infeksi saluran kemih
DM  → diabetes melitus
GDP → gula darah puasa
```

### `context_required`

Hanya diperluas jika konteks memenuhi aturan.

Contoh:

```text
BB 70 kg → berat badan 70 kg
TB 165 cm → tinggi badan 165 cm
```

### `review_required`

Tidak diterapkan otomatis sebelum validasi.

---

## 12. Disambiguasi Berbasis Konteks

Fungsi:

```text
_context_matches
```

Aturan tersedia untuk:

- `BB`;
- `TB`;
- `Px`;
- `N`;
- `RR`;
- `temp`;
- `KB`;
- `th`.

Contoh:

```text
TB 165 cm
```

memenuhi konteks antropometri sehingga menjadi:

```text
tinggi badan 165 cm
```

Sementara:

```text
riwayat TB dalam keluarga
```

tidak memenuhi konteks tinggi badan. Teks `tb` dipertahankan dan warning ditambahkan.

---

## 13. Normalisasi Angka dan Satuan

Fungsi:

```text
_space_number_units
```

Resource:

```text
data/input/id_units.json
```

Contoh:

```text
500mg       → 500 mg
126 mg / dl → 126 mg/dL
12 gr/dl    → 12 g/dL
160 / 100   → 160/100
95 %        → 95%
mmhg        → mmHg
```

Implementasi mempertahankan:

- angka;
- desimal;
- rasio;
- dosis;
- simbol persen;
- satuan klinis.

Implementasi belum mengubah angka dan satuan menjadi objek terstruktur seperti `value`, `unit`, `range`, atau `frequency`. Ekstraksi struktur tersebut direncanakan pada Tahap 2.

---

## 14. Final Spacing

Fungsi:

```text
_final_spacing
```

Operasi:

- menghapus spasi ganda;
- merapikan newline;
- menghapus spasi sebelum tanda baca;
- membedakan koma desimal dari koma tanda baca;
- menambahkan spasi setelah titik koma;
- menstandarkan `x/menit`.

---

## 15. Segmentasi Kalimat

Fungsi:

```text
segment_sentences
```

Pendekatan:

- rule-based;
- menggunakan newline dan tanda akhir kalimat;
- menambahkan pemisah pada tanda baca yang menempel;
- tidak memecah angka desimal.

Contoh:

```text
Saya demam.Dok, apakah berbahaya?Sudah 2 hari.
```

menjadi:

```json
[
  "saya demam.",
  "dokter, apakah berbahaya?",
  "sudah 2 hari."
]
```

Segmentasi transformer belum digunakan. Pendekatan seperti `indo_text_segmentation` lebih sesuai dievaluasi sebagai semantic chunking setelah sentence splitting.

---

## 16. Penandaan Boilerplate

Fungsi:

```text
_extract_boilerplate
```

Hanya dijalankan untuk profil `answer`.

Pola awal:

- `Alo`;
- `Halo`;
- `Hai`;
- `Waalaikumsalam`;
- `Demikian informasi...`;
- `Semoga bermanfaat...`;
- `Semoga membantu...`;
- `Terima kasih` pada akhir teks.

Output:

```json
{
  "normalized_text": "teks lengkap",
  "content_text": "teks tanpa boilerplate yang terdeteksi",
  "boilerplate": [
    "alo ibu anna,",
    "semoga bermanfaat."
  ]
}
```

Teks lengkap tidak dihapus agar provenance tetap tersedia.

---

## 17. Audit Trail

Audit diaktifkan menggunakan:

```python
result = normalizer.normalize(
    text,
    audit=True,
    profile="question"
)
```

Jika `audit=False`:

- `normalized_text` tetap dihasilkan;
- daftar `steps` dan `changes` dikosongkan;
- jumlah replacement tetap tersedia.

Audit mencatat:

- perubahan per tahap;
- perubahan token;
- jumlah penggantian;
- jenis perubahan;
- sumber aturan;
- status ekspansi;
- warning;
- versi algoritma;
- versi resource.

---

## 18. Convenience API

### 18.1 `normalize_text`

Digunakan jika hanya membutuhkan string hasil:

```python
from rag.id_preprocess import normalize_text

normalized = normalize_text(
    "Px dgn DM tipe 2",
    profile="clinical"
)
```

Hasil:

```text
pasien dengan diabetes melitus tipe 2
```

### 18.2 `normalize_queries`

Digunakan untuk objek `QueryDecomposedModel`.

Fungsi ini:

- menerima list model atau tuple `(gold_id, model)`;
- menormalisasi `full_query`;
- menormalisasi `base_entity`;
- mempertahankan teks awal pada `original_label` jika belum tersedia;
- mengubah objek secara in-place;
- mengembalikan list yang sama.

---

## 19. Integrasi dengan `run.py`

Argumen:

```text
--normalize_id
--normalization_profile
--normalization_resource_dir
```

Contoh:

```bash
python run.py \
  --input_file data/input/contoh.csv \
  --output_file output.csv \
  --flag inference \
  --custom_data \
  --normalize_id \
  --normalization_profile clinical \
  --normalization_resource_dir data/input
```

Perilaku:

- tanpa `--normalize_id`, baseline tidak berubah;
- dengan `--normalize_id`, query dinormalisasi setelah `load_data`;
- normalisasi dilakukan sebelum retrieval dan mapping.

---

## 20. Runner Alodokter

Command:

```bash
python scripts/preprocess_alodokter.py
```

Default input:

```text
Riset/crawler_alodokter/hasil_crawl_alodokter_qa_pairs.json
```

Default output:

```text
Riset/crawler_alodokter/hasil_normalisasi_tahap_1.jsonl
```

Proses per record:

1. membaca `question.raw_text`;
2. menjalankan profil `question`;
3. membaca `answer.raw_text`;
4. menjalankan profil `answer`;
5. membuat `record_id` stabil dari URL;
6. menyimpan hasil sebagai JSONL;
7. menghitung jumlah kelompok perubahan dan warning.

Struktur output:

```json
{
  "record_id": "string",
  "source": "alodokter",
  "url": "string",
  "title": "string",
  "question": {
    "raw_text": "string",
    "normalized_text": "string",
    "content_text": "string",
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
    "raw_text": "string",
    "normalized_text": "string",
    "content_text": "string",
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

---

## 21. Notebook Tahap 1

Notebook:

```text
Riset/Tahap_1_Normalisasi_Alodokter.ipynb
```

Isi:

1. konfigurasi path;
2. validasi resource;
3. demonstrasi normalisasi;
4. pemrosesan seluruh data;
5. ringkasan audit;
6. daftar perubahan yang sering muncul;
7. inspeksi warning;
8. penyimpanan JSONL;
9. validasi hasil.

Notebook menggunakan implementasi pada `rag/id_preprocess.py`, bukan menyalin ulang algoritma normalisasi.

---

## 22. Pengujian

### 22.1 Unit test

Command:

```bash
python -m unittest discover -s tests -v
```

Kasus yang diuji:

1. ekspansi informal pada profil `question`;
2. profil `answer` tidak menggunakan lapisan informal;
3. singkatan ambigu dipertahankan tanpa konteks;
4. ukuran `BB` dan `TB` diperluas jika konteks cocok;
5. angka, unit, desimal, dan negasi dipertahankan;
6. segmentasi kalimat tanpa spasi;
7. idempotensi.

Hasil terakhir:

```text
7/7 unit test lulus
```

### 22.2 Audit gold set

Command:

```bash
python scripts/audit_id_preprocess.py
```

Gold set:

```text
data/gold/id_normalization_gold.jsonl
```

Hasil terakhir:

| Metrik | Hasil |
|---|---:|
| Total kasus | 5 |
| Exact match | 5 |
| Exact normalized match | 1,0 |
| Kasus berubah | 5 |
| Koreksi typo | 3 |
| Ekspansi singkatan | 14 |
| Normalisasi satuan | 5 |

### 22.3 Output Alodokter

| Indikator | Hasil |
|---|---:|
| Record diproses | 150 |
| Record ID unik | 150 |
| Kelompok perubahan pertanyaan | 269 |
| Kelompok perubahan jawaban | 46 |
| Warning konteks | 9 |

---

## 23. Keputusan tentang Stemming

Stemming tidak diaktifkan.

Alasan:

- dapat merusak istilah klinis;
- dapat mengubah nama konsep;
- tidak diperlukan untuk input LLM atau NER;
- dense embedding tidak memerlukan stemming;
- hasil stem tidak selalu cocok dengan label terminology.

Contoh risiko:

```text
pemeriksaan → periksa
pengobatan  → obat
pendarahan  → darah
menularkan  → tular
```

Jika dibutuhkan, stemming sebaiknya menjadi representasi tambahan untuk eksperimen sparse/lexical retrieval, bukan menggantikan `normalized_text`.

---

## 24. Hubungan dengan Tahap 2

Output Tahap 1 dapat digunakan sebagai input awal Tahap 2.

Pertanyaan:

```text
document_id = record_id-question
text        = question.normalized_text
sentences   = question.sentences
speaker     = patient
```

Jawaban:

```text
document_id = record_id-answer
text        = answer.content_text
speaker     = doctor
```

Pertanyaan dan jawaban harus diproses terpisah karena:

- pertanyaan memuat fakta dan keluhan pasien;
- jawaban memuat hipotesis, diagnosis banding, rekomendasi, dan informasi umum;
- entitas dari jawaban tidak boleh otomatis dianggap sebagai kondisi pasien.

---

## 25. Bagian yang Belum Diimplementasikan

### 25.1 Protected-token mechanism

Belum terdapat tahap eksplisit untuk mendeteksi, menyimpan, dan memulihkan:

- nama obat;
- kode klinis;
- URL;
- istilah Inggris;
- singkatan kapital;
- identifier;
- token sensitif lainnya.

Saat ini keamanan terutama berasal dari exact dictionary replacement dan kamus yang terbatas.

### 25.2 Fuzzy typo correction

Belum diaktifkan. Keputusan ini disengaja untuk menghindari perubahan agresif.

### 25.3 Structured numeric extraction

Nilai dan unit baru dinormalisasi sebagai teks, belum menjadi:

```json
{
  "value": 126,
  "unit": "mg/dL"
}
```

### 25.4 Semantic segmentation

Segmentasi masih rule-based. Model semantic segmentation belum diintegrasikan.

### 25.5 Boilerplate coverage

Pola boilerplate masih terbatas dan belum mencakup seluruh variasi sapaan atau penutup.

### 25.6 Gold set skala riset

Gold set saat ini hanya berfungsi sebagai smoke test teknis. Belum cukup untuk menyimpulkan akurasi klinis pada seluruh korpus.

### 25.7 Validasi ahli

Kamus dan hasil normalisasi belum seluruhnya divalidasi oleh tenaga klinis atau ahli Bahasa Indonesia.

---

## 26. Risiko Implementasi

| Risiko | Kondisi Saat Ini | Mitigasi Berikutnya |
|---|---|---|
| Nama obat berubah | Belum ada protected token | Protected lexicon |
| Singkatan salah ekspansi | Context rules + warning | Perluas disambiguasi |
| Typo tidak terkoreksi | Exact dictionary | Tambah kandidat fuzzy dengan review |
| Kalimat salah terpotong | Rule-based | Gold sentence boundary |
| Boilerplate tertinggal | Pola terbatas | Perluas pola dan evaluasi |
| Informasi klinis hilang | Preservasi diuji | Tambah preservation metrics |
| Kamus bias | Seed lexicon | Validasi klinisi |

---

## 27. Rekomendasi Penguatan

Urutan penguatan yang disarankan:

1. implementasikan protected-token mechanism;
2. buat registry nama obat dan kode klinis;
3. tambah gold set terstratifikasi;
4. validasi kamus oleh klinisi;
5. tambah metrik preservation rate;
6. ukur sentence-boundary precision, recall, dan F1;
7. perluas boilerplate;
8. evaluasi semantic segmentation untuk teks panjang;
9. tambahkan fuzzy suggestion tanpa auto-replacement;
10. versioning resource dan changelog kamus.

---

## 28. Cara Menjalankan

### Normalisasi seluruh data Alodokter

```bash
python scripts/preprocess_alodokter.py
```

### Menentukan input dan output

```bash
python scripts/preprocess_alodokter.py \
  --input-file Riset/crawler_alodokter/hasil_crawl_alodokter_qa_pairs.json \
  --output-file Riset/crawler_alodokter/hasil_normalisasi_tahap_1.jsonl \
  --resource-dir data/input
```

### Menjalankan audit

```bash
python scripts/audit_id_preprocess.py
```

### Menjalankan unit test

```bash
python -m unittest discover -s tests -v
```

### Mengaktifkan normalisasi pada pipeline

```bash
python run.py ... \
  --normalize_id \
  --normalization_profile clinical \
  --normalization_resource_dir data/input
```

---

## 29. Definisi Selesai Saat Ini

Tahap 1 saat ini telah memiliki:

- modul normalisasi deterministik;
- profil `clinical`, `question`, dan `answer`;
- kamus singkatan berlapis;
- disambiguasi berbasis konteks;
- kamus typo;
- normalisasi satuan;
- cleaning Unicode dan tanda baca;
- preservasi desimal;
- segmentasi kalimat;
- boilerplate extraction;
- audit trail;
- runner Alodokter;
- notebook;
- integrasi opsional ke baseline;
- gold smoke test;
- unit test;
- output 150 pasangan konsultasi.

Tahap 1 sudah dapat digunakan untuk eksperimen Tahap 2, tetapi protected-token mechanism, evaluasi skala riset, dan validasi ahli masih diperlukan sebelum dianggap final.

---

## 30. Kesimpulan

Implementasi Tahap 1 menyediakan lapisan normalisasi Bahasa Indonesia yang ringan, deterministik, dan dapat diaudit. Sistem memisahkan perlakuan pertanyaan pasien dan jawaban dokter, memperluas singkatan berbasis status dan konteks, mempertahankan informasi numerik klinis, serta menghasilkan kalimat dan metadata audit.

Output utamanya:

```text
raw_text
→ normalized_text
→ sentences
→ content_text
→ changes
→ warnings
→ provenance versi
```

Implementasi sudah cukup sebagai baseline preprocessing untuk ekstraksi entitas klinis Tahap 2. Penguatan berikutnya harus berfokus pada perlindungan token klinis, perluasan gold set, validasi klinis, dan evaluasi preservation rate.
