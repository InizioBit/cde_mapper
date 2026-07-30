# Audit Ketidaksesuaian Label ICD-10

## Ruang Lingkup

Audit ini memeriksa dua file:

- `Riset/data/Hospital C.csv`
- `Riset/data/Hospital D.csv`

Kolom yang dianalisis:

- `kode_diagnosa`: label ICD-10 yang dipakai sebagai target.
- `subjective`: teks klinis atau catatan yang menjadi input.

Audit dilakukan dengan dua pendekatan:

1. Pemeriksaan otomatis terhadap kode ICD-10 yang tertulis eksplisit di kolom `subjective`, terutama pola `Utama : ...` dan `Tambahan : ...`.
2. Penilaian berbasis pengetahuan ICD-10 terhadap kecocokan makna diagnosis dan label.

Catatan penting: audit ini bukan pengganti validasi coder medis tersertifikasi. Namun, hasilnya cukup kuat untuk menemukan kandidat salah label, label tambahan yang diperlakukan sebagai label utama, dan teks input yang tidak cukup mendukung label.

## Ringkasan Temuan

File temuan awal tersimpan di:

`Riset/data/temuan_awal_ketidaksesuaian_icd10.csv`

Jumlah kandidat masalah yang ditemukan: **4.653 baris**.

| File | Pola Masalah | Jumlah Baris |
|---|---:|---:|
| Hospital C.csv | Label hanya muncul sebagai diagnosis tambahan | 2.182 |
| Hospital C.csv | Teks memuat kode ICD lain tanpa memuat label | 1.668 |
| Hospital C.csv | Kode `Utama` berbeda dari label | 3 |
| Hospital D.csv | Kode `Utama` berbeda dari label | 733 |
| Hospital D.csv | Label hanya muncul sebagai diagnosis tambahan | 412 |
| Hospital D.csv | Teks memuat kode ICD lain tanpa memuat label | 390 |

## Ringkasan Per Label

### Hospital C

| Label | Total | Tanpa Kode ICD Tertulis | Memuat Label | Kode Lain Tanpa Label | Utama Beda | Label Hanya Tambahan |
|---|---:|---:|---:|---:|---:|---:|
| I10 | 10.024 | 7.917 | 1.112 | 995 | 1 | 791 |
| K30 | 9.572 | 8.176 | 1.028 | 368 | 1 | 564 |
| R11 | 5.016 | 4.271 | 569 | 176 | 0 | 301 |
| A09 | 2.269 | 1.431 | 784 | 54 | 0 | 162 |
| E11 | 1.000 | 488 | 467 | 45 | 0 | 340 |
| N18 | 526 | 207 | 294 | 25 | 1 | 9 |
| J18 | 39 | 25 | 14 | 0 | 0 | 14 |
| J06 | 31 | 23 | 3 | 5 | 0 | 1 |
| Z09 | 3 | 3 | 0 | 0 | 0 | 0 |
| O82 | 1 | 0 | 1 | 0 | 0 | 0 |

### Hospital D

| Label | Total | Tanpa Kode ICD Tertulis | Memuat Label | Kode Lain Tanpa Label | Utama Beda | Label Hanya Tambahan |
|---|---:|---:|---:|---:|---:|---:|
| J06.9 | 3.720 | 3.076 | 545 | 99 | 196 | 103 |
| Z00.1 | 3.089 | 1.015 | 2.069 | 5 | 29 | 49 |
| Z34.8 | 2.389 | 2.243 | 142 | 4 | 2 | 4 |
| P03.4 | 2.177 | 1.953 | 155 | 69 | 75 | 6 |
| O82.0 | 2.176 | 2.130 | 43 | 3 | 1 | 1 |
| P22.0 | 2.019 | 1.538 | 438 | 43 | 104 | 61 |
| A09 | 1.908 | 1.611 | 259 | 38 | 92 | 71 |
| A49.9 | 1.630 | 1.531 | 41 | 58 | 70 | 12 |
| J00 | 1.584 | 929 | 650 | 5 | 57 | 54 |
| J18.0 | 1.532 | 1.224 | 253 | 55 | 89 | 34 |
| Y59.9 | 1.462 | 324 | 1.137 | 1 | 18 | 17 |
| Z01.4 | 1.461 | 1.430 | 21 | 10 | 0 | 0 |

## Interpretasi Berdasarkan ICD-10

### 1. Label `K30` sering tidak didukung oleh teks

`K30` adalah dyspepsia. Label ini wajar jika teks memuat keluhan atau diagnosis seperti dispepsia, epigastric pain, nyeri ulu hati, mual terkait lambung, gastritis fungsional, atau gangguan pencernaan atas.

Namun pada Hospital C, banyak baris berlabel `K30` berisi teks seperti:

- bacterial infection
- ISPA
- vertigo
- febris
- cellulitis
- observation for suspected tuberculosis

Contoh eksplisit:

| File | Line | Label | Kode/Teks yang Lebih Menonjol |
|---|---:|---|---|
| Hospital C.csv | 293 | K30 | `L03.1 Cellulitis of other parts of limb` |
| Hospital C.csv | 299 | K30 | `L03.1` dan `Z03.0 Observation for suspected tuberculosis` |
| Hospital C.csv | 26180 | K30 | `A16.2 Tuberculosis of lung...` sebagai diagnosis utama |

Analisis: jika tujuan dataset adalah prediksi diagnosis utama, baris seperti ini seharusnya tidak berlabel `K30`. Jika `K30` hanya diagnosis tambahan, dataset perlu diubah menjadi multi-label atau label utama harus diganti sesuai diagnosis utama.

### 2. Label `R11` tercampur dengan diagnosis penyakit

`R11` adalah nausea and vomiting. Kode ini adalah kode gejala, bukan diagnosis etiologis. Label ini cocok jika masalah utama memang mual/muntah tanpa diagnosis penyakit yang lebih spesifik.

Pada Hospital C, sebagian baris `R11` memang memuat nausea/vomitus. Namun ada juga teks yang memuat diagnosis lain seperti fatty liver, abdominal pain, dyspepsia, ascites, atau catatan keperawatan umum.

Analisis: `R11` perlu dibedakan antara gejala utama dan gejala tambahan. Jika diagnosis penyebab sudah diketahui, kode penyakit biasanya lebih tepat sebagai label utama daripada `R11`.

### 3. Label `A09` tidak selalu berarti semua diare atau infeksi

`A09` adalah gastroenteritis and colitis of infectious and unspecified origin. Kode ini cocok untuk gastroenteritis, enterocolitis, diare infeksius, atau GEA.

Masalah yang ditemukan:

- Ada baris `A09` dengan diagnosis utama lain seperti rhinitis alergi, bacterial infection unspecified, convulsions, atau injury.
- Ada juga teks yang hanya menyebut nausea tanpa diare/gastroenteritis.

Contoh:

| File | Line | Label | Kode Utama Tertulis |
|---|---:|---|---|
| Hospital D.csv | 302 | A09 | `J30.4 Allergic rhinitis, unspecified` |
| Hospital D.csv | 436 | A09 | `A49.9 Bacterial infection, unspecified` |
| Hospital D.csv | 476 | A09 | `R56 Convulsions` |
| Hospital D.csv | 735 | A09 | `S59.9 Unspecified injury of forearm` |

Analisis: baris `A09` yang hanya muncul sebagai `Tambahan` perlu dipisahkan dari diagnosis utama. Jika dataset single-label, label harus mengikuti diagnosis utama yang benar.

### 4. `J00`, `J06.9`, dan `J18.0` sering tertukar dalam spektrum respirasi

Makna kode:

- `J00`: acute nasopharyngitis atau common cold.
- `J06.9`: acute upper respiratory infection, unspecified.
- `J18.0`: bronchopneumonia, unspecified.

Ketiganya berada dalam kelompok respirasi, tetapi level klinisnya berbeda. Common cold/ISPA atas tidak sama dengan pneumonia atau bronkopneumonia.

Contoh mismatch:

| File | Line | Label | Kode Utama Tertulis |
|---|---:|---|---|
| Hospital D.csv | 61 | J00 | `R50.9 Fever, unspecified`; `J00` hanya tambahan |
| Hospital D.csv | 258 | J06.9 | `J02 Acute pharyngitis`; `J06.9` hanya tambahan |
| Hospital D.csv | 899 | J18.0 | `J06.8 Other acute upper respiratory infections`; `J18.0` hanya tambahan |
| Hospital D.csv | 1769 | J18.0 | `J21 Acute bronchiolitis` |

Analisis: untuk model klasifikasi, pencampuran ini berbahaya karena kata seperti batuk, pilek, sesak, demam, dan ISPA dapat muncul pada banyak kode. Label harus dipastikan apakah merujuk diagnosis utama, diagnosis tambahan, atau semua diagnosis.

### 5. `A49.9` terlalu umum dan sering dipakai untuk febris/dugaan infeksi

`A49.9` adalah bacterial infection, unspecified. Kode ini cocok jika infeksi bakteri memang didiagnosis tetapi lokasinya tidak spesifik.

Masalah:

- Teks seperti `susp bacterial infection`, `febris`, atau `viral infection` tidak selalu cukup untuk `A49.9`.
- Jika lokasi atau penyakit spesifik ada, kode lebih spesifik biasanya lebih tepat.

Contoh mismatch:

| File | Line | Label | Kode Utama Tertulis |
|---|---:|---|---|
| Hospital D.csv | 1159 | A49.9 | `D50.9 Iron deficiency anaemia` |
| Hospital D.csv | beberapa baris | A49.9 | `A04.9`, `B34`, atau diagnosis infeksi lain yang lebih spesifik |

Analisis: label `A49.9` perlu diaudit ketat karena kode ini sering menjadi "keranjang umum" untuk demam atau dugaan infeksi.

### 6. `Y59.9` tampak bermasalah untuk kunjungan vaksinasi biasa

`Y59.9` adalah vaccine or biological substance, unspecified, dalam konteks penyebab luar/adverse effect. Kode ini bukan kode utama yang lazim untuk kunjungan imunisasi rutin.

Pada data Hospital D, banyak teks berisi:

- `Pro inj gardasil`
- vaksin gardasil dosis ke-3
- routine child health examination
- kesiapan peningkatan manajemen kesehatan

Analisis: jika konteksnya adalah tindakan imunisasi/profilaksis tanpa adverse event, kode yang lebih sesuai biasanya berada pada kelompok encounter for immunization, misalnya `Z23`. `Y59.9` lebih tepat jika ada efek samping atau komplikasi akibat vaksin/biological substance. Ini termasuk kandidat kuat salah label konseptual.

### 7. `Z00.1` tidak sama dengan semua kunjungan anak

`Z00.1` adalah routine child health examination. Label ini cocok untuk pemeriksaan kesehatan anak rutin.

Masalah:

- Beberapa baris memuat `Y59.9` sebagai diagnosis utama.
- Banyak teks hanya berupa diagnosis keperawatan seperti `Kesiapan peningkatan manajemen kesehatan`, tanpa informasi pemeriksaan kesehatan anak.

Analisis: jika tidak ada konteks child health examination, label `Z00.1` kurang didukung. Jika baris memuat diagnosis utama lain, label perlu dikoreksi.

### 8. `Z34.8` perlu hati-hati jika ada komplikasi kehamilan

`Z34.8` adalah supervision of other normal pregnancy. Kode ini cocok untuk kontrol kehamilan normal.

Masalah:

- Teks seperti `susp ISK`, `miopia tinggi`, atau masalah klinis lain dapat mengubah konteks dari pengawasan kehamilan normal menjadi kehamilan dengan kondisi penyerta atau komplikasi.
- Banyak baris hanya menyebut usia kehamilan tanpa diagnosis medis lain. Ini mungkin masih cocok, tetapi tetap perlu konteks kunjungan.

Analisis: `Z34.8` sebaiknya dipakai untuk kehamilan normal. Jika ada komplikasi atau kondisi patologis yang menjadi alasan kunjungan, label utama mungkin perlu kode obstetri lain.

### 9. `O82.0` tidak selalu didukung oleh catatan persalinan

`O82.0` adalah delivery by elective caesarean section. Label ini cocok jika benar terjadi persalinan melalui sectio caesarea elektif.

Masalah:

- Banyak teks hanya berisi `kesiapan persalinan`, `BSC 2x`, atau catatan ansietas/pasca partum.
- Riwayat SC atau rencana persalinan tidak otomatis sama dengan `O82.0`.

Analisis: perlu dibedakan antara riwayat caesarean section, persiapan operasi, persalinan aktual, dan jenis SC elektif.

### 10. Label neonatal `P03.4` dan `P22.0` perlu validasi klinis

Makna kode:

- `P03.4`: newborn affected by caesarean delivery.
- `P22.0`: respiratory distress syndrome of newborn.

Masalah:

- Banyak teks berisi diagnosis keperawatan seperti risiko hipotermi, risiko jatuh, menyusui tidak efektif, risiko infeksi.
- Beberapa baris `P22.0` memiliki diagnosis utama lain seperti `Q21.3`, `H35.1`, `K40`, `Q25.0`, atau `P24.0`.
- Beberapa baris `P03.4` memiliki diagnosis utama `P22.1`, `P22.0`, `P24.0`, `Z38.0`, atau bahkan kode maternal seperti `O82.0`.

Analisis: diagnosis keperawatan bayi baru lahir tidak cukup untuk menentukan `P03.4` atau `P22.0`. `P22.0` membutuhkan konteks respiratory distress syndrome neonatal, bukan sekadar "pola napas tidak efektif" tanpa diagnosis medis. `P03.4` membutuhkan hubungan bayi terdampak oleh persalinan caesarean, bukan sekadar bayi lahir atau perawatan neonatal rutin.

## Pola Ketidaksesuaian Paling Penting

### A. Label berbeda dari `Utama`

Ini kategori paling kuat sebagai kandidat salah label jika dataset dimaksudkan untuk prediksi diagnosis utama.

Contoh pola terbanyak:

| Pola | Jumlah |
|---|---:|
| `P22.0 -> Q21.3` | 58 |
| `J06.9 -> R50.9` | 32 |
| `J06.9 -> R50` | 24 |
| `Z00.1 -> Y59.9` | 23 |
| `P22.0 -> H35.1` | 22 |
| `P22.0 -> K40` | 21 |
| `A09 -> R10.4` | 20 |
| `P03.4 -> P22.1` | 19 |
| `J18.0 -> J15.9` | 19 |

Interpretasi: tanda panah berarti label CSV berada di kiri, sedangkan kode `Utama` yang tertulis di teks berada di kanan. Misalnya `P22.0 -> Q21.3` berarti baris dilabeli neonatal respiratory distress syndrome, tetapi diagnosis utamanya tertulis tetralogy of Fallot.

### B. Label hanya muncul sebagai `Tambahan`

Ini bukan selalu salah secara klinis, tetapi salah untuk desain dataset single-label diagnosis utama.

Contoh:

- Label `A09`, tetapi `Utama : J30.4`, sedangkan `A09` hanya `Tambahan`.
- Label `J00`, tetapi `Utama : R50.9`, sedangkan `J00` hanya `Tambahan`.
- Label `J18.0`, tetapi `Utama : J06.8`, sedangkan `J18.0` hanya `Tambahan`.

Jika riset ingin memprediksi semua diagnosis pasien, dataset harus dibuat multi-label. Jika riset ingin memprediksi diagnosis utama, baris seperti ini perlu direlabel.

### C. Teks berupa diagnosis keperawatan, bukan diagnosis medis ICD-10

Banyak baris berisi kode SDKI seperti:

- `D.0001 Bersihan jalan nafas tidak efektif`
- `D.0076 Nausea`
- `D.0080 Ansietas`
- `D.0140 Risiko hipotermi`
- `D.0143 Risiko jatuh`

Ini bukan kode ICD-10. Diagnosis keperawatan dapat menjadi sinyal klinis, tetapi tidak cukup kuat sebagai ground truth ICD-10 tanpa diagnosis medis dokter.

## Rekomendasi Pembersihan Data

1. Pisahkan dataset menjadi dua skenario: prediksi diagnosis utama single-label dan prediksi seluruh diagnosis multi-label.

2. Untuk single-label, gunakan kode setelah `Utama :` sebagai label target. Jika ada beberapa `Utama`, pilih aturan yang eksplisit, misalnya diagnosis utama pertama atau berdasarkan urutan coder.

3. Baris dengan label hanya sebagai `Tambahan` jangan dipakai sebagai single-label tanpa koreksi. Pilih salah satu:
   - ubah label menjadi kode `Utama`;
   - ubah dataset menjadi multi-label;
   - keluarkan dari training set.

4. Baris tanpa kode ICD tertulis dan hanya berisi diagnosis keperawatan perlu diberi status `low_confidence`. Jangan dipakai sebagai data training utama sebelum divalidasi coder.

5. Audit manual prioritas tinggi sebaiknya dimulai dari:
   - `Hospital D.csv` dengan kategori `label_berbeda_dari_utama`;
   - `Hospital C.csv` kategori `label_hanya_tambahan`;
   - label `K30`, `A09`, `J06.9`, `A49.9`, `Y59.9`, `P03.4`, dan `P22.0`.

6. Untuk model ICD-10, hindari mencampur kode gejala, diagnosis penyakit, encounter, external cause, obstetri, dan neonatal tanpa strategi klasifikasi yang jelas. Contohnya `R11`, `Z00.1`, `Y59.9`, `O82.0`, dan `P22.0` memiliki logika coding yang sangat berbeda.

## Kesimpulan

Data pelabelan ICD-10 di `Riset/data` mengandung ketidaksesuaian yang cukup signifikan. Masalah terbesar bukan hanya salah ketik kode, tetapi ketidakkonsistenan definisi label: sebagian label mewakili diagnosis utama, sebagian diagnosis tambahan, sebagian gejala, sebagian encounter, dan sebagian lagi tampak berasal dari catatan keperawatan.

Jika dataset ini langsung dipakai untuk pelatihan model prediksi ICD-10, model berisiko belajar pola yang keliru. Misalnya, teks ISPA dapat belajar ke `K30`, teks vaksinasi rutin dapat belajar ke `Y59.9`, atau catatan neonatal umum dapat belajar ke `P22.0`. Sebelum eksperimen model dilanjutkan, dataset perlu dibersihkan dengan aturan label yang tegas dan validasi manual pada baris prioritas tinggi.
