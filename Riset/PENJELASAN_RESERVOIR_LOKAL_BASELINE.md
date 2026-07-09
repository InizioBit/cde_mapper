# Penjelasan Reservoir Lokal pada Baseline

Dokumen ini menjelaskan maksud kalimat pada bagian 3.1 rencana implementasi:

> Sistem mengecek reservoir lokal untuk entitas yang sudah pernah dipetakan.

Reservoir lokal pada baseline adalah tempat penyimpanan pasangan istilah klinis atau variabel dengan konsep standar yang sudah diketahui. Tujuannya adalah agar sistem tidak selalu menjalankan retrieval dan reranking dari awal untuk entitas yang sebelumnya sudah pernah dipetakan.

## Lokasi Konfigurasi

Lokasi file reservoir ditentukan di:

```text
rag/param.py
```

Konfigurasi yang relevan:

```python
DB_FILE = 'variables.db'
MAPPING_FILE = f"{DATA_DIR}/input/mapping_templates.json"
```

Artinya, database reservoir lokal menggunakan file:

```text
variables.db
```

Karena path tersebut relatif, file akan dibuat di root proyek saat pipeline dijalankan dari root repositori:

```text
D:\Program\cde_mapper\variables.db
```

Pada kondisi proyek saat diperiksa, file `variables.db` belum ada. File ini akan dibuat otomatis saat kode membuat objek `DataManager`.

## File Seed Awal

Reservoir lokal diinisialisasi dari file JSON:

```text
data/input/mapping_templates.json
```

File tersebut berisi contoh mapping, prompt examples, aturan, dan bagian data awal untuk database. Bagian yang dipakai sebagai seed reservoir adalah key:

```json
"database_data": [...]
```

Jika tabel reservoir masih kosong, data dari `database_data` akan dimasukkan ke database SQLite.

## Modul yang Mengelola Reservoir

Reservoir lokal dikelola oleh:

```text
rag/sql.py
```

Kelas utamanya adalah:

```python
DataManager
```

Saat dibuat, `DataManager` membuka koneksi SQLite, membuat tabel jika belum ada, lalu mengisi data awal dari `mapping_templates.json` jika tabel masih kosong.

Kode inisialisasi terdapat di:

```python
self.conn = sqlite3.connect(db_file)
self.create_table()
if initial_json and self.is_table_empty():
    self.insert_mapping_bulk_json(initial_json)
```

## Skema Tabel

Tabel reservoir bernama:

```text
concept_mappings
```

Skemanya:

```sql
CREATE TABLE IF NOT EXISTS concept_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_name TEXT UNIQUE,
    standard_label TEXT,
    concept_code TEXT,
    omop_id INTEGER
);
```

Makna kolom:

- `variable_name`: istilah/variabel lokal yang dicari, misalnya nama CDE atau entitas hasil dekomposisi.
- `standard_label`: label konsep standar yang menjadi hasil mapping.
- `concept_code`: kode konsep standar, misalnya kode SNOMED, OMOP, atau kode lain.
- `omop_id`: identifier konsep OMOP jika tersedia.

## Alur Pemakaian dalam Pipeline

Reservoir dipakai di:

```text
rag/retriever.py
```

Pada fungsi `map_data`, database dibuat dengan:

```python
db = DataManager(DB_FILE, initial_json=MAPPING_FILE)
```

Kemudian pada proses pemetaan, sistem memanggil fungsi:

```python
find_entity_in_db(entity_str, data_manager)
```

Fungsi ini mencoba mencari entitas dengan dua cara:

1. Mencari berdasarkan `variable_name`.
2. Jika tidak ditemukan, mencari berdasarkan `standard_label`.

Jika ditemukan, hasil reservoir langsung dikonversi menjadi kandidat mapping tanpa perlu menjalankan retrieval ke Qdrant atau Athena API.

## Urutan Logika Baseline

Secara ringkas, alurnya adalah:

1. Input CDE dibaca dari file.
2. LLM melakukan query decomposition.
3. Sistem mengambil `base_entity`, `additional_entities`, `categories`, `unit`, atau `visit`.
4. Sistem mengecek apakah entitas tersebut sudah ada di tabel `concept_mappings`.
5. Jika ada, hasil reservoir dipakai langsung.
6. Jika tidak ada, sistem melanjutkan retrieval ke Qdrant/Athena API.
7. Setelah hasil dinilai benar, mapping baru dapat ditambahkan kembali ke reservoir atau training examples.

## Catatan Penting

Reservoir lokal baseline saat ini masih bersifat teknis dan sederhana. Ia menyimpan pasangan `variable_name` ke `standard_label`, `concept_code`, dan `omop_id`. Dalam pipeline riset usulan, reservoir ini perlu diperluas agar mendukung:

- status validasi ahli;
- provenance atau sumber mapping;
- vocabulary target, misalnya SNOMED CT, LOINC, ICD-10, UCUM;
- confidence score;
- konteks klinis;
- tanggal validasi;
- nama atau peran validator;
- audit trail perubahan mapping.

Dengan perluasan tersebut, reservoir tidak hanya menjadi cache mapping, tetapi menjadi knowledge reservoir tervalidasi yang dapat meningkatkan konsistensi dan akurasi pipeline dari waktu ke waktu.
