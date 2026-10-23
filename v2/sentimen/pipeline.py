"""Alur analisis: muat CSV -> bersihkan -> label sentimen -> aspek -> ringkasan."""
import json, math, re
from collections import Counter, defaultdict
import pandas as pd
from .normalisasi import normalisasi, token
from .aspek import analisis_aspek

KOLOM = {
    'Ulasan': ['ulasan', 'review', 'review_text', 'komentar', 'text', 'teks'],
    'Nama_Produk': ['nama_produk', 'produk', 'product', 'product_name', 'nama produk'],
    'Rating': ['rating', 'bintang', 'star', 'stars', 'score'],
}
STOP = set('yang dan di ke dari ini itu untuk dengan ada saya sudah juga atau tapi karena pada akan bisa sama jadi lagi aja saja nya udah banget sekali lebih sih deh dong kok yg dgn tidak belum bukan barang barangnya produk beli order pesan sampai sampe kali lah nih ya kan mau kalo kalau hanya cuma agak masih sangat semua setelah sebelum dalam oleh seperti yaitu juga lain gan kak toko seller penjual terima kasih review coba kira dikit baru'.split())
URUTAN = ['Positif', 'Netral', 'Negatif']


def muat_csv(path):
    for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            df = pd.read_csv(path, encoding=enc, sep=None, engine='python')
            break
        except Exception:
            df = None
    if df is None:
        raise ValueError('File tidak bisa dibaca sebagai CSV.')
    peta = {}
    low = {c.lower().strip(): c for c in df.columns}
    for baku, alias in KOLOM.items():
        for al in [baku.lower()] + alias:
            if al in low:
                peta[low[al]] = baku
                break
    df = df.rename(columns=peta)
    if 'Ulasan' not in df.columns:
        raise ValueError("Kolom ulasan tidak ditemukan. Beri nama kolomnya 'Ulasan' (kolom lain: Nama_Produk, Rating).")
    if 'Nama_Produk' not in df.columns:
        df['Nama_Produk'] = 'Semua ulasan'
    if 'Rating' not in df.columns:
        df['Rating'] = float('nan')
    df['Rating'] = pd.to_numeric(df['Rating'].astype(str).str.replace('bintang', '', regex=False).str.strip(), errors='coerce')
    df['Ulasan'] = df['Ulasan'].fillna('').astype(str).str.strip()
    return df[df['Ulasan'].str.len() > 0].reset_index(drop=True)


def siapkan(df, buang_duplikat=True):
    df = df.copy()
    df['produk'] = (df['Nama_Produk'].astype(str).str.split('Varian:').str[0].str.replace(r'\s+', ' ', regex=True).str.strip().str[:80])
    n_awal = len(df)
    if buang_duplikat:
        kunci = df['Ulasan'].str.lower() + '|' + df['produk'] + '|' + df['Rating'].astype(str)
        df = df[~kunci.duplicated()].reset_index(drop=True)
    return df, n_awal - len(df)


def label_df(df, mesin, cb=None, ukuran=64):
    """Jalankan mesin pada seluruh ulasan. cb(persen, pesan) opsional."""
    teks = df['Ulasan'].tolist()
    hasil = []
    for i in range(0, len(teks), ukuran):
        hasil.extend(mesin.analisis_banyak(teks[i:i + ukuran]))
        if cb:
            cb(min(85, int(85 * (i + ukuran) / max(1, len(teks)))), f'Menilai ulasan {min(i + ukuran, len(teks)):,}'.replace(',', '.') + f' dari {len(teks):,}'.replace(',', '.'))
    df['label'] = [h['label'] for h in hasil]
    df['skor'] = [h['skor'] for h in hasil]
    df['campuran'] = [bool(h['campuran']) for h in hasil]
    if hasil and 'bert' in hasil[0]:
        for k, nm in (('Positif', 'p_pos'), ('Netral', 'p_net'), ('Negatif', 'p_neg')):
            df[nm] = [h['bert'][k] for h in hasil]
    asp = []
    for i, t in enumerate(teks):
        asp.append(json.dumps([[a, l] for a, l, _ in analisis_aspek(t)], ensure_ascii=False))
        if cb and i % 500 == 0:
            cb(85 + int(14 * i / max(1, len(teks))), 'Mengelompokkan topik')
    df['aspek'] = asp
    df['konflik'] = ((df.Rating >= 4) & (df.label == 'Negatif')) | ((df.Rating <= 2) & (df.label == 'Positif'))
    df.insert(0, 'rid', range(1, len(df) + 1))
    return df


def _pct(x, n):
    return 0.0 if n == 0 else round(100 * x / n, 1)


def _aspek_tabel(df):
    t = defaultdict(Counter)
    for s in df['aspek']:
        for a, l in json.loads(s):
            t[a][l] += 1
    return t


def _kata_dominan(df, k=40):
    cnt = {l: Counter() for l in URUTAN}
    for teks, l in zip(df['Ulasan'], df['label']):
        for w in set(token(normalisasi(teks))):
            if len(w) > 2 and w not in STOP and not w.isdigit():
                cnt[l][w] += 1
    n = {l: max(1, sum((df.label == l))) for l in URUTAN}
    hasil = {}
    for l in ('Positif', 'Negatif'):
        lain = [x for x in URUTAN if x != l]
        skor = []
        for w, c in cnt[l].items():
            if c < 3: continue
            c_lain = sum(cnt[x][w] for x in lain)
            n_lain = sum(n[x] for x in lain)
            if (c / n[l]) < 2 * (c_lain / max(1, n_lain)): continue
            lo = math.log((c + 1) / (n[l] + 2)) - math.log((c_lain + 1) / (n_lain + 2))
            skor.append((lo * math.log(c + 1), w, c))
        skor.sort(reverse=True)
        hasil[l] = [{'kata': w, 'jumlah': c} for _, w, c in skor[:k]]
    return hasil


def ringkas(df, min_produk=8, top_produk=60, dengan_kata=True):
    n = len(df)
    c = df.label.value_counts()
    r = dict(n=n, pos=int(c.get('Positif', 0)), net=int(c.get('Netral', 0)), neg=int(c.get('Negatif', 0)),
             camp=int(df.campuran.sum()), konflik=int(df.konflik.sum()))
    for k in ('pos', 'net', 'neg', 'camp', 'konflik'):
        r[k + '_pct'] = _pct(r[k], n)
    r['rating'] = None if df.Rating.isna().all() else round(float(df.Rating.mean()), 2)
    r['ada_rating'] = bool(not df.Rating.isna().all())
    at = _aspek_tabel(df)
    r['aspek'] = sorted([{'nama': a, 'puji': v['Positif'], 'keluh': v['Negatif'], 'total': v['Positif'] + v['Negatif']} for a, v in at.items()],
                        key=lambda x: -x['total'])
    # matriks rating x label
    if r['ada_rating']:
        m = []
        for rt in (5, 4, 3, 2, 1):
            s = df[df.Rating == rt]
            m.append({'rating': rt, 'n': int(len(s)), 'Positif': int((s.label == 'Positif').sum()), 'Netral': int((s.label == 'Netral').sum()), 'Negatif': int((s.label == 'Negatif').sum())})
        r['matriks'] = m
    bins = df.skor.clip(-4, 4).round().astype(int).value_counts()
    r['hist'] = [dict(x=x, n=int(bins.get(x, 0))) for x in range(-4, 5)]
    if dengan_kata:
        r['kata'] = _kata_dominan(df)
    # produk
    prod = []
    for nama, g in df.groupby('produk'):
        if len(g) < min_produk: continue
        cg = g.label.value_counts(); ag = _aspek_tabel(g)
        keluh = sorted(((v['Negatif'], k) for k, v in ag.items() if v['Negatif']), reverse=True)[:2]
        puji = sorted(((v['Positif'], k) for k, v in ag.items() if v['Positif']), reverse=True)[:2]
        prod.append(dict(nama=nama, n=int(len(g)), pos=_pct(cg.get('Positif', 0), len(g)), net=_pct(cg.get('Netral', 0), len(g)),
                         neg=_pct(cg.get('Negatif', 0), len(g)), rating=None if g.Rating.isna().all() else round(float(g.Rating.mean()), 2),
                         keluh=[k for _, k in keluh], puji=[k for _, k in puji]))
    prod.sort(key=lambda x: -x['n'])
    r['produk'] = prod[:top_produk]
    r['n_produk'] = int(df.produk.nunique())
    ur = [a['nama'] for a in r['aspek']]
    r['heat_aspek'] = ur
    big = df.produk.value_counts()
    big = [x for x in big.index if big[x] >= min_produk][:12]
    r['heat_produk'] = _heat(df, 'produk', big, lambda v: v, ur) if len(big) > 1 else []
    r['heat_rating'] = _heat(df, 'Rating', [5, 4, 3, 2, 1], lambda v: f'Bintang {v}', ur) if r['ada_rating'] else []
    r['judul'], r['subjudul'] = _kalimat(r)
    return r


def _heat(df, kunci, nilai, nama_fn, urut_aspek):
    out = []
    for v in nilai:
        g = df[df[kunci] == v]
        t = _aspek_tabel(g)
        out.append(dict(nama=nama_fn(v), n=int(len(g)), sel=[dict(puji=t[a]['Positif'], keluh=t[a]['Negatif']) for a in urut_aspek]))
    return out


def _kalimat(r):
    p, ng = r['pos_pct'], r['neg_pct']
    if p >= 70: j = f'Pelanggan umumnya puas: {p:.0f}% ulasan positif.'
    elif p >= 50: j = f'Sentimen condong positif: {p:.0f}% ulasan positif, {ng:.0f}% negatif.'
    elif p >= 35: j = f'Sentimen terbelah: {p:.0f}% positif dan {ng:.0f}% negatif.'
    else: j = f'Sentimen condong negatif: {ng:.0f}% ulasan negatif.'
    keluh = [a for a in r['aspek'] if a['keluh'] > 0]
    keluh.sort(key=lambda a: -a['keluh'])
    if keluh and keluh[0]['keluh'] >= 3:
        top = keluh[0]
        s = f"Keluhan terbanyak ada di {top['nama'].lower()} ({top['keluh']} ulasan)."
    else:
        s = 'Belum ada topik keluhan yang menonjol.'
    return j, s
