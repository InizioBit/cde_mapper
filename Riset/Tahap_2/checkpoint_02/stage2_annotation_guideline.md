# Pedoman Anotasi Entitas Klinis Tahap 2

## 1. Tujuan

Pedoman ini menetapkan kontrak anotasi untuk ekstraksi entitas klinis Bahasa Indonesia. Setiap anotasi harus dapat ditelusuri ke `normalized_text`, kalimat sumber, character offset, speaker, dan provenance dokumen.

## 2. Prinsip Umum

1. Hanya anotasi informasi yang tertulis.
2. Jangan menambahkan diagnosis berdasarkan interpretasi anotator.
3. `mention` harus sama persis dengan substring `normalized_text`.
4. Gunakan offset karakter half-open: `[start_char, end_char)`.
5. `evidence` harus berasal dari kalimat yang memuat mention.
6. Pertanyaan dan jawaban diproses terpisah.
7. Entitas pada jawaban dokter tidak otomatis menjadi fakta pasien.
8. Jika atribut tidak tersedia, gunakan `null`, `unknown`, atau array kosong.
9. Jangan menebak nilai, unit, dosis, temporal, atau experiencer.

## 3. Unit Anotasi

Satu unit anotasi adalah satu mention klinis pada satu dokumen:

```text
document
└── sentence
    └── entity mention
```

Mention yang sama pada dua kalimat berbeda menghasilkan dua entitas berbeda.

## 4. Batas Entity Span

### 4.1 Gunakan span klinis terlengkap

```text
diabetes melitus tipe 2
```

Anotasi:

```text
mention: diabetes melitus tipe 2
base_entity: diabetes melitus
categories: [tipe 2]
```

### 4.2 Jangan memasukkan kata penghubung

```text
mengalami demam dan batuk
```

Entitas:

- `demam`;
- `batuk`.

Kata `mengalami` dan `dan` bukan bagian mention.

### 4.3 Pertahankan modifier yang mengubah makna

```text
nyeri dada kiri
```

Mention dapat menggunakan `nyeri dada kiri`, dengan:

```text
base_entity: nyeri dada
associated_entities: [kiri]
```

## 5. Entity Type

### 5.1 `condition`

Diagnosis atau penyakit:

- diabetes melitus;
- hipertensi;
- infeksi saluran kemih;
- penyakit jantung.

### 5.2 `symptom`

Keluhan yang dirasakan:

- demam;
- batuk;
- mual;
- nyeri dada;
- pusing.

### 5.3 `clinical_finding`

Temuan klinis yang bukan diagnosis pasti:

- benjolan merah;
- pembengkakan;
- ruam;
- luka terbuka.

### 5.4 `measurement`

Pemeriksaan yang menghasilkan nilai:

- tekanan darah;
- gula darah puasa;
- hemoglobin;
- suhu tubuh.

### 5.5 `drug`

Obat, suplemen, atau zat aktif:

- parasetamol;
- metoklopramid;
- vitamin D.

### 5.6 `procedure`

Pemeriksaan atau tindakan:

- ultrasonografi;
- pemeriksaan darah;
- operasi;
- penambalan gigi.

### 5.7 `anatomy`

Bagian tubuh:

- perut;
- pinggul;
- dada;
- kulit.

### 5.8 `demographic`

Karakteristik pasien:

- usia;
- jenis kelamin;
- kehamilan.

### 5.9 `unit`

Satuan pengukuran:

- mg;
- mg/dL;
- mmHg;
- kg.

Unit dapat menjadi atribut measurement dan entitas tersendiri jika diperlukan untuk pemetaan UCUM.

### 5.10 `visit`

Konteks kunjungan:

- kontrol;
- kunjungan pertama;
- rawat jalan.

### 5.11 `other`

Gunakan hanya jika mention klinis tidak dapat dimasukkan ke tipe lain. Setiap penggunaan `other` harus ditinjau saat adjudikasi.

## 6. Domain Awal

| Entity type | Domain awal |
|---|---|
| condition | condition |
| symptom | condition atau observation sesuai pedoman proyek |
| clinical_finding | observation |
| measurement | measurement |
| drug | drug |
| procedure | procedure |
| anatomy | observation |
| demographic | observation |
| unit | unit |
| visit | visit |
| other | all |

Pemilihan terminology target dilakukan pada Tahap 3.

## 7. Nilai, Unit, dan Obat

Contoh:

```text
tekanan darah 160/100 mmHg
```

```json
{
  "base_entity": "tekanan darah",
  "value": "160/100",
  "unit": "mmHg"
}
```

Contoh:

```text
parasetamol 500 mg dua kali sehari
```

```json
{
  "base_entity": "parasetamol",
  "dose": "500 mg",
  "frequency": "dua kali sehari"
}
```

Jangan menghubungkan nilai atau dosis ke entitas yang tidak jelas.

## 8. Assertion

### `present`

Entitas dinyatakan ada:

```text
saya demam
```

### `negated`

Entitas dinyatakan tidak ada:

```text
saya tidak demam
```

### `uncertain`

Entitas disebut sebagai kemungkinan:

```text
mungkin mengalami infeksi
```

### `hypothetical`

Entitas disebut pada kondisi bersyarat:

```text
jika nanti muncul demam
```

Negasi harus diterapkan pada scope yang tepat, bukan seluruh kalimat secara otomatis.

## 9. Temporal

### `present`

Kondisi sedang terjadi:

```text
saat ini demam
```

### `past`

Kondisi terjadi pada masa lalu:

```text
dulu pernah mengalami demam
```

### `future`

Kondisi atau tindakan masa depan:

```text
nanti lakukan pemeriksaan
```

### `unknown`

Tidak terdapat informasi waktu yang cukup.

Simpan frasa sumber pada `temporal_expression`, misalnya `sejak dua hari`.

## 10. Experiencer

### `patient`

Kondisi dialami pasien:

```text
saya demam
```

### `family`

Kondisi dialami anggota keluarga:

```text
ibu saya menderita diabetes
```

### `other`

Kondisi dialami orang lain yang bukan keluarga.

### `unknown`

Pemilik kondisi tidak dapat ditentukan.

## 11. Speaker dan Source

| Source field | Speaker |
|---|---|
| question | patient |
| answer | doctor |

Kombinasi lain tidak valid.

## 12. Epistemic Status

### `patient_fact`

Fakta atau laporan yang disampaikan pasien.

### `differential_diagnosis`

Kemungkinan diagnosis pada jawaban dokter:

```text
keluhan dapat disebabkan oleh penyakit jantung
```

### `general_information`

Informasi edukatif yang tidak menyatakan kondisi pasien.

### `recommended`

Pemeriksaan atau tindakan yang disarankan.

### `conditional`

Entitas pada kalimat bersyarat.

### `hypothetical`

Contoh atau situasi hipotetis.

### `unknown`

Status tidak dapat ditentukan.

## 13. Offset dan Evidence

Offset menggunakan karakter Unicode Python:

```python
normalized_text[start_char:end_char] == mention
```

Aturan:

- `start_char` inklusif;
- `end_char` eksklusif;
- offset dihitung pada `normalized_text`;
- evidence harus berada pada `sentences[sentence_id]`;
- mention harus berada dalam evidence.

## 14. Associated Entities

Gunakan ID entitas untuk hubungan lokal.

Contoh:

```text
pemeriksaan ultrasonografi pada perut
```

- prosedur berasosiasi dengan anatomi `perut`;
- anatomi dapat berasosiasi kembali dengan prosedur.

Jangan menggunakan associated entity untuk hubungan terminologi yang belum diketahui.

## 15. Confidence

Pada gold annotation gunakan:

```text
confidence = 1.0
```

Pada prediksi model:

```text
0.0 <= confidence <= 1.0
```

Confidence tidak boleh digunakan untuk menyembunyikan output tanpa evidence.

## 16. Kasus Question

Question terutama diperlakukan sebagai laporan pasien. Namun:

- kondisi keluarga harus memiliki experiencer `family`;
- pertanyaan hipotetis tetap `hypothetical`;
- diagnosis yang hanya ditanyakan belum tentu `present`;
- judul tidak digunakan sebagai evidence utama.

## 17. Kasus Answer

Answer harus membedakan:

- fakta pasien yang diulang dokter;
- diagnosis banding;
- informasi umum;
- rekomendasi;
- kondisi bersyarat;
- contoh hipotetis.

Nama penyakit pada jawaban tidak otomatis diberi `patient_fact`.

## 18. Larangan Anotasi

Jangan:

- mendiagnosis berdasarkan gejala;
- menambahkan unit yang tidak tertulis;
- memperbaiki mention saat menentukan offset;
- menganggap semua entitas answer sebagai kondisi pasien;
- menghapus entitas negated;
- mengubah experiencer family menjadi patient;
- menggunakan teks di luar dokumen sebagai evidence.

## 19. Adjudikasi

Catat disagreement berdasarkan kategori:

- span boundary;
- entity type;
- base entity;
- domain;
- assertion;
- temporal;
- experiencer;
- epistemic status;
- value-unit relation;
- drug-dose relation.

Keputusan adjudikasi harus disimpan bersama alasan dan identitas versi pedoman.

## 20. Definisi Selesai Pedoman

Pedoman dianggap siap jika:

- seluruh entity type memiliki definisi;
- seluruh atribut konteks memiliki contoh;
- question dan answer dibedakan;
- aturan offset dan evidence jelas;
- contoh valid lolos Pydantic;
- contoh invalid ditolak;
- reviewer klinis dapat menggunakan pedoman tanpa asumsi tambahan.
