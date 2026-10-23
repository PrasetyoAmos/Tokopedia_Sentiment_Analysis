# v2: sentimen murni dari teks

Tujuan: mengetahui sentimen ulasan (positif, negatif, netral) dari **isi komentar**, tanpa rating, lalu menyusun laporan per produk untuk manajemen: bagaimana sentimennya dan apa yang dibicarakan.

## Isi
| Berkas | Fungsi |
|---|---|
| `sentimen/mesin_aturan.py` | Mesin sentimen berbasis aturan: normalisasi slang, negasi (`tidak buruk`, `kurang bagus`), intensifier, kata kontras (`bagus tapi lama`), emoji. Rating tidak dipakai |
| `sentimen/mesin_transformer.py` | Mesin model terlatih (IndoBERT/IndoRoBERTa dari Hugging Face), antarmuka sama dengan mesin aturan |
| `sentimen/aspek.py` | Topik yang dibicarakan (kualitas, ukuran, pengiriman, kemasan, penjual, harga, keaslian) beserta sentimen per klausa |
| `skrip/buat_sampel_emas.py` | Membuat sampel ulasan untuk diberi label manual |
| `skrip/evaluasi.py` | Menghitung presisi, recall, F1 per kelas, macro-F1, dan confusion matrix terhadap label manual |
| `skrip/laporan.py` | Membuat laporan HTML per produk |
| `data_contoh/` | Dua sampel berlabel awal (119 dan 100 ulasan) |
| `contoh_laporan/` | Contoh keluaran laporan dari dataset v1 |

## Pemakaian
```bash
pip install pandas scikit-learn
python skrip/laporan.py ../v1/uploads/ulasan.csv --keluar laporan.html
python skrip/evaluasi.py data_contoh/sampel_uji_awal.csv
```

## Memakai model terlatih
```bash
pip install transformers torch
python skrip/evaluasi.py data_contoh/sampel_uji_awal.csv --mesin keduanya
python skrip/laporan.py ../v1/uploads/ulasan.csv --mesin transformer --keluar laporan_bert.html
```
Tambahkan `--model nama/model` untuk model lain. Jika label modelnya tidak dikenal (bukan positive/negative/neutral), kode akan berhenti dengan pesan yang menjelaskan cara memetakannya.
Kode jalur transformer diuji dengan model tiruan, belum dengan model asli, karena lingkungan pengembangan tidak bisa mengunduhnya.

## Akurasi yang diukur
Label pada `data_contoh/` **diberi oleh Claude dari isi teks dan belum diperiksa pemilik proyek**. Anggap angka ini sebagai perkiraan awal.
`sampel_emas_awal.csv` dipakai untuk menyetel kamus; `sampel_uji_awal.csv` (100 ulasan lain) tidak dipakai menyetel.
Hasil pada sampel uji (84 ulasan berlabel jelas): akurasi 81%, macro-F1 0,73. Recall negatif 73%, presisi negatif 96%.
Ulasan bercampur (16 dari 100) ditandai terpisah dan tidak dihitung dalam metrik.

## Langkah berikutnya
1. Periksa dan koreksi label di `data_contoh/`, atau buat sampel sendiri 300 baris dengan `buat_sampel_emas.py`.
2. Jalankan `--mesin keduanya` dan bandingkan hasilnya dengan mesin aturan.
3. Rapikan penamaan produk (varian digabung) dan perbaiki scraper (lihat `v1/docs/SCRAPER_AUDIT.md`).
