# Peran Terminologi Klinis dan Mesin Vector dalam Pipeline Riset

## 1. Posisi Kedua Komponen

Pipeline pemetaan terminologi klinis memerlukan dua lapisan yang berbeda tetapi saling melengkapi:

1. **Sumber terminologi** menentukan konsep standar yang tersedia, identitasnya, serta aturan klinis yang melekat pada konsep tersebut.
2. **Mesin retrieval** menemukan kandidat konsep yang paling relevan dari ruang terminologi yang besar.

Dalam baseline saat ini, fungsi tersebut dijalankan oleh terminologi berstruktur OMOP dan Qdrant. Athena digunakan sebagai sumber kandidat terminologi eksternal, sedangkan Qdrant menyimpan dense dan sparse vector untuk pencarian kandidat.

```text
Terminologi OMOP                    Mesin retrieval
"konsep apa yang tersedia?"        "konsep mana yang paling relevan?"
          │                                    │
          └────────────────┬───────────────────┘
                           ▼
                  Kandidat konsep Top-k
                           ▼
              domain/vocabulary filtering
                           ▼
                    Gemma reranking
                           ▼
                  Konsep standar final
```

Terminologi tidak dapat digantikan hanya dengan mesin vector. Sebaliknya, terminologi yang lengkap tanpa mekanisme retrieval akan sulit digunakan untuk mencari konsep dari jutaan label dan sinonim.

## 2. Kontribusi Sumber Terminologi OMOP

Terminologi OMOP berfungsi sebagai **ruang kandidat standar** atau knowledge base. Lapisan ini menentukan konsep, kode, label, sinonim, domain, vocabulary, hubungan, status standard, dan masa berlaku yang dapat digunakan pipeline.

### 2.1 Struktur informasi konsep

Tabel pentingnya meliputi:

- `CONCEPT`: identitas konsep, kode, nama, domain, vocabulary, kelas, dan status standard;
- `CONCEPT_SYNONYM`: sinonim atau variasi nama konsep;
- `CONCEPT_RELATIONSHIP`: relasi dan pemetaan antar-konsep;
- `CONCEPT_ANCESTOR`: hierarki ancestor–descendant;
- `VOCABULARY`: identitas sumber terminology;
- `DOMAIN`: pengelompokan klinis konsep.

Contoh representasi konsep:

```json
{
  "concept_id": "3025315",
  "concept_code": "29463-7",
  "concept_name": "Body weight",
  "vocabulary_id": "LOINC",
  "domain_id": "Measurement",
  "standard_concept": "S",
  "invalid_reason": null
}
```

Struktur OMOP menyatukan SNOMED CT, LOINC, RxNorm, ATC, UCUM, ICD-10, dan vocabulary lain dalam skema metadata yang konsisten. Tanpa lapisan ini, setiap terminologi harus diproses menggunakan struktur, identifier, dan aturan yang berbeda.

### 2.2 Identitas konsep dan ground truth

OMOP concept ID menyediakan identifier internal untuk:

- menyusun gold standard;
- menghubungkan kode vocabulary dengan satu konsep;
- membandingkan hasil retrieval;
- menghitung Accuracy@k, Recall@k, MRR, dan NDCG;
- mendeteksi duplikasi kandidat;
- menyimpan hasil validasi ahli.

Contoh:

```text
OMOP concept ID : 3025315
Vocabulary      : LOINC
Concept code    : 29463-7
Standard label  : Body weight
```

`3025315` dan `LOINC:29463-7` merupakan dua identifier untuk konsep yang sama, bukan dua gold concept terpisah.

### 2.3 Filtering klinis

Metadata terminologi memungkinkan kandidat difilter berdasarkan:

```text
domain_id
vocabulary_id
standard_concept
concept_class_id
invalid_reason
```

Contoh aturan:

- diagnosis diarahkan ke domain `Condition`;
- laboratorium diarahkan ke domain `Measurement`;
- unit hanya menerima vocabulary `UCUM`;
- konsep tidak aktif dieliminasi;
- standard concept diprioritaskan;
- ICD-10 diperlakukan sebagai klasifikasi diagnosis, bukan selalu konsep klinis utama.

Filtering ini penting karena similarity tinggi belum menjamin kecocokan klinis.

### 2.4 Relasi lintas vocabulary

`CONCEPT_RELATIONSHIP` memungkinkan alur seperti:

```text
kode lokal             → standard concept
non-standard concept   → standard concept
ICD-10                 → SNOMED CT
source LOINC           → standard LOINC
```

Pipeline dengan demikian tidak hanya bergantung pada kemiripan label, tetapi juga dapat memakai pemetaan eksplisit yang tersedia dalam terminology graph.

### 2.5 Auditabilitas dan provenance

Hasil mapping dapat menyimpan:

```json
{
  "mention": "BB",
  "normalized_mention": "berat badan",
  "omop_concept_id": "3025315",
  "vocabulary": "LOINC",
  "code": "29463-7",
  "standard_label": "Body weight",
  "domain": "Measurement",
  "terminology_version": "...",
  "validation_status": "validated"
}
```

Informasi tersebut membuat hasil dapat ditelusuri, direplikasi, dan divalidasi oleh ahli.

## 3. Kontribusi Mesin Penyimpanan dan Pencarian Vector

Qdrant, FAISS, atau mesin vector lain bukan sumber kebenaran terminologi. Mesin tersebut berfungsi sebagai **candidate generator** yang menemukan konsep paling mirip dari kumpulan konsep dan sinonim.

### 3.1 Mengatasi perbedaan bahasa dan bentuk istilah

Exact match gagal ketika istilah input dan label standar berbeda:

```text
Input Indonesia : gula darah puasa
Label standar   : Fasting glucose [Mass/volume] in Blood
```

Embedding mengubah kedua teks menjadi representasi vector. Konsep tetap dapat masuk ke Top-k apabila vector-nya berdekatan meskipun bentuk katanya tidak identik.

Kemampuan ini relevan untuk:

- istilah Indonesia–Inggris;
- sinonim lokal;
- variasi susunan kata;
- typo yang telah dinormalisasi;
- singkatan yang telah diekspansi;
- istilah klinis komposit.

### 3.2 Mengurangi ruang kandidat

Collection baseline berisi sekitar 3,7 juta point. Seluruh konsep tidak mungkin dikirim langsung ke LLM.

```text
3.700.000 point
      ↓ retrieval
10–50 kandidat
      ↓ filtering
5–10 kandidat
      ↓ Gemma reranking
1 konsep final
```

Candidate generation menurunkan biaya komputasi, jumlah token, dan beban penalaran LLM.

### 3.3 Dense retrieval

Dense retrieval menggunakan embedding seperti SapBERT.

Kelebihan:

- menangkap kemiripan makna;
- toleran terhadap perbedaan susunan kata;
- dapat menemukan sinonim;
- dapat mendukung pencarian lintas bahasa jika digunakan embedding multilingual.

Contoh target perilaku:

```text
"berat badan"   ↔ "body weight"
"kencing manis" ↔ "diabetes mellitus"
```

Kelemahannya adalah konsep yang secara semantik dekat dapat tertukar ketika konteks klinisnya berbeda.

### 3.4 Sparse atau lexical retrieval

Sparse retrieval seperti BM42/BM25 mempertahankan sinyal kata dan token.

Kelebihan:

- kuat untuk istilah dan kode spesifik;
- menjaga kata pembeda yang penting;
- membantu pencarian singkatan tertentu;
- membedakan konsep yang semantik dasarnya dekat.

Contoh:

```text
glucose fasting
glucose 2 hours postprandial
```

Dense retrieval dapat menganggap keduanya sangat berdekatan, sedangkan lexical retrieval mempertahankan perbedaan `fasting` dan `postprandial`.

### 3.5 Hybrid retrieval

```text
Dense  → kemiripan makna
Sparse → kemiripan kata/token
```

Hybrid retrieval menggabungkan kedua sinyal agar recall meningkat tanpa kehilangan seluruh ketepatan leksikal. Baseline saat ini menggabungkan kandidat dense dan sparse secara interleaving kemudian melakukan deduplikasi.

Hasil internal smoke benchmark:

```text
Accuracy@1  = 0,60
Accuracy@5  = 0,70
Accuracy@10 = 0,90
MRR         = 0,64
```

Gold concept masuk ke Top-10 untuk 9 dari 10 query, tetapi hanya 6 query yang benar pada rank pertama. Mesin retrieval dengan demikian meningkatkan coverage kandidat, tetapi belum menghilangkan kebutuhan filtering dan reranking.

## 4. Hubungan Terminologi dan Mesin Retrieval

| Aspek | Terminologi OMOP | Mesin vector |
|---|---|---|
| Menyediakan konsep dan kode | Ya | Tidak |
| Menyediakan domain/vocabulary | Ya | Hanya menyimpan metadata |
| Menentukan validitas konsep | Ya | Tidak |
| Menyediakan relasi antar-konsep | Ya | Tidak secara native |
| Menjadi dasar gold ID | Ya | Tidak |
| Menyimpan embedding | Tidak secara standar | Ya |
| Menemukan konsep semantik mirip | Tidak secara langsung | Ya |
| Mempercepat retrieval Top-k | Tidak | Ya |

Jika hanya menggunakan terminologi OMOP:

- konsep dan kode tersedia;
- exact match dan SQL search masih dapat dilakukan;
- pencarian perbedaan bahasa atau sinonim menjadi lebih sulit;
- semantic search pada jutaan konsep tidak efisien.

Jika hanya menggunakan mesin vector:

- kandidat semantik dapat ditemukan;
- tidak ada jaminan bahwa konsep aktif atau standard;
- tidak ada aturan vocabulary dan domain yang dapat dipercaya tanpa metadata;
- hasil sulit diaudit tanpa identifier dan provenance terminologi.

## 5. Alur End-to-End yang Diusulkan

```text
Teks klinis Bahasa Indonesia
             │
             ▼
normalisasi dan ekstraksi entitas
             │
             ▼
penentuan domain dan target vocabulary
             │
     ┌───────┼────────┐
     ▼       ▼        ▼
reservoir  lexical   dense
 lookup    retrieval retrieval
     └───────┼────────┘
             ▼
  deduplikasi dan rank fusion
             │
             ▼
filter domain, vocabulary, validity
             │
             ▼
        Gemma reranking
             │
             ▼
     validasi ahli bila perlu
             │
             ▼
    konsep final dan reservoir
```

Contoh untuk `BB 70 kg`:

1. normalisasi menghasilkan `berat badan 70 kg`;
2. ekstraksi memisahkan entitas `berat badan` dan unit `kg`;
3. aturan memilih target LOINC untuk pengukuran dan UCUM untuk unit;
4. dense dan lexical retrieval menghasilkan kandidat Top-k;
5. filtering menghapus kandidat salah domain atau salah vocabulary;
6. Gemma memilih kandidat final;
7. hasil divalidasi dan disimpan bersama provenance.

## 6. Kontribusi Ilmiah Riset

Penggunaan OMOP atau Qdrant secara individual bukan kebaruan penelitian. Kontribusi ilmiah muncul dari adaptasi dan integrasinya untuk Bahasa Indonesia.

### 6.1 Pengayaan terminologi lokal

Konsep standar dapat diperkaya dengan:

```text
label standar Inggris
+ sinonim resmi
+ sinonim Bahasa Indonesia
+ singkatan medis lokal
+ istilah awam
+ variasi ejaan
```

Contoh:

```text
SNOMED CT : Diabetes mellitus
Sinonim lokal:
- diabetes melitus
- DM
- kencing manis
```

### 6.2 Retrieval multi-sinyal

Pipeline menggabungkan:

```text
exact reservoir lookup
+ lexical retrieval
+ dense semantic retrieval
+ terminology relationship
+ clinical filtering
+ LLM reranking
```

### 6.3 Pemetaan multi-terminologi

```text
diagnosis             → SNOMED CT
pelaporan diagnosis   → ICD-10
laboratorium          → LOINC
unit                  → UCUM
obat                  → RxNorm/ATC
```

OMOP menjadi skema penyatu dan mesin retrieval menjadi candidate generator.

## 7. Alternatif Infrastruktur ketika Athena atau Qdrant Tidak Tersedia

Athena dan Qdrant menjalankan fungsi yang berbeda, sehingga penggantinya juga perlu dipisahkan:

```text
Athena  → sumber/layanan terminologi
Qdrant  → penyimpanan dan pencarian vector
```

### 7.1 Dampak kegagalan Athena pada pipeline saat ini

Kegagalan Athena tidak otomatis memutus inferensi. Implementasi `RetrieverAthenaAPI` menangkap exception dan mengembalikan list kandidat kosong. Merger kemudian masih dapat meneruskan kandidat dari Qdrant dense dan sparse:

```text
                     ┌─ Qdrant dense  ── kandidat
query ── retrieval ──┼─ Qdrant sparse ── kandidat
                     └─ Athena         ── [] jika gagal
                                │
                                ▼
                     merger tetap menghasilkan Top-k
```

Hal ini dimungkinkan karena collection Qdrant `concept_mapping_1` telah menyimpan snapshot konsep beserta OMOP concept ID, code, label, vocabulary, domain, dan status standard. Pada baseline 10 query, Athena tidak menghasilkan kandidat, tetapi Qdrant tetap mencapai coverage `1.00`, `query_failure_rate=0.0`, dan Accuracy@10 `0.90`.

Meskipun demikian, Qdrant hanya mewakili snapshot yang pernah dimasukkan ke collection. Qdrant tidak dapat memperbarui versi terminologi, menentukan perubahan status konsep, atau menyediakan relasi baru tanpa proses indexing dari sumber terminologi. Oleh sebab itu:

- untuk Tahap 0–1, Qdrant dense-sparse cukup sebagai fallback operasional;
- untuk eksperimen utama, snapshot terminologi yang versioned tetap diperlukan sebagai sumber kebenaran;
- Athena atau terminology API lain sebaiknya bersifat opsional/enrichment;
- query baru dinyatakan gagal jika seluruh sumber wajib tidak menghasilkan kandidat;
- kegagalan satu sumber harus dicatat sebagai partial source failure, bukan disamarkan sebagai passed.

Konfigurasi sumber sebaiknya membedakan komponen wajib dan opsional:

```yaml
retrieval_sources:
  qdrant_dense:
    enabled: true
    required: true
  qdrant_sparse:
    enabled: true
    required: true
  athena:
    enabled: false
    required: false
```

Karena Athena tidak berkontribusi pada eksperimen yang sudah dijalankan, penamaan hasil yang tepat adalah **baseline hybrid dense-sparse Qdrant dengan Athena tidak tersedia**, bukan baseline ensemble Qdrant–Athena.

### 7.2 Rancangan lokal yang direkomendasikan

Untuk eksperimen riset, pilihan paling reproducible adalah snapshot terminologi lokal, SQLite FTS5, dan FAISS.

```text
Snapshot terminologi lokal
(OMOP, SNOMED CT, LOINC, ICD-10, UCUM)
                 │
          preprocessing
                 │
       ┌─────────┴─────────┐
       ▼                   ▼
 SQLite FTS5             FAISS
 lexical/BM25         dense vector
       └─────────┬─────────┘
                 ▼
       Reciprocal Rank Fusion
                 ▼
          filtering + Gemma
```

Keuntungannya:

- inference tidak bergantung internet;
- versi terminologi dapat dipatok;
- eksperimen lebih mudah direplikasi;
- kegagalan satu API tidak menghentikan pipeline;
- data, indeks, dan konfigurasi dapat diaudit.

### 7.3 Alternatif mesin retrieval

| Pilihan | Cocok untuk | Kelebihan | Keterbatasan |
|---|---|---|---|
| FAISS | Eksperimen lokal | Ringan, cepat, sudah menjadi dependency proyek | Filtering metadata perlu dikelola sendiri |
| SQLite FTS5 + FAISS | Prototipe reproducible | Lexical dan dense lokal tanpa server | Update/index orchestration dibuat sendiri |
| PostgreSQL + pgvector | Service dan filtering kompleks | Vector, metadata, SQL, dan reservoir dapat disatukan | Memerlukan database server |
| Qdrant lokal | Retrieval service khusus | Filtering dan vector API tersedia | Memerlukan deployment service |

FAISS menyimpan indeks dense dalam file, misalnya:

```text
data/index/faiss/concepts.index
data/index/faiss/concepts_metadata.jsonl
```

SQLite FTS5 dapat menyimpan lexical index:

```sql
CREATE TABLE concepts (
    row_id INTEGER PRIMARY KEY,
    concept_id TEXT,
    concept_code TEXT,
    concept_name TEXT,
    vocabulary_id TEXT,
    domain_id TEXT,
    synonyms TEXT
);

CREATE VIRTUAL TABLE concepts_fts USING fts5(
    concept_name,
    synonyms,
    content='concepts',
    content_rowid='row_id'
);
```

### 7.4 Alternatif terminology service

- **Snowstorm** dapat digunakan sebagai terminology server SNOMED CT dan mendukung hierarki serta ECL. Penggunaannya memerlukan distribusi SNOMED CT yang sesuai lisensi.
- **LOINC FHIR Terminology Service** menyediakan operasi FHIR seperti `$lookup`, `$validate-code`, dan `$expand`, tetapi layanan eksternal tetap perlu cache atau fallback lokal.
- **FHIR terminology server lokal** dapat menyediakan antarmuka standar untuk `CodeSystem`, `ValueSet`, dan `ConceptMap`.
- **Snapshot OMOP lokal** dapat langsung dimuat ke SQLite, DuckDB, atau PostgreSQL dan menjadi sumber utama yang versioned.

Referensi:

- [OHDSI Standardized Vocabularies](https://ohdsi.github.io/TheBookOfOhdsi/StandardizedVocabularies.html)
- [FAISS](https://github.com/facebookresearch/faiss)
- [pgvector](https://github.com/pgvector/pgvector)
- [SNOMED International Terminology Services](https://www.implementation.snomed.org/terminology-services)
- [LOINC FHIR Terminology Service](https://loinc.org/fhir/)
- [HL7 FHIR Terminology Service](https://www.hl7.org/fhir/terminology-service.html)

### 7.5 Strategi fallback

API eksternal sebaiknya menjadi sumber tambahan, bukan satu-satunya jalur retrieval.

```python
candidates = []

candidates.extend(reservoir_search(query))
candidates.extend(local_bm25_search(query))
candidates.extend(local_faiss_search(query))

try:
    candidates.extend(external_terminology_search(query))
except Exception:
    logger.warning("Terminology API unavailable; using local candidates")

return reciprocal_rank_fusion(candidates)
```

Status hasil perlu dibedakan secara eksplisit:

```text
success                     → seluruh sumber wajib berhasil
success_with_partial_error  → kandidat tersedia, tetapi sumber opsional gagal
failed_no_candidates        → seluruh sumber tidak menghasilkan kandidat
```

## 8. Rancangan Implementasi yang Direkomendasikan

| Komponen | Pilihan utama |
|---|---|
| Sumber terminologi | Snapshot OMOP/SNOMED CT/LOINC/ICD-10/UCUM lokal |
| Metadata store | SQLite atau DuckDB |
| Lexical retrieval | SQLite FTS5/BM25 |
| Dense retrieval | FAISS |
| Penggabungan kandidat | Reciprocal Rank Fusion |
| Filtering | Python/SQL berdasarkan domain, vocabulary, dan validity |
| Reranking | Gemma |
| Reservoir | SQLite yang sudah tersedia |
| API eksternal | Opsional/fallback |

Arsitektur ini disarankan untuk eksperimen disertasi karena tidak bergantung pada Athena atau Qdrant publik. Jika kebutuhan berkembang menjadi concurrent production service, metadata dan vector dapat dipindahkan ke PostgreSQL + pgvector atau Qdrant yang dikelola sendiri.

## 9. Evaluasi Kontribusi Setiap Komponen

Kontribusi ilmiah harus dibuktikan melalui ablation study.

| Eksperimen | Pertanyaan yang diuji |
|---|---|
| Exact/lexical only | Seberapa kuat pencarian kata tanpa embedding? |
| Dense only | Berapa kontribusi semantic embedding? |
| Sparse only | Berapa kontribusi lexical representation? |
| Dense + sparse | Apakah hybrid retrieval meningkatkan recall? |
| + sinonim Indonesia | Apakah pengayaan lokal meningkatkan coverage? |
| + domain/vocabulary filter | Apakah aturan klinis meningkatkan precision? |
| + Gemma reranking | Apakah LLM memperbaiki posisi kandidat benar? |
| + reservoir | Apakah hasil validasi meningkatkan konsistensi dan efisiensi? |

### 9.1 Variabel terminologi

- vocabulary coverage;
- jumlah konsep aktif dan standard;
- synonym coverage;
- pengaruh `CONCEPT_SYNONYM`;
- pengaruh sinonim Bahasa Indonesia;
- coverage cross-vocabulary mapping;
- error salah domain atau vocabulary.

### 9.2 Variabel retrieval

- Accuracy@1/3/5/10;
- Precision@k dan Recall@k;
- MRR dan NDCG;
- candidate diversity;
- latency dan memory usage;
- ukuran indeks;
- perbandingan dense, sparse, dan hybrid;
- recall sebelum dan setelah filtering.

## 10. Risiko Metodologis

- Versi snapshot terminologi yang berbeda dapat menghasilkan kandidat berbeda.
- Konsep tidak aktif dapat masuk jika `invalid_reason` tidak difilter.
- Sinonim lokal yang salah dapat meningkatkan false positive.
- Embedding dapat mencampurkan konsep yang semantik dasarnya berdekatan.
- Target vocabulary yang salah membuat gold concept tidak mungkin ditemukan.
- Query dari reservoir tidak boleh digunakan sebagai gold set utama karena menimbulkan data leakage.
- Vector retrieval dapat meningkatkan recall tanpa meningkatkan Accuracy@1.
- LLM reranking dapat memperburuk urutan, seperti pada baseline Gemma.
- API eksternal dapat gagal, berubah, atau menerapkan rate limit.
- Lisensi dan versi SNOMED CT, LOINC, serta terminologi lain harus dicatat.

Mitigasi utamanya adalah versioned terminology snapshot, gold standard independen, filtering validity, audit per sumber kandidat, fallback lokal, dan validasi ahli.

## 11. Kesimpulan

> **Terminologi OMOP memberikan pengetahuan, identitas, struktur, dan validitas konsep; mesin retrieval memberikan kemampuan menemukan kandidat secara cepat, leksikal, dan semantik.**

Kontribusi OMOP berada pada standardisasi multi-terminologi, filtering klinis, hubungan antar-konsep, ground truth, dan auditabilitas. Kontribusi mesin retrieval berada pada perluasan recall, pencarian lintas bahasa, pengurangan ruang kandidat, dan efisiensi sebelum reranking.

Nilai ilmiah riset terletak pada pembuktian apakah kombinasi berikut secara signifikan lebih baik daripada baseline tanpa adaptasi Bahasa Indonesia:

```text
terminologi standar
+ normalisasi Bahasa Indonesia
+ sinonim lokal
+ lexical dan dense retrieval
+ clinical filtering
+ Gemma reranking
+ validated reservoir
```

Untuk menjaga reproducibility, pipeline sebaiknya menjadikan snapshot terminologi lokal, SQLite FTS5, dan FAISS sebagai jalur utama, sedangkan terminology API eksternal diperlakukan sebagai sumber tambahan atau fallback.
