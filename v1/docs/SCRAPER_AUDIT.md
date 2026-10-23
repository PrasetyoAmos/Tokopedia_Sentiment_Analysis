# Audit scraper (`utils/improved_scraper.py`, kelas `TokopediaScraper` di `app.py`)

Dibaca dari kode dan diuji pada tiga CSV hasil scraping (Aerostreet 100 halaman, Aerostreet 4K+, Xiaomi 1000).

## Temuan
1. **Tidak ada pembuangan duplikat.** Setiap ulasan langsung ditambahkan ke daftar.
2. **Halaman bisa terambil dua kali.** Setelah klik "Laman berikutnya" scraper hanya menunggu 3 detik dan tidak memastikan isi halaman berubah.
   Jika klik pertama gagal, jalur cadangan meng-klik tombol lewat JavaScript lalu melanjutkan loop tanpa `break`.
   Pada halaman terakhir tombol yang nonaktif tidak memicu error, sehingga halaman yang sama dibaca lagi.
3. **Ulasan pendek dibuang.** Ulasan di bawah 10 karakter (mis. "bagus", "mantap") dilewati. Pada ketiga CSV tidak ada ulasan di bawah 10 karakter, jadi distribusi sentimen cenderung condong ke ulasan panjang.
4. **Rating default 5.** Jika elemen rating tidak ditemukan, rating diisi `"5"`. Cabang utama juga bisa menghasilkan string kosong bila `aria-label` kosong.
5. **Teks diubah saat dibersihkan.** Koma, `/`, dan `|` dihapus dari ulasan ("dan/atau" menjadi "danatau").
6. **Tidak ada penanda unik.** Tanggal ulasan, nama pengguna, atau ID ulasan tidak disimpan, sehingga duplikat akibat scraping tidak bisa dibedakan dari ulasan sah yang kebetulan sama.
7. **Selector rapuh.** `article.css-ccpe8t` adalah nama kelas hasil build yang berubah sewaktu-waktu. Halaman tidak di-scroll, jadi konten lazy-load bisa terlewat.

## Hasil pada data
| Dataset | Baris | Baris identik penuh (teks+produk+rating) | Teks sama | Blok halaman berulang |
|---|---|---|---|---|
| Aerostreet 100 halaman | 737 | 7 | 70 | 0 |
| Aerostreet 4K+ | 3.539 | 34 | 385 | 0 |
| Xiaomi 1000 | 8.794 | 41 | 398 | 0 |

Tidak ada bukti satu halaman penuh terambil ulang di CSV final. Sebagian besar teks sama berbeda produk atau rating, jadi kemungkinan ulasan umum yang sah.
Baris identik penuh (7/34/41) tidak bisa dipastikan sah atau duplikat tanpa ID ulasan.

## Perbaikan yang disarankan untuk v2
Simpan tanggal dan pengenal ulasan, buang duplikat berdasarkan pengenal itu, verifikasi isi halaman berubah sebelum membaca, hentikan saat tombol berikutnya nonaktif,
biarkan rating hilang sebagai kosong, simpan teks asli, dan jangan membuang ulasan pendek.
