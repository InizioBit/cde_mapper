# Checkpoint 3 — Gold Set Awal

Folder ini menyiapkan proses pembuatan gold set, tetapi **tidak menganggap
label otomatis sebagai gold**. Unit sampling adalah satu pasangan konsultasi:
pertanyaan pasien dan jawaban dokter.

## Berkas

- `stage2_annotation_tasks.jsonl`: 40 pasangan hasil sampling terstratifikasi.
- `stage2_annotator_a.jsonl`: lembar kerja anotator A.
- `stage2_annotator_b.jsonl`: lembar kerja anotator B.
- `stage2_sampling_manifest.json`: provenance dan distribusi strata.
- `stage2_annotation_disagreement.jsonl`: perbedaan yang ditemukan oleh audit.
- `stage2_checkpoint_03_audit.json`: status kelengkapan, validitas, dan agreement.
- `stage2_gold_statistics.json`: statistik sementara/final sesuai status anotasi.

`stage2_gold_v1.jsonl` belum boleh dibuat selama adjudikasi klinis belum selesai.

## Alur verifikasi

1. Jalankan `checkpoint_03_prepare_gold.py`.
2. Bagikan berkas A dan B secara terpisah; anotator tidak saling melihat hasil.
3. Anotator mengisi `entities` untuk question dan answer sesuai pedoman
   Checkpoint 2, lalu mengubah `annotation_meta.status` menjadi `complete`.
4. Jalankan `checkpoint_03_audit_annotations.py`.
5. Tinjau setiap baris disagreement dan lakukan adjudikasi oleh tenaga klinis.
6. Bekukan hasil adjudikasi sebagai `stage2_gold_v1.jsonl`, catat keputusan,
   statistik, hash berkas, serta pisahkan data evaluasi dari few-shot.

Kunci pencocokan agreement saat ini adalah `start_char`, `end_char`, dan
`entity_type`. Agreement atribut dihitung hanya pada entitas yang kunci
span-tipenya sama. Nilai `null` berarti belum ada dua anotasi lengkap yang
dapat dibandingkan, bukan agreement nol.
