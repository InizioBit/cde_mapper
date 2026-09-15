# Template Proposal Disertasi LaTeX

Template ini digunakan untuk menyusun dokumen proposal disertasi berbahasa Indonesia menggunakan LaTeX.

## Struktur File

- `Proposal Disertasi.tex` — file utama dokumen
- `metadata.tex` — metadata dokumen seperti judul, nama mahasiswa, dan dosen pembimbing
- `pengesahan.tex` — halaman pengesahan
- `bab-1.tex` — Bab 1 dengan contoh sitasi `\citet` dan `\citep`
- `bab-2.tex` — Bab 2 dengan contoh penyisipan gambar
- `bab-3.tex` — Bab 3 dengan contoh persamaan dan referensi persamaan
- `bab-4.tex` — Bab 4 dengan contoh tabel
- `term-mapping.bib` — basis data referensi
- `media/` — folder gambar yang dipakai dalam dokumen
- `backup/` — arsip versi lama beberapa bab

## Cara Pakai

1. Ubah isi `metadata.tex` sesuai kebutuhan.
2. Edit isi bab pada `bab-1.tex` sampai `bab-4.tex`.
3. Sesuaikan halaman pengesahan pada `pengesahan.tex`.
4. Tambahkan atau perbarui referensi di `term-mapping.bib`.
5. Simpan gambar pendukung di folder `media/` jika diperlukan.
6. Kompilasi file `Proposal Disertasi.tex`.

## Bagian yang Perlu Diubah

Pada `metadata.tex`, minimal ubah bagian berikut:

- `\judul` — judul penelitian
- `\penulis` — nama mahasiswa
- `\nim` — nomor induk mahasiswa
- `\promotor` — dosen pembimbing utama
- `\kopromotor` — dosen pembimbing pendamping

Jika diperlukan, sesuaikan juga:

- `\jenisdokumen`
- `\programstudi`
- `\departemen`
- `\fakultas`
- `\universitas`
- `\tanggal`
- data penguji

## Contoh yang Sudah Tersedia

Template ini sudah memuat beberapa contoh elemen akademik dasar:

- `bab-1.tex` — contoh sitasi naratif dengan `\citet{Zhou2023}` dan sitasi dalam kurung dengan `\citep{Jiang2024, Pachaiyappan2024}`
- `bab-2.tex` — contoh gambar dengan `\includegraphics`, `\caption`, dan `\label`
- `bab-3.tex` — contoh environment `equation`, `\label`, dan referensi persamaan dengan `\eqref`
- `bab-4.tex` — contoh tabel dengan `table`, `tabular`, `\caption`, dan `\label`

## Kompilasi

Contoh kompilasi dengan urutan umum:

```bash
pdflatex "Proposal Disertasi.tex"
bibtex "Proposal Disertasi"
pdflatex "Proposal Disertasi.tex"
pdflatex "Proposal Disertasi.tex"
```

## Catatan

- Template ini sudah disederhanakan sehingga Bab 1–4 berisi kerangka chapter, section, dan subsection dengan teks singkat.
- Contoh sitasi pada `bab-1.tex` memakai entri yang tersedia di `term-mapping.bib`.
- Contoh gambar pada `bab-2.tex` memakai file dari folder `media/`.
- Contoh persamaan pada `bab-3.tex` sudah dilengkapi referensi silang dalam teks.
- Pastikan semua file pendukung yang dipanggil dari dokumen utama tersedia.