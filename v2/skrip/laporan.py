"""Laporan sentimen per produk untuk manajemen (HTML satu halaman).
Pemakaian: python skrip/laporan.py <csv> --keluar laporan.html [--min-ulasan 15]
Sentimen dihitung dari TEKS saja. Rating ditampilkan hanya sebagai pembanding."""
import argparse, os, re, sys, html
from collections import Counter, defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import pandas as pd
from sentimen import MesinAturan, analisis_aspek, ASPEK

ap = argparse.ArgumentParser()
ap.add_argument('csv'); ap.add_argument('--keluar', default='laporan.html'); ap.add_argument('--min-ulasan', type=int, default=15)
ap.add_argument('--top', type=int, default=10)
a = ap.parse_args()

d = pd.read_csv(a.csv, encoding='utf-8-sig')
d['Rating'] = pd.to_numeric(d['Rating'].astype(str).str.replace('bintang', '', regex=False).str.strip(), errors='coerce')
d['produk'] = d['Nama_Produk'].astype(str).str.split('Varian:').str[0].str.replace(r'\s+', ' ', regex=True).str.strip().str[:70]
n_awal = len(d)
d['kunci'] = d['Ulasan'].astype(str).str.strip().str.lower() + '|' + d['produk'] + '|' + d['Rating'].astype(str)
d = d.drop_duplicates('kunci').reset_index(drop=True)
n_dup = n_awal - len(d)

m = MesinAturan()
res = d['Ulasan'].astype(str).apply(m.analisis)
d['label'] = res.apply(lambda r: r['label']); d['skor'] = res.apply(lambda r: r['skor']); d['campuran'] = res.apply(lambda r: r['campuran'])
d['aspek'] = d['Ulasan'].astype(str).apply(analisis_aspek)
d['konflik'] = ((d.Rating >= 4) & (d.label == 'Negatif')) | ((d.Rating <= 2) & (d.label == 'Positif'))

def pct(x, n): return 0 if n == 0 else round(100 * x / n, 1)
def ringkas(df):
    n = len(df); c = df.label.value_counts()
    return dict(n=n, pos=pct(c.get('Positif', 0), n), neg=pct(c.get('Negatif', 0), n), net=pct(c.get('Netral', 0), n),
                camp=pct(df.campuran.sum(), n), rating=round(df.Rating.mean(), 2), konflik=int(df.konflik.sum()))
def aspek_tabel(df):
    t = defaultdict(lambda: Counter())
    for lst in df.aspek:
        for asp, lab, _ in lst: t[asp][lab] += 1
    return t
def kutipan(df, lab, k=3):
    s = df[df.label == lab].copy(); s['p'] = s.Ulasan.astype(str).str.len()
    s = s[(s.p >= 25) & (s.p <= 220)].sort_values('skor', ascending=(lab == 'Negatif')).head(k)
    return [html.escape(str(x)) for x in s.Ulasan]
def bar(p, n, g):
    return f'<div class="bar"><span class="p" style="width:{p}%"></span><span class="n" style="width:{n}%"></span><span class="g" style="width:{g}%"></span></div>'

tot = ringkas(d)
produk = d.groupby('produk').filter(lambda x: len(x) >= a.min_ulasan).groupby('produk')
baris = sorted(((p, g) for p, g in produk), key=lambda t: -len(t[1]))[:a.top]

H = ['<!doctype html><html lang="id"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
     '<title>Laporan Sentimen Ulasan</title><style>:root{--bg:#fff;--fg:#1d2433;--mut:#667085;--ln:#e4e7ec;--pos:#12805c;--neg:#c4320a;--net:#98a2b3}',
     '@media(prefers-color-scheme:dark){:root{--bg:#10141c;--fg:#e8ecf4;--mut:#98a2b3;--ln:#283042;--pos:#3ccf91;--neg:#ff7a59;--net:#667085}}',
     'body{font:15px/1.5 system-ui,sans-serif;background:var(--bg);color:var(--fg);max-width:980px;margin:0 auto;padding:24px 16px}',
     'h1{font-size:24px;margin:0 0 4px}h2{font-size:18px;margin:32px 0 8px}h3{font-size:15px;margin:0}.mut{color:var(--mut)}',
     '.kpi{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}.kpi div{flex:1;min-width:140px;border:1px solid var(--ln);border-radius:10px;padding:12px}',
     '.kpi b{display:block;font-size:26px}.bar{display:flex;height:10px;border-radius:5px;overflow:hidden;background:var(--ln)}',
     '.p{background:var(--pos)}.n{background:var(--neg)}.g{background:var(--net)}table{border-collapse:collapse;width:100%}',
     'td,th{padding:8px;border-bottom:1px solid var(--ln);text-align:left;vertical-align:top}th{color:var(--mut);font-weight:600;font-size:13px}',
     '.card{border:1px solid var(--ln);border-radius:10px;padding:14px;margin:12px 0}q{display:block;margin:4px 0;color:var(--mut)}',
     '.pos{color:var(--pos);font-weight:600}.neg{color:var(--neg);font-weight:600}.note{font-size:13px;color:var(--mut);margin-top:24px}</style>',
     '<h1>Laporan Sentimen Ulasan</h1>',
     f'<div class="mut">{tot["n"]:,} ulasan dianalisis (setelah membuang {n_dup:,} baris identik). Sentimen dihitung dari isi teks, bukan rating.</div>'.replace(',', '.', 2) if False else f'<div class="mut">{format(tot["n"], ",").replace(",", ".")} ulasan dianalisis (setelah membuang {format(n_dup, ",").replace(",", ".")} baris identik). Sentimen dihitung dari isi teks, bukan rating.</div>',
     '<div class="kpi">',
     f'<div><span class="mut">Positif</span><b class="pos">{tot["pos"]}%</b></div>',
     f'<div><span class="mut">Negatif</span><b class="neg">{tot["neg"]}%</b></div>',
     f'<div><span class="mut">Netral</span><b>{tot["net"]}%</b></div>',
     f'<div><span class="mut">Ulasan campuran</span><b>{tot["camp"]}%</b></div></div>',
     f'<div>{bar(tot["pos"], tot["neg"], tot["net"])}</div>']

H.append('<h2>Topik yang dibicarakan</h2><table><tr><th>Topik</th><th>Memuji</th><th>Mengeluh</th><th>Porsi keluhan</th></tr>')
at = aspek_tabel(d)
for asp in sorted(at, key=lambda k: -sum(at[k].values())):
    p_, n_ = at[asp]['Positif'], at[asp]['Negatif']
    H.append(f'<tr><td>{asp}</td><td class="pos">{p_}</td><td class="neg">{n_}</td><td>{pct(n_, p_ + n_)}%</td></tr>')
H.append('</table>')

H.append(f'<h2>Per produk (minimal {a.min_ulasan} ulasan)</h2>')
for nama, g in baris:
    r = ringkas(g); at = aspek_tabel(g)
    keluh = sorted(((v['Negatif'], k) for k, v in at.items() if v['Negatif']), reverse=True)[:2]
    puji = sorted(((v['Positif'], k) for k, v in at.items() if v['Positif']), reverse=True)[:2]
    H.append(f'<div class="card"><h3>{html.escape(nama)}</h3><div class="mut">{r["n"]} ulasan | Positif {r["pos"]}% | Negatif {r["neg"]}% | Netral {r["net"]}%</div>{bar(r["pos"], r["neg"], r["net"])}')
    H.append('<p>' + ('Paling dipuji: ' + ', '.join(f'{k} ({c})' for c, k in puji) if puji else '') + '<br>' +
             ('Paling dikeluhkan: ' + ', '.join(f'{k} ({c})' for c, k in keluh) if keluh else '') + '</p>')
    for lab, cls in (('Negatif', 'neg'), ('Positif', 'pos')):
        for q in kutipan(g, lab, 2): H.append(f'<q class="{cls}-q">{lab}: {q}</q>')
    H.append('</div>')

H.append(f'<h2>Pembanding dengan rating</h2><p>Rating rata-rata {tot["rating"]}. <b>{tot["konflik"]}</b> ulasan ({pct(tot["konflik"], tot["n"])}%) '
         'bernilai berlawanan dengan ratingnya (rating 4-5 tetapi teks negatif, atau rating 1-2 tetapi teks positif). Ulasan seperti ini biasanya menunjuk masalah yang tersembunyi di balik bintang.</p>')
H.append('<p class="note">Catatan metode: mesin aturan berbasis kamus. Pada 84 ulasan uji berlabel awal (diberi label oleh Claude, belum diperiksa pemilik proyek): akurasi 81%, macro-F1 0,73. '
         'Ketepatan pada data Anda perlu diperiksa dengan sampel berlabel sendiri (lihat README).</p></html>')
open(a.keluar, 'w', encoding='utf-8').write('\n'.join(H))
print('Ditulis:', a.keluar)
print(f'Total {tot["n"]} | Positif {tot["pos"]}% Negatif {tot["neg"]}% Netral {tot["net"]}% | konflik rating {tot["konflik"]}')
