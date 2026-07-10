# Laporan Tahap 1 - Normalisasi Bahasa Indonesia

Dokumen ini adalah laporan implementasi Tahap 1 berdasarkan `Riset/LAPORAN_BASELINE.md` dan rencana implementasi pipeline riset.

## Tujuan

Tahap 1 bertujuan menambahkan lapisan normalisasi Bahasa Indonesia sebelum teks klinis diproses oleh komponen baseline CDE-Mapper. Lapisan ini menyiapkan input yang lebih stabil untuk tahap ekstraksi entitas, query decomposition, retrieval, dan reranking.

## Dasar dari Tahap 0

Tahap 0 menunjukkan bahwa baseline sudah dapat diaudit secara reproducible di WSL conda env `cde-mapper`, tetapi input baseline masih berorientasi data dictionary/CDE per baris. Gap utama untuk riset lanjutan adalah belum adanya normalisasi Bahasa Indonesia, singkatan medis lokal, typo lokal, dan audit intrinsic sebelum mapping terminologi.

## Artefak yang Dibuat

- `rag/id_preprocess.py`: modul normalisasi deterministik Bahasa Indonesia.
- `data/input/id_abbreviations.json`: kamus singkatan medis lokal.
- `data/input/id_typos.json`: kamus koreksi typo/ejaan tidak baku.
- `data/input/id_units.json`: kamus normalisasi satuan.
- `data/gold/id_normalization_gold.jsonl`: dataset uji kecil input-output normalisasi.
- `scripts/audit_id_preprocess.py`: skrip audit intrinsic normalisasi.
- `scripts/audit_id_preprocess_wsl.sh`: wrapper audit untuk WSL conda env `cde-mapper`.
- `Riset/id_preprocess_audit_result.json`: hasil audit runtime.
- `Riset/LAPORAN_TAHAP_1_NORMALISASI.md`: laporan implementasi tahap ini.

## Desain Implementasi

Normalisasi dibuat deterministik dan ringan agar dapat dijalankan sebelum stack Qdrant, Athena, GPU, atau LLM aktif. Modul `rag/id_preprocess.py` tidak mengimpor komponen retrieval baseline sehingga dapat dipakai sebagai preprocessing awal maupun sebagai bagian dari smoke/audit test.

Urutan normalisasi:

1. Unicode dan casing: mengganti karakter tipografi umum, menghapus spasi tepi, dan menurunkan casing.
2. Separator dan simbol: menstandarkan spasi di sekitar `/`, `%`, koma, dan titik koma.
3. Koreksi typo: mengganti variasi seperti `demem -> demam`, `diabetis -> diabetes`, dan `mellitus -> melitus`.
4. Ekspansi singkatan: mengganti `px`, `dgn`, `dm`, `gdp`, `td`, `bb`, `tb`, `hb`, `spo2`, dan singkatan lokal lain.
5. Normalisasi satuan: menjaga bentuk canonical seperti `mg/dL`, `g/dL`, `mmHg`, dan `x/menit`.
6. Final spacing: membersihkan spasi ganda dan spasi sebelum tanda baca.

Stemming Bahasa Indonesia belum diaktifkan. Keputusan ini sengaja diambil karena istilah klinis dan nama konsep dapat rusak jika stemming diterapkan tanpa evaluasi khusus.

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

Ringkasan hasil eksekusi pada WSL conda env `cde-mapper`:

- status: berhasil;
- Python: `3.10.19`;
- platform: WSL2 Linux;
- jumlah kasus gold: `5`;
- exact normalized match: `1.0` atau `5/5`;
- changed cases: `5/5`;
- total penggantian typo: `3`;
- total ekspansi singkatan: `14`;
- total normalisasi satuan: `5`;
- durasi audit: `0.0292` detik.

## Integrasi ke Pipeline

Integrasi awal yang disarankan:

- jalankan `normalize_text` sebelum `load_data` memanggil `map_data` untuk input custom Bahasa Indonesia;
- atau normalisasi `QueryDecomposedModel.full_query` sebelum query decomposition;
- simpan `original_text` dan `normalized_text` pada artefak audit agar perubahan tetap dapat ditelusuri.

Untuk tahap berikutnya, output normalisasi menjadi input bagi ekstraksi entitas klinis multi-entitas dari teks panjang.

## Batasan

- Kamus masih kecil dan bersifat seed lexicon.
- Fuzzy matching typo belum diaktifkan agar tidak terjadi penggantian agresif pada istilah klinis.
- Normalisasi belum menangani negasi, temporalitas, atau segmentasi multi-kalimat secara mendalam; aspek tersebut masuk Tahap 2.
- Dataset gold masih kecil sehingga hanya layak sebagai smoke/intrinsic test awal, bukan evaluasi final riset.

## Status

Status: Tahap 1 sudah memiliki modul normalisasi, kamus awal, gold set kecil, skrip audit reproducible, dan laporan implementasi.
