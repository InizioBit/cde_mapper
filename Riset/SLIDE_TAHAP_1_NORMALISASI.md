---
marp: true
theme: default
paginate: true
title: Tahap 1 - Normalisasi Bahasa Indonesia
description: Pra-pemrosesan teks konsultasi klinis Alodokter
---

# Tahap 1  
## Normalisasi Bahasa Indonesia

Pra-pemrosesan teks konsultasi klinis untuk pipeline pemetaan terminologi

**Data:** 150 pasangan pertanyaan–jawaban Alodokter  
**Keluaran:** teks terstandar, segmentasi kalimat, dan audit trail

---

# Posisi Tahap 1 dalam Pipeline

```text
Teks klinis panjang
        ↓
Tahap 1 — Normalisasi Bahasa
        ↓
Teks bersih dan terstandar
        ↓
Tahap 2 — Ekstraksi Multi-Entitas
        ↓
Mapping rules → Query decomposition
        ↓
Retrieval → Filtering → Reranking
        ↓
Validasi ahli → Knowledge reservoir
```

Tahap 1 memperbaiki **bentuk teks**, bukan membuat keputusan klinis.

---

# Mengapa Normalisasi Diperlukan?

Pertanyaan pasien banyak mengandung:

- singkatan informal: `sy`, `yg`, `tp`, `skrg`, `dgn`;
- singkatan medis: `ISK`, `DM`, `TD`, `GDP`, `USG`;
- typo dan ejaan tidak baku;
- huruf kapital dan spasi tidak konsisten;
- tanda baca berulang atau tanpa spasi;
- angka, dosis, durasi, dan satuan;
- campuran Bahasa Indonesia dan Inggris.

Jawaban dokter lebih formal, tetapi mengandung sapaan, penutup, nama obat, diagnosis banding, negasi, dan ketidakpastian.

---

# Profil Data Alodokter

| Karakteristik | Pertanyaan | Jawaban |
|---|---:|---:|
| Record tersedia | 150 | 150 |
| Rata-rata panjang | ±53 kata | ±200 kata |
| Gaya bahasa | Informal | Relatif formal |
| Singkatan lokal | Tinggi | Lebih rendah |
| Boilerplate | Sapaan kepada dokter | Sapaan dan penutup |
| Risiko klinis | Dosis, durasi, keluhan | Hipotesis dan informasi umum |

`clean_text` hasil crawler masih sama dengan `raw_text`, sehingga normalisasi perlu dilakukan sebagai tahap tersendiri.

---

# Prinsip Desain

1. **Deterministik**  
   Input yang sama menghasilkan output yang sama.

2. **Konservatif**  
   Tidak menghapus angka, dosis, satuan, negasi, atau nama obat.

3. **Dapat diaudit**  
   Setiap perubahan dapat ditelusuri.

4. **Idempotent**  
   Normalisasi berulang tidak mengubah hasil.

5. **Berbasis profil**  
   Pertanyaan dan jawaban diperlakukan berbeda.

6. **Kompatibel dengan baseline**  
   Normalisasi diaktifkan secara opsional.

---

# Alur Normalisasi yang Diimplementasikan

```text
raw_text
   ↓
Normalisasi Unicode dan casing
   ↓
Cleaning karakter kontrol, spasi, dan tanda baca
   ↓
Koreksi typo berbasis kamus
   ↓
Normalisasi informal dan ekspansi singkatan
   ↓
Normalisasi angka dan satuan
   ↓
Final spacing
   ↓
Segmentasi kalimat
   ↓
Penandaan boilerplate
   ↓
normalized_text + audit trail
```

---

# Normalisasi Unicode dan Cleaning

Operasi utama:

- Unicode normalization menggunakan **NFKC**;
- standardisasi tanda kutip dan tanda hubung;
- pemisahan pola camel-case tertentu;
- penghapusan karakter kontrol;
- perapian spasi dan baris baru;
- perapian tanda baca berulang;
- penambahan spasi pada batas kalimat yang menempel;
- preservasi desimal Indonesia seperti `2,5 mg`.

Contoh:

```text
dktr.slmt mlmSy ... kambuh..dan
↓
dokter. selamat malam saya ... kambuh. dan
```

---

# Kamus Singkatan Berlapis

Kamus master dibagi menjadi:

- `medical_clinical`;
- `maternal_child_health`;
- `body_function_and_measurement`;
- `clinical_documentation`;
- `informal_conversation`;
- `ambiguous_not_automatic`.

Setiap entri mempunyai status:

| Status | Perlakuan |
|---|---|
| `automatic` | Langsung diperluas |
| `context_required` | Diperluas jika konteks sesuai |
| `review_required` | Menunggu validasi ahli |

---

# Ekspansi Berbasis Konteks

Singkatan tertentu tidak aman jika diperluas secara langsung:

| Singkatan | Kemungkinan Makna |
|---|---|
| `TB` | tinggi badan / tuberkulosis |
| `BB` | berat badan / konteks lain |
| `Px` | pasien / pemeriksaan |
| `N` | nadi / karakter biasa |
| `RR` | frekuensi napas / konteks lain |
| `mg` | miligram / minggu |
| `dr` | dari / dokter |

Contoh:

```text
TB 165 cm → tinggi badan 165 cm
riwayat TB keluarga → tetap "tb" + warning
```

---

# Profil Pertanyaan dan Jawaban

## Profil `question`

- normalisasi informal lebih aktif;
- ekspansi singkatan percakapan;
- ekspansi istilah klinis;
- mempertahankan keluhan, angka, negasi, dan temporalitas.

## Profil `answer`

- lebih konservatif;
- tidak mengaktifkan seluruh normalisasi informal;
- memisahkan sapaan dan penutup ke `boilerplate`;
- menyimpan teks lengkap dan `content_text`.

Pertanyaan dan jawaban tidak digabung karena mempunyai peran semantik berbeda.

---

# Contoh Transformasi Pertanyaan

### Input

```text
Sy skrg ISK, tp blm minum obat 500mg.
Dok, kira2 berbahaya ngga?
```

### Output

```text
saya sekarang infeksi saluran kemih,
tetapi belum minum obat 500 mg.
dokter, kira-kira berbahaya tidak?
```

### Perubahan yang tercatat

`sy`, `skrg`, `ISK`, `tp`, `blm`, `dok`, `kira2`, `ngga`, dan `500mg`.

---

# Penanganan Angka dan Satuan

Tujuan utama adalah standardisasi tanpa kehilangan informasi klinis.

```text
500mg       → 500 mg
126 mg / dl → 126 mg/dL
12 gr/dl    → 12 g/dL
160 / 100   → 160/100
95 %        → 95%
2,5mg       → 2,5 mg
mmhg        → mmHg
```

Yang dipertahankan:

- nilai numerik;
- desimal koma atau titik;
- rasio;
- dosis;
- durasi;
- rentang;
- frekuensi.

---

# Segmentasi Kalimat

Segmentasi saat ini menggunakan aturan deterministik.

```text
Saya demam.Dok, apakah berbahaya?Sudah 2 hari.
```

menjadi:

```text
1. Saya demam.
2. Dok, apakah berbahaya?
3. Sudah 2 hari.
```

Pendekatan transformer seperti `indo_text_segmentation` dapat dievaluasi sebagai **semantic chunking** untuk teks panjang, bukan sebagai pengganti langsung sentence splitter.

---

# Penandaan Boilerplate

Untuk jawaban dokter:

```text
Alo Ibu Anna,
[isi klinis]
Semoga bermanfaat.
```

disimpan sebagai:

```json
{
  "normalized_text": "teks lengkap",
  "content_text": "isi klinis",
  "boilerplate": [
    "alo ibu anna,",
    "semoga bermanfaat."
  ]
}
```

Boilerplate ditandai, bukan dihapus permanen, agar provenance tetap terjaga.

---

# Struktur Output Tahap 1

```json
{
  "record_id": "stable-id",
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
  }
}
```

Format JSONL memudahkan pemrosesan per record dan audit eksperimen.

---

# Hasil Implementasi

| Indikator | Hasil |
|---|---:|
| Pasangan konsultasi diproses | 150 |
| ID record unik | 150 |
| Kelompok perubahan pertanyaan | 269 |
| Kelompok perubahan jawaban | 46 |
| Warning konteks ambigu | 9 |
| Unit test | 7/7 lulus |
| Gold normalization | 5/5 |
| Exact normalized match | 1,0 |

Artefak:

```text
Riset/crawler_alodokter/
hasil_normalisasi_tahap_1.jsonl
```

---

# Integrasi dengan Pipeline

Normalisasi dapat diaktifkan pada entry point:

```bash
python run.py ... \
  --normalize_id \
  --normalization_profile clinical
```

Untuk Alodokter:

```bash
python scripts/preprocess_alodokter.py
```

Notebook eksperimen:

```text
Riset/Tahap_1_Normalisasi_Alodokter.ipynb
```

Baseline tetap berjalan seperti sebelumnya jika flag normalisasi tidak diberikan.

---

# Apakah Stemming Diperlukan?

**Tidak sebagai transformasi default.**

Risiko stemming pada teks klinis:

```text
pemeriksaan → periksa
pengobatan  → obat
pendarahan  → darah
menularkan  → tular
```

Rekomendasi:

```text
normalized_text
├── teks utuh → Tahap 2, LLM, dense retrieval
└── stemmed_text opsional → eksperimen lexical retrieval
```

Sastrawi dapat diuji pada ablation study, bukan menggantikan `normalized_text`.

---

# Input untuk Tahap 2

Output Tahap 1 sudah dapat digunakan untuk eksperimen Tahap 2:

```text
document_id = record_id
text        = question.normalized_text
sentences   = question.sentences
speaker     = patient
```

Jawaban dokter diproses secara terpisah:

```text
text        = answer.content_text
speaker     = doctor
```

Jawaban tidak boleh langsung dianggap sebagai fakta pasien karena dapat mengandung diagnosis banding, contoh hipotetis, dan informasi umum.

---

# Keterbatasan Saat Ini

1. Protected-token mechanism belum eksplisit.
2. Nama obat dan kode klinis belum memiliki registry perlindungan khusus.
3. Sebagian bentuk informal masih dapat tertinggal.
4. Segmentasi kalimat masih rule-based.
5. Boilerplate menggunakan pola terbatas.
6. Aturan konteks singkatan belum mencakup semua kasus.
7. Gold set masih kecil.
8. Belum ada validasi kamus menyeluruh oleh klinisi.

Tahap 1 sudah operasional, tetapi masih memerlukan penguatan sebelum evaluasi final riset.

---

# Rencana Penguatan

- tambahkan protected-token detection;
- perluas kamus berdasarkan error analysis korpus;
- validasi singkatan bersama tenaga klinis;
- susun gold set terstratifikasi;
- ukur sentence-boundary precision, recall, dan F1;
- ukur preservation rate angka, unit, obat, negasi, dan temporalitas;
- evaluasi semantic segmentation untuk teks panjang;
- lakukan ablation study:
  - tanpa normalisasi;
  - normalisasi dasar;
  - kamus informal;
  - singkatan kontekstual;
  - semantic segmentation.

---

# Kesimpulan

- Tahap 1 mengubah teks konsultasi yang tidak baku menjadi teks yang lebih stabil dan dapat diaudit.
- Profil pertanyaan dan jawaban dipisahkan.
- Singkatan ambigu ditangani menggunakan aturan konteks dan warning.
- Informasi klinis seperti angka, dosis, satuan, negasi, dan teks asli dipertahankan.
- Stemming tidak digunakan sebagai default.
- Output sudah dapat menjadi input eksperimen Tahap 2.
- Penguatan utama berikutnya adalah protected-token mechanism dan evaluasi gold set yang lebih besar.

---

# Terima Kasih

**Tahap berikutnya:**  
Ekstraksi multi-entitas klinis, assertion, dan temporalitas dari teks hasil normalisasi.
