# Tokopedia Sentiment Analysis, v1 (arsip skripsi)

Aplikasi Flask untuk mengambil (scraping) ulasan produk Tokopedia, menganalisis sentimennya, dan menampilkan dashboard serta laporan.
Versi ini dibekukan sebagai arsip skripsi. Pengembangan lanjutan ada di `v2/` (belum dibuat).

## Menjalankan
```bash
cd v1
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python app.py
```
Buka http://127.0.0.1:5000. Folder `uploads/`, `results/`, dan `static/plots/` dibuat otomatis.
Untuk scraping, siapkan `tools/chromedriver.exe` (lihat `tools/README.md`).

## Struktur
| Folder / berkas | Isi |
|---|---|
| `app.py` | Aplikasi Flask: scraping, analisis, dashboard, panel admin |
| `utils/` | Analyzer sentimen (emoji/aturan, versi besar), scraper, pembuat laporan, lexicon |
| `templates/`, `static/` | Tampilan |
| `scripts/prepare_ml_data.py` | Menyiapkan data latih/val/uji dari hasil scraping |
| `docs/` | Audit perhitungan dan scraper |

## Batasan yang diketahui
Lihat `docs/AUDIT_PROYEK.md` dan `docs/SCRAPER_AUDIT.md`. Ringkasnya:
- Sentimen sangat dipengaruhi rating; metrik di dashboard sebagian berupa angka tetap.
- Scraper tidak membuang duplikat dan membuang ulasan di bawah 10 karakter.
- Kredensial login dan `secret_key` masih tertulis di kode.

Dataset dan hasil analisis tidak disertakan di repo ini.
