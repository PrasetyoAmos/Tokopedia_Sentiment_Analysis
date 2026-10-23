"""Bandingkan prediksi mesin dengan label manual. Pemakaian: python skrip/evaluasi.py sampel_emas.csv"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sentimen import MesinAturan

d = pd.read_csv(sys.argv[1], encoding='utf-8-sig')
d = d[d.label_manual.isin(['Positif', 'Negatif', 'Netral', 'Campuran'])].copy()
m = MesinAturan()
hasil = d.Ulasan.astype(str).apply(m.analisis)
d['prediksi'] = hasil.apply(lambda r: r['label'])
d['campuran_terdeteksi'] = hasil.apply(lambda r: r['campuran'])

tiga = d[d.label_manual != 'Campuran']
urut = ['Positif', 'Negatif', 'Netral']
print(f'Baris berlabel: {len(d)} | label jelas (tanpa Campuran): {len(tiga)} | Campuran: {(d.label_manual=="Campuran").sum()}\n')
print(classification_report(tiga.label_manual, tiga.prediksi, labels=urut, zero_division=0, digits=3))
print('Macro-F1:', round(f1_score(tiga.label_manual, tiga.prediksi, labels=urut, average='macro', zero_division=0), 3))
print('\nConfusion matrix (baris=label manual, kolom=prediksi):')
print(pd.DataFrame(confusion_matrix(tiga.label_manual, tiga.prediksi, labels=urut), index=urut, columns=urut))
c = d[d.label_manual == 'Campuran']
print(f'\nUlasan Campuran: terdeteksi sebagai campuran {c.campuran_terdeteksi.mean():.0%}; prediksi: {c.prediksi.value_counts().to_dict()}')
salah = tiga[tiga.label_manual != tiga.prediksi]
print(f'\nSalah ({len(salah)}):')
for _, r in salah.iterrows():
    print(f'  [{r.id}] manual={r.label_manual} mesin={r.prediksi} | {str(r.Ulasan)[:110]}')
