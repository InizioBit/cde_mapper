# Setup Tahap 1

## Ringkasan

Tahap 1 menyiapkan environment implementasi API Athena lokal menggunakan conda env `cde-mapper-win`.

Stack yang disiapkan:

- Python FastAPI untuk REST API lokal.
- Playwright untuk membuka halaman Athena secara headless.
- SQLite melalui SQLAlchemy dan aiosqlite untuk cache lokal.
- python-dotenv untuk konfigurasi environment.

## Hasil Pemeriksaan Environment

Conda env tersedia:

```text
cde-mapper-win -> C:\Users\didik\anaconda3\envs\cde-mapper-win
```

Python:

```text
Python 3.10.19
```

## Dependency yang Terpasang

| Package | Version |
|---|---:|
| fastapi | 0.141.1 |
| uvicorn | 0.52.0 |
| playwright | 1.61.0 |
| pydantic | 2.9.2 |
| SQLAlchemy | 2.0.35 |
| aiosqlite | 0.22.1 |
| python-dotenv | 1.0.1 |

## Browser Playwright

Browser yang sudah diinstal:

- Chromium
- Chromium headless shell
- FFmpeg dependency Playwright

Lokasi cache Playwright:

```text
C:\Users\didik\AppData\Local\ms-playwright
```

## Perintah Instalasi Ulang

Jika perlu membuat ulang setup pada mesin yang sama atau mesin lain:

```powershell
conda activate cde-mapper-win
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Atau tanpa aktivasi env:

```powershell
conda run -n cde-mapper-win python -m pip install -r requirements.txt
conda run -n cde-mapper-win python -m playwright install chromium
```

## Smoke Test

Perintah:

```powershell
conda run -n cde-mapper-win python -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(headless=True); page=b.new_page(); page.set_content('<title>ok</title><h1>Athena local API</h1>'); print(page.title()); b.close(); p.stop()"
```

Hasil:

```text
ok
```

## Status

Tahap 1 selesai. Environment sudah siap untuk Tahap 2, yaitu membuat konfigurasi aplikasi dan struktur awal FastAPI.
