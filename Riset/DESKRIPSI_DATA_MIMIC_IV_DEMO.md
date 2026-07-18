# Deskripsi Data MIMIC-IV Clinical Database Demo 2.2

## Ringkasan

Folder `Riset/mimic-iv-clinical-database-demo-2.2` berisi **MIMIC-IV Clinical Database Demo v2.2**, yaitu subset terbuka dari MIMIC-IV yang terdiri dari **100 pasien**. Data ini berasal dari rekam medis elektronik terdeidentifikasi pasien yang dirawat di Beth Israel Deaconess Medical Center.

Demo ini disediakan untuk keperluan workshop, eksplorasi awal, dan penilaian kelayakan studi sebelum memakai MIMIC-IV penuh. Dataset demo ini **tidak menyertakan free-text clinical notes**.

File utama pendukung:

- `README.txt`: penjelasan singkat dataset demo.
- `LICENSE.txt`: lisensi ODbL.
- `SHA256SUMS.txt`: checksum file.
- `demo_subject_id.csv`: daftar `subject_id` pasien yang tersedia dalam demo.

## Struktur Folder

Dataset dibagi menjadi dua modul utama:

```text
mimic-iv-clinical-database-demo-2.2/
  hosp/
  icu/
  demo_subject_id.csv
  README.txt
  LICENSE.txt
  SHA256SUMS.txt
```

### Modul `hosp`

Folder `hosp` berisi data level rumah sakit, seperti demografi pasien, rawat inap, diagnosis, prosedur, hasil laboratorium, order obat, pharmacy, administrasi obat, transfer, dan layanan klinis.

### Modul `icu`

Folder `icu` berisi data level ICU, seperti ICU stay, chart events, input cairan/obat, output, prosedur ICU, datetime events, dan kamus item ICU.

## Kunci Relasi Data

Beberapa kolom penting yang menghubungkan tabel:

| Kolom | Makna |
|---|---|
| `subject_id` | ID pasien terdeidentifikasi. |
| `hadm_id` | ID hospital admission atau episode rawat inap. |
| `stay_id` | ID episode ICU. |
| `itemid` | ID item lokal MIMIC untuk lab, chart event, atau ICU event. |
| `icd_code` | Kode diagnosis/prosedur ICD. |
| `icd_version` | Versi ICD, misalnya ICD-9 atau ICD-10. |
| `poe_id` | Provider order entry ID. |
| `pharmacy_id` | ID order farmasi. |
| `emar_id` | ID administrasi obat elektronik. |

Relasi umum:

```text
patients.subject_id
  -> admissions.subject_id
      -> diagnoses_icd.hadm_id
      -> procedures_icd.hadm_id
      -> labevents.hadm_id
      -> prescriptions.hadm_id
      -> pharmacy.hadm_id
      -> transfers.hadm_id
      -> icustays.hadm_id
          -> chartevents.stay_id
          -> inputevents.stay_id
          -> outputevents.stay_id
          -> procedureevents.stay_id
```

## Daftar Tabel dan Jumlah Baris

Jumlah baris berikut termasuk header CSV, sehingga jumlah record data aktual adalah `baris - 1`.

### Tabel Umum

| File | Isi | Baris |
|---|---|---:|
| `demo_subject_id.csv` | Daftar pasien demo | 101 |

### Tabel `hosp`

| File | Isi | Baris |
|---|---|---:|
| `hosp/patients.csv` | Demografi pasien | 101 |
| `hosp/admissions.csv` | Episode rawat inap | 276 |
| `hosp/transfers.csv` | Perpindahan lokasi/unit pasien | 1191 |
| `hosp/services.csv` | Perubahan layanan klinis | 320 |
| `hosp/provider.csv` | Provider ID | 40509 |
| `hosp/diagnoses_icd.csv` | Diagnosis ICD per admission | 4507 |
| `hosp/procedures_icd.csv` | Prosedur ICD per admission | 723 |
| `hosp/d_icd_diagnoses.csv` | Kamus diagnosis ICD | 109776 |
| `hosp/d_icd_procedures.csv` | Kamus prosedur ICD | 85258 |
| `hosp/d_hcpcs.csv` | Kamus HCPCS | 89201 |
| `hosp/hcpcsevents.csv` | Event HCPCS | 62 |
| `hosp/drgcodes.csv` | DRG code per admission | 455 |
| `hosp/labevents.csv` | Hasil pemeriksaan laboratorium | 107728 |
| `hosp/d_labitems.csv` | Kamus item laboratorium | 1623 |
| `hosp/microbiologyevents.csv` | Pemeriksaan mikrobiologi | 2900 |
| `hosp/prescriptions.csv` | Resep obat | 18088 |
| `hosp/pharmacy.csv` | Detail order farmasi | 15307 |
| `hosp/poe.csv` | Provider order entry | 45155 |
| `hosp/poe_detail.csv` | Detail order entry | 3796 |
| `hosp/emar.csv` | Electronic medication administration record | 35836 |
| `hosp/emar_detail.csv` | Detail administrasi obat | 72019 |
| `hosp/omr.csv` | Online medical record measurements | 2965 |

### Tabel `icu`

| File | Isi | Baris |
|---|---|---:|
| `icu/icustays.csv` | Episode ICU | 141 |
| `icu/caregiver.csv` | Caregiver ID | 15469 |
| `icu/d_items.csv` | Kamus item ICU | 4015 |
| `icu/chartevents.csv` | Observasi/chart ICU, termasuk vital sign dan device data | 668863 |
| `icu/datetimeevents.csv` | Event ICU bernilai waktu/tanggal | 15281 |
| `icu/inputevents.csv` | Input cairan/obat ICU | 20405 |
| `icu/ingredientevents.csv` | Ingredient dari input events | 25729 |
| `icu/outputevents.csv` | Output cairan ICU | 9363 |
| `icu/procedureevents.csv` | Prosedur ICU | 1469 |

## Deskripsi Tabel Penting

### `hosp/patients.csv`

Berisi satu baris per pasien. Kolom penting:

- `subject_id`: ID pasien.
- `gender`: jenis kelamin.
- `anchor_age`: usia terdeidentifikasi.
- `anchor_year`: tahun anchor terdeidentifikasi.
- `anchor_year_group`: rentang tahun sumber.
- `dod`: date of death jika tersedia.

### `hosp/admissions.csv`

Berisi episode rawat inap. Kolom penting:

- `subject_id`, `hadm_id`: penghubung pasien dan admission.
- `admittime`, `dischtime`, `deathtime`: waktu masuk, keluar, dan meninggal.
- `admission_type`: tipe admission.
- `admission_location`, `discharge_location`: lokasi masuk dan keluar.
- `insurance`, `language`, `marital_status`, `race`: atribut administrasi/demografi.
- `hospital_expire_flag`: indikator meninggal saat rawat inap.

### `hosp/diagnoses_icd.csv`

Berisi diagnosis ICD untuk tiap admission.

- `subject_id`, `hadm_id`: pasien dan admission.
- `seq_num`: urutan diagnosis.
- `icd_code`, `icd_version`: kode dan versi ICD.

Kamus penjelasnya berada pada `hosp/d_icd_diagnoses.csv`.

### `hosp/procedures_icd.csv`

Berisi prosedur ICD untuk admission tertentu.

- `subject_id`, `hadm_id`: pasien dan admission.
- `seq_num`: urutan prosedur.
- `chartdate`: tanggal prosedur.
- `icd_code`, `icd_version`: kode dan versi ICD.

Kamus penjelasnya berada pada `hosp/d_icd_procedures.csv`.

### `hosp/labevents.csv`

Berisi hasil pemeriksaan laboratorium.

- `labevent_id`: ID event lab.
- `subject_id`, `hadm_id`: pasien dan admission.
- `itemid`: kode item lab.
- `charttime`, `storetime`: waktu pemeriksaan dan penyimpanan.
- `value`, `valuenum`, `valueuom`: nilai lab dalam bentuk teks/numerik dan satuan.
- `ref_range_lower`, `ref_range_upper`: rentang referensi.
- `flag`: penanda abnormal.

Kamus item lab berada pada `hosp/d_labitems.csv`.

### `hosp/prescriptions.csv`, `hosp/pharmacy.csv`, `hosp/emar.csv`

Tabel-tabel ini berkaitan dengan obat:

- `prescriptions.csv`: data resep, obat, dosis, route.
- `pharmacy.csv`: detail order farmasi, waktu mulai/berhenti, frekuensi, route, dispensation.
- `emar.csv`: administrasi obat elektronik.
- `emar_detail.csv`: detail dosis diberikan, route, site, infusion rate, barcode, dan informasi administrasi.

Kolom relasi penting:

- `subject_id`
- `hadm_id`
- `pharmacy_id`
- `poe_id`
- `emar_id`

### `hosp/transfers.csv` dan `hosp/services.csv`

`transfers.csv` merekam perpindahan pasien antar unit/lokasi.

Kolom penting:

- `transfer_id`
- `eventtype`
- `careunit`
- `intime`, `outtime`

`services.csv` merekam perubahan layanan klinis.

Kolom penting:

- `transfertime`
- `prev_service`
- `curr_service`

### `icu/icustays.csv`

Berisi episode ICU.

- `subject_id`, `hadm_id`, `stay_id`: pasien, admission, ICU stay.
- `first_careunit`, `last_careunit`: unit ICU awal dan akhir.
- `intime`, `outtime`: waktu masuk dan keluar ICU.
- `los`: length of stay ICU.

### `icu/chartevents.csv`

Tabel terbesar dalam demo ini. Berisi observasi ICU seperti vital signs, setting alat, assessment, atau catatan terstruktur lain.

Kolom penting:

- `subject_id`, `hadm_id`, `stay_id`
- `caregiver_id`
- `charttime`, `storetime`
- `itemid`
- `value`, `valuenum`, `valueuom`
- `warning`

Makna `itemid` dijelaskan di `icu/d_items.csv`.

### `icu/inputevents.csv`

Berisi input cairan/obat di ICU, termasuk infusion atau drug push.

Kolom penting:

- `starttime`, `endtime`, `storetime`
- `itemid`
- `amount`, `amountuom`
- `rate`, `rateuom`
- `orderid`, `linkorderid`
- `ordercategoryname`
- `patientweight`
- `statusdescription`

### `icu/outputevents.csv`

Berisi output cairan ICU, misalnya urine output atau drain output.

Kolom penting:

- `charttime`, `storetime`
- `itemid`
- `value`, `valueuom`

### `icu/procedureevents.csv`

Berisi tindakan/prosedur ICU.

Kolom penting:

- `starttime`, `endtime`, `storetime`
- `itemid`
- `value`, `valueuom`
- `location`, `locationcategory`
- `ordercategoryname`
- `statusdescription`

## Kamus Item

### `hosp/d_labitems.csv`

Kamus untuk item laboratorium.

Kolom:

- `itemid`
- `label`
- `fluid`
- `category`

Contoh item: `Lactate`, `Free Calcium`, `Hematocrit`.

### `icu/d_items.csv`

Kamus untuk item ICU.

Kolom:

- `itemid`
- `label`
- `abbreviation`
- `linksto`
- `category`
- `unitname`
- `param_type`
- `lownormalvalue`
- `highnormalvalue`

Kolom `linksto` membantu mengetahui tabel event mana yang memakai item tersebut, misalnya `chartevents`, `inputevents`, atau `procedureevents`.

## Karakteristik Data

1. **Data longitudinal**

   Satu pasien dapat memiliki beberapa admission. Satu admission dapat memiliki satu atau lebih ICU stay, lab event, order, resep, dan transfer.

2. **Data time-series**

   Tabel seperti `labevents`, `chartevents`, `inputevents`, dan `outputevents` memiliki timestamp sehingga cocok untuk analisis temporal.

3. **Data terminologi campuran**

   Dataset memakai beberapa sistem kode:

   - ICD untuk diagnosis dan prosedur.
   - HCPCS untuk event tertentu.
   - Item lokal MIMIC untuk lab dan ICU events.
   - Nama obat dan formulary code untuk medication.

4. **Data terdeidentifikasi**

   Tanggal, usia, dan identitas pasien telah digeser/dideidentifikasi. Tanggal tidak boleh ditafsirkan sebagai tanggal dunia nyata.

5. **Tidak ada catatan bebas**

   Folder demo ini tidak berisi clinical notes. Semua data berbentuk tabel terstruktur.

## Relevansi Untuk Pipeline CDE/OMOP Mapping

Dataset ini relevan untuk riset mapping karena menyediakan banyak kandidat variabel klinis nyata yang perlu dinormalisasi ke konsep standar.

Contoh kandidat variabel:

- Demografi/administratif:
  - `gender`
  - `race`
  - `insurance`
  - `language`
  - `marital_status`
  - `hospital_expire_flag`

- Visit/admission:
  - `admission_type`
  - `admission_location`
  - `discharge_location`
  - `first_careunit`
  - `last_careunit`
  - `los`

- Measurement/laboratorium:
  - `Lactate`
  - `Free Calcium`
  - `Hematocrit`
  - item lain dari `d_labitems.csv`

- ICU observation:
  - vital sign dan device settings dari `chartevents.csv`
  - item ICU dari `d_items.csv`

- Drug:
  - `Fentanyl Citrate`
  - `Lorazepam`
  - `Midazolam`
  - obat lain dari `prescriptions.csv` dan `pharmacy.csv`

- Condition/procedure:
  - diagnosis ICD dari `diagnoses_icd.csv`
  - prosedur ICD dari `procedures_icd.csv`

## Potensi Tahapan Pemanfaatan

1. **Inventaris variabel**

   Ambil nama kolom, label item lab, label item ICU, nama obat, diagnosis, dan prosedur sebagai kandidat CDE.

2. **Normalisasi terminologi**

   Bersihkan label, satuan, kategori, dan konteks tabel.

3. **Klasifikasi domain**

   Kelompokkan kandidat ke domain OMOP seperti:

   - Person
   - Visit
   - Observation
   - Measurement
   - Drug
   - Condition
   - Procedure
   - Unit

4. **Mapping ke OMOP**

   Gunakan pipeline retrieval/LLM untuk memetakan label MIMIC ke OMOP concept.

5. **Evaluasi**

   Gunakan kamus seperti ICD, lab item, dan struktur tabel sebagai gold/reference parsial untuk memeriksa kualitas mapping.

## Catatan Kualitas dan Kehati-hatian

- Dataset ini hanya demo 100 pasien, sehingga tidak representatif untuk analisis epidemiologi final.
- Jumlah event besar pada `chartevents` dan `labevents`, tetapi variasi pasien terbatas.
- Kode lokal MIMIC seperti `itemid` perlu diterjemahkan melalui dictionary sebelum dimaknai.
- Untuk mapping OMOP, label item saja sering belum cukup; konteks tabel, kategori, unit, dan domain klinis perlu dipakai.
- Tanggal telah dideidentifikasi sehingga analisis waktu relatif masih mungkin, tetapi tanggal absolut tidak bermakna secara kalender nyata.

## Kesimpulan

`mimic-iv-clinical-database-demo-2.2` adalah dataset demo EHR terstruktur yang cukup kaya untuk eksperimen awal pipeline CDE mapping. Data ini mencakup pasien, admission, ICU stay, diagnosis, prosedur, lab, obat, transfer, dan event ICU. Untuk riset ini, dataset dapat dipakai sebagai sumber kandidat variabel klinis nyata, bahan evaluasi domain mapping, dan uji coba normalisasi terminologi ke OMOP.
