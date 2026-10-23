"""Bandingkan prediksi mesin dengan label manual.
Pemakaian:
  python skrip/evaluasi.py data_contoh/sampel_uji_awal.csv                       # mesin aturan
  python skrip/evaluasi.py data_contoh/sampel_uji_awal.csv --mesin transformer   # model terlatih
  python skrip/evaluasi.py data_contoh/sampel_uji_awal.csv --mesin keduanya      # bandingkan
  tambahkan --model nama/model-di-huggingface bila ingin model lain"""
import argparse, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score
from sentimen import buat_mesin

ap = argparse.ArgumentParser()
ap.add_argument('csv'); ap.add_argument('--mesin', choices=['aturan', 'transformer', 'keduanya'], default='aturan')
ap.add_argument('--model', default=None); ap.add_argument('--tampilkan-salah', type=int, default=15)
a = ap.parse_args()

d = pd.read_csv(a.csv, encoding='utf-8-sig')
d = d[d.label_manual.isin(['Positif', 'Negatif', 'Netral', 'Campuran'])].copy()
urut = ['Positif', 'Negatif', 'Netral']
daftar = ['aturan', 'transformer'] if a.mesin == 'keduanya' else [a.mesin]
ringkasan = {}
for nama in daftar:
    kw = {'model': a.model} if (nama == 'transformer' and a.model) else {}
    m = buat_mesin(nama, **kw)
    hasil = m.analisis_banyak(d.Ulasan.astype(str).tolist())
    d['prediksi_' + nama] = [h['label'] for h in hasil]
    d['campuran_' + nama] = [h['campuran'] for h in hasil]
    tiga = d[d.label_manual != 'Campuran']
    y, p = tiga.label_manual, tiga['prediksi_' + nama]
    print(f'\n===== Mesin: {nama} =====')
    print(f'Baris berlabel: {len(d)} | label jelas: {len(tiga)} | Campuran: {(d.label_manual == "Campuran").sum()}')
    print(classification_report(y, p, labels=urut, zero_division=0, digits=3))
    print('Confusion matrix (baris=label manual, kolom=prediksi):')
    print(pd.DataFrame(confusion_matrix(y, p, labels=urut), index=urut, columns=urut))
    c = d[d.label_manual == 'Campuran']
    print(f'Ulasan Campuran: ditandai campuran {c["campuran_" + nama].mean():.0%}; prediksi: {c["prediksi_" + nama].value_counts().to_dict()}')
    ringkasan[nama] = (accuracy_score(y, p), f1_score(y, p, labels=urut, average='macro', zero_division=0))
    salah = tiga[y != p]
    print(f'\nSalah ({len(salah)}), {a.tampilkan_salah} pertama:')
    for _, r in salah.head(a.tampilkan_salah).iterrows():
        print(f'  [{r.id}] manual={r.label_manual} mesin={r["prediksi_" + nama]} | {str(r.Ulasan)[:100]}')
print('\n===== Ringkasan =====')
for k, (acc, f1) in ringkasan.items():
    print(f'{k:12s} akurasi={acc:.3f}  macro-F1={f1:.3f}')
