"""Buat sampel ulasan untuk diberi label manual (positif/negatif/netral/campuran) berdasarkan ISI TEKS.
Pemakaian: python skrip/buat_sampel_emas.py <csv1> [<csv2> ...] --jumlah 300 --keluar sampel_emas.csv
Rating hanya dipakai untuk menyebar sampel (agar ulasan negatif cukup terwakili), tidak ditampilkan ke pemberi label."""
import argparse, pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument('csv', nargs='+'); ap.add_argument('--jumlah', type=int, default=300)
ap.add_argument('--keluar', default='sampel_emas.csv'); ap.add_argument('--seed', type=int, default=42)
a = ap.parse_args()

d = pd.concat([pd.read_csv(f, encoding='utf-8-sig').assign(sumber=f.replace('\\', '/').split('/')[-1]) for f in a.csv], ignore_index=True)
d['Rating'] = pd.to_numeric(d['Rating'].astype(str).str.replace('bintang', '', regex=False).str.strip(), errors='coerce')
d['kunci'] = d['Ulasan'].astype(str).str.strip().str.lower()
d = d.drop_duplicates('kunci')
bagian = {'rendah': (d.Rating <= 2, 0.33), 'tiga': (d.Rating == 3, 0.17), 'tinggi': (d.Rating >= 4, 0.50)}
hasil = []
for nama, (m, porsi) in bagian.items():
    s = d[m]; n = min(int(a.jumlah * porsi), len(s))
    hasil.append(s.sample(n, random_state=a.seed))
out = pd.concat(hasil).sample(frac=1, random_state=a.seed).reset_index(drop=True)
out.insert(0, 'id', range(1, len(out) + 1))
out['label_manual'] = ''     # isi: Positif / Negatif / Netral
out[['id', 'Ulasan', 'label_manual', 'Rating', 'sumber']].to_csv(a.keluar, index=False, encoding='utf-8-sig')
print(f'{len(out)} baris ditulis ke {a.keluar}')
