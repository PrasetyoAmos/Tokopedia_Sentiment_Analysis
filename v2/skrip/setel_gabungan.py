"""Cari pengaturan mesin gabungan terbaik dari hasil evaluasi.
Langkah:
  python skrip/evaluasi.py data_contoh/sampel_uji_awal.csv data_contoh/sampel_uji_2.csv --mesin keduanya --simpan prediksi.csv
  python skrip/setel_gabungan.py prediksi.csv
Hanya baris berlabel Positif/Negatif/Netral dipakai. Angka yang dilaporkan berasal dari validasi silang
(parameter dipilih dari sebagian data, diuji pada sisanya), jadi lebih jujur daripada memilih parameter lalu mengukur pada data yang sama."""
import itertools, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np, pandas as pd
from sklearn.metrics import f1_score
from sentimen.mesin_gabungan import gabung

d = pd.read_csv(sys.argv[1], encoding='utf-8-sig')
d = d[d.label_manual.isin(['Positif', 'Negatif', 'Netral'])].reset_index(drop=True)
R = [dict(skor=r.rule_skor, positif=r.rule_pos, negatif=r.rule_neg, campuran=bool(r.rule_camp)) for r in d.itertuples()]
P = [{'Positif': r.b_pos, 'Netral': r.b_net, 'Negatif': r.b_neg} for r in d.itertuples()]
y = d.label_manual.values
print(f'{len(d)} ulasan berlabel: {pd.Series(y).value_counts().to_dict()}')


def prediksi(idx, w, tau, per, py):
    return np.array([gabung(R[i], P[i], w, tau, per, py)[0] for i in idx])


def skor(idx, w, tau, per, py):
    p = prediksi(idx, w, tau, per, py); t = y[idx]
    acc = (p == t).mean()
    f1n = f1_score(t, p, labels=['Negatif'], average='macro', zero_division=0)
    f1p = f1_score(t, p, labels=['Positif'], average='macro', zero_division=0)
    return (acc + f1n + f1p) / 3, acc, f1n   # Netral terlalu sedikit untuk ikut menentukan


grid = list(itertools.product([.2, .3, .4, .5, .6, .7], [.15, .25, .35, .45], [None, .6, 1.0, 1.5, 2.0], [.8, .9, .95]))
semua = np.arange(len(d))
rng = np.random.RandomState(0); acak = rng.permutation(len(d)); lipat = np.array_split(acak, 5)
cv_acc, cv_f1n = [], []
for k in range(5):
    uji = lipat[k]; latih = np.concatenate([lipat[j] for j in range(5) if j != k])
    terbaik = max(grid, key=lambda g: skor(latih, *g)[0])
    _, a, f = skor(uji, *terbaik); cv_acc.append(a); cv_f1n.append(f)
print(f'\nValidasi silang 5 lipat (parameter dipilih tanpa melihat data uji):')
print(f'  gabungan disetel   akurasi={np.mean(cv_acc):.3f}  F1 Negatif={np.mean(cv_f1n):.3f}')
for nama, kol in (('aturan', 'prediksi_aturan'), ('IndoBERT', 'prediksi_transformer')):
    if kol in d:
        p = d[kol].values
        print(f'  {nama:18s} akurasi={(p == y).mean():.3f}  F1 Negatif={f1_score(y, p, labels=["Negatif"], average="macro", zero_division=0):.3f}')
bawaan = skor(semua, .45, .3, None, .85)
print(f'  gabungan bawaan    akurasi={bawaan[1]:.3f}  F1 Negatif={bawaan[2]:.3f}   (w=0,45 ambang=0,3, tanpa aturan percaya)')
g = max(grid, key=lambda g: skor(semua, *g)[0])
s_, a_, f_ = skor(semua, *g)
print(f'\nPengaturan terbaik pada seluruh data: bobot_aturan={g[0]} ambang={g[1]} percaya={g[2]} p_yakin={g[3]}')
print(f'  (akurasi {a_:.3f}, F1 Negatif {f_:.3f} pada data yang sama; angka ini optimis, pakai angka validasi silang di atas)')
print('Coba: python skrip/evaluasi.py <file> --mesin gabungan --bobot %s --ambang %s%s --p-yakin %s' % (g[0], g[1], '' if g[2] is None else ' --percaya %s' % g[2], g[3]))
