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
ap.add_argument('csv', nargs='+', help='satu atau beberapa file berlabel (digabung)'); ap.add_argument('--simpan', default=None, help='simpan prediksi per ulasan (untuk setel_gabungan.py)'); ap.add_argument('--mesin', choices=['aturan', 'transformer', 'gabungan', 'keduanya', 'semua'], default='aturan')
ap.add_argument('--model', default=None); ap.add_argument('--bobot', type=float, default=0.45); ap.add_argument('--ambang', type=float, default=0.3); ap.add_argument('--percaya', type=float, default=None); ap.add_argument('--p-yakin', type=float, default=0.85); ap.add_argument('--tampilkan-salah', type=int, default=15)
a = ap.parse_args()

d = pd.concat([pd.read_csv(f, encoding='utf-8-sig').assign(berkas=os.path.basename(f)) for f in a.csv], ignore_index=True)
d = d[d.label_manual.isin(['Positif', 'Negatif', 'Netral', 'Campuran'])].copy()
urut = ['Positif', 'Negatif', 'Netral']
daftar = {'keduanya': ['aturan', 'transformer'], 'semua': ['aturan', 'transformer', 'gabungan']}.get(a.mesin, [a.mesin])
ringkasan = {}
cache = {}
for nama in daftar:
    kw = {'model': a.model} if (nama in ('transformer', 'gabungan') and a.model) else {}
    if nama == 'gabungan':
        kw.update(bobot_aturan=a.bobot, ambang=a.ambang, percaya=a.percaya, p_yakin=a.p_yakin)
        if 'transformer' in cache: kw['transformer'] = cache['transformer']  # pakai ulang model yang sudah dimuat
    m = buat_mesin(nama, **kw)
    if nama == 'transformer': cache['transformer'] = m
    hasil = m.analisis_banyak(d.Ulasan.astype(str).tolist())
    d['prediksi_' + nama] = [h['label'] for h in hasil]
    if nama == 'aturan':
        d['rule_skor'] = [h['skor'] for h in hasil]; d['rule_pos'] = [h['positif'] for h in hasil]
        d['rule_neg'] = [h['negatif'] for h in hasil]; d['rule_camp'] = [bool(h['campuran']) for h in hasil]
    if nama == 'transformer':
        for k, c in (('Positif', 'b_pos'), ('Netral', 'b_net'), ('Negatif', 'b_neg')): d[c] = [h['prob'][k] for h in hasil]
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

if a.simpan:
    d.to_csv(a.simpan, index=False, encoding='utf-8-sig'); print('Prediksi disimpan ke', a.simpan)
