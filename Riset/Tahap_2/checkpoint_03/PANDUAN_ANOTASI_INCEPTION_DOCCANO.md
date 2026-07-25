# Panduan Anotasi Gold Set dengan INCEpTION dan doccano

## 1. Tujuan

Panduan ini menjelaskan cara menganotasi sampel Checkpoint 3 menggunakan
INCEpTION atau doccano. Target akhirnya adalah dua hasil anotasi independen:

```text
stage2_annotator_a.jsonl
stage2_annotator_b.jsonl
```

Setelah keduanya selesai, hasil dibandingkan, disagreement diadjudikasi oleh
tenaga klinis, lalu dibekukan sebagai:

```text
stage2_gold_v1.jsonl
```

Sumber tugas terdapat pada:

```text
stage2_annotation_tasks.jsonl
```

Setiap tugas memuat pasangan `question` dan `answer`. Keduanya harus
dianotasi sebagai dokumen terpisah karena mempunyai `source_field`, `speaker`,
assertion, dan epistemic status yang dapat berbeda.

Pedoman label utama tetap:

```text
../checkpoint_02/stage2_annotation_guideline.md
```

Dokumentasi alat:

- [INCEpTION User Guide](https://inception-project.github.io/releases/40.2/docs/user-guide.html)
- [doccano Get Started](https://doccano.github.io/doccano/)
- [doccano NER Tutorial](https://doccano.github.io/doccano/tutorial/)

---

## 2. Prinsip wajib

1. Anotator A dan B bekerja secara independen.
2. Anotator tidak boleh melihat hasil anotator lain sebelum audit.
3. Teks yang dianotasi adalah `normalized_text`, bukan `raw_text`.
4. `mention` harus sama persis dengan substring teks.
5. Offset menggunakan interval half-open `[start_char, end_char)`.
6. Kata pada posisi `end_char` tidak termasuk span.
7. Jangan menyimpulkan diagnosis yang tidak tertulis.
8. Question dan answer tidak boleh digabung menjadi satu teks tanpa penanda.
9. Entitas pada jawaban dokter tidak otomatis merupakan fakta pasien.
10. Label strata seperti `negation`, `long_answer`, atau `drug_or_dose`
    bukan label anotasi.
11. Jika informasi tidak tersedia, gunakan `null`, `unknown`, atau array kosong
    sesuai skema; jangan menebak.
12. Kasus ambigu dicatat dalam `notes` untuk adjudikasi.

Validasi offset:

```text
normalized_text[start_char:end_char] == mention
```

---

## 3. Data label

### 3.1 Entity type

| Label | Digunakan untuk | Contoh |
|---|---|---|
| `condition` | Diagnosis atau penyakit | diabetes melitus, hipertensi |
| `symptom` | Keluhan yang dirasakan | demam, batuk, nyeri dada |
| `clinical_finding` | Temuan klinis non-diagnosis | benjolan merah, ruam |
| `measurement` | Pemeriksaan yang menghasilkan nilai | tekanan darah, gula darah |
| `drug` | Obat, suplemen, zat aktif, atau produk farmakologis | parasetamol, vitamin D |
| `procedure` | Pemeriksaan atau tindakan | ultrasonografi, operasi |
| `anatomy` | Bagian tubuh | perut, dada, kulit |
| `demographic` | Karakteristik pasien | perempuan, usia 33 tahun, kehamilan |
| `unit` | Satuan pengukuran | mg, mmHg, kg |
| `visit` | Konteks kunjungan | kontrol, rawat jalan |
| `other` | Mention klinis yang tidak masuk tipe lain | wajib ditinjau saat adjudikasi |

### 3.2 Domain

Nilai yang diperbolehkan:

```text
condition
measurement
observation
drug
procedure
unit
visit
all
```

Pemetaan awal:

| Entity type | Domain awal |
|---|---|
| `condition` | `condition` |
| `symptom` | `condition` atau `observation`, sesuai pedoman proyek |
| `clinical_finding` | `observation` |
| `measurement` | `measurement` |
| `drug` | `drug` |
| `procedure` | `procedure` |
| `anatomy` | `observation` |
| `demographic` | `observation` |
| `unit` | `unit` |
| `visit` | `visit` |
| `other` | `all` |

### 3.3 Assertion

| Label | Makna | Contoh |
|---|---|---|
| `present` | Entitas dinyatakan ada/terjadi | “saya demam” |
| `negated` | Entitas disangkal | “saya tidak demam” |
| `uncertain` | Entitas mungkin atau belum pasti | “mungkin infeksi” |
| `hypothetical` | Entitas bersifat syarat/skenario | “jika demam muncul” |

### 3.4 Temporal

| Label | Makna | Contoh |
|---|---|---|
| `present` | Sedang atau masih terjadi | “masih terasa sekarang” |
| `past` | Terjadi pada masa lalu | “pernah demam kemarin” |
| `future` | Direncanakan/akan terjadi | “akan diperiksa besok” |
| `unknown` | Waktu tidak dapat ditentukan | “memiliki diabetes” tanpa konteks waktu jelas |

Ekspresi waktu literal disimpan pada `temporal_expression`, misalnya
`"sejak dua hari"` atau `"kemarin"`.

### 3.5 Experiencer

| Label | Makna | Contoh |
|---|---|---|
| `patient` | Dialami penanya/pasien | “saya demam” |
| `family` | Dialami anggota keluarga | “ibu saya diabetes” |
| `other` | Dialami orang lain non-keluarga | “teman saya batuk” |
| `unknown` | Pemilik kondisi tidak dapat ditentukan | pernyataan tanpa subjek jelas |

### 3.6 Epistemic status

| Label | Makna | Contoh |
|---|---|---|
| `patient_fact` | Fakta yang dilaporkan pasien | “saya minum parasetamol” |
| `differential_diagnosis` | Kandidat diagnosis | “dapat disebabkan penyakit jantung” |
| `general_information` | Informasi medis umum | “vaksin memicu pembentukan antibodi” |
| `recommended` | Rekomendasi dokter | “sebaiknya lakukan pemeriksaan darah” |
| `conditional` | Bergantung pada syarat | “jika demam muncul” |
| `hypothetical` | Skenario yang belum terjadi | “bila nanti mengalami...” |
| `unknown` | Status pengetahuan tidak dapat ditentukan | konteks tidak cukup |

### 3.7 Atribut bebas atau opsional

| Atribut | Aturan |
|---|---|
| `normalized_mention` | Bentuk mention yang dinormalisasi |
| `base_entity` | Konsep dasar tanpa modifier |
| `associated_entities` | Daftar `entity_id` yang berkaitan |
| `categories` | Modifier/kategori yang masih relevan |
| `value` | Nilai numerik atau tekstual |
| `unit` | Satuan yang terkait dengan nilai |
| `dose` | Dosis lengkap, misalnya `500 mg` |
| `frequency` | Frekuensi, misalnya `dua kali sehari` |
| `route` | Rute pemberian, misalnya `oral` |
| `method` | Metode pemeriksaan/tindakan |
| `visit` | Jenis kunjungan |
| `sentence_id` | Indeks kalimat, mulai dari `0` |
| `evidence` | Kalimat yang memuat mention |
| `confidence` | Nilai `0.0`–`1.0`; bukan pengganti catatan ambiguitas |

`source_field` dan `speaker` berasal dari dokumen:

| Dokumen | `source_field` | `speaker` |
|---|---|---|
| Pertanyaan | `question` | `patient` |
| Jawaban | `answer` | `doctor` |

---

## 4. Contoh anotasi

### 4.1 Negasi

Teks:

```text
saya tidak demam sejak dua hari.
```

Span:

```text
mention             = demam
start_char          = 11
end_char            = 16
entity_type         = symptom
domain              = condition
assertion           = negated
temporal            = present
temporal_expression = sejak dua hari
experiencer         = patient
epistemic_status    = patient_fact
```

Kata `tidak` tidak dimasukkan ke span `demam`; maknanya direkam melalui
`assertion=negated`.

### 4.2 Kondisi anggota keluarga

Teks:

```text
ibu saya menderita diabetes melitus.
```

Span:

```text
mention          = diabetes melitus
start_char       = 19
end_char         = 35
entity_type      = condition
assertion        = present
temporal         = unknown
experiencer      = family
epistemic_status = patient_fact
```

`ibu saya` adalah petunjuk experiencer. Fokus entitas klinisnya adalah
`diabetes melitus`.

### 4.3 Measurement dan unit

Teks:

```text
tekanan darah saya 160/100 mmHg.
```

Entitas pertama:

```text
mention      = tekanan darah
start_char   = 0
end_char     = 13
entity_type  = measurement
value        = 160/100
unit         = mmHg
```

Entitas kedua, jika unit dipertahankan untuk pemetaan UCUM:

```text
mention      = mmHg
start_char   = 27
end_char     = 31
entity_type  = unit
unit         = mmHg
```

Kedua entitas dapat dihubungkan melalui `associated_entities`.

### 4.4 Obat, dosis, dan frekuensi

Teks:

```text
saya minum parasetamol 500 mg dua kali sehari.
```

```text
mention          = parasetamol
start_char       = 11
end_char         = 22
entity_type      = drug
dose             = 500 mg
frequency        = dua kali sehari
assertion        = present
temporal         = present
experiencer      = patient
epistemic_status = patient_fact
```

Dosis dan frekuensi menjadi atribut obat, bukan bagian wajib dari span obat.

### 4.5 Diagnosis banding pada jawaban dokter

Teks:

```text
keluhan nyeri dada dapat disebabkan oleh penyakit jantung.
```

Entitas `penyakit jantung`:

```text
mention          = penyakit jantung
start_char       = 41
end_char         = 57
entity_type      = condition
assertion        = uncertain
temporal         = unknown
experiencer      = patient
epistemic_status = differential_diagnosis
source_field     = answer
speaker          = doctor
```

Pernyataan ini tidak boleh dianotasi sebagai diagnosis pasien yang sudah pasti.

### 4.6 Rekomendasi bersyarat

Teks:

```text
sebaiknya lakukan pemeriksaan darah jika demam muncul.
```

`pemeriksaan darah`:

```text
entity_type      = procedure
assertion        = hypothetical
temporal         = future
epistemic_status = recommended
```

`demam`:

```text
entity_type      = symptom
assertion        = hypothetical
temporal         = future
epistemic_status = conditional
```

---

## 5. Persiapan data untuk alat anotasi

Satu record Checkpoint 3 dipecah menjadi dua dokumen:

```text
gold-v1-001-question
gold-v1-001-answer
```

Metadata minimal yang harus tetap dibawa:

```json
{
  "task_id": "gold-v1-001",
  "document_id": "<parent_record_id>-question",
  "parent_record_id": "<parent_record_id>",
  "source_field": "question",
  "speaker": "patient",
  "text": "<question.normalized_text>"
}
```

Untuk answer:

```text
source_field = answer
speaker      = doctor
text         = answer.normalized_text
```

Jangan mengimpor cuplikan teks yang ditampilkan notebook. Tampilan notebook
memotong teks untuk inspeksi; anotasi harus memakai `normalized_text` lengkap.

---

## 6. Panduan menggunakan INCEpTION

INCEpTION direkomendasikan jika seluruh atribut ingin dicatat langsung pada
span dan adjudikasi dilakukan di dalam satu platform.

### 6.1 Membuat proyek

1. Masuk sebagai project manager.
2. Buat project baru, misalnya `Tahap 2 - Gold v1`.
3. Tambahkan user anotator A, anotator B, dan adjudikator.
4. Berikan A dan B hak anotasi.
5. Berikan tenaga klinis hak curation.
6. Masukkan pedoman Checkpoint 2 ke bagian guidelines proyek.
7. Impor 80 dokumen: 40 question dan 40 answer.
8. Pastikan nama dokumen mempertahankan `task_id` dan `source_field`.

### 6.2 Membuat layer

Buat custom span layer:

```text
Layer name : ClinicalEntity
Type       : span
Granularity: character atau token
Overlap    : aktifkan hanya jika pedoman memang membutuhkan nested span
```

Jika pemilihan harus menghasilkan offset karakter yang sama persis dengan
skema, lakukan uji impor-ekspor pada beberapa dokumen sebelum anotasi massal.

### 6.3 Membuat feature

Feature dengan nilai tertutup:

```text
entity_type
domain
assertion
temporal
experiencer
epistemic_status
```

Isi daftar nilai sesuai Bagian 3. Gunakan dropdown/tagset agar anotator tidak
membuat ejaan baru seperti `negative`, `negation`, atau `current`.

Feature teks/numerik:

```text
normalized_mention
base_entity
value
unit
dose
frequency
route
method
visit
temporal_expression
confidence
notes
```

`mention`, offset, dan teks evidence sebaiknya direkonstruksi dari span dan
kalimat saat konversi ekspor. `source_field`, `speaker`, `document_id`, dan
`parent_record_id` diambil dari metadata/nama dokumen, bukan diketik ulang
oleh anotator.

### 6.4 Prosedur anotator

1. Buka dokumen question atau answer.
2. Baca seluruh dokumen sebelum menandai span.
3. Seleksi mention klinis terlengkap yang sesuai pedoman.
4. Pilih `entity_type`.
5. Isi seluruh feature wajib.
6. Isi atribut opsional hanya jika tertulis atau dapat ditentukan secara aman.
7. Periksa bahwa kata negasi tidak ikut ke span.
8. Periksa experiencer dan epistemic status.
9. Catat ambiguitas dalam `notes`.
10. Tandai dokumen sebagai finished/complete.

### 6.5 Anotasi independen

- A dan B mendapat kumpulan dokumen yang sama.
- Keduanya tidak membuka halaman curation.
- Project manager tidak menggabungkan anotasi sebelum seluruh paket selesai.
- Identitas user pada ekspor harus dipertahankan agar hasil dapat dipisahkan.

### 6.6 Curation/adjudikasi

1. Buka halaman curation setelah A dan B menandai dokumen selesai.
2. Periksa perbedaan span terlebih dahulu.
3. Periksa `entity_type`.
4. Periksa assertion, temporal, experiencer, dan epistemic status.
5. Adjudikator memilih salah satu anotasi atau membuat keputusan baru.
6. Setiap keputusan substantif dicatat pada `stage2_adjudication_log.md`.
7. Ekspor anotasi individual dan hasil curation secara terpisah.
8. Konversi hasil ekspor ke kontrak JSONL Checkpoint 2.
9. Jalankan validator skema dan audit Checkpoint 3.

### 6.7 Pemeriksaan sebelum ekspor

- Semua dokumen berstatus selesai.
- Tidak ada feature wajib yang kosong.
- `other` telah ditinjau.
- Question dan answer tidak tertukar.
- Semua disagreement sudah diputuskan.
- Versi project, pedoman, dan tanggal ekspor dicatat.

---

## 7. Panduan menggunakan doccano

doccano direkomendasikan untuk anotasi span dan `entity_type` yang sederhana.
Karena skema penelitian memiliki banyak atribut per entitas, gunakan workflow
dua bagian:

```text
doccano              → span + entity_type
lembar atribut JSONL → atribut klinis setiap span
```

Jangan menganggap label dokumen atau komentar bebas sebagai pengganti atribut
terstruktur.

### 7.1 Membuat proyek

1. Instal dan jalankan doccano sesuai dokumentasi resmi.
2. Buat project bertipe `Sequence Labeling`.
3. Nama project, misalnya `Tahap 2 Gold v1 - Annotator A`.
4. Aktifkan collaborative annotation hanya jika konfigurasi menjamin hasil
   setiap pengguna tetap terpisah.
5. Untuk isolasi yang paling mudah diaudit, buat dua project identik:

```text
Tahap 2 Gold v1 - Annotator A
Tahap 2 Gold v1 - Annotator B
```

6. Tambahkan anggota sesuai project.
7. Salin pedoman Checkpoint 2 ke guideline project.
8. Impor 80 dokumen yang sama ke kedua project.

### 7.2 Membuat label NER

Buat sebelas label berikut, tanpa variasi ejaan:

```text
condition
symptom
clinical_finding
measurement
drug
procedure
anatomy
demographic
unit
visit
other
```

Gunakan warna dan shortcut yang sama pada project A dan B.

### 7.3 Format impor konseptual

doccano menerima format sesuai tipe project dan versi yang digunakan. Data
yang disiapkan minimal membawa teks dan metadata yang dapat ditelusuri:

```json
{
  "text": "saya tidak demam sejak dua hari.",
  "task_id": "contoh-negasi",
  "document_id": "contoh-negasi-question",
  "parent_record_id": "contoh-negasi",
  "source_field": "question",
  "speaker": "patient"
}
```

Lakukan uji impor 2–3 record terlebih dahulu dan pastikan metadata tetap dapat
dihubungkan kembali pada saat ekspor.

### 7.4 Prosedur anotator

1. Buka dokumen.
2. Baca seluruh teks.
3. Sorot mention klinis.
4. Pilih satu `entity_type`.
5. Hindari memasukkan kata negasi, kata penghubung, atau experiencer ke span,
   kecuali memang bagian dari konsep klinis.
6. Catat task yang ambigu pada daftar terpisah.
7. Selesaikan seluruh dokumen dan ekspor hasil per anotator.

Contoh keluaran span doccano:

```json
{
  "text": "saya tidak demam sejak dua hari.",
  "labels": [
    [11, 16, "symptom"]
  ]
}
```

### 7.5 Melengkapi atribut

Setelah ekspor, setiap span diberi `entity_id`, lalu anotator melengkapi lembar
atribut dengan kunci yang stabil:

```json
{
  "document_id": "contoh-negasi-question",
  "entity_id": "contoh-negasi-question-e001",
  "mention": "demam",
  "start_char": 11,
  "end_char": 16,
  "entity_type": "symptom",
  "normalized_mention": "demam",
  "base_entity": "demam",
  "domain": "condition",
  "assertion": "negated",
  "temporal": "present",
  "temporal_expression": "sejak dua hari",
  "experiencer": "patient",
  "epistemic_status": "patient_fact",
  "notes": ""
}
```

Lembar atribut A dan B harus tetap terpisah. Jangan menggunakan satu lembar
bersama karena hal tersebut menghilangkan independensi.

### 7.6 Agreement dan adjudikasi

1. Ekspor project A dan B secara terpisah.
2. Cocokkan record menggunakan `document_id`.
3. Cocokkan entitas awal menggunakan:

```text
start_char + end_char + entity_type
```

4. Bandingkan atribut pada span yang cocok.
5. Masukkan perbedaan ke `stage2_annotation_disagreement.jsonl`.
6. Tenaga klinis memutuskan hasil final.
7. Catat alasan pada `stage2_adjudication_log.md`.
8. Bangun dan validasi `stage2_gold_v1.jsonl`.

---

## 8. Contoh satu record final

Contoh berikut menunjukkan bentuk target setelah hasil alat dikonversi. Ini
bukan format impor langsung INCEpTION atau doccano.

```json
{
  "document_id": "schema-q1-question",
  "parent_record_id": "schema-q1",
  "source_field": "question",
  "speaker": "patient",
  "normalized_text": "saya tidak demam sejak dua hari.",
  "sentences": [
    "saya tidak demam sejak dua hari."
  ],
  "entities": [
    {
      "entity_id": "schema-q1-e1",
      "mention": "demam",
      "normalized_mention": "demam",
      "base_entity": "demam",
      "entity_type": "symptom",
      "domain": "condition",
      "associated_entities": [],
      "categories": [],
      "value": null,
      "unit": null,
      "dose": null,
      "frequency": null,
      "route": null,
      "method": null,
      "visit": null,
      "assertion": "negated",
      "temporal": "present",
      "temporal_expression": "sejak dua hari",
      "experiencer": "patient",
      "epistemic_status": "patient_fact",
      "source_field": "question",
      "speaker": "patient",
      "sentence_id": 0,
      "start_char": 11,
      "end_char": 16,
      "evidence": "saya tidak demam sejak dua hari.",
      "confidence": 1.0
    }
  ],
  "schema_version": "1.0.0"
}
```

---

## 9. Checklist anotator

Untuk setiap dokumen:

- [ ] Saya membaca teks lengkap.
- [ ] Saya menggunakan `normalized_text`.
- [ ] Semua mention merupakan substring persis.
- [ ] Span tidak memasukkan kata negasi/penghubung yang tidak diperlukan.
- [ ] `entity_type` sesuai taksonomi.
- [ ] Assertion ditentukan dari konteks.
- [ ] Temporal dan ekspresi waktunya diperiksa.
- [ ] Experiencer diperiksa.
- [ ] Epistemic status diperiksa, khususnya pada jawaban dokter.
- [ ] Nilai, unit, dosis, frekuensi, dan route tidak ditebak.
- [ ] Kasus ambigu dicatat.
- [ ] Dokumen ditandai selesai.

## 10. Checklist project manager

- [ ] Project A dan B menggunakan dokumen serta label yang sama.
- [ ] Anotator bekerja independen.
- [ ] `task_id`, `document_id`, dan `source_field` dapat dipulihkan.
- [ ] Ekspor A dan B disimpan terpisah.
- [ ] Hash dan waktu ekspor dicatat.
- [ ] Semua record lolos validasi skema.
- [ ] Agreement dihitung sebelum adjudikasi.
- [ ] Semua disagreement diselesaikan tenaga klinis.
- [ ] Gold v1 tidak digunakan sebagai few-shot atau data pengembangan.
- [ ] Gold v1 dibekukan dengan versi dan SHA-256.

---

## 11. Pemilihan alat

Gunakan INCEpTION apabila:

- atribut per span ingin diisi dalam satu antarmuka;
- diperlukan curation bawaan;
- adjudikator perlu melihat hasil A dan B berdampingan.

Gunakan doccano apabila:

- prioritas awal adalah span dan `entity_type`;
- tim membutuhkan antarmuka NER yang lebih sederhana;
- tersedia proses tambahan untuk melengkapi atribut dan adjudikasi.

Untuk kontrak Checkpoint 2 yang memiliki banyak atribut, INCEpTION adalah
pilihan utama. doccano tetap layak sebagai workflow dua langkah selama
identitas dokumen, offset, independensi anotator, dan audit trail dijaga.
