# Audit Proyek Sentimen Tokopedia

## A. Kenapa output Python tidak sama dengan hitungan manual

Diverifikasi dari kode `app.py`, `utils/emoji_enhanced_analyzer.py`, dan data di `ml_data/`.

1. **Analyzer utama bukan Naive Bayes.** Jalur yang dipakai aplikasi adalah `EmojiEnhancedSentimentAnalyzer` (lexicon + emoji + rating).
   GaussianNB + TF-IDF hanya ada di `basic_analyze_sentiment` (app.py ±baris 1080), yaitu cadangan jika analyzer utama gagal.
   Jadi angka di dashboard dan angka dari rumus Naive Bayes manual berasal dari dua metode yang berbeda.
2. **Label "benar" berasal dari rating, bukan anotasi manusia.** Di `ml_data/` dan `scripts/prepare_ml_data.py`: rating 4-5 = positif, 1-2 = negatif, 3 dibuang.
   Di jalur utama, rating 1-2 hampir selalu dipaksa Negatif dan rating 4-5 hampir selalu Positif (`calculate_final_sentiment`).
   Akibatnya "akurasi" (app.py ±baris 2257, `assumed_label`) sebagian besar mengukur kecocokan rating dengan rating sendiri.
   Rating 3 juga dianggap Negatif di sana, sedangkan `prepare_ml_data.py` membuangnya.
3. **Kelas sangat timpang.** Data uji 695 baris: 680 positif, 15 negatif (97,8% positif). Data latih: 3172 positif, 71 negatif.
   Pada data Anda, model yang selalu menebak "positif" sudah mendapat akurasi 97,84%.
4. **Metrik dashboard memakai angka tetap** bila tidak tersedia (app.py ±baris 2576, 2603, 2697-2700):
   confidence 85, accuracy 0,94, f1 0,92, precision 0,91, recall 0,93, average_rating 4,8, accuracy_score "95.2%", processing_time "2.5 seconds".
   Jalur utama tidak menghasilkan precision/recall/F1 sama sekali, jadi yang tampil adalah angka tetap itu.
   Jika training gagal, `emergency_fallback` mengisi semua metrik dengan 0,5.
5. **Jalur cadangan (GaussianNB):** TF-IDF di-fit pada seluruh data sebelum split (kebocoran), lalu prediksi dihitung di seluruh data.
   Aturan kata menimpa prediksi model, sedangkan metrik dihitung dari prediksi model murni sebelum ditimpa.
   Pencocokan kata memakai `word in text` (substring): "ok" cocok di "stok", dan "tidak" masuk daftar kata negatif.

### Hasil uji ulang di data Anda (latih = train_data.csv, uji = test_data.csv, 695 baris, 15 negatif)

| Model | Akurasi | F1 weighted | F1 macro | Presisi neg | Recall neg |
|---|---|---|---|---|---|
| GaussianNB + TF-IDF (seperti di app) | 0,8403 | 0,8946 | 0,4976 | 0,047 | 0,333 |
| MultinomialNB + TF-IDF | 0,9784 | 0,9677 | 0,4945 | 0,000 | 0,000 |
| MultinomialNB + Count (hitungan manual klasik) | 0,9655 | 0,9612 | 0,4912 | 0,000 | 0,000 |
| MultinomialNB + Count, prior seimbang | 0,8518 | 0,9016 | 0,5118 | 0,060 | 0,400 |
| Tebak positif semua (baseline) | 0,9784 | - | - | - | - |

Pilihan model dan rumus saja sudah menggeser akurasi dari 0,84 ke 0,98. Tidak satu pun model mengalahkan baseline "tebak positif semua".
Dalam arti sebenarnya, semua model tidak mampu mendeteksi kelas negatif.
Catatan: 10 teks di data uji juga muncul di data latih.

Yang perlu Anda samakan dengan hitungan manual: (a) jenis Naive Bayes, (b) pembobotan Count vs TF-IDF, (c) metrik (akurasi, weighted, macro, atau kelas positif saja), (d) data uji yang sama.

## B. File yang tidak berguna

Dependensi nyata aplikasi: `app.py` mengimpor `utils.emoji_enhanced_analyzer` (butuh `advanced_negation_handler`), `utils.optimized_sentiment_analyzer`,
`utils.business_report_generator`, `utils.json_helper`, `utils.improved_scraper`; memuat `utils/sentiment_lexicon.json` dan `tools/chromedriver.exe`;
dan memanggil template `admin, csv_preview, dashboard, dashboard_pdf_template, index, login, results, review`.

| Kategori | Alasan |
|---|---|
| Sekitar 330 file di root (`test_*`, `quick_*`, `simple_*`, `debug_*`, `final_*`, `verify_*`, `organize_*`, `*.md` laporan) | Mayoritas berukuran 0 byte; sisanya skrip sekali pakai |
| `backup*`, `archive*`, `organized_*`, `corrupted_files`, `temp_files`, `organization_scripts`, `batch_scripts` | Sisa upaya merapikan dan cadangan |
| `tests/` (±100 skrip), `testing/`, `test_charts/`, `test_business_report/`, `demo_plots/` | Skrip debug, bukan unit test |
| `docs/`, `documentation/`, `development/`, `devtools/` | Catatan "FIX_SUMMARY/COMPLETE" yang saling menduplikasi |
| `analysis/`, `config/`, `data/`, `models/`, `drivers/`, `logs/` | Kosong atau tidak dirujuk |
| `utils/`: `enhanced_*`, `unified_*`, `full_emoji_*`, `improved_sentiment_analyzer`, `indobert_analyzer` (0 byte), `ml_integration_template`, `promo_decision_analytics`, `domain_compatibility_checker`, `enhanced_visualization`, `analyze_sentiment_system`, `diagnose_*`, `ENHANCED_SENTIMENT_IMPLEMENTATION.py`, `enhanced_sentiment_lexicon.json`, `positive_negation_patterns.json` | Tidak diimpor oleh `app.py` maupun modul yang dipakai |
| `templates/`: `dashboard_backup`, `dashboard_legacy`, `dashboard_new`, `dashboard_old_backup`, `preview_csv`, `results_pdf` | Tidak dipanggil `render_template` |
| `results/*.corrupted.*`, `*.bak`, file 0 byte | File rusak |
| `scripts/` kecuali `prepare_ml_data.py`; `tools/` kecuali `chromedriver.exe` | Sisa skrip organisasi; profil Chrome sementara |

### Dipertahankan
`app.py`, `README.md`, `.env`, `.gitignore`, `utils/` (8 file di atas), `templates/` (8 file dipakai), `static/`, `uploads/` (dataset asli),
`results/` (hasil analisis), `ml_data/` (train/val/test), `scripts/prepare_ml_data.py`, `tools/chromedriver.exe`, `venv/`, `.vscode/`.

### Perlu perhatian
- `requirements.txt` kosong (0 byte). Jalankan `pip freeze > requirements.txt` dari venv Anda.
- `results/` berisi 4 salinan identik `enhanced_sentiment_results_20250708_1427xx.csv` (1,9 MB); sisakan satu.
- Kredensial login tertulis langsung di kode (`admin/admin123`, `boss/boss123`, app.py ±baris 1341).
- `venv/` boleh dihapus kapan saja dan dibuat ulang; saya tidak menyentuhnya.
