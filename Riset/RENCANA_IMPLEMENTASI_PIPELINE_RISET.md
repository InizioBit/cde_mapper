# Rencana Implementasi Pipeline Riset

Dokumen ini merangkum rencana implementasi lanjutan untuk riset adaptasi CDE-Mapper pada pemetaan terminologi klinis Bahasa Indonesia. Rencana ini disusun dari baseline proyek pada `README.md`, isi folder `Riset`, dan struktur kode yang sudah tersedia di repositori.

## 1. Ringkasan Konteks

Baseline proyek adalah CDE-Mapper, yaitu pipeline pemetaan elemen data klinis ke controlled vocabulary berbasis Retrieval-Augmented Generation. Implementasi saat ini sudah mendukung:

- pemuatan data tabular atau query CDE melalui `rag/data_loader.py`;
- pembentukan indeks vektor Qdrant dengan dense dan sparse embedding melalui `rag/vector_index.py`;
- penggabungan retriever lokal dan Athena API melalui `CustomMergeRetriever`;
- filter domain dan vocabulary untuk OMOP, SNOMED, LOINC, UCUM, RxNorm, ATC, dan vocabulary lain;
- dekomposisi query CDE ke struktur `base_entity`, `domain`, `additional_entities`, `categories`, `unit`, `visit`, dan `method` melalui LLM;
- reranking kandidat menggunakan LLM dengan kategori relevansi;
- penyimpanan hasil tervalidasi ke reservoir lokal melalui `rag/sql.py`;
- evaluasi retrieval menggunakan accuracy@k, precision@k, recall@k, MRR, dan NCGD.

Rencana riset lanjutan pada `Riset/Alur Riset.tex`, diagram `Framework Usulan 09072026.png`, proposal disertasi, dan spreadsheet panduan NLP mengarah pada perluasan baseline menjadi pipeline Bahasa Indonesia untuk teks klinis panjang, multi-entitas, multi-terminologi, dan validasi human-in-the-loop.

## 2. Analisis Struktur Proyek

Repositori saat ini dapat dipetakan sebagai berikut:

- `run.py`: entry point eksperimen/inferensi baseline. File ini menginisialisasi embedding, sparse embedding, retriever Qdrant, Athena retriever, merger retriever, lalu memanggil `map_data`.
- `rag/`: inti pipeline CDE-Mapper.
  - `vector_index.py`: pembuatan/pembaruan indeks Qdrant, filter domain-vocabulary, dan integrasi Athena API.
  - `retriever.py`: orkestrasi pemetaan query, query decomposition, lookup reservoir, retrieval, reranking, dan penyusunan hasil.
  - `llm_chain.py`: prompt extraction, query decomposition, relationship extraction, LLM reranking, dan parsing JSON.
  - `py_model.py`: skema Pydantic untuk query decomposed, hasil retriever, dan hasil pemetaan.
  - `compress.py`, `embeddingfilter.py`: merger dan filtering berbasis embedding.
  - `utils.py`: utilitas dokumen, exact/fuzzy match, vocabulary selection, post-processing, CSV output, dan metrik evaluasi.
  - `sql.py`: reservoir lokal untuk pasangan entitas-kode yang sudah dipakai/tervalidasi.
- `evaluation/`: skrip evaluasi, visualisasi, uji signifikansi, dan evaluasi query decomposition.
- `data/`: dataset, vocabulary, template mapping, dan sumber evaluasi baseline.
- `Riset/`: artefak rancangan riset lanjutan.
  - `Alur Riset.tex`: narasi tujuh langkah framework adaptasi Bahasa Indonesia.
  - `Framework Usulan 09072026.png`: diagram end-to-end dari input teks klinis panjang sampai knowledge reservoir.
  - `Panduan_Komponen_NLP_Formatted.xlsx`: panduan awal komponen NLP untuk preprocessing dan ekstraksi entitas.
  - `Proposal Disertasi-Anie Rose Irawati.pdf`: proposal riset yang menekankan gap bahasa Indonesia, teks panjang, multi-standar, gold standard, ablation study, dan validasi ahli.

## 3. Baseline, Target Pipeline Usulan, dan Kebaruan

### 3.1 Baseline yang Sudah Ada

Baseline yang tersedia di repositori adalah adaptasi implementasi CDE-Mapper untuk pemetaan elemen data klinis ke controlled vocabulary. Baseline ini sudah memproses query dalam format data dictionary, bukan teks klinis panjang bebas. Tiap baris data diperlakukan sebagai satu query atau satu CDE yang kemudian didekomposisi, dicari kandidat standarnya, direrank, dan diekspor sebagai hasil mapping.

Komponen baseline yang sudah ada:

- `run.py` sebagai entry point inferensi dan eksperimen;
- `rag/data_loader.py` untuk membaca input query dari file tabular atau teks;
- `rag/py_model.py` dengan `QueryDecomposedModel` yang sudah memuat `base_entity`, `domain`, `categories`, `unit`, `formula`, `visit`, dan `additional_entities`;
- `rag/llm_chain.py` untuk query decomposition, prompt few-shot, parsing JSON, relationship extraction, dan LLM reranking;
- `rag/vector_index.py` untuk indeks Qdrant, dense retrieval, sparse retrieval, payload index, filter domain/vocabulary, serta integrasi Athena API;
- `rag/compress.py` dan `rag/embeddingfilter.py` untuk merger retriever dan filtering berbasis embedding;
- `rag/retriever.py` untuk orkestrasi lookup reservoir, retrieval kandidat, exact/fuzzy match, LLM reranking, dan penyusunan output;
- `rag/sql.py` sebagai reservoir lokal untuk pasangan entitas dan kode yang sudah ditemukan;
- `evaluation/` dan fungsi metrik di `rag/utils.py` untuk accuracy@k, precision@k, recall@k, MRR, dan NCGD.

Alur baseline secara ringkas:

1. Input berupa data dictionary atau query CDE.
2. Query dibaca dan diubah menjadi objek `QueryDecomposedModel`.
3. LLM melakukan dekomposisi query menjadi base entity, domain, unit, kategori, visit, dan additional entities.
4. Sistem mengecek reservoir lokal untuk entitas yang sudah pernah dipetakan.
5. Jika belum ada di reservoir, sistem menjalankan retrieval dari Qdrant dan Athena API.
6. Kandidat difilter berdasarkan domain/vocabulary dan exact/fuzzy match.
7. LLM melakukan reranking kandidat dan memberi skor relevansi.
8. Hasil final diekspor ke CSV/JSON serta dapat ditambahkan ke training examples/reservoir.

Batasan baseline:

- fokus utama masih pada CDE atau data dictionary per baris, belum pada ekstraksi multi-entitas dari teks klinis panjang;
- orientasi bahasa dan contoh prompt masih kuat pada bahasa Inggris;
- normalisasi Bahasa Indonesia, singkatan medis lokal, typo lokal, dan code-mixing belum menjadi komponen eksplisit;
- target terminology mengikuti OMOP/Athena vocabulary umum, belum diposisikan secara khusus untuk kebutuhan SATUSEHAT dan pemetaan simultan SNOMED CT, LOINC, ICD-10, dan UCUM;
- filtering domain dan vocabulary sudah ada, tetapi belum dilengkapi aturan klinis lokal yang eksplisit untuk Bahasa Indonesia;
- reservoir sudah ada, tetapi mekanisme human-in-the-loop dan status validasi ahli belum menjadi workflow riset utama;
- evaluasi sudah mendukung metrik retrieval, tetapi belum mencakup evaluasi ekstraksi entitas long-text, negasi, temporalitas, agreement ahli, coverage, dan efisiensi pipeline end-to-end.

### 3.2 Target Pipeline Usulan

Berdasarkan alur rencana riset di proposal dan `Riset/Alur Riset.tex`, pipeline usulan menargetkan framework adaptif untuk pemetaan terminologi klinis Bahasa Indonesia. Pipeline tidak hanya menerima satu CDE per baris, tetapi juga mampu menerima teks klinis panjang, mengekstrak banyak entitas klinis, menentukan terminologi target, lalu memetakan setiap entitas ke vocabulary standar yang relevan.

Target input:

- teks klinis panjang Bahasa Indonesia, misalnya catatan ringkas pasien, hasil pemeriksaan, atau narasi klinis;
- data dictionary lokal dengan kolom seperti label, categorical, unit, formula, visit, dan method;
- istilah klinis campuran Indonesia-Inggris, singkatan lokal, ejaan tidak baku, typo, dan satuan;
- hasil validasi ahli sebagai sumber pembaruan knowledge reservoir.

Target proses end-to-end:

1. Pra-pemrosesan dan normalisasi bahasa untuk membersihkan teks, melakukan segmentasi kalimat, memperluas singkatan medis lokal, memperbaiki typo, menstandarkan simbol/angka/satuan, dan menangani variasi ejaan.
2. Ekstraksi entitas klinis dari teks panjang menggunakan LLM, NER, atau kombinasi rule-based, sehingga satu dokumen dapat menghasilkan banyak entitas seperti diagnosis, laboratorium, tanda vital, obat, prosedur, unit, kunjungan, kategori, dan metode.
3. Klasifikasi tipe CDE dan penentuan terminologi target melalui mapping rules. Diagnosis/keluhan/temuan diarahkan ke SNOMED CT, diagnosis pelaporan ke ICD-10, laboratorium dan observasi ke LOINC, satuan ke UCUM, dan domain lain ke vocabulary pendukung.
4. Query decomposition untuk entitas komposit agar entitas seperti `gula darah puasa 126 mg/dL` dipecah menjadi base entity, domain, konteks puasa, unit, dan atribut lain.
5. Ensemble retrieval kandidat konsep menggunakan jalur leksikal, jalur semantik, API terminologi, sinonim lokal, dan lookup reservoir.
6. Filtering berbasis aturan dan threshold untuk mengeliminasi kandidat yang salah domain, salah vocabulary, tidak aktif, atau tidak sesuai konteks klinis.
7. Reranking dan keputusan akhir menggunakan LLM atau reranker, dengan label keputusan `exact`, `highly_relevant`, `partial`, atau `not_relevant`, confidence score, dan reasoning.
8. Validasi human-in-the-loop untuk hasil confidence rendah/menengah, lalu hasil validasi disimpan ke knowledge reservoir agar pemetaan berikutnya lebih konsisten.

Target output:

- daftar entitas klinis terstruktur dari tiap dokumen atau baris data dictionary;
- JSON entitas dengan `mention`, `base_entity`, `domain`, `associated_entities`, `categories`, `unit`, `visit`, `method`, `assertion`, `temporal`, dan `target_vocabularies`;
- kandidat Top-k per vocabulary target;
- kandidat final Top-1 dan Top-k dengan kode standar, label standar, vocabulary, domain, confidence score, dan alasan pemilihan;
- status validasi ahli dan provenance mapping;
- laporan evaluasi pipeline yang mencakup ekstraksi entitas, query decomposition, retrieval, mapping final, coverage, konsistensi, agreement, dan efisiensi.

Contoh target perilaku:

- Input `Px dgn DM tipe 2, GDP 126 mg/dL, TD 150/90` dinormalisasi menjadi `pasien dengan diabetes melitus tipe 2, gula darah puasa 126 mg/dL, tekanan darah 150/90`.
- Sistem mengekstrak tiga entitas utama: diabetes melitus tipe 2, gula darah puasa, dan tekanan darah.
- Diabetes melitus tipe 2 diarahkan ke SNOMED CT dan ICD-10; gula darah puasa diarahkan ke LOINC; tekanan darah diarahkan ke terminologi observasi/vital sign yang relevan.
- Kandidat final dipilih melalui retrieval, filtering konteks, reranking, dan validasi bila confidence belum tinggi.

### 3.3 Perbedaan, Kebaruan, dan Perbaikan Usulan

Perbedaan utama pipeline usulan dibanding baseline adalah perluasan dari pemetaan CDE berbahasa Inggris atau data dictionary terstruktur menjadi pipeline klinis Bahasa Indonesia yang dapat bekerja pada teks panjang, multi-entitas, dan multi-terminologi.

Kebaruan/perbaikan yang diusulkan:

- Dari single-query CDE menjadi long-text multi-entity extraction. Baseline memproses satu query per baris, sedangkan usulan mengekstrak banyak entitas dari satu teks klinis panjang.
- Dari pipeline berorientasi bahasa Inggris menjadi pipeline Bahasa Indonesia. Usulan menambahkan normalisasi Bahasa Indonesia, kamus singkatan medis lokal, koreksi typo/ejaan tidak baku, serta penanganan code-mixing.
- Dari query decomposition umum menjadi decomposition klinis lokal. Usulan memecah entitas komposit berdasarkan base entity, domain, unit, visit/context, method, kategori, negasi, dan temporalitas.
- Dari vocabulary mapping umum menjadi target multi-terminologi yang selaras dengan SATUSEHAT. Usulan mengarahkan entitas ke SNOMED CT, LOINC, ICD-10, UCUM, dan vocabulary pendukung sesuai aturan klinis.
- Dari retrieval hybrid baseline menjadi ensemble retrieval yang diperkaya lokal. Usulan menambahkan sinonim Indonesia, istilah lokal, lexical retriever, multilingual/clinical embedding, Athena/API search, dan reservoir lookup.
- Dari filter domain/vocabulary dasar menjadi filtering berbasis aturan klinis. Usulan menambahkan aturan seperti diagnosis tidak menerima kandidat lab, unit harus UCUM, ICD-10 hanya untuk diagnosis, dan lab harus sesuai spesimen/waktu/unit.
- Dari reranking kandidat menjadi keputusan akhir yang lebih auditable. Usulan menyimpan reasoning, confidence score, label exact/highly/partial/not relevant, serta Top-k untuk validasi dan analisis error.
- Dari reservoir teknis menjadi knowledge reservoir tervalidasi ahli. Usulan menambahkan human-in-the-loop, status validasi, provenance, dan mekanisme pembelajaran dari hasil validasi.
- Dari evaluasi retrieval-only menjadi evaluasi end-to-end. Usulan menilai entity extraction, query decomposition, retrieval, mapping final, coverage, agreement ahli, konsistensi, efisiensi, dan ablation study.

Implikasi kontribusi riset:

- kontribusi metodologis: framework adaptif hybrid LLM-semantic retrieval untuk terminologi klinis Bahasa Indonesia;
- kontribusi teknis: pipeline modular yang menggabungkan preprocessing lokal, entity extraction, mapping rules, query decomposition, ensemble retrieval, filtering, reranking, dan reservoir;
- kontribusi praktis: prototipe yang relevan untuk interoperabilitas SATUSEHAT dan standardisasi istilah klinis lokal;
- kontribusi evaluatif: rancangan gold standard, ablation study, dan metrik end-to-end untuk menilai manfaat setiap komponen.

## 4. Tahap Implementasi

### Tahap 0 - Audit Baseline dan Reproducibility

Tujuan: memastikan baseline berjalan konsisten sebelum adaptasi Bahasa Indonesia.

Pekerjaan:

- rapikan command eksperimen di `README.md` agar sesuai entry point saat ini (`run.py` dan parameter `--flag`, `--input_file`, `--document_file_path`);
- buat konfigurasi eksperimen versi lokal, misalnya `configs/baseline.yaml`;
- dokumentasikan dependency aktual dari `pyproject.toml`;
- jalankan smoke test kecil pada dataset yang sudah ada;
- catat baseline metrik: accuracy@1/3/5/10, precision@k, recall@k, MRR, NCGD, coverage, latency per query.

Keluaran:

- baseline report;
- script reproducible untuk menjalankan indexing dan inference;
- daftar gap teknis yang harus diperbaiki sebelum adaptasi.

Status implementasi Tahap 0:

- konfigurasi baseline dibuat di `configs/baseline.yaml`;
- input smoke test dibuat di `data/input/baseline_smoke.csv`;
- smoke audit dibuat di `scripts/baseline_smoke.py`;
- wrapper WSL conda env `cde-mapper` dibuat di `scripts/audit_baseline_wsl.sh`;
- laporan baseline dibuat di `Riset/LAPORAN_BASELINE.md`;
- hasil audit runtime disimpan di `Riset/baseline_audit_result.json`.
- audit integrasi online Qdrant, Athena, dan Together dibuat di `scripts/audit_baseline_integration.py`;
- gold subset retrieval 10 query dibuat di `data/gold/baseline_retrieval_gold.jsonl`;
- runner hybrid dense-sparse reproducible dibuat di `scripts/baseline_experiment.py`;
- reranking full inference Gemma dibuat di `scripts/baseline_llm_rerank.py`;
- evaluator artefak Top-k dibuat di `evaluation/baseline_retrieval_eval.py`;
- dependency snapshot aktual disimpan di `configs/cde-mapper-environment.json`;
- metrik retrieval dan reranking disimpan di `Riset/baseline_metrics.json` dan `Riset/baseline_reranked_metrics.json`;
- Athena mengembalikan HTTP 403 pada audit 10 Juli 2026; kegagalan sumber ini dicatat eksplisit dan tidak menggagalkan fallback hybrid Qdrant.

### Tahap 1 - Normalisasi Bahasa Indonesia

Tujuan: mengubah teks klinis Bahasa Indonesia mentah menjadi teks bersih dan standar.

Urutan pekerjaan yang diperbaiki:

1. Profilkan korpus secara terpisah untuk `question` dan `answer`. Inventarisasi singkatan, bentuk informal, typo, angka, dosis, satuan, nama obat, negasi, serta boilerplate. Pertanyaan memakai profil normalisasi lebih aktif; jawaban dokter memakai profil konservatif.
2. Tetapkan kontrak keluaran yang mempertahankan `raw_text`, menghasilkan `normalized_text`, dan mencatat `normalization_changes`, `warnings`, serta versi kamus. Perubahan harus idempotent dan dapat diaudit.
3. Bangun kamus master berlapis **sebelum ekspansi singkatan diaktifkan**. Lapisan minimal mencakup singkatan klinis, kesehatan ibu-anak, fungsi tubuh/pengukuran, dokumentasi klinis, dan percakapan informal. Setiap entri memuat bentuk singkat, ekspansi, status (`automatic`, `context_required`, atau `review_required`), konteks, dan peringatan ambiguitas.
4. Turunkan kamus runtime hanya dari entri yang aman. Entri ambigu seperti `dr` (`dari`/`dokter`), `mg` (`miligram`/`minggu`), `TB` (`tinggi badan`/`tuberkulosis`), `BB`, dan `Px` tidak boleh diperluas otomatis tanpa aturan konteks. Kamus master disimpan di `data/input/id_abbreviations_layered.json`, sedangkan kamus runtime kompatibel disimpan di `data/input/id_abbreviations.json`.
5. Lakukan validasi kamus dalam dua tahap: validasi berbasis korpus untuk frekuensi dan contoh pemakaian, kemudian validasi ahli bahasa/klinisi untuk ekspansi dan ambiguitas. Entri baru masuk sebagai `review_required` dan baru dipromosikan setelah validasi.
6. Implementasikan pembersihan konservatif dengan Regex dan opsi `text-normalization`: normalisasi Unicode, spasi, karakter kontrol, serta tanda baca berulang. Jangan menghapus angka, desimal, rentang, dosis, satuan, negasi, atau nama obat.
7. Lindungi token klinis sebelum koreksi, termasuk nama obat, kode, angka, satuan, singkatan kapital, dan istilah campuran Indonesia-Inggris. Setelah itu lakukan normalisasi informal serta koreksi typo berbasis kamus. Fuzzy matching hanya menghasilkan kandidat jika confidence rendah dan tidak boleh langsung mengubah istilah klinis.
8. Normalisasi angka dan satuan secara terpisah, misalnya `500mg -> 500 mg`, sambil menjaga nilai, rentang waktu, frekuensi, rasio tekanan darah, dan pemisah desimal.
9. Lakukan segmentasi kalimat menggunakan `indo_text_segmentation` atau fallback rule-based setelah cleaning ringan dan ekspansi yang diperlukan untuk memperjelas batas kalimat.
10. Tandai sapaan dan penutup jawaban sebagai boilerplate. Simpan teks lengkap untuk audit dan buat representasi tanpa boilerplate hanya untuk proses downstream; jangan menghapus negasi, ketidakpastian, atau diagnosis banding.
11. Evaluasi Sastrawi sebagai fitur eksperimen untuk lexical retrieval, bukan transformasi default `normalized_text`, karena stemming dapat merusak istilah klinis dan label terminologi.
12. Bentuk gold set terstratifikasi dan ukur abbreviation expansion accuracy, typo recovery rate, sentence-boundary F1, exact normalized match, serta preservation rate untuk angka, unit, obat, negasi, dan temporalitas. Lakukan error analysis per jenis transformasi.

Integrasi kode:

- sebelum `load_data` masuk ke `map_data`;
- atau sebagai transformasi awal pada `QueryDecomposedModel.full_query`.

Keluaran:

- modul normalisasi;
- kamus master singkatan berlapis beserta status validasi dan provenance;
- kamus runtime berisi ekspansi yang aman;
- daftar singkatan ambigu dan aturan konteks;
- kamus typo, bentuk informal, sinonim lokal, dan satuan;
- dataset uji kecil berisi input-output normalisasi;
- audit trail perubahan per teks;
- metrik intrinsic: exact normalized match, abbreviation expansion accuracy, typo recovery rate, sentence-boundary F1, clinical-information preservation rate, dan error analysis.

Status implementasi Tahap 1:

- modul normalisasi deterministik berprofil `clinical`, `question`, dan `answer` dibuat di `rag/id_preprocess.py`;
- kamus awal singkatan medis lokal dibuat di `data/input/id_abbreviations.json`;
- kamus master berlapis dengan metadata, status, konteks, ambiguitas, dan provenance dibuat di `data/input/id_abbreviations_layered.json`;
- kamus koreksi typo/ejaan tidak baku dibuat di `data/input/id_typos.json`;
- kamus normalisasi satuan dibuat di `data/input/id_units.json`;
- dataset uji kecil input-output normalisasi dibuat di `data/gold/id_normalization_gold.jsonl`;
- cleaning Unicode, tanda baca, spasi, preservasi desimal, normalisasi satuan, dan segmentasi kalimat deterministik sudah diimplementasikan;
- ekspansi singkatan `automatic` dan `context_required` sudah dibedakan; singkatan ambigu dipertahankan beserta warning ketika konteks tidak cukup;
- audit trail mencatat langkah, perubahan token, jumlah penggantian, warning, boilerplate, versi normalizer, dan versi resource;
- sapaan dan penutup jawaban ditandai sebagai boilerplate tanpa menghapus teks lengkap;
- integrasi opt-in ke entry point tersedia melalui `--normalize_id`, `--normalization_profile`, dan `--normalization_resource_dir`;
- runner korpus Alodokter dibuat di `scripts/preprocess_alodokter.py`;
- artefak 150 pasangan hasil normalisasi dibuat di `Riset/crawler_alodokter/hasil_normalisasi_tahap_1.jsonl`;
- tujuh unit test preservasi dan perilaku normalizer dibuat di `tests/test_id_preprocess.py`;
- audit intrinsic dibuat di `scripts/audit_id_preprocess.py`;
- wrapper WSL conda env `cde-mapper` dibuat di `scripts/audit_id_preprocess_wsl.sh`;
- laporan Tahap 1 dibuat di `Riset/LAPORAN_TAHAP_1_NORMALISASI.md`;
- hasil audit runtime disimpan di `Riset/id_preprocess_audit_result.json`.

### Tahap 2 - Ekstraksi Entitas Klinis dari Teks Panjang

Tujuan: memperluas baseline dari satu CDE per baris menjadi banyak entitas dari satu dokumen klinis.

Pekerjaan:

- buat modul `rag/id_entity_extraction.py`;
- definisikan skema JSON multi-entitas:

```json
{
  "document_id": "string",
  "entities": [
    {
      "mention": "string",
      "base_entity": "string",
      "domain": "condition|measurement|observation|drug|procedure|unit|visit|all",
      "associated_entities": [],
      "categories": [],
      "unit": "string|null",
      "visit": "string|null",
      "method": "string|null",
      "assertion": "present|negated|uncertain",
      "temporal": "present|past|future|unknown"
    }
  ]
}
```

- gunakan prompt LLM few-shot untuk ekstraksi entitas diagnosis, lab, tanda vital, obat, prosedur, unit, dan konteks kunjungan;
- tambahkan rule sederhana untuk negasi (`tidak`, `tanpa`, `bukan`) dan temporal (`sebelumnya`, `dulu`, `kini`, `saat ini`);
- siapkan fallback NER/rule-based jika LLM gagal menghasilkan JSON valid;
- tambahkan validasi Pydantic agar output ekstraksi aman diproses downstream.

Integrasi kode:

- perluasan `QueryDecomposedModel` atau model baru `ClinicalEntityModel`;
- fungsi adapter yang mengubah output multi-entitas menjadi list query untuk `map_data`.

Keluaran:

- ekstraktor multi-entitas;
- prompt dan contoh few-shot Bahasa Indonesia;
- evaluasi entity extraction: precision, recall, F1, assertion accuracy, temporal accuracy.

### Tahap 3 - Mapping Rules dan Pemilihan Terminologi Target

Tujuan: menentukan domain dan vocabulary target berdasarkan konteks SATUSEHAT dan tipe entitas.

Pekerjaan:

- buat konfigurasi rules, misalnya `data/input/id_mapping_rules.json`;
- definisikan mapping awal:
  - diagnosis, keluhan, temuan klinis -> SNOMED CT;
  - diagnosis untuk pelaporan statistik -> ICD-10;
  - pemeriksaan lab dan observasi -> LOINC;
  - satuan -> UCUM;
  - obat -> RxNorm, ATC, atau vocabulary lokal bila tersedia;
  - prosedur -> SNOMED CT atau vocabulary prosedur yang relevan;
- perluas `select_vocabulary` di `rag/utils.py` atau buat adapter khusus Bahasa Indonesia;
- implementasikan fallback broader match jika tidak ada kandidat spesifik;
- tambahkan flag `target_vocabularies` agar satu entitas dapat dipetakan ke lebih dari satu vocabulary, misalnya SNOMED CT dan ICD-10.

Keluaran:

- file rules yang dapat dikonfigurasi;
- unit test rules untuk contoh umum;
- tabel cakupan rules per domain.

### Tahap 4 - Query Decomposition untuk Entitas Komposit

Tujuan: memecah entitas kompleks agar retrieval tidak terlalu umum.

Pekerjaan:

- adaptasi `extract_information` di `rag/llm_chain.py` untuk Bahasa Indonesia;
- perkuat skema `QueryDecomposedModel` dengan `method`, `assertion`, `temporal`, dan `target_vocabularies`;
- buat prompt dekomposisi khusus:
  - `gula darah puasa 126 mg/dL` -> base entity `glukosa`, domain `measurement`, visit/context `puasa`, unit `mg/dL`;
  - `DM tipe 2` -> base entity `diabetes melitus`, additional entity `tipe 2`;
  - `TD 150/90` -> base entity `tekanan darah`, unit `mmHg`, kategori/komponen sistolik-diastolik jika perlu;
- buat evaluasi query decomposition menggunakan pola `evaluation/QD_eval.py`.

Keluaran:

- prompt decomposition Bahasa Indonesia;
- dataset gold query decomposition;
- metrik per field: base entity accuracy, domain accuracy, unit F1, category F1, visit F1.

### Tahap 5 - Knowledge Base dan Ensemble Retrieval

Tujuan: menghasilkan kandidat konsep Top-k dari jalur leksikal dan semantik.

Pekerjaan:

- siapkan dokumen terminologi terindeks dengan metadata lengkap: label, synonyms, vocabulary, domain, standard concept, concept class, active/validity;
- tambah sinonim Bahasa Indonesia dan istilah lokal pada dokumen indeks;
- pertahankan Qdrant dense retrieval dan sparse retrieval yang sudah tersedia;
- evaluasi embedding:
  - baseline SapBERT/biomedical embedding saat ini;
  - multilingual embedding;
  - embedding yang di-fine-tune pada pasangan istilah Indonesia-Inggris bila data tersedia;
- tambahkan lexical retriever lokal berbasis BM25/rapidfuzz untuk ejaan lokal dan singkatan;
- implementasikan weighted reciprocal rank atau merger yang eksplisit untuk dense, sparse, API, dan reservoir lookup.

Integrasi kode:

- `rag/vector_index.py` untuk indeks dan filter;
- `rag/compress.py` untuk merger;
- `rag/athena_api_retriever.py` untuk kandidat Athena;
- `rag/sql.py` untuk reservoir lookup sebelum retrieval.

Keluaran:

- indeks terminologi dengan sinonim Indonesia;
- retriever ensemble yang dapat dikonfigurasi bobotnya;
- laporan retrieval-only Top-k.

### Tahap 6 - Filtering Berbasis Rules dan Threshold

Tujuan: mengurangi kandidat yang salah domain, vocabulary, atau konteks.

Pekerjaan:

- perluas `update_qdrant_search_filter` dan `update_api_search_filter` untuk rules Bahasa Indonesia dan target SATUSEHAT;
- tambahkan filter semantic type:
  - diagnosis tidak menerima konsep lab;
  - lab glukosa puasa tidak menerima glukosa urin atau glukosa sewaktu jika konteks/unit tidak cocok;
  - ICD-10 hanya dipakai untuk diagnosis/klasifikasi;
  - unit hanya menerima UCUM;
- tambahkan threshold per domain karena lab, diagnosis, obat, dan unit punya distribusi skor berbeda;
- simpan alasan eliminasi kandidat untuk audit.

Keluaran:

- modul/domain filter yang deterministik;
- log kandidat sebelum dan sesudah filter;
- metrik pengaruh filtering terhadap recall@k dan precision@k.

### Tahap 7 - Reranking dan Keputusan Akhir

Tujuan: memilih kandidat final dengan mempertimbangkan label, sinonim, definisi, domain, unit, dan konteks dokumen.

Pekerjaan:

- adaptasi `pass_to_chat_llm_chain` untuk prompt Bahasa Indonesia;
- tambah format keluaran reranking:

```json
{
  "candidate_id": "string",
  "candidate_label": "string",
  "relationship": "exact|highly_relevant|partial|not_relevant",
  "score": 0.0,
  "reasoning": "string"
}
```

- gunakan self-consistency untuk kasus confidence rendah atau kandidat berdekatan;
- coba cross-encoder reranker sebagai varian non-LLM;
- simpan Top-1 dan Top-k, bukan hanya kandidat final, untuk evaluasi dan validasi ahli.

Keluaran:

- reranker Bahasa Indonesia;
- confidence calibration;
- laporan error kategori exact/highly/partial/not relevant.

### Tahap 8 - Human-in-the-Loop dan Knowledge Reservoir

Tujuan: membuat hasil validasi ahli menjadi memori sistem yang meningkatkan konsistensi pemetaan berikutnya.

Pekerjaan:

- rapikan skema reservoir agar menyimpan:
  - mention asli;
  - normalized mention;
  - base entity;
  - domain;
  - vocabulary;
  - code/concept id;
  - label standar;
  - context;
  - validator;
  - status validasi;
  - timestamp;
- ubah alur inferensi agar lookup reservoir dilakukan sebelum retrieval;
- hasil confidence rendah diarahkan ke antrean validasi;
- hasil validasi masuk kembali ke `mapping_templates.json` atau database training examples dengan kontrol versi.

Keluaran:

- reservoir tervalidasi;
- format ekspor validasi ahli;
- ukuran pertumbuhan reservoir dan reuse rate.

### Tahap 9 - Evaluasi, Ablation Study, dan Analisis

Tujuan: membuktikan kontribusi setiap komponen pipeline.

Dataset:

- dataset benchmark baseline yang sudah ada di `data/eval_datasets`;
- data dictionary klinis Bahasa Indonesia;
- teks klinis panjang sintetis/sekunder yang dianotasi;
- gold standard pemetaan oleh ahli untuk SNOMED CT, LOINC, ICD-10, dan UCUM.

Skenario eksperimen:

- baseline CDE-Mapper tanpa adaptasi Bahasa Indonesia;
- + normalisasi;
- + entity extraction long-text;
- + mapping rules SATUSEHAT;
- + query decomposition Bahasa Indonesia;
- + sinonim lokal;
- + ensemble retrieval;
- + filtering;
- + LLM reranking;
- + reservoir.

Metrik:

- entity extraction: precision, recall, F1, assertion accuracy, temporal accuracy;
- query decomposition: field-level precision/recall/F1;
- retrieval: recall@k, precision@k, MRR, NCGD, accuracy@k;
- mapping final: accuracy, precision, recall, F1, coverage;
- validasi ahli: agreement/Kappa jika tersedia;
- efisiensi: latency, token cost, jumlah API call, memory/index size;
- konsistensi: stabilitas hasil antar run dan reuse dari reservoir.

Keluaran:

- tabel ablation study;
- grafik hasil;
- error analysis per domain dan vocabulary;
- rekomendasi threshold dan konfigurasi final.

## 5. Prioritas Implementasi Praktis

Urutan yang disarankan agar risiko teknis terkendali:

1. Audit baseline dan buat smoke test.
2. Buat normalisasi Bahasa Indonesia dan kamus singkatan.
3. Buat skema multi-entitas dan adapter ke pipeline CDE-Mapper saat ini.
4. Implementasi mapping rules SATUSEHAT dan target vocabulary.
5. Adaptasi prompt query decomposition dan reranking ke Bahasa Indonesia.
6. Tambah sinonim Indonesia ke indeks dan evaluasi retrieval-only.
7. Tambah filtering domain/vocabulary/context.
8. Aktifkan reservoir validasi ahli.
9. Jalankan ablation study lengkap.

## 6. Risiko dan Mitigasi

- Data gold standard Bahasa Indonesia terbatas: mulai dari subset kecil terkurasi, gunakan active learning untuk memilih kasus validasi paling informatif.
- LLM tidak konsisten menghasilkan JSON: gunakan Pydantic validation, output fixing parser, retry terbatas, dan fallback rule-based.
- Istilah klinis campuran Indonesia-Inggris: gunakan normalisasi dua arah dan sinonim lokal dalam indeks.
- Stemming dapat merusak istilah medis: jadikan stemming opsional dan hanya setelah evaluasi error.
- Retrieval terlalu luas untuk entitas pendek: gunakan mapping rules, domain filter, dan reservoir exact match.
- Biaya reranking LLM tinggi: jalankan LLM hanya setelah filtering Top-k, gunakan cross-encoder lokal sebagai varian, dan cache hasil.
- Reservoir bisa menyimpan pemetaan salah: semua entri perlu status validasi dan provenance.

## 7. Artefak yang Perlu Dibuat

- `rag/id_preprocess.py`
- `rag/id_entity_extraction.py`
- `rag/id_mapping_rules.py` atau perluasan `rag/utils.py`
- `data/input/id_abbreviations.json`
- `data/input/id_mapping_rules.json`
- `data/input/id_synonyms.jsonl`
- `data/gold/id_entity_extraction_gold.jsonl`
- `data/gold/id_query_decomposition_gold.jsonl`
- `data/gold/id_mapping_gold.jsonl`
- `evaluation/id_entity_eval.py`
- `evaluation/id_pipeline_eval.py`
- `configs/id_pipeline.yaml`
- `Riset/LAPORAN_BASELINE.md`
- `Riset/LAPORAN_ABLATION_STUDY.md`

## 8. Definisi Selesai

Pipeline riset dianggap siap untuk eksperimen utama jika:

- input teks klinis Bahasa Indonesia dapat diproses menjadi banyak entitas terstruktur;
- setiap entitas mendapat target vocabulary berdasarkan rules;
- kandidat Top-k dapat dihasilkan dari ensemble retrieval;
- kandidat dapat difilter, direrank, dan diberi confidence score;
- hasil confidence rendah dapat diekspor untuk validasi ahli;
- hasil validasi masuk ke reservoir dan dipakai pada inferensi berikutnya;
- eksperimen baseline dan ablation study dapat dijalankan ulang dengan konfigurasi yang sama;
- semua metrik utama tersedia dalam laporan evaluasi.
