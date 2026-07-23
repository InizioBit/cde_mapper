# Laporan Tahap 1 - Normalisasi Bahasa Indonesia

Dokumen ini adalah laporan implementasi Tahap 1 berdasarkan `Riset/LAPORAN_BASELINE.md` dan rencana implementasi pipeline riset.

## Tujuan

Tahap 1 bertujuan menambahkan lapisan normalisasi Bahasa Indonesia sebelum teks klinis diproses oleh komponen baseline CDE-Mapper. Lapisan ini menyiapkan input yang lebih stabil untuk tahap ekstraksi entitas, query decomposition, retrieval, dan reranking.

## Dasar dari Tahap 0

Tahap 0 menunjukkan bahwa baseline sudah dapat diaudit secara reproducible di WSL conda env `cde-mapper`, tetapi input baseline masih berorientasi data dictionary/CDE per baris. Gap utama untuk riset lanjutan adalah belum adanya normalisasi Bahasa Indonesia, singkatan medis lokal, typo lokal, dan audit intrinsic sebelum mapping terminologi.

## Artefak yang Dibuat

- `rag/id_preprocess.py`: modul normalisasi deterministik Bahasa Indonesia.
- `data/input/id_abbreviations.json`: kamus singkatan medis lokal.
- `data/input/id_abbreviations_layered.json`: kamus master berlapis dengan status ekspansi, konteks, ambiguitas, dan provenance.
- `data/input/id_typos.json`: kamus koreksi typo/ejaan tidak baku.
- `data/input/id_units.json`: kamus normalisasi satuan.
- `data/gold/id_normalization_gold.jsonl`: dataset uji kecil input-output normalisasi.
- `scripts/audit_id_preprocess.py`: skrip audit intrinsic normalisasi.
- `scripts/preprocess_alodokter.py`: runner normalisasi `question` dan `answer` untuk korpus Alodokter.
- `scripts/audit_id_preprocess_wsl.sh`: wrapper audit untuk WSL conda env `cde-mapper`.
- `Riset/id_preprocess_audit_result.json`: hasil audit runtime.
- `Riset/crawler_alodokter/hasil_normalisasi_tahap_1.jsonl`: artefak audit 150 pasangan konsultasi.
- `tests/test_id_preprocess.py`: unit test normalisasi, konteks, preservasi klinis, segmentasi, dan idempotensi.
- `Riset/LAPORAN_TAHAP_1_NORMALISASI.md`: laporan implementasi tahap ini.

## Desain Implementasi

Normalisasi dibuat deterministik dan ringan agar dapat dijalankan sebelum stack Qdrant, Athena, GPU, atau LLM aktif. Modul `rag/id_preprocess.py` tidak mengimpor komponen retrieval baseline sehingga dapat dipakai sebagai preprocessing awal maupun sebagai bagian dari smoke/audit test. Implementasi menyediakan profil `question` yang lebih aktif, profil `answer` yang konservatif, dan profil `clinical` untuk query CDE.

Urutan normalisasi:

1. Unicode dan casing: normalisasi NFKC, mengganti karakter tipografi umum, menghapus spasi tepi, dan menurunkan casing.
2. Karakter kontrol, separator, dan simbol: menstandarkan spasi di sekitar `/`, `%`, koma, dan titik koma tanpa merusak desimal seperti `2,5`.
3. Koreksi typo: mengganti variasi seperti `demem -> demam`, `diabetis -> diabetes`, dan `mellitus -> melitus`.
4. Ekspansi singkatan: menerapkan entri `automatic`, memeriksa aturan untuk `context_required`, mempertahankan entri ambigu, dan menghasilkan warning.
5. Normalisasi satuan: menjaga bentuk canonical seperti `mg/dL`, `g/dL`, `mmHg`, dan `x/menit`.
6. Final spacing: membersihkan spasi ganda dan spasi sebelum tanda baca.
7. Segmentasi kalimat: memisahkan kalimat berbasis baris dan tanda akhir tanpa memecah angka desimal.
8. Penandaan boilerplate: pada profil `answer`, sapaan dan penutup dipisahkan ke `boilerplate` dan `content_text` tanpa mengubah `normalized_text` lengkap.

Stemming Bahasa Indonesia belum diaktifkan. Keputusan ini sengaja diambil karena istilah klinis dan nama konsep dapat rusak jika stemming diterapkan tanpa evaluasi khusus.

### Strategi Kamus Singkatan Berlapis

Kamus perlu tersedia sebelum ekspansi singkatan diaktifkan. `data/input/id_abbreviations_layered.json` menjadi sumber master, sedangkan `data/input/id_abbreviations.json` mempertahankan format sederhana yang dibaca normalizer saat ini.

Lapisan master mencakup singkatan klinis, kesehatan ibu-anak, fungsi tubuh/pengukuran, dokumentasi klinis, percakapan informal, dan daftar ambigu. Setiap entri diberi status:

- `automatic`: cukup aman untuk ekspansi berbasis token utuh;
- `context_required`: hanya boleh diperluas jika konteks pendukung cocok;
- `review_required`: belum boleh diterapkan otomatis sebelum validasi ahli.

Entri ambigu seperti `dr`, `mg`, `TB`, `BB`, dan `Px` harus ditahan atau didisambiguasi. Kamus runtime saat ini masih mempertahankan beberapa entri lama yang bergantung konteks demi kompatibilitas; implementasi berikutnya perlu membuat pembaca kamus master agar hanya entri berstatus `automatic`, atau entri `context_required` yang lolos aturan, yang diterapkan.

## Contoh Perilaku

| Input | Output normalisasi |
|---|---|
| `Px dgn DM tipe 2, GDP 126 mg/dL, TD 150/90` | `pasien dengan diabetes melitus tipe 2, gula darah puasa 126 mg/dL, tekanan darah 150/90` |
| `Pasien demem dan batuk, spo2 95 %, n 88 x/menit` | `pasien demam dan batuk, saturasi oksigen 95%, nadi 88 x/menit` |
| `BB 70 kg, TB 165 cm, Hb 12 gr/dl` | `berat badan 70 kg, tinggi badan 165 cm, hemoglobin 12 g/dL` |
| `Riw HT, TD 160 / 100 mmhg` | `riwayat hipertensi, tekanan darah 160/100 mmHg` |

## Evaluasi Intrinsic

Audit dilakukan pada `data/gold/id_normalization_gold.jsonl` dengan metrik:

- exact normalized match;
- jumlah kasus yang berubah;
- jumlah penggantian typo, singkatan, dan satuan;
- error analysis per kasus.

Command audit:

```bash
wsl -e bash -lc "cd /mnt/d/Program/cde_mapper && bash scripts/audit_id_preprocess_wsl.sh"
```

Hasil audit terbaru disimpan di:

```text
Riset/id_preprocess_audit_result.json
```

Ringkasan hasil audit kompatibilitas:

- status: berhasil;
- jumlah kasus gold: `5`;
- exact normalized match: `1.0` atau `5/5`;
- changed cases: `5/5`;
- total penggantian typo: `3`;
- total ekspansi singkatan: `14`;
- total normalisasi satuan: `5`;
- tujuh unit test tambahan: seluruhnya lulus.

Runner Alodokter berhasil memproses 150 pasangan:

- kelompok perubahan pada pertanyaan: `269`;
- kelompok perubahan pada jawaban: `46`;
- warning konteks ambigu: `9`;
- teks asli, teks normalisasi, `content_text`, kalimat, perubahan, warning, boilerplate, dan versi resource tersimpan per record.

## Integrasi ke Pipeline

Integrasi tersedia secara opt-in:

```bash
python run.py ... --normalize_id --normalization_profile clinical
```

Fungsi `normalize_queries` menormalisasi `full_query` dan `base_entity`, serta mempertahankan teks awal melalui `original_label`. Baseline tidak berubah bila flag `--normalize_id` tidak diberikan.

Normalisasi korpus Alodokter dapat dijalankan dengan:

```bash
python scripts/preprocess_alodokter.py
```

Untuk tahap berikutnya, output normalisasi menjadi input bagi ekstraksi entitas klinis multi-entitas dari teks panjang.

## Batasan

- Kamus masih berupa seed lexicon dan entri klinis tetap memerlukan validasi ahli.
- Fuzzy matching typo tidak diterapkan otomatis agar tidak terjadi penggantian agresif pada istilah klinis.
- Aturan konteks saat ini deterministik dan terbatas pada singkatan berisiko tinggi; kasus yang tidak cukup jelas menghasilkan warning.
- Normalizer mempertahankan negasi dan temporalitas, tetapi klasifikasi assertion/temporal menjadi tanggung jawab Tahap 2.
- Segmentasi saat ini merupakan fallback rule-based; evaluasi model `indo_text_segmentation` masih dapat dilakukan sebagai eksperimen.
- Dataset gold berisi lima kasus dan unit test teknis, sehingga belum merupakan evaluasi final riset.

## Status

Status: Tahap 1 telah diimplementasikan secara end-to-end untuk normalisasi deterministik, kamus berlapis, disambiguasi konteks, profil `question`/`answer`, segmentasi, boilerplate, audit trail, integrasi opt-in, runner Alodokter, dan pengujian.
