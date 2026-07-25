# Slide 1 — Ujian Pre-Komprehensif

## Adaptasi CDE-Mapper untuk Pemetaan Terminologi Klinis Bahasa Indonesia

### Pendekatan Hybrid Berbasis LLM dan Semantic Retrieval

**Anie Rose Irawati**  
Program Doktor Ilmu Komputer  
Universitas Gadjah Mada

**Promotor:** Afiahayati, S.Kom., M.Cs., Ph.D.  
**Ko-Promotor:** Dr. Lukman Heryawan, S.T., M.T.

> **Note presenter:** Buka dengan satu kalimat inti: penelitian ini mengembangkan pipeline end-to-end yang mengubah teks klinis panjang Bahasa Indonesia menjadi entitas terstruktur dan kandidat kode SNOMED CT, LOINC, serta ICD-10. Tekankan bahwa presentasi mencakup usulan ilmiah sekaligus progres implementasi sampai Tahap 2 Checkpoint 3.

---

# Slide 2 — Alur Presentasi

1. Konteks dan urgensi
2. Research gap dan posisi penelitian
3. Tujuan, kebaruan, dan kontribusi
4. Metode dan arsitektur usulan
5. Progres implementasi Tahap 0–2
6. Rancangan evaluasi, risiko, dan rencana lanjutan

> **Note presenter:** Sampaikan bahwa alur bergerak dari “mengapa penelitian diperlukan” menuju “bagaimana solusi dibangun dan dibuktikan”. Batasi pengantar agar bagian progres implementasi memperoleh waktu cukup.

---

# Slide 3 — Transformasi Digital Membutuhkan Kesetaraan Makna

- Pertukaran data belum menjamin interoperabilitas.
- Sistem berbeda harus memahami konsep klinis dengan makna yang sama.
- Data yang secara tekstual mirip dapat ditafsirkan berbeda tanpa terminologi standar.
- Konsistensi semantik menentukan kualitas:
  - integrasi data;
  - analisis klinis;
  - pengambilan keputusan;
  - penelitian kesehatan.

**Pesan utama:** interoperabilitas sintaksis tanpa interoperabilitas semantik masih menyisakan risiko salah makna.

> **Note presenter:** Jelaskan perbedaan sederhana: FHIR membantu struktur pertukaran, sedangkan terminologi klinis membantu kesamaan arti. Gunakan analogi “wadah dan isi”: format pertukaran adalah wadah, terminologi standar memastikan isi dipahami sama.

---

# Slide 4 — Konteks Indonesia: SATUSEHAT

- SATUSEHAT dibangun dalam kerangka interoperabilitas berbasis FHIR.
- Ekosistem nasional memerlukan terminologi standar untuk mengisi resource FHIR.
- Terminologi yang relevan meliputi:
  - SNOMED CT;
  - LOINC;
  - keluarga ICD;
  - terminologi nasional seperti KPTL.
- Pemetaan terminologi menjadi salah satu titik kritis implementasi.

**Tantangan:** data sumber masih heterogen, lokal, dan sering tidak terstruktur.

> **Note presenter:** Hindari menyatakan bahwa satu terminologi menggantikan terminologi lain. Tekankan pembagian fungsi: SNOMED CT untuk representasi konsep klinis yang kaya, LOINC untuk observasi/laboratorium, dan ICD untuk klasifikasi pelaporan/statistik.

---

# Slide 5 — Mengapa Memerlukan Multi-Terminologi?

| Kebutuhan | Terminologi utama | Contoh |
|---|---|---|
| Diagnosis, gejala, temuan, prosedur | SNOMED CT | Diabetes melitus tipe 2 |
| Pertanyaan observasi atau tes | LOINC | Glukosa darah puasa |
| Klasifikasi diagnosis | ICD-10 | E11.9 |

- Satu episode klinis dapat membutuhkan lebih dari satu representasi.
- Pemilihan target harus mengikuti tipe entitas dan tujuan penggunaan.
- Karena itu, pipeline tidak cukup hanya melakukan pencarian pada satu vocabulary.

> **Note presenter:** Gunakan contoh diabetes: konsep penyakit dapat direpresentasikan di SNOMED CT, pemeriksaan glukosanya di LOINC, dan klasifikasi diagnosisnya di ICD-10. Ini menjelaskan mengapa routing multi-terminologi menjadi bagian ilmiah penelitian.

---

# Slide 6 — Realitas Teks Klinis Bahasa Indonesia

- Istilah baku dan istilah sehari-hari bercampur.
- Singkatan dapat ambigu: `DM`, `TD`, `TB`, `BB`, `Px`.
- Terdapat typo, code-mixing, variasi satuan, dan tanda baca tidak konsisten.
- Informasi klinis hadir pada teks panjang dan lintas kalimat.
- Negasi, waktu, experiencer, dan ketidakpastian mengubah makna.

Contoh masukan:

```text
Px dgn DM tipe 2, GDP 126 mg/dL, TD 150/90
```

> **Note presenter:** Tekankan bahwa masalah bukan sekadar menerjemahkan kata. Sistem harus menjaga angka dan satuan, membedakan singkatan ambigu, serta memahami apakah kondisi terjadi pada pasien, keluarga, atau hanya merupakan informasi umum dari dokter.

---

# Slide 7 — Mengapa Clinical Mapping Sulit?

1. Memerlukan pemahaman hierarki dan relasi ontologi.
2. Entitas komposit harus didekomposisi.
3. Teks panjang mengandung banyak mention klinis.
4. Variasi bahasa dan istilah lokal sangat tinggi.
5. Kesalahan berpotensi memengaruhi keselamatan pasien.
6. Keluaran harus sesuai standar dan dapat diaudit.
7. Gold standard membutuhkan validasi ahli klinis.

> **Note presenter:** Sampaikan bahwa tugas ini lebih kompleks daripada fuzzy matching biasa. Kandidat yang secara leksikal mirip belum tentu sesuai domain, spesimen, waktu, metode, atau tujuan penggunaan.

---

# Slide 8 — Evolusi Pendekatan Pemetaan

```text
Rule-based / lexical
        ↓
Machine learning
        ↓
Deep learning & contextual embedding
        ↓
Knowledge graph & semantic retrieval
        ↓
LLM + Retrieval-Augmented Generation
        ↓
Hybrid, constrained, human-in-the-loop
```

- Rule-based: transparan, tetapi sulit diskalakan.
- Embedding: menangkap semantik, tetapi dapat kehilangan kecocokan istilah spesifik.
- LLM: kuat memahami konteks, tetapi berisiko halusinasi.
- Hybrid: menggabungkan kekuatan dan mengendalikan kelemahannya.

> **Note presenter:** Jangan menggambarkan evolusi sebagai penggantian total. Aturan tetap diperlukan untuk constraint, sparse retrieval tetap penting untuk kecocokan istilah, dan ahli tetap dibutuhkan untuk kasus berisiko.

---

# Slide 9 — Titik Awal: CDE-Mapper

CDE-Mapper menyediakan fondasi:

- dekomposisi Clinical Data Element;
- hybrid retrieval;
- metadata filtering;
- multi-stage ranking;
- pemetaan ke controlled vocabularies;
- knowledge reservoir untuk hasil berulang.

**Kekuatan:** efektif untuk CDE komposit dan kandidat multi-vocabulary.  
**Posisi penelitian:** mengadaptasi, bukan membangun seluruh sistem dari nol.

> **Note presenter:** Jelaskan bahwa kontribusi penelitian adalah adaptasi substantif terhadap batas arsitektur dan konteks penggunaan, bukan hanya mengganti bahasa input. Fondasi baseline dipertahankan agar peningkatan dapat dibandingkan secara terukur.

---

# Slide 10 — Tiga Research Gap Utama

### Gap 1 — Multi-standar

Mayoritas penelitian fokus pada satu terminologi, sedangkan kebutuhan nasional bersifat multi-terminologi.

### Gap 2 — Teks panjang

CDE-Mapper berfokus pada item CDE; dokumen klinis panjang dapat memuat banyak entitas dan konteks.

### Gap 3 — Bahasa Indonesia

Baseline diuji pada bahasa Inggris; Bahasa Indonesia mempunyai singkatan, morfologi, istilah lokal, dan sumber daya klinis yang berbeda.

> **Note presenter:** Hubungkan setiap gap dengan modul solusi: routing multi-terminologi untuk gap pertama, long-text entity extraction untuk gap kedua, serta normalisasi dan retrieval adaptif Bahasa Indonesia untuk gap ketiga.

---

# Slide 11 — Rumusan Masalah

1. Bagaimana memetakan istilah klinis Bahasa Indonesia secara simultan ke SNOMED CT, LOINC, dan ICD-10?
2. Bagaimana memperluas CDE-Mapper agar mampu mengekstraksi banyak entitas dari teks klinis panjang?
3. Bagaimana mengadaptasi retrieval ensemble terhadap variasi linguistik dan keterbatasan sumber daya Bahasa Indonesia?

**Pertanyaan evaluatif:** apakah adaptasi tersebut meningkatkan akurasi, coverage, robustness, dan efisiensi dibanding baseline?

> **Note presenter:** Tiga pertanyaan pertama mengikuti rumusan proposal. Pertanyaan evaluatif menjembatani rumusan masalah dengan desain eksperimen dan metrik yang akan digunakan.

---

# Slide 12 — Tujuan Penelitian

### Tujuan umum

Mengembangkan dan mengevaluasi framework adaptif untuk pemetaan terminologi klinis Bahasa Indonesia.

### Tujuan khusus

1. Memodifikasi CDE-Mapper untuk pemetaan simultan ke tiga terminologi.
2. Mengintegrasikan long-text clinical entity extraction.
3. Membangun retrieval ensemble yang sesuai dengan Bahasa Indonesia.
4. Menyediakan pipeline yang reproducible, auditable, dan human-in-the-loop.

> **Note presenter:** Bedakan tujuan ilmiah dari artefak teknis. Framework dan evaluasinya adalah tujuan penelitian; kode, skema JSON, notebook, kamus, dan audit trail adalah sarana untuk membuktikannya.

---

# Slide 13 — Kebaruan yang Diusulkan

- **Long-text first:** banyak entitas diekstraksi sebelum mapping.
- **Language-adaptive:** normalisasi konservatif dan sumber daya lokal Bahasa Indonesia.
- **Multi-terminology routing:** target dipilih berdasarkan tipe dan konteks entitas.
- **Hybrid retrieval:** dense + sparse + filtering + reranking.
- **Context-aware entities:** assertion, temporal, experiencer, dan epistemic status.
- **Validated reservoir:** pengetahuan disimpan bersama status validasi dan provenance.
- **End-to-end evaluation:** menelusuri error dari ekstraksi sampai kode akhir.

> **Note presenter:** Tegaskan bahwa kebaruan merupakan kombinasi terintegrasi. Hindari mengklaim setiap algoritma komponennya baru; kontribusinya terletak pada adaptasi arsitektur, kontrak antar-modul, konteks Bahasa Indonesia, dan pembuktian end-to-end.

---

# Slide 14 — Kontribusi Penelitian

| Dimensi | Kontribusi |
|---|---|
| Metodologis | Framework hybrid LLM–semantic retrieval untuk teks klinis Indonesia |
| Teknis | Pipeline modular, tervalidasi skema, dan memiliki audit trail |
| Data | Korpus normalisasi, pedoman anotasi, dan gold set bertahap |
| Evaluatif | Baseline, ablation, metrik komponen dan end-to-end |
| Praktis | Prototipe pendukung standardisasi dan interoperabilitas |

> **Note presenter:** Pada kontribusi data, sampaikan bahwa gold set masih dalam proses. Yang sudah tersedia saat ini adalah rancangan, sampel terstratifikasi, template dua anotator, validator, dan mekanisme disagreement.

---

# Slide 15 — Batasan dan Ruang Lingkup

- Bahasa utama: Bahasa Indonesia klinis dengan kemungkinan code-mixing.
- Input:
  - teks konsultasi kesehatan;
  - teks klinis panjang;
  - istilah atau field RME.
- Target utama: SNOMED CT, LOINC, dan ICD-10.
- Fokus penelitian: dukungan keputusan mapping, bukan pengganti ahli.
- Data sensitif harus dianonimkan dan dikelola sesuai tata kelola penelitian.
- Keluaran ber-confidence rendah diarahkan ke validasi manual.

> **Note presenter:** Tekankan bahwa sistem tidak melakukan diagnosis dan tidak mengambil keputusan klinis final. Ia mengekstraksi dan merekomendasikan kandidat terminologi dengan jejak audit.

---

# Slide 16 — Paradigma Penelitian

- Jenis: penelitian pengembangan.
- Pendekatan: kuantitatif-eksperimental.
- Siklus:

```text
Desain → Implementasi → Verifikasi → Evaluasi → Error analysis → Perbaikan
```

- Pembandingan:
  - baseline;
  - model usulan;
  - ablation study.
- Validasi data acuan melibatkan minimal dua anotator dan adjudikator klinis.

> **Note presenter:** Jelaskan bahwa proses iteratif tidak berarti data uji terus dipakai untuk tuning. Development set digunakan untuk perbaikan, sedangkan hold-out evaluation set harus tetap dikunci.

---

# Slide 17 — Lima Tahapan Penelitian dalam Proposal

1. **Persiapan dan analisis**
2. **Perancangan dan pengembangan model**
3. **Implementasi inti model**
4. **Evaluasi dan validasi**
5. **Analisis dan dokumentasi**

Tahapan bersifat berurutan sekaligus iteratif.

> **Note presenter:** Ini adalah struktur metodologi makro pada proposal. Setelah slide ini, jelaskan bahwa implementasi teknis memecahnya menjadi checkpoint yang lebih kecil agar setiap keluaran dapat diverifikasi sebelum menjadi input tahap berikutnya.

---

# Slide 18 — Arsitektur Usulan: Delapan Transformasi

```text
1. Normalisasi Bahasa Indonesia
2. Ekstraksi entitas klinis
3. Klasifikasi tipe dan target
4. Dekomposisi entitas komposit
5. Ensemble retrieval
6. Filtering berbasis constraint
7. Reranking dan keputusan
8. Knowledge reservoir tervalidasi
```

Setiap tahap menyimpan provenance dan keluaran terstruktur.

> **Note presenter:** Tekankan bahwa pemisahan komponen memungkinkan error localization. Bila kode akhir salah, penelitian dapat menentukan apakah penyebabnya ekstraksi, routing, retrieval, filtering, atau reranking.

---

# Slide 19 — Pipeline Implementasi yang Dapat Diaudit

| Tahap | Fokus |
|---:|---|
| 0 | Audit baseline dan reproducibility |
| 1 | Normalisasi Bahasa Indonesia |
| 2 | Ekstraksi entitas teks panjang |
| 3 | Mapping rules dan target terminology |
| 4 | Query decomposition |
| 5 | Knowledge base dan ensemble retrieval |
| 6 | Filtering |
| 7 | Reranking dan keputusan |
| 8 | Human-in-the-loop dan reservoir |
| 9 | Evaluasi dan ablation |

> **Note presenter:** Ini adalah operasionalisasi dari metode proposal berdasarkan `RENCANA_IMPLEMENTASI_PIPELINE_RISET.md`. Tahap 0 ditambahkan untuk memastikan baseline benar-benar reproducible sebelum modifikasi.

---

# Slide 20 — Contoh Alur End-to-End

Masukan:

```text
Px dgn DM tipe 2, GDP 126 mg/dL, TD 150/90
```

Normalisasi:

```text
pasien dengan diabetes melitus tipe 2,
gula darah puasa 126 mg/dL,
tekanan darah 150/90
```

Entitas:

- diabetes melitus tipe 2;
- gula darah puasa 126 mg/dL;
- tekanan darah 150/90.

Routing:

- diagnosis → SNOMED CT dan ICD-10;
- observasi → LOINC.

> **Note presenter:** Contoh ini menunjukkan mengapa satu input menghasilkan beberapa entitas dan beberapa target. Hindari menjanjikan kode LOINC tertentu sebelum seluruh konteks, seperti spesimen dan metode, tersedia.

---

# Slide 21 — Sumber dan Peran Data

- Controlled vocabularies: SNOMED CT, LOINC, ICD-10.
- Dataset baseline CDE-Mapper: antara lain NCBI dan BC5CDR.
- Data lokal/RME yang telah dianonimkan.
- Konsultasi kesehatan daring untuk variasi bahasa pasien.
- Korpus Alodokter yang digunakan dalam implementasi awal:
  - 150 pasangan question–answer;
  - dipertahankan provenance dan field sumbernya.

**Prinsip:** data pengembangan, few-shot, dan evaluasi harus dipisahkan.

> **Note presenter:** Sampaikan bahwa penggunaan data daring harus memperhatikan ketentuan sumber, anonimisasi, dan persetujuan etik bila diperlukan. Angka 150 pasangan merujuk pada artefak implementasi saat ini, bukan ukuran akhir seluruh disertasi.

---

# Slide 22 — Dua Gold Standard yang Berbeda

### A. Gold ekstraksi entitas

- Unit: span dan atribut entitas dalam dokumen.
- Digunakan untuk Tahap 2 dan evaluasi Checkpoint 4–7.
- Implementasi awal: 40 pasangan terstratifikasi.

### B. Gold terminology mapping

- Unit: entitas/istilah dan kode standar yang benar.
- Proposal merencanakan sekitar 100–200 istilah.
- Digunakan untuk evaluasi routing, retrieval, dan mapping akhir.

**Keduanya saling terhubung, tetapi tidak dapat saling menggantikan.**

> **Note presenter:** Ini perlu disampaikan untuk mencegah kesan inkonsistensi jumlah sampel. Checkpoint 3 saat ini menyiapkan gold untuk entity extraction, sedangkan proposal juga membutuhkan gold pemetaan kode. Ukuran akhir dapat diperluas setelah pilot dan perhitungan kebutuhan sampel.

---

# Slide 23 — Tahap 0: Audit Baseline

Tujuan: memastikan baseline berjalan konsisten sebelum adaptasi.

Artefak yang telah tersedia:

- konfigurasi baseline;
- smoke input dan smoke audit;
- snapshot dependency;
- runner hybrid retrieval;
- runner reranking Gemma;
- gold subset retrieval 10 query;
- evaluator Top-k;
- manifest dan laporan runtime.

Temuan infrastruktur:

- fallback hybrid Qdrant dapat berjalan;
- akses Athena pernah mengembalikan HTTP 403 dan dicatat sebagai partial source error.

> **Note presenter:** Tegaskan bahwa kegagalan Athena tidak disembunyikan. Sistem tetap menghasilkan keluaran melalui fallback, tetapi eksperimen ini belum merepresentasikan kondisi semua sumber tersedia.

---

# Slide 24 — Hasil Awal Tahap 0

### Pilot retrieval, 10 query

| Metrik | Hybrid | Setelah reranking |
|---|---:|---:|
| Coverage | 1,00 | 1,00 |
| Accuracy@1 | 0,60 | 0,50 |
| Accuracy@5 | 0,70 | 0,80 |
| Accuracy@10 | 0,90 | 0,90 |
| MRR | 0,640 | 0,634 |
| Mean latency | 1,47 detik | 4,22 detik |

**Interpretasi awal:** reranking memperbaiki cakupan peringkat menengah, tetapi belum meningkatkan Top-1 dan menambah latensi.

> **Note presenter:** Beri penekanan kuat bahwa ini smoke/pilot berukuran 10 query, bukan hasil utama disertasi. `partial_source_error_rate=1.0` karena gangguan salah satu sumber juga membatasi interpretasi. Temuan ini berguna untuk merancang eksperimen, bukan untuk generalisasi.

---

# Slide 25 — Tahap 1: Normalisasi Konservatif

```text
raw_text
→ validasi dan Unicode
→ cleaning konservatif
→ token terlindungi
→ bentuk informal
→ ekspansi singkatan kontekstual
→ koreksi typo terbatas
→ angka dan satuan
→ segmentasi kalimat
→ boilerplate
→ normalized_text + audit trail
```

Prinsip utama: meningkatkan keterbacaan mesin tanpa menghilangkan makna klinis.

> **Note presenter:** Tekankan kata “konservatif”. Angka, dosis, unit, negasi, temporalitas, nama obat, dan istilah campuran harus dipertahankan. Stemming tidak digunakan sebagai transformasi default karena dapat merusak istilah klinis.

---

# Slide 26 — Kamus Singkatan Berlapis

Setiap entri memiliki:

- bentuk singkat dan ekspansi;
- kategori/domain;
- status:
  - `automatic`;
  - `context_required`;
  - `review_required`;
- konteks;
- ambiguitas;
- provenance dan versi.

Contoh risiko:

| Singkatan | Kemungkinan makna |
|---|---|
| `TB` | tinggi badan / tuberkulosis |
| `BB` | berat badan / konteks lain |
| `mg` | miligram / minggu |
| `Px` | pasien / pemeriksaan |

> **Note presenter:** Jelaskan bahwa kamus bukan sekadar pasangan key–value. Keputusan ekspansi harus mempertimbangkan konteks; jika konteks tidak cukup, token dipertahankan dan warning dicatat.

---

# Slide 27 — Progres dan Audit Tahap 1

Telah diimplementasikan:

- profil `clinical`, `question`, dan `answer`;
- kamus singkatan, typo, dan unit;
- perlindungan token klinis;
- segmentasi deterministik;
- deteksi boilerplate tanpa menghapus teks;
- audit trail dan versioning;
- runner untuk 150 pasangan Alodokter;
- tujuh unit test normalizer.

Audit kecil:

- 5/5 exact normalized match;
- 14 ekspansi singkatan;
- 3 koreksi typo;
- 5 normalisasi unit.

> **Note presenter:** Jelaskan keterbatasan: hasil 100% berasal dari lima kasus gold terkontrol dan hanya memverifikasi implementasi awal. Evaluasi yang lebih besar tetap diperlukan untuk abbreviation accuracy, typo recovery, sentence-boundary F1, dan preservation rate.

---

# Slide 28 — Mengapa Tahap 2 Lebih dari NER Biasa?

Entitas harus membawa konteks klinis:

```text
mention + entity_type
+ assertion
+ temporal
+ experiencer
+ epistemic status
+ value/unit/dose/frequency/route
+ evidence dan offset
```

Contoh:

```text
“ibu saya menderita diabetes”
```

- entitas: `diabetes`;
- tipe: `condition`;
- experiencer: `family`;
- bukan kondisi penanya.

> **Note presenter:** Tekankan bahwa kesalahan experiencer atau negasi dapat mengubah makna secara fundamental. Karena itu, evaluasi span saja tidak cukup untuk jawaban dokter dan konsultasi pasien.

---

# Slide 29 — Strategi Checkpoint Tahap 2

### Milestone A — Fondasi

1. Kontrak input dan provenance
2. Skema entitas dan pedoman anotasi
3. Gold set awal

### Milestone B — Ekstraktor

4. Baseline entity span
5. Atribut klinis
6. Assertion, temporal, experiencer

### Milestone C — End-to-end

7. Teks panjang dan jawaban dokter
8. Validasi, retry, fallback, deduplikasi
9. Adapter downstream dan evaluasi final

> **Note presenter:** Jelaskan bahwa checkpoint mencegah kompleksitas ditumpuk sekaligus. Entity span harus stabil sebelum atribut kompleks; question diuji sebelum konteks jawaban dokter yang lebih sulit.

---

# Slide 30 — Checkpoint 1: Kontrak Input

Transformasi:

```text
150 pasangan konsultasi
→ 150 dokumen question
+ 150 dokumen answer
= 300 dokumen tervalidasi
```

Setiap dokumen menyimpan:

- `document_id` dan `parent_record_id`;
- `source_field` dan `speaker`;
- `raw_text` dan `normalized_text`;
- sentences;
- versi normalizer dan resource;
- provenance serta SHA-256.

**Status audit: pass.**

> **Note presenter:** Jelaskan bahwa pemisahan question dan answer diperlukan karena speaker dan epistemic status berbeda. Audit memastikan seluruh pasangan lengkap, ID unik, teks tidak kosong, dan setiap kalimat dapat ditelusuri kembali.

---

# Slide 31 — Checkpoint 2: Taksonomi Entitas

```text
condition        symptom
clinical_finding measurement
drug             procedure
anatomy          demographic
unit             visit
other
```

Tujuan:

- cukup luas untuk konsultasi klinis;
- dapat diarahkan ke domain terminologi;
- stabil untuk anotasi awal;
- dapat diperluas melalui adjudikasi.

`other` hanya digunakan bila tipe lain tidak sesuai dan wajib ditinjau.

> **Note presenter:** Berikan contoh singkat: diabetes sebagai condition, demam sebagai symptom, tekanan darah sebagai measurement, parasetamol sebagai drug, ultrasonografi sebagai procedure, dan mmHg sebagai unit.

---

# Slide 32 — Checkpoint 2: Atribut Entitas

| Kelompok | Atribut |
|---|---|
| Identitas | mention, normalized mention, base entity, entity type |
| Semantik | domain, categories, associated entities |
| Nilai klinis | value, unit, dose, frequency, route, method, visit |
| Konteks | assertion, temporal, experiencer, epistemic status |
| Audit | source field, speaker, sentence ID, offsets, evidence, confidence |

Validasi utama:

```text
normalized_text[start_char:end_char] == mention
```

> **Note presenter:** Jelaskan manfaat tiap kelompok: identitas untuk konsep, nilai klinis untuk dekomposisi, konteks untuk mencegah salah tafsir, dan audit untuk reproducibility.

---

# Slide 33 — Hasil Checkpoint 2

- 300 dokumen Checkpoint 1 tervalidasi.
- 9 contoh positif lolos skema.
- 6 contoh negatif ditolak sesuai harapan.
- Semua tipe entitas inti tercakup.
- Contoh mencakup:
  - question dan answer;
  - assertion present, negated, uncertain, hypothetical;
  - temporal;
  - patient dan family experiencer;
  - differential diagnosis dan recommendation.
- JSON Schema serta pedoman anotasi tersedia.

**Status audit: pass.**

> **Note presenter:** Contoh negatif digunakan untuk membuktikan validator menolak offset salah, speaker tidak sesuai, sentence ID invalid, confidence di luar rentang, ID duplikat, dan evidence yang tidak memuat mention.

---

# Slide 34 — Checkpoint 3: Desain Gold Set Entitas

- Unit sampling: pasangan question–answer.
- Ukuran pilot: 40 pasangan atau 80 dokumen.
- Sampling deterministik dan terstratifikasi.
- Strata mencakup:
  - negasi dan ketidakpastian;
  - temporalitas;
  - obat/dosis dan measurement;
  - family experiencer;
  - rekomendasi;
  - pertanyaan/jawaban panjang.

**Strata adalah alat sampling, bukan label gold.**

> **Note presenter:** Gunakan contoh `drug_or_dose`, `negation`, atau `long_answer`. Label tersebut hanya membantu memilih kasus yang beragam. Label gold sebenarnya berupa span, entity type, dan atribut yang diberikan anotator.

---

# Slide 35 — Workflow Anotasi dan Status Checkpoint 3

```text
Paket tugas yang sama
       ↙       ↘
Annotator A  Annotator B
       ↘       ↙
Agreement & disagreement
           ↓
Adjudikasi klinis
           ↓
Gold set v1 + hash + versi
```

Status saat ini:

- 40 tugas untuk A dan B sudah tersedia;
- struktur dan audit valid;
- anotasi lengkap: 0/40;
- status: `pending_annotation`;
- gold v1 belum dibuat.

> **Note presenter:** Tekankan integritas ilmiah: sistem tidak menghasilkan gold otomatis. Tools yang direkomendasikan adalah INCEpTION untuk fitur per-span dan curation, atau doccano untuk span/type yang dilanjutkan lembar atribut terstruktur.

---

# Slide 36 — Rencana Tahap 3–8

1. **Routing:** tipe entitas → terminologi target.
2. **Decomposition:** base entity, domain, unit, category, visit, method.
3. **Retrieval:** dense + sparse, Top-k kandidat.
4. **Filtering:** domain, semantic type, threshold, constraint.
5. **Reranking:** konteks, definisi, sinonim, keputusan relevansi.
6. **Human-in-the-loop:** validasi ahli.
7. **Knowledge reservoir:** hanya menyimpan pemetaan tervalidasi.

> **Note presenter:** Sampaikan bahwa implementasi Checkpoint 4 dapat dimulai sambil anotasi berjalan, tetapi tidak boleh dinyatakan selesai secara ilmiah tanpa gold set final.

---

# Slide 37 — Baseline dan Ablation Study

### Baseline

- lexical/exact/fuzzy matching;
- dense retrieval saja;
- sparse retrieval saja;
- LLM-only tanpa retrieval;
- CDE-Mapper original.

### Ablation

- tanpa normalisasi lokal;
- tanpa long-text extraction;
- tanpa query decomposition;
- tanpa filtering;
- tanpa reranking;
- tanpa knowledge reservoir.

**Tujuan:** mengukur kontribusi nyata setiap komponen.

> **Note presenter:** Jelaskan bahwa model paling kompleks belum tentu paling baik. Ablation dibutuhkan untuk membuktikan apakah setiap modul meningkatkan kualitas atau hanya menambah latensi dan biaya.

---

# Slide 38 — Kerangka Evaluasi

| Level | Metrik |
|---|---|
| Normalisasi | exact match, abbreviation accuracy, typo recovery, preservation |
| Ekstraksi | span precision/recall/F1, type F1 |
| Konteks | assertion, temporal, experiencer, epistemic accuracy |
| Dekomposisi | field-level precision/recall/F1 |
| Retrieval | Accuracy@k, Recall@k, Precision@k, MRR, NDCG |
| Mapping akhir | accuracy, precision, recall, F1, coverage |
| Operasional | latency, failure rate, consistency, biaya |

> **Note presenter:** Jelaskan bahwa metrik dipisahkan per komponen untuk menghindari kesimpulan keliru. End-to-end error dapat berasal dari entitas yang tidak ditemukan, kandidat yang tidak diretrieval, atau kandidat benar yang gagal dipilih.

---

# Slide 39 — Risiko, Etik, dan Mitigasi

| Risiko | Mitigasi |
|---|---|
| Variasi bahasa ekstrem | normalisasi konservatif dan error analysis |
| Singkatan ambigu | aturan konteks, warning, review |
| Halusinasi LLM | constrained output, retrieval, validator, fallback |
| Kandidat benar hilang | ensemble retrieval dan evaluasi Recall@k |
| Reservoir menyimpan error | status validasi, provenance, approval ahli |
| Bias/evaluasi bocor | pemisahan development, few-shot, dan hold-out |
| Data sensitif | anonimisasi, kontrol akses, tata kelola etik |
| Ketergantungan layanan | logging, retry, fallback, manifest |

> **Note presenter:** Tekankan bahwa auditability adalah bagian desain, bukan tambahan administratif. Setiap transformasi penting menyimpan versi, hash, warning, dan evidence.

---

# Slide 40 — Kesimpulan dan Rencana Terdekat

### Kesimpulan

- Masalah utama adalah kesenjangan semantik pada teks klinis Indonesia.
- Solusi yang diusulkan menggabungkan normalisasi, ekstraksi konteks, retrieval hybrid, constraint, reranking, dan validasi ahli.
- Tahap 0 dan Tahap 1 telah memiliki implementasi serta audit awal.
- Tahap 2 Checkpoint 1–2 lulus audit.
- Checkpoint 3 siap untuk anotasi independen dan adjudikasi.

### Rencana terdekat

1. Menyelesaikan gold set entitas.
2. Membangun baseline entity-span Checkpoint 4.
3. Menyiapkan gold terminology mapping.
4. Melanjutkan routing, retrieval, dan evaluasi end-to-end.

## Terima kasih — Pertanyaan dan Masukan

> **Note presenter:** Tutup dengan posisi yang jujur: fondasi teknis dan audit sudah tersedia, tetapi evaluasi ilmiah utama menunggu gold set dan eksperimen skala memadai. Undang masukan penguji terutama terkait desain gold standard, target terminologi, dan strategi evaluasi.
