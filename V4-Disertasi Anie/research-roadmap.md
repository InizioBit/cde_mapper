# Research Roadmap: Proposal Research Canvas

## 1. Identitas Riset

| Elemen | Isi |
| --- | --- |
| Judul kerja | Adaptasi CDE-Mapper untuk Pemetaan Terminologi Klinis Bahasa Indonesia: Pendekatan Hybrid Berbasis LLM dan Semantic Retrieval |
| Domain | Informatika kesehatan, interoperabilitas data klinis, clinical terminology mapping |
| Konteks implementasi | Transformasi digital kesehatan Indonesia dan ekosistem SATUSEHAT |
| Terminologi target | SNOMED CT, LOINC, ICD-10 |
| Unit analisis | Istilah klinis dan dokumen klinis berbahasa Indonesia, termasuk teks panjang rekam medis |

## 2. Latar Belakang dan Fenomena

Transformasi digital kesehatan di Indonesia membutuhkan interoperabilitas data yang tidak hanya memungkinkan pertukaran informasi, tetapi juga menjamin kesetaraan makna klinis antar sistem. Dalam praktiknya, data klinis Indonesia masih muncul dalam format yang heterogen, terminologi lokal, singkatan, variasi ejaan, campuran bahasa, dan teks naratif panjang sehingga sulit langsung dipetakan ke standar internasional seperti SNOMED CT, LOINC, dan ICD-10.

SATUSEHAT telah mengarahkan penggunaan FHIR dan terminologi standar, tetapi kesenjangan antara kebijakan interoperabilitas dan kondisi dokumentasi klinis di lapangan masih besar. Karena itu, pemetaan terminologi klinis Bahasa Indonesia menjadi kebutuhan strategis agar data kesehatan nasional dapat dipertukarkan, dipahami, dan dimanfaatkan secara konsisten.

## 3. Masalah Inti

1. Interoperabilitas melalui SATUSEHAT membutuhkan pemetaan otomatis lintas standar, tetapi mayoritas penelitian masih berfokus pada satu terminologi, terutama SNOMED CT.
2. CDE-Mapper efektif untuk elemen data klinis spesifik, tetapi belum dirancang untuk menangani teks klinis panjang yang berisi banyak entitas dalam satu dokumen.
3. Pendekatan yang ada umumnya dikembangkan dan diuji pada bahasa Inggris, sehingga belum sepenuhnya sesuai dengan karakteristik linguistik, variasi istilah lokal, dan keterbatasan sumber daya terminologi Bahasa Indonesia.

## 4. Research Gap

| Jenis Gap | Kondisi Literatur / Praktik | Dampak | Arah Solusi |
| --- | --- | --- | --- |
| Gap metodologis | Rule-based transparan tetapi kurang fleksibel; ML/DL butuh data besar; LLM/RAG kuat tetapi perlu kontrol retrieval dan validasi | Belum ada pendekatan yang sekaligus akurat, efisien, dan robust untuk teks klinis heterogen | Mengadaptasi CDE-Mapper dengan long-text entity extraction, retrieval ensemble, filtering, reranking, dan confidence selection |
| Gap cakupan | Banyak studi hanya menargetkan SNOMED CT atau item data pendek | Tidak memenuhi kebutuhan pemetaan simultan SNOMED CT, LOINC, dan ICD-10 | Membangun pipeline multi-standar dalam satu framework terpadu |
| Gap konteks | Bahasa Indonesia bersifat low-resource, banyak singkatan, variasi lokal, dan dokumentasi tidak standar | Model bahasa dominan atau berbahasa Inggris dapat menurun performanya ketika diterapkan pada data lokal | Menyesuaikan preprocessing, knowledge base, sinonim lokal, dan evaluasi berbasis gold standard Bahasa Indonesia |

## 5. Pertanyaan Penelitian

1. Bagaimana memodifikasi arsitektur CDE-Mapper agar mampu melakukan pemetaan simultan istilah klinis Bahasa Indonesia ke SNOMED CT, LOINC, dan ICD-10?
2. Bagaimana mengintegrasikan modul long-text entity extraction berbasis LLM agar sistem mampu mengenali banyak entitas klinis dari dokumen rekam medis panjang?
3. Bagaimana membangun retrieval ensemble yang sesuai dengan karakteristik Bahasa Indonesia, variasi istilah lokal, dan keterbatasan terminologi klinis nasional?

## 6. Tujuan Penelitian

### Tujuan Umum

Mengembangkan dan mengevaluasi framework adaptif untuk pemetaan terminologi klinis Bahasa Indonesia ke kosakata terkendali standar guna mendukung interoperabilitas data kesehatan nasional.

### Tujuan Khusus

1. Memodifikasi arsitektur CDE-Mapper untuk pemetaan simultan ke SNOMED CT, LOINC, dan ICD-10.
2. Mengintegrasikan modul long-text entity extraction berbasis LLM untuk pengenalan entitas klinis dari teks panjang.
3. Membangun retrieval ensemble yang mampu memproses variasi istilah klinis Bahasa Indonesia.
4. Mengevaluasi performa framework terhadap baseline dan varian ablation study.

## 7. Proposisi Solusi

Penelitian mengusulkan framework hybrid yang mengadaptasi CDE-Mapper dengan tiga pengembangan utama:

1. Long-text entity extraction untuk memecah dokumen klinis panjang menjadi entitas atau Clinical Data Elements yang dapat dipetakan.
2. Retrieval ensemble untuk mengambil kandidat konsep dari knowledge base SNOMED CT, LOINC, dan ICD-10 dengan memanfaatkan kombinasi pendekatan semantik dan leksikal.
3. Filtering, reranking, dan confidence selection untuk memilih kandidat kode yang paling relevan serta menandai kasus yang memerlukan validasi manual.

## 8. Kerangka Konseptual

```text
Dokumen / istilah klinis Bahasa Indonesia
        ↓
Preprocessing bahasa Indonesia
(case folding, normalisasi singkatan, variasi ejaan, istilah lokal)
        ↓
Long-text entity extraction / NER berbasis LLM
        ↓
Decomposition menjadi CDE / entitas klinis
        ↓
Retrieval ensemble terhadap SNOMED CT, LOINC, ICD-10
        ↓
Filtering + reranking + confidence selection
        ↓
Kode terminologi standar + skor keyakinan + kandidat validasi ahli
```

## 9. Metode Penelitian

| Komponen | Rancangan |
| --- | --- |
| Jenis penelitian | Penelitian pengembangan dengan pendekatan kuantitatif-eksperimental |
| Strategi utama | Adaptasi dan evaluasi framework CDE-Mapper untuk Bahasa Indonesia dan teks panjang |
| Data | Istilah klinis dan dokumen klinis berbahasa Indonesia dari sumber sekunder, korpus/dataset anotasi, dan sumber yang telah dianonimkan |
| Terminologi target | SNOMED CT, LOINC, ICD-10 |
| Gold standard | Anotasi manual oleh ahli klinis atau perekam medis untuk pasangan entitas-kode standar |
| Eksperimen | Perbandingan baseline, model usulan, dan varian ablation study |
| Analisis | Evaluasi kuantitatif performa mapping, error analysis, dan analisis kontribusi tiap modul |

## 10. Desain Pipeline Eksperimen

1. Mengumpulkan dan menyiapkan dataset istilah serta dokumen klinis Bahasa Indonesia.
2. Menyusun kamus singkatan, variasi ejaan, sinonim lokal, dan knowledge base terminologi target.
3. Membuat gold standard pemetaan melalui anotasi ahli.
4. Mengimplementasikan preprocessing Bahasa Indonesia.
5. Mengintegrasikan long-text entity extraction berbasis LLM.
6. Menjalankan retrieval ensemble untuk SNOMED CT, LOINC, dan ICD-10.
7. Melakukan filtering, reranking, dan confidence selection.
8. Membandingkan hasil dengan baseline dan varian ablation.
9. Melakukan error analysis untuk mengidentifikasi kesalahan ekstraksi, retrieval, reranking, terminologi, dan bahasa.

## 11. Baseline dan Ablation Study

| Skenario | Tujuan |
| --- | --- |
| Rule-based / lexical matching | Mengukur performa dasar berbasis kesamaan leksikal dan kamus |
| Retrieval tunggal | Mengukur kontribusi setiap retriever secara individual |
| CDE-Mapper teradaptasi minimal | Menguji performa arsitektur dasar pada data Bahasa Indonesia |
| Tanpa long-text entity extraction | Mengukur dampak modul ekstraksi teks panjang |
| Tanpa reranking | Mengukur dampak reranking terhadap pemilihan kandidat akhir |
| Framework lengkap | Mengukur performa akhir solusi yang diusulkan |

## 12. Metrik Evaluasi

| Metrik | Fungsi |
| --- | --- |
| Accuracy@k / Top-k accuracy | Menilai apakah kode benar muncul dalam daftar kandidat teratas |
| Precision | Mengukur ketepatan hasil ekstraksi dan mapping |
| Recall | Mengukur kelengkapan entitas atau kode yang berhasil ditemukan |
| F1-score | Mengukur keseimbangan precision dan recall |
| Coverage | Mengukur proporsi input yang berhasil diberi kandidat kode valid |
| Agreement / Kappa | Mengukur konsistensi anotasi ahli dan validitas gold standard |
| Consistency | Mengukur kestabilan hasil sistem pada input yang serupa |
| Efisiensi | Mengukur waktu inferensi dan kelayakan komputasi |

## 13. Luaran yang Diharapkan

1. Framework adaptif untuk pemetaan terminologi klinis Bahasa Indonesia ke SNOMED CT, LOINC, dan ICD-10.
2. Prototipe pipeline yang mampu memproses teks klinis panjang dan menghasilkan kandidat kode standar.
3. Dataset atau gold standard pemetaan terminologi klinis Bahasa Indonesia yang tervalidasi ahli.
4. Evaluasi empiris atas kontribusi modul long-text entity extraction, retrieval ensemble, filtering, dan reranking.
5. Rekomendasi teknis untuk standardisasi data klinis nasional dan implementasi interoperabilitas SATUSEHAT.

## 14. Kontribusi Penelitian

| Aspek | Kontribusi |
| --- | --- |
| Teoretis | Memperluas kajian clinical terminology mapping untuk bahasa non-Inggris, teks panjang, dan pemetaan multi-standar |
| Metodologis | Mengusulkan integrasi LLM, semantic retrieval, long-text NER, dan reranking dalam satu framework adaptif |
| Praktis | Mendukung standardisasi data klinis Indonesia agar dapat digunakan dalam interoperabilitas nasional |
| Kebijakan | Memberikan dasar teknis bagi implementasi SATUSEHAT yang lebih inklusif dan kontekstual |

## 15. Risiko dan Mitigasi

| Risiko | Dampak | Mitigasi |
| --- | --- | --- |
| Data klinis terbatas atau sensitif | Dataset tidak cukup representatif | Menggunakan data anonim, sumber sekunder, dan validasi ahli pada sampel terpilih |
| Variasi bahasa klinis sangat luas | Retrieval dan mapping menurun | Memperkaya kamus sinonim, singkatan, variasi ejaan, dan istilah lokal |
| LLM menghasilkan ekstraksi kurang stabil | Error propagation ke tahap mapping | Menggunakan filtering, confidence threshold, reranking, dan validasi manual untuk kasus rendah keyakinan |
| Gold standard sulit dibuat | Evaluasi menjadi kurang kuat | Melibatkan ahli klinis/perekam medis dan mengukur inter-annotator agreement |
| Komputasi mahal | Sulit diterapkan pada fasilitas rendah sumber daya | Mengutamakan retrieval ensemble dan model yang lebih ringan dibanding full LLM inference di semua tahap |

## 16. Roadmap Penelitian

| Fase | Fokus | Aktivitas Utama | Luaran |
| --- | --- | --- | --- |
| Fase 1 | Persiapan dan analisis | Studi literatur, analisis SATUSEHAT, identifikasi terminologi target, desain dataset | Kerangka konseptual dan spesifikasi kebutuhan |
| Fase 2 | Dataset dan gold standard | Pengumpulan data, preprocessing awal, anotasi ahli, pengukuran agreement | Dataset uji dan gold standard |
| Fase 3 | Pengembangan model | Adaptasi CDE-Mapper, long-text extraction, retrieval ensemble, filtering, reranking | Prototipe framework |
| Fase 4 | Eksperimen dan evaluasi | Baseline comparison, ablation study, penghitungan metrik, error analysis | Hasil evaluasi kuantitatif dan analisis kesalahan |
| Fase 5 | Dokumentasi dan diseminasi | Penyusunan laporan, rekomendasi implementasi, publikasi ilmiah | Disertasi, artikel, dan rekomendasi teknis |

## 17. Indikator Keberhasilan

1. Framework mampu menerima teks klinis Bahasa Indonesia dan menghasilkan kandidat kode SNOMED CT, LOINC, dan ICD-10.
2. Model usulan menunjukkan peningkatan terhadap baseline pada metrik accuracy@k, F1-score, coverage, atau efisiensi.
3. Ablation study menunjukkan kontribusi nyata dari modul long-text extraction, retrieval ensemble, dan reranking.
4. Gold standard memiliki tingkat kesepakatan antar-anotator yang memadai.
5. Error analysis menghasilkan rekomendasi perbaikan untuk penerapan di konteks SATUSEHAT.

## 18. Ringkasan Nilai Strategis

Penelitian ini menempatkan pemetaan terminologi klinis Bahasa Indonesia sebagai fondasi penting untuk interoperabilitas semantik data kesehatan nasional. Dengan mengadaptasi CDE-Mapper ke konteks lokal, mengintegrasikan long-text entity extraction, dan memperluas pemetaan ke SNOMED CT, LOINC, serta ICD-10, penelitian ini diharapkan menjadi blueprint bagi pengembangan sistem standardisasi data klinis pada lingkungan berbahasa Indonesia dan wilayah low-resource dengan tantangan serupa.