# Ide Implementasi Tahap 2 — Ekstraksi Entitas Klinis dari Teks Panjang

## 1. Tujuan

Tahap 2 bertujuan mengubah teks hasil normalisasi Bahasa Indonesia menjadi sekumpulan entitas klinis terstruktur. Satu dokumen dapat menghasilkan banyak entitas, seperti:

- diagnosis dan penyakit;
- gejala atau keluhan;
- temuan klinis;
- pemeriksaan laboratorium;
- tanda vital;
- obat dan suplemen;
- prosedur atau tindakan;
- anatomi;
- nilai dan satuan;
- konteks kunjungan;
- negasi, ketidakpastian, temporalitas, dan experiencer.

Output Tahap 2 menjadi masukan bagi:

1. Tahap 3 — pemilihan domain dan terminologi target;
2. Tahap 4 — query decomposition;
3. Tahap 5 — retrieval kandidat konsep.

---

## 2. Dasar Data Tahap 1

Sumber input:

```text
Riset/crawler_alodokter/hasil_normalisasi_tahap_1.jsonl
```

Ringkasan 150 pasangan konsultasi:

| Karakteristik | Question | Answer |
|---|---:|---:|
| Record tidak kosong | 150 | 150 |
| Rata-rata kata | 53,1 | 200,3 |
| Maksimum kata | 173 | 862 |
| Rata-rata kalimat | 3,9 | 16,1 |
| Maksimum kalimat | 16 | 57 |
| Penanda negasi | 142 | 424 |
| Penanda ketidakpastian | 3 | 146 |
| Penanda temporal | 181 | 308 |
| Nilai dan satuan klinis | 15 | 43 |
| Penanda rekomendasi | 3 | 117 |

Implikasi:

- `question.normalized_text` terutama berisi fakta, keluhan, riwayat, dan kekhawatiran pasien;
- `answer.normalized_text` banyak memuat diagnosis banding, kemungkinan, edukasi, contoh hipotetis, dan rekomendasi;
- pertanyaan dan jawaban tidak boleh digabung menjadi satu dokumen;
- setiap entitas harus memiliki provenance, speaker, assertion, temporal, dan experiencer.

---

## 3. Acuan Library dan Algoritma

Mengacu pada `Panduan_Komponen_NLP_Formatted.xlsx` baris 13–21.

### 3.1 Medical LLM/NER

Contoh pada panduan:

- Numind/John Snow Labs Medical NER;
- model medis yang dapat menghasilkan entitas klinis terstruktur.

Rencana penggunaan:

- baseline pembanding entity-span extraction;
- anggota ensemble setelah baseline Bahasa Indonesia stabil;
- bukan ekstraktor utama sebelum performa lintas bahasa dan lisensinya dievaluasi.

Risiko:

- model yang dirujuk berorientasi bahasa Inggris;
- data Alodokter informal dan berbahasa Indonesia;
- komponen klinis tertentu memerlukan lisensi.

### 3.2 Prompt Engineering

Gunakan instruksi yang eksplisit untuk:

- entity span;
- base entity;
- entity type dan domain;
- nilai dan unit;
- obat, dosis, frekuensi, dan route;
- assertion;
- temporal;
- experiencer;
- sumber dan evidence.

### 3.3 Few-shot Learning

Buat contoh terpisah untuk:

- pertanyaan pasien;
- jawaban dokter;
- negasi;
- diagnosis banding;
- riwayat keluarga;
- obat dan dosis;
- laboratorium dan tanda vital;
- rekomendasi;
- informasi medis umum.

### 3.4 Spark NLP Contextual Assertion

Potensial sebagai pembanding untuk:

- negasi;
- ketidakpastian;
- temporalitas.

Sebelum digunakan, evaluasi:

- dukungan Bahasa Indonesia;
- lisensi;
- kebutuhan model klinis;
- performa pada teks konsultasi informal.

### 3.5 Custom Rule-based

Gunakan sebagai:

- fallback jika LLM gagal;
- validasi output LLM;
- deteksi angka dan satuan;
- negasi;
- temporal expression;
- dosis dan frekuensi;
- tekanan darah;
- umur dan durasi.

### 3.6 JSON Mode dan Pydantic

JSON mode digunakan jika model/provider mendukung structured output. Hasil tetap harus divalidasi menggunakan Pydantic karena JSON valid belum menjamin:

- mention benar-benar terdapat dalam teks;
- offset benar;
- entity type sesuai;
- assertion dan temporal benar;
- nilai dan unit konsisten.

---

## 4. Arsitektur Awal yang Direkomendasikan

```text
Output Tahap 1
        ↓
Adapter question/answer
        ↓
Sentence window atau semantic chunk
        ↓
LLM + prompt few-shot + JSON mode
        ↓
Pydantic schema validation
        ↓
Rule-based assertion, temporal, value, dan unit
        ↓
Deduplikasi dan konsolidasi
        ↓
Confidence dan provenance
        ↓
Adapter ke Tahap 3 dan Tahap 4
```

Untuk implementasi versi pertama:

```text
Together AI/LLM
+ few-shot Bahasa Indonesia
+ JSON mode
+ Pydantic
+ rule-based validation
```

Medical NER dan Spark NLP ditambahkan sebagai pembanding atau anggota ensemble setelah baseline stabil.

---

## 5. Langkah Implementasi

### Langkah 1 — Tetapkan kontrak input

Bentuk dua dokumen berbeda dari setiap record.

Pertanyaan:

```json
{
  "document_id": "record-id-question",
  "parent_record_id": "record-id",
  "source_field": "question",
  "speaker": "patient",
  "normalized_text": "...",
  "sentences": []
}
```

Jawaban:

```json
{
  "document_id": "record-id-answer",
  "parent_record_id": "record-id",
  "source_field": "answer",
  "speaker": "doctor",
  "normalized_text": "...",
  "sentences": []
}
```

Prioritas awal adalah `question.normalized_text`. Jawaban dokter diproses dalam eksperimen terpisah.

### Langkah 2 — Tetapkan kebijakan sumber

| Sumber | Interpretasi |
|---|---|
| Pertanyaan pasien | Fakta, keluhan, riwayat, obat, dan hasil pasien |
| Jawaban dokter | Hipotesis, diagnosis banding, rekomendasi, atau informasi umum |
| Judul | Metadata pendukung |
| Boilerplate | Tidak diproses sebagai fakta klinis |

Entitas pada jawaban dokter tidak boleh otomatis dianggap sebagai kondisi pasien.

### Langkah 3 — Definisikan taksonomi entitas

Taksonomi awal:

- `condition`;
- `symptom`;
- `clinical_finding`;
- `measurement`;
- `drug`;
- `procedure`;
- `anatomy`;
- `unit`;
- `demographic`;
- `visit`;
- `other`.

Tahap 2 hanya memberikan domain awal. Pemilihan vocabulary target dilakukan pada Tahap 3.

### Langkah 4 — Definisikan skema JSON

```json
{
  "document_id": "string",
  "entities": [
    {
      "entity_id": "string",
      "mention": "string",
      "normalized_mention": "string",
      "base_entity": "string",
      "entity_type": "condition|symptom|clinical_finding|measurement|drug|procedure|anatomy|unit|demographic|visit|other",
      "domain": "condition|measurement|observation|drug|procedure|unit|visit|all",
      "associated_entities": [],
      "categories": [],
      "value": null,
      "unit": null,
      "dose": null,
      "frequency": null,
      "route": null,
      "method": null,
      "visit": null,
      "assertion": "present|negated|uncertain|hypothetical",
      "temporal": "present|past|future|unknown",
      "temporal_expression": null,
      "experiencer": "patient|family|other|unknown",
      "source_field": "question|answer",
      "speaker": "patient|doctor",
      "sentence_id": 0,
      "start_char": 0,
      "end_char": 10,
      "evidence": "string",
      "confidence": 0.0
    }
  ]
}
```

Field wajib untuk audit:

- `mention`;
- `sentence_id`;
- `start_char`;
- `end_char`;
- `evidence`;
- `source_field`;
- `speaker`;
- `experiencer`.

### Langkah 5 — Siapkan chunking

Strategi:

- pertanyaan pendek diproses sebagai teks utuh;
- pertanyaan panjang menggunakan window beberapa kalimat;
- jawaban pendek diproses sebagai teks utuh;
- jawaban panjang dipotong berdasarkan kelompok kalimat;
- gunakan overlap satu kalimat;
- pertahankan sentence ID dan offset asli;
- evaluasi semantic segmentation untuk dokumen panjang.

### Langkah 6 — Susun pedoman anotasi

Pedoman harus menjelaskan:

- batas entity span;
- span terpanjang atau span minimal;
- penyakit dan subtype;
- perbedaan gejala, diagnosis, dan temuan;
- merek dan zat aktif obat;
- nilai dan unit;
- negasi;
- ketidakpastian;
- temporalitas;
- riwayat keluarga;
- kondisi hipotetis;
- rekomendasi;
- informasi umum dokter.

Contoh:

```text
"tidak mengalami demam"

mention     = demam
assertion   = negated
temporal    = present
experiencer = patient
```

```text
"ibu saya menderita diabetes"

mention     = diabetes
assertion   = present
experiencer = family
```

### Langkah 7 — Bangun gold set

Ambil sampel terstratifikasi:

- pertanyaan pendek dan panjang;
- banyak entitas;
- obat dan dosis;
- laboratorium;
- tanda vital;
- negasi;
- temporalitas;
- riwayat keluarga;
- diagnosis banding;
- jawaban panjang;
- rekomendasi.

Tahap awal:

- 30–50 pasangan;
- dua anotator;
- adjudikasi tenaga klinis;
- hitung inter-annotator agreement.

### Langkah 8 — Rancang prompt utama

Prompt harus memerintahkan model:

1. hanya mengekstrak entitas yang tertulis;
2. tidak menambahkan diagnosis baru;
3. mempertahankan mention persis;
4. membedakan fakta pasien dari hipotesis dokter;
5. memberi entity type dan domain awal;
6. mengekstrak nilai, unit, dosis, frekuensi, dan route;
7. menandai assertion, temporal, dan experiencer;
8. menyertakan evidence;
9. mengembalikan array kosong jika tidak ada entitas;
10. hanya mengeluarkan JSON sesuai skema.

### Langkah 9 — Buat few-shot pertanyaan

Contoh harus mencakup:

- keluhan multipel;
- riwayat penyakit;
- obat dan dosis;
- laboratorium;
- tanda vital;
- negasi;
- durasi;
- kondisi keluarga.

### Langkah 10 — Buat few-shot jawaban

Contoh harus mencakup:

- diagnosis banding;
- kemungkinan penyebab;
- informasi umum;
- rekomendasi pemeriksaan;
- tindakan yang disarankan;
- kondisi hipotetis;
- red flags;
- larangan menganggap semua entitas sebagai fakta pasien.

### Langkah 11 — Ekstraksi dua tahap

#### Tahap A — Entity span detection

Temukan mention klinis dalam teks.

Contoh:

```text
pinggul
ngilu
perut
bahu
sikut
infeksi saluran kemih
ciflos
500 mg
```

#### Tahap B — Attribute extraction

Untuk setiap mention, tentukan:

- normalized mention;
- base entity;
- entity type;
- domain;
- nilai dan unit;
- associated entity;
- assertion;
- temporal;
- experiencer;
- evidence;
- confidence.

### Langkah 12 — Tambahkan rule-based extractor

Aturan awal:

```text
tidak|tanpa|bukan|belum
→ kandidat negasi

mungkin|kemungkinan|diduga|bisa jadi
→ uncertain

sejak|selama|dulu|sebelumnya|saat ini
→ temporal expression

mg|ml|kg|cm|mmHg|mg/dL|g/dL|%
→ unit
```

Tambahkan aturan untuk:

- tekanan darah;
- dosis;
- frekuensi;
- durasi;
- umur;
- nilai laboratorium.

Rule digunakan untuk validasi atau warning, bukan selalu menimpa LLM.

### Langkah 13 — Tangani assertion

Assertion minimal:

- `present`;
- `negated`;
- `uncertain`;
- `hypothetical`.

Untuk jawaban dokter, tambahkan `epistemic_status`:

- `general_information`;
- `differential_diagnosis`;
- `recommended`;
- `conditional`;
- `patient_fact`.

### Langkah 14 — Tangani temporal dan experiencer

Contoh:

```text
"sejak dua hari lalu"
→ temporal: present
→ temporal_expression: sejak dua hari lalu

"dulu pernah mengalami"
→ temporal: past

"jika nanti muncul demam"
→ temporal: future
→ assertion: hypothetical

"ibu saya menderita DM"
→ experiencer: family
```

### Langkah 15 — Validasi dengan Pydantic

Validasi:

- semua field wajib tersedia;
- enum valid;
- offset berada dalam batas teks;
- `mention` cocok dengan substring;
- entity ID unik;
- nilai dan unit konsisten;
- confidence berada pada rentang yang ditentukan;
- tidak ada teks naratif di luar JSON.

Jika gagal:

1. lakukan satu kali repair/retry;
2. jika masih gagal, jalankan fallback rule-based;
3. simpan raw output, error, dan warning.

### Langkah 16 — Deduplikasi

Gabungkan entitas berdasarkan:

- overlap span;
- normalized mention;
- sentence ID;
- entity type;
- assertion;
- experiencer.

Jangan menggabungkan:

```text
pasien tidak demam
ibu pasien mengalami demam
```

karena assertion dan experiencer berbeda.

### Langkah 17 — Confidence dan provenance

Sinyal confidence:

- mention ditemukan pada teks;
- offset valid;
- kesepakatan LLM dan rule;
- konsistensi domain;
- konsistensi nilai dan unit;
- kesepakatan antar-ekstraktor;
- JSON valid;
- evidence tersedia.

Metadata:

```text
extraction_method
model_name
model_version
prompt_version
rule_version
processing_time
```

### Langkah 18 — Adapter ke Tahap 3 dan 4

Satu dokumen diubah menjadi beberapa query:

```text
document
├── entity 1 → query mapping
├── entity 2 → query mapping
└── entity 3 → query mapping
```

Pertahankan:

- parent record ID;
- source field;
- speaker;
- mention;
- normalized mention;
- base entity;
- domain;
- unit;
- assertion;
- temporal;
- experiencer;
- evidence.

### Langkah 19 — Simpan audit artifact

```json
{
  "document_id": "...",
  "input_text": "...",
  "chunks": [],
  "raw_model_output": {},
  "validated_entities": [],
  "rule_findings": [],
  "warnings": [],
  "errors": [],
  "model_name": "...",
  "prompt_version": "...",
  "processing_time": 0.0
}
```

---

## 6. Evaluasi

### 6.1 Entity extraction

- strict span precision;
- strict span recall;
- strict span F1;
- relaxed/overlap span F1;
- entity-type macro-F1;
- hallucination rate;
- missed-entity rate.

### 6.2 Attribute extraction

- base-entity accuracy;
- domain accuracy;
- value-unit accuracy;
- assertion macro-F1;
- temporal accuracy;
- experiencer accuracy;
- epistemic-status accuracy.

### 6.3 Keandalan sistem

- JSON-validity rate;
- Pydantic pass rate;
- fallback rate;
- duplicate rate;
- coverage;
- latency per dokumen;
- biaya per dokumen.

---

## 7. Ablation Study

Bandingkan:

1. LLM zero-shot;
2. LLM + few-shot;
3. LLM + rule negasi/temporal;
4. LLM + rule + Pydantic;
5. Medical NER saja;
6. rule-based saja;
7. ensemble LLM + Medical NER + rule;
8. pertanyaan saja;
9. pertanyaan dan jawaban diproses terpisah;
10. tanpa chunking;
11. sentence-window chunking;
12. semantic segmentation.

---

## 8. Risiko dan Mitigasi

| Risiko | Mitigasi |
|---|---|
| LLM menambahkan diagnosis | Wajib evidence dan mention-offset |
| Hipotesis dokter dianggap fakta pasien | Speaker, source field, dan epistemic status |
| Negasi salah cakupan | Rule window + validasi LLM |
| Entitas terpotong pada chunk | Overlap satu kalimat |
| Duplikasi antar-chunk | Span-aware deduplication |
| Model medis tidak mendukung Indonesia | Jadikan baseline pembanding |
| JSON rusak | JSON mode, Pydantic, retry, fallback |
| Nama obat salah dikenali | Protected lexicon dan validasi kamus obat |
| Biaya LLM tinggi | Chunk selektif dan cache |
| Gold set tidak konsisten | Pedoman anotasi dan adjudikasi klinis |

---

## 9. Urutan Implementasi Praktis

```text
1. Kontrak input question/answer
2. Skema entitas dan Pydantic
3. Pedoman anotasi
4. Gold set kecil
5. Prompt zero-shot
6. Prompt few-shot
7. Entity span extraction
8. Attribute extraction
9. Assertion, temporal, experiencer
10. Rule-based validation
11. JSON retry dan fallback
12. Deduplikasi
13. Confidence dan provenance
14. Adapter ke Tahap 3/4
15. Evaluasi
16. Ablation study
```

---

## 10. Keluaran Tahap 2

- modul ekstraksi entitas klinis;
- model Pydantic;
- adapter input Tahap 1;
- prompt Bahasa Indonesia;
- few-shot examples;
- rules negasi, temporal, value, dan unit;
- gold set;
- output JSON multi-entitas;
- audit artifact;
- adapter menuju Tahap 3 dan Tahap 4;
- laporan evaluasi;
- laporan error analysis dan ablation study.

---

## 11. Definisi Selesai

Tahap 2 dinyatakan selesai apabila:

- input question dan answer dipisahkan;
- multi-entitas dapat diekstrak;
- setiap entitas mempunyai mention dan evidence;
- offset mention valid;
- entity type dan domain tersedia;
- assertion, temporal, dan experiencer tersedia;
- output selalu lolos validasi atau masuk fallback;
- provenance model, prompt, dan rule tersimpan;
- tersedia adapter ke Tahap 3 dan Tahap 4;
- gold set dan metrik evaluasi tersedia;
- hasil error analysis terdokumentasi.

---

## 12. Kesimpulan

Output Tahap 1 sudah cukup untuk memulai Tahap 2. Implementasi awal yang paling sesuai adalah kombinasi:

```text
LLM Bahasa Indonesia
+ prompt few-shot
+ JSON mode
+ Pydantic validation
+ custom rule-based
```

Prioritas utama bukan memilih model paling kompleks, tetapi memastikan:

- fakta pasien terpisah dari hipotesis dokter;
- setiap entitas memiliki evidence dan provenance;
- negasi, ketidakpastian, temporalitas, dan experiencer ditangani;
- output konsisten dan dapat diaudit;
- evaluasi dilakukan terhadap gold set yang disepakati.
