# Checkpoint Implementasi Tahap 2 — Ekstraksi Entitas Klinis

## 1. Tujuan

Implementasi Tahap 2 dibagi menjadi **9 checkpoint dalam 3 milestone** agar setiap komponen dapat:

- diuji secara terpisah;
- diverifikasi sebelum melanjutkan;
- menghasilkan artefak audit;
- diulang secara reproducible;
- dibandingkan melalui ablation study;
- dilacak kembali ke input Tahap 1.

Prinsip implementasi:

```text
Jangan langsung membangun:
LLM + chunking + atribut + negasi + temporal
+ ensemble + mapping

Bangun bertahap:
input → skema → gold set → entity span → atribut
→ konteks → teks panjang → validasi → integrasi
```

---

# Milestone A — Fondasi Data dan Evaluasi

## 2. Checkpoint 1 — Kontrak Input dan Provenance

### 2.1 Tujuan

Memastikan output Tahap 1 dapat dibaca secara konsisten tanpa kehilangan sumber informasi.

Setiap record Alodokter diubah menjadi dua dokumen:

```text
record
├── question → speaker: patient
└── answer   → speaker: doctor
```

Pertanyaan:

```json
{
  "document_id": "record-id-question",
  "parent_record_id": "record-id",
  "source_field": "question",
  "speaker": "patient",
  "raw_text": "...",
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
  "raw_text": "...",
  "normalized_text": "...",
  "sentences": []
}
```

### 2.2 Pemeriksaan

- jumlah input tetap 150 record;
- terbentuk 150 dokumen pertanyaan;
- terbentuk 150 dokumen jawaban;
- `document_id` unik;
- `parent_record_id` sesuai;
- tidak ada `normalized_text` kosong;
- question dan answer tidak tertukar;
- raw text tetap tersedia;
- urutan kalimat dapat ditelusuri.

### 2.3 Artefak

```text
stage2_checkpoint_01_input.jsonl
stage2_checkpoint_01_audit.json
```

### 2.4 Exit criteria

- seluruh record berhasil dikonversi;
- seluruh ID unik;
- provenance lengkap;
- tidak ada kehilangan teks;
- jumlah question dan answer sesuai input.

---

## 3. Checkpoint 2 — Skema Entitas dan Pedoman Anotasi

### 3.1 Tujuan

Menentukan secara formal definisi entitas, batas span, dan atribut yang harus dihasilkan.

### 3.2 Taksonomi awal

- `condition`;
- `symptom`;
- `clinical_finding`;
- `measurement`;
- `drug`;
- `procedure`;
- `anatomy`;
- `demographic`;
- `unit`;
- `visit`;
- `other`.

### 3.3 Atribut entitas

- mention;
- normalized mention;
- base entity;
- entity type;
- domain;
- value dan unit;
- dose, frequency, dan route;
- assertion;
- temporal;
- experiencer;
- source field;
- speaker;
- sentence ID;
- character offset;
- evidence;
- confidence.

### 3.4 Hal yang harus didefinisikan

- batas entity span;
- span minimal atau terpanjang;
- diagnosis vs gejala;
- gejala vs temuan klinis;
- penyakit dan subtype;
- merek obat vs zat aktif;
- nilai dan satuan;
- kondisi pasien vs keluarga;
- fakta vs kemungkinan;
- rekomendasi vs tindakan yang sudah dilakukan;
- informasi umum dokter;
- kondisi hipotetis.

### 3.5 Pemeriksaan

Lakukan desk review pada contoh:

```text
tidak mengalami demam
```

```json
{
  "mention": "demam",
  "entity_type": "symptom",
  "assertion": "negated",
  "temporal": "present",
  "experiencer": "patient"
}
```

Contoh:

```text
ibu saya menderita diabetes
```

```json
{
  "mention": "diabetes",
  "entity_type": "condition",
  "assertion": "present",
  "experiencer": "family"
}
```

### 3.6 Artefak

```text
stage2_entity_schema.md
stage2_annotation_guideline.md
stage2_schema_examples.jsonl
```

### 3.7 Exit criteria

- skema disepakati;
- setiap field memiliki definisi;
- tersedia contoh positif dan negatif;
- label yang berpotensi tumpang tindih memiliki aturan;
- skema question dan answer konsisten;
- skema dapat divalidasi.

Checkpoint ini harus selesai sebelum prompt final dibuat.

---

## 4. Checkpoint 3 — Gold Set Awal

### 4.1 Tujuan

Menyediakan data acuan yang tidak digunakan sebagai few-shot untuk mengukur performa ekstraktor.

### 4.2 Komposisi

Pilih 30–50 pasangan terstratifikasi:

- pertanyaan pendek dan panjang;
- banyak entitas;
- obat dan dosis;
- laboratorium;
- tanda vital;
- negasi;
- ketidakpastian;
- temporalitas;
- riwayat keluarga;
- diagnosis banding;
- rekomendasi;
- jawaban panjang.

### 4.3 Proses anotasi

1. Anotator pertama membuat anotasi.
2. Anotator kedua membuat anotasi independen.
3. Hasil dibandingkan.
4. Perbedaan dicatat.
5. Tenaga klinis melakukan adjudikasi.
6. Gold set final dibekukan sebagai versi 1.

### 4.4 Pemeriksaan

Ukur agreement untuk:

- entity span;
- entity type;
- assertion;
- temporal;
- experiencer;
- epistemic status.

### 4.5 Artefak

```text
stage2_gold_v1.jsonl
stage2_annotation_disagreement.jsonl
stage2_adjudication_log.md
stage2_gold_statistics.json
```

### 4.6 Exit criteria

- seluruh record selesai dianotasi;
- setiap entitas mempunyai evidence;
- setiap mention mempunyai offset;
- disagreement telah diselesaikan;
- versi gold set dikunci;
- data few-shot dan evaluation dipisahkan.

---

# Milestone B — Ekstraktor Klinis

## 5. Checkpoint 4 — Baseline Entity-Span Extraction

### 5.1 Tujuan

Menguji kemampuan sistem menemukan mention klinis sebelum menambahkan atribut yang kompleks.

Mulai hanya dari:

```text
question.normalized_text
```

### 5.2 Output minimal

```json
{
  "mention": "nyeri pinggul",
  "entity_type": "symptom",
  "sentence_id": 0,
  "start_char": 7,
  "end_char": 20,
  "evidence": "..."
}
```

### 5.3 Eksperimen

Bandingkan:

1. LLM zero-shot;
2. LLM few-shot;
3. rule-based;
4. Medical NER jika tersedia.

### 5.4 Pemeriksaan

- mention terdapat dalam teks;
- offset cocok dengan mention;
- evidence tersedia;
- entity type valid;
- JSON valid;
- entitas duplikat;
- false positive;
- false negative;
- hallucination rate.

### 5.5 Metrik

- strict span precision;
- strict span recall;
- strict span F1;
- relaxed span F1;
- entity-type macro-F1;
- hallucination rate.

### 5.6 Artefak

```text
stage2_checkpoint_04_predictions.jsonl
stage2_checkpoint_04_metrics.json
stage2_checkpoint_04_false_positive.jsonl
stage2_checkpoint_04_false_negative.jsonl
```

### 5.7 Exit criteria

- seluruh output dapat diparse;
- semua mention mempunyai evidence;
- semua offset valid;
- baseline metrics tersedia;
- error utama telah dikategorikan;
- prompt dan model version tercatat.

---

## 6. Checkpoint 5 — Ekstraksi Atribut Klinis

### 6.1 Tujuan

Menambahkan atribut pada mention yang sudah ditemukan.

Atribut:

- normalized mention;
- base entity;
- domain awal;
- associated entities;
- value;
- unit;
- dose;
- frequency;
- route;
- method;
- visit.

### 6.2 Contoh

Input:

```text
gula darah puasa 126 mg/dL
```

Output:

```json
{
  "mention": "gula darah puasa 126 mg/dL",
  "base_entity": "gula darah puasa",
  "entity_type": "measurement",
  "domain": "measurement",
  "value": 126,
  "unit": "mg/dL"
}
```

### 6.3 Pemeriksaan

- base entity tidak kehilangan makna;
- value sesuai sumber;
- unit sesuai sumber;
- value dipasangkan dengan entitas yang benar;
- dosis dipasangkan dengan obat yang benar;
- domain awal sesuai entity type;
- atribut yang tidak tersedia bernilai `null`;
- model tidak menebak atribut yang tidak tertulis.

### 6.4 Metrik

- base-entity accuracy;
- domain accuracy;
- value accuracy;
- unit accuracy;
- value-unit association accuracy;
- drug-dose association accuracy.

### 6.5 Artefak

```text
stage2_checkpoint_05_entities.jsonl
stage2_checkpoint_05_attribute_metrics.json
stage2_checkpoint_05_relation_errors.jsonl
```

### 6.6 Exit criteria

- nilai dan unit konsisten;
- atribut yang tidak tersedia tidak dihalusinasikan;
- relation error telah dianalisis;
- attribute metrics tersedia.

---

## 7. Checkpoint 6 — Assertion, Temporal, dan Experiencer

### 7.1 Tujuan

Menentukan status klinis dan pemilik kondisi untuk setiap entitas.

### 7.2 Assertion

- `present`;
- `negated`;
- `uncertain`;
- `hypothetical`.

### 7.3 Temporal

- `present`;
- `past`;
- `future`;
- `unknown`.

### 7.4 Experiencer

- `patient`;
- `family`;
- `other`;
- `unknown`.

### 7.5 Contoh

```text
Saya tidak demam
```

```text
demam → negated, present, patient
```

```text
Ibu saya menderita diabetes
```

```text
diabetes → present, unknown/present, family
```

```text
Jika nanti muncul sesak
```

```text
sesak → hypothetical, future, patient
```

### 7.6 Pemeriksaan

- scope negasi;
- present vs negated;
- present vs uncertain;
- fakta vs hypothetical;
- patient vs family;
- past vs present;
- temporal expression;
- evidence keputusan.

### 7.7 Metrik

- assertion macro-F1;
- temporal accuracy atau macro-F1;
- experiencer accuracy;
- confusion matrix tiap atribut.

### 7.8 Artefak

```text
stage2_checkpoint_06_context.jsonl
stage2_checkpoint_06_assertion_metrics.json
stage2_checkpoint_06_temporal_metrics.json
stage2_checkpoint_06_experiencer_metrics.json
```

### 7.9 Exit criteria

- setiap entitas memiliki assertion;
- setiap entitas memiliki temporal;
- setiap entitas memiliki experiencer;
- evidence tersedia;
- disagreement antara LLM dan rule tercatat;
- confusion matrix tersedia.

---

# Milestone C — Pipeline Riset End-to-End

## 8. Checkpoint 7 — Teks Panjang dan Jawaban Dokter

### 8.1 Tujuan

Menangani teks panjang dan membedakan fakta pasien dari informasi yang diberikan dokter.

Checkpoint ini dimulai setelah ekstraksi pertanyaan pasien stabil.

### 8.2 Strategi chunking

Bandingkan:

1. teks utuh;
2. fixed-size chunk;
3. sentence-window;
4. sentence-window dengan overlap;
5. semantic segmentation opsional.

Setiap chunk harus menyimpan:

- chunk ID;
- sentence ID;
- character offset;
- parent document ID;
- overlap metadata.

### 8.3 Epistemic status jawaban

- `patient_fact`;
- `differential_diagnosis`;
- `general_information`;
- `recommended`;
- `conditional`;
- `hypothetical`.

Contoh:

```text
Keluhan ini dapat disebabkan oleh diabetes.
```

Entitas `diabetes` bukan otomatis kondisi pasien:

```json
{
  "mention": "diabetes",
  "assertion": "uncertain",
  "epistemic_status": "differential_diagnosis",
  "speaker": "doctor",
  "source_field": "answer"
}
```

### 8.4 Pemeriksaan

- entitas terpotong di batas chunk;
- duplikasi karena overlap;
- konteks negasi hilang;
- diagnosis banding menjadi fakta;
- rekomendasi dianggap sudah dilakukan;
- informasi umum dianggap kondisi pasien;
- perbedaan teks utuh dan chunking.

### 8.5 Artefak

```text
stage2_checkpoint_07_long_text.jsonl
stage2_checkpoint_07_answer_entities.jsonl
stage2_checkpoint_07_chunk_comparison.json
stage2_checkpoint_07_epistemic_errors.jsonl
```

### 8.6 Exit criteria

- chunk dapat ditelusuri ke teks asli;
- overlap tidak menghasilkan duplikasi final;
- speaker dan source selalu tersedia;
- diagnosis banding tidak otomatis menjadi fakta pasien;
- rekomendasi dapat dibedakan dari tindakan aktual.

---

## 9. Checkpoint 8 — Validasi, Retry, Fallback, dan Konsolidasi

### 9.1 Tujuan

Membuat output tahan terhadap JSON rusak, kegagalan model, dan hasil tidak konsisten.

### 9.2 Alur validasi

```text
raw model output
→ JSON parsing
→ Pydantic validation
→ mention-offset validation
→ rule validation
→ repair/retry
→ fallback
→ deduplication
→ final entities
```

### 9.3 Validasi wajib

- enum valid;
- mention terdapat dalam teks;
- offset cocok;
- evidence tersedia;
- confidence valid;
- entity ID unik;
- span berada dalam batas teks;
- value dan unit konsisten;
- source dan speaker tersedia;
- parent document ID valid.

### 9.4 Prosedur kegagalan

1. Simpan raw response.
2. Catat parsing error.
3. Lakukan satu kali repair atau retry.
4. Jika gagal, jalankan fallback rule-based.
5. Beri status kegagalan eksplisit.
6. Jangan menghilangkan record tanpa log.

### 9.5 Deduplikasi

Gabungkan berdasarkan:

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

### 9.6 Metrik

- JSON validity rate;
- Pydantic pass rate;
- retry rate;
- fallback rate;
- rejected-entity rate;
- duplicate rate;
- coverage.

### 9.7 Artefak

```text
stage2_checkpoint_08_validated.jsonl
stage2_checkpoint_08_validation_report.json
stage2_checkpoint_08_retry_log.jsonl
stage2_checkpoint_08_rejected_entities.jsonl
```

### 9.8 Exit criteria

- output final valid atau memiliki failure status;
- seluruh kegagalan tercatat;
- setiap perubahan pascaproses dapat ditelusuri;
- deduplikasi mempertahankan perbedaan konteks;
- fallback dapat dijalankan secara reproducible.

---

## 10. Checkpoint 9 — Adapter Downstream dan Evaluasi Final

### 10.1 Tujuan

Memastikan output Tahap 2 dapat digunakan oleh Tahap 3 dan Tahap 4.

Transformasi:

```text
satu dokumen
→ banyak entitas
→ satu query mapping per entitas
```

### 10.2 Field yang harus dipertahankan

- parent record ID;
- document ID;
- entity ID;
- source field;
- speaker;
- mention;
- normalized mention;
- base entity;
- entity type;
- domain;
- value dan unit;
- assertion;
- temporal;
- experiencer;
- epistemic status;
- evidence;
- confidence.

### 10.3 Audit integrasi

- jumlah entitas sebelum dan setelah adapter;
- tidak ada entity ID hilang;
- atribut tidak berubah;
- entitas negated tetap ditandai;
- entitas answer mempertahankan epistemic status;
- query decomposition menerima output;
- error downstream dapat dilacak ke teks sumber.

### 10.4 Evaluasi final

- strict span precision, recall, F1;
- relaxed span F1;
- entity-type macro-F1;
- assertion macro-F1;
- temporal accuracy;
- experiencer accuracy;
- epistemic-status accuracy;
- hallucination rate;
- JSON validity rate;
- coverage;
- latency;
- biaya per dokumen.

### 10.5 Artefak

```text
stage2_final_entities.jsonl
stage2_mapping_queries.jsonl
stage2_final_metrics.json
stage2_error_analysis.md
stage2_ablation_report.md
stage2_run_manifest.json
```

### 10.6 Exit criteria

- output diterima Tahap 3 dan Tahap 4;
- metrik final tersedia;
- error analysis selesai;
- ablation study selesai;
- versi model, prompt, rule, schema, dan gold set tercatat;
- eksperimen dapat direproduksi.

---

## 11. Ringkasan Urutan Checkpoint

```text
MILESTONE A — FONDASI

Checkpoint 1  Kontrak input dan provenance
      ↓
Checkpoint 2  Skema dan pedoman anotasi
      ↓
Checkpoint 3  Gold set

MILESTONE B — EKSTRAKTOR

Checkpoint 4  Entity-span baseline
      ↓
Checkpoint 5  Atribut klinis
      ↓
Checkpoint 6  Assertion, temporal, experiencer

MILESTONE C — END-TO-END

Checkpoint 7  Teks panjang dan jawaban dokter
      ↓
Checkpoint 8  Validasi, retry, fallback, deduplikasi
      ↓
Checkpoint 9  Adapter downstream dan evaluasi final
```

---

## 12. Gate yang Tidak Boleh Dilewati

- jangan membuat prompt final sebelum skema selesai;
- jangan membuat gold set tanpa pedoman anotasi;
- jangan menilai model menggunakan data few-shot;
- jangan menambahkan atribut sebelum entity span dapat diaudit;
- jangan memproses jawaban dokter sebelum assertion dan experiencer stabil;
- jangan mengintegrasikan ke mapping sebelum output lolos validasi;
- jangan membandingkan eksperimen tanpa versi model, prompt, rule, dan data;
- jangan menghapus output gagal tanpa audit log.

---

## 13. Manifest Audit Setiap Eksperimen

Setiap run sebaiknya menghasilkan:

```json
{
  "run_id": "string",
  "timestamp": "ISO-8601",
  "input_file": "string",
  "input_hash": "string",
  "record_count": 150,
  "gold_version": "string",
  "schema_version": "string",
  "model_name": "string",
  "model_version": "string",
  "prompt_version": "string",
  "rule_version": "string",
  "temperature": 0,
  "chunking_method": "string",
  "success_count": 150,
  "failure_count": 0,
  "processing_time": 0.0,
  "estimated_cost": 0.0
}
```

Untuk LLM, simpan:

- raw request;
- raw response;
- request ID jika tersedia;
- model name dan version;
- parameter generation;
- retry count;
- timestamp;
- latency;
- token usage;
- estimasi biaya.

LLM tidak selalu deterministik meskipun menggunakan prompt yang sama. Manifest diperlukan untuk reproducibility.

---

## 14. Template Laporan Audit per Checkpoint

Setiap checkpoint sebaiknya memiliki laporan:

```markdown
# Laporan Checkpoint

## Identitas
- checkpoint:
- run_id:
- input version:
- schema version:
- model version:
- prompt version:
- rule version:

## Ringkasan
- jumlah input:
- berhasil:
- gagal:
- warning:
- durasi:

## Metrik
- ...

## Error Analysis
- false positive:
- false negative:
- parsing error:
- context error:

## Artefak
- ...

## Exit Criteria
- [ ] ...

## Keputusan
- pass / revise / fail
```

---

## 15. Strategi Verifikasi

### 15.1 Verifikasi otomatis

- JSON parsing;
- Pydantic validation;
- unique ID;
- mention-offset consistency;
- enum validation;
- evidence validation;
- duplicate detection;
- record count;
- provenance completeness.

### 15.2 Verifikasi manual

- sampel acak;
- seluruh false positive;
- seluruh false negative;
- seluruh warning;
- seluruh retry/fallback;
- entitas confidence rendah;
- diagnosis banding;
- negasi;
- experiencer family;
- rekomendasi dokter.

### 15.3 Verifikasi klinis

- definisi entity type;
- base entity;
- assertion;
- temporal;
- experiencer;
- interpretasi jawaban dokter;
- kasus ambigu;
- adjudikasi gold set.

---

## 16. Definisi Selesai Tahap 2

Tahap 2 dinyatakan selesai jika:

- sembilan checkpoint lulus;
- question dan answer diproses terpisah;
- multi-entitas berhasil diekstrak;
- setiap entitas mempunyai evidence;
- mention-offset valid;
- entity type dan domain tersedia;
- atribut nilai dan unit tersedia jika disebutkan;
- assertion tersedia;
- temporal tersedia;
- experiencer tersedia;
- epistemic status tersedia untuk jawaban;
- output lolos validasi atau memiliki status kegagalan;
- provenance model, prompt, rule, dan data tersimpan;
- tersedia adapter ke Tahap 3 dan Tahap 4;
- gold set dan metrik final tersedia;
- error analysis dan ablation study terdokumentasi;
- eksperimen dapat dijalankan ulang.

---

## 17. Kesimpulan

Pembagian yang direkomendasikan adalah:

```text
9 checkpoint
dibagi dalam
3 milestone
```

Milestone A memastikan definisi masalah dan data evaluasi stabil. Milestone B menghasilkan ekstraktor yang dapat diuji pada fakta pasien. Milestone C menangani teks panjang, jawaban dokter, validasi, serta integrasi downstream.

Checkpoint paling kritis adalah:

1. skema dan pedoman anotasi;
2. gold set;
3. evidence dan offset;
4. assertion dan experiencer;
5. provenance question/answer;
6. validasi sebelum mapping.

Tanpa checkpoint tersebut, output dapat terlihat meyakinkan tetapi tidak dapat diverifikasi secara ilmiah.
