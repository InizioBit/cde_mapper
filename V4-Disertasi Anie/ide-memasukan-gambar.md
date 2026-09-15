**Menurut saya, sebagian gambar layak dimasukkan kembali secara selektif.** Tujuannya membantu pembaca memahami metode, sambil mempertahankan keringkasan Bab III. Berdasarkan gambar dan materi versi lama yang sebelumnya kita tinjau, saya menyarankan keputusan berikut.

## 1. Gambar LLM dan arsitekturnya

| Materi versi lama | Saran | Alasan |
|---|---|---|
| **Evolusi LLM** | Tidak perlu dimasukkan kembali | Sejarah perkembangan model tidak langsung menjelaskan kontribusi penelitian. |
| **Arsitektur Transformer** | Opsional | Berguna jika pembaca membutuhkan penjelasan mekanisme perhatian, tetapi diagram lengkap encoder–decoder lebih rinci daripada kebutuhan pipeline. |
| **BERT, GPT, T5, dan LLaMA** | Ringkas menjadi satu diagram peran model | Yang perlu terlihat adalah hubungan model dengan tugas: representasi teks, ekstraksi, dekomposisi, dan reranking. |
| **Detail arsitektur, pretraining, dan benchmark LLaMA** | Tetap dikeluarkan | Penelitian mengadaptasi pipeline pemetaan; detail pelatihan LLaMA tidak menjadi variabel penelitian. |

**Pilihan terbaik:** satu diagram sederhana pada bagian **“LLM untuk Ekstraksi dan Dekomposisi Kueri”**, yang menunjukkan:

```text
Teks klinis
    ↓
LLM + instruksi + contoh
    ↓
Entitas dan atribut terstruktur
    ↓
Dekomposisi menjadi kueri pencarian
```

Diagram ini langsung membantu menjelaskan rumusan masalah tentang pengolahan teks panjang. Beri keterangan jelas bahwa diagram tersebut merupakan ilustrasi proses, sedangkan arsitektur lengkap model usulan berada di Bab IV.

## 2. Gambar RAG

| Materi versi lama | Saran | Alasan |
|---|---|---|
| **Arsitektur umum RAG** | Layak dimasukkan kembali, dalam bentuk sederhana | Membantu menjelaskan bagaimana pengetahuan terminologi digunakan oleh LLM. |
| **Evolusi RAG: Naive, Advanced, Modular** | Tidak perlu menjadi gambar tersendiri | Klasifikasi perkembangan RAG dapat dijelaskan singkat; ketiganya tidak menjadi pembanding eksperimen dalam rancangan sekarang. |
| **Framework CDE-Mapper** | Tetap dipertahankan | Menunjukkan fondasi sistem yang diadaptasi dan membantu membedakan baseline dari model usulan. |

Untuk gambar RAG, gunakan istilah yang sesuai dengan penelitian:

```text
Kueri entitas → Retrieval → Kandidat konsep terminologi
                                  ↓
Kueri + konteks klinis + kandidat → LLM → Hasil penilaian
```

Ini membuat pembaca memahami bahwa informasi yang diambil adalah **kandidat konsep**, dan keluaran LLM berkaitan dengan **pemetaan atau penilaian kandidat**.

## 3. Rekomendasi susunan gambar

Saya menyarankan **dua gambar utama di Bab III**, dengan satu gambar tambahan jika diperlukan:

1. **Diagram sederhana RAG untuk pemetaan terminologi** — menjelaskan prinsip pengambilan kandidat dan penggunaan konteks.
2. **Framework CDE-Mapper** — menjelaskan susunan komponen baseline.
3. **Opsional: diagram ekstraksi dan dekomposisi berbasis LLM** — jika perbedaan kedua proses masih sulit dipahami melalui teks.

Sementara itu, **gambar arsitektur adaptasi lengkap tetap menjadi pusat penjelasan Bab IV**.

Setiap gambar cukup diikuti satu paragraf yang menjelaskan:
- Apa yang mengalir antarkomponen.
- Fungsi komponen yang relevan.
- Hubungannya dengan penelitian.

## Kesimpulan

**Saya paling menyarankan memasukkan kembali gambar arsitektur RAG yang disederhanakan.** Gambar evolusi LLM/RAG dan rincian keluarga model tidak perlu dikembalikan. Jika ingin memperkuat aspek teks panjang, tambahkan diagram ekstraksi–dekomposisi yang langsung mendukung rumusan masalah kedua.

Dengan pilihan ini, Bab III tetap ringkas sekaligus lebih mudah dipahami secara visual. Dokumen belum saya ubah.