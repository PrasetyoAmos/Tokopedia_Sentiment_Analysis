"""Sentimen Ulasan v2 - aplikasi lokal.
Jalankan:  python app.py            (mesin aturan, tanpa unduhan)
           python app.py --transformer   (tambah pilihan IndoBERT; butuh torch + transformers)
Buka http://127.0.0.1:5000"""
import argparse, io, json, os, sys, threading, time, uuid, webbrowser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
from flask import Flask, jsonify, request, render_template, Response, abort
from sentimen import buat_mesin
from sentimen.pipeline import muat_csv, siapkan, label_df, ringkas

DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024
JOBS, HASIL, MESIN = {}, {}, {}
TRANSFORMER_AKTIF = False
DEFAULT_MESIN = 'aturan'
LOCK = threading.Lock()


def _mesin(nama):
    with LOCK:
        if nama not in MESIN:
            if nama == 'gabungan':  # satu model IndoBERT dipakai bersama
                if 'transformer' not in MESIN: MESIN['transformer'] = buat_mesin('transformer')
                MESIN[nama] = buat_mesin('gabungan', transformer=MESIN['transformer'])
            else:
                MESIN[nama] = buat_mesin(nama)
        return MESIN[nama]


def _jalankan(jid, sumber, nama_berkas, nama_mesin, buang_dup, awal=0):
    j = JOBS[jid]
    def cb(p, m): j.update(persen=int(awal + p * (100 - awal) / 100), pesan=m)
    try:
        t0 = time.time()
        cb(3, 'Membaca file')
        df = muat_csv(sumber)
        n_mentah = len(df)
        df, n_dup = siapkan(df, buang_dup)
        if len(df) == 0: raise ValueError('Tidak ada ulasan yang bisa dianalisis.')
        cb(6, 'Menyiapkan mesin ' + ('IndoBERT (pertama kali agak lama)' if nama_mesin in ('transformer', 'gabungan') else 'aturan'))
        try:
            mesin = _mesin(nama_mesin)
        except Exception as e:  # model belum terunduh / tidak ada internet / memori kurang
            if nama_mesin == 'aturan': raise
            j['catatan'] = 'IndoBERT tidak bisa dimuat, memakai mesin aturan. Penyebab: ' + str(e).splitlines()[0][:160]
            nama_mesin = 'aturan'; mesin = _mesin('aturan')
        df = label_df(df, mesin, cb)
        cb(99, 'Menyusun ringkasan')
        r = ringkas(df)
        r.update(berkas=nama_berkas, mesin=nama_mesin, n_mentah=n_mentah, duplikat=n_dup, detik=round(time.time() - t0, 1))
        HASIL[jid] = dict(df=df, ringkasan=r, mesin=mesin)
        j.update(status='selesai', persen=100, pesan='Selesai')
        r['catatan'] = j.get('catatan', '')
    except BaseException as e:  # termasuk SystemExit agar tugas tidak menggantung
        j.update(status='gagal', pesan=str(e) or e.__class__.__name__)


def _mulai(sumber, nama, mesin, dup):
    jid = uuid.uuid4().hex[:10]
    JOBS[jid] = dict(status='jalan', persen=0, pesan='Mulai')
    threading.Thread(target=_jalankan, args=(jid, sumber, nama, mesin, dup), daemon=True).start()
    return jid


def _scrape_lalu_analisis(jid, url, halaman, tampil, nama_mesin, dup):
    j = JOBS[jid]
    try:
        from sentimen.scraper import ambil
        data = ambil(url, halaman, tampil, cb=lambda p, m: j.update(persen=p, pesan=m))
        if not data: raise ValueError('Tidak ada ulasan yang berhasil diambil.')
        os.makedirs(os.path.join(DIR, 'data'), exist_ok=True)
        nama = time.strftime('scrape_%Y%m%d_%H%M%S.csv')
        pd.DataFrame(data).to_csv(os.path.join(DIR, 'data', nama), index=False, encoding='utf-8-sig')
        j.update(persen=40, pesan=f'{len(data)} ulasan terambil, mulai menganalisis')
        _jalankan(jid, os.path.join(DIR, 'data', nama), nama, nama_mesin, dup, awal=40)
    except ImportError:
        j.update(status='gagal', pesan='Fitur ini butuh: pip install selenium beautifulsoup4')
    except Exception as e:
        j.update(status='gagal', pesan=str(e))


@app.post('/api/scrape')
def scrape():
    url = request.form.get('url', '').strip()
    if 'tokopedia.com' not in url: return jsonify(error='Tempel link halaman ulasan produk dari tokopedia.com.'), 400
    try: halaman = max(1, min(int(request.form.get('halaman', 5)), 300))
    except ValueError: return jsonify(error='Jumlah halaman harus angka.'), 400
    mesin = request.form.get('mesin', 'aturan')
    if mesin in ('transformer', 'gabungan') and not TRANSFORMER_AKTIF: mesin = 'aturan'
    jid = uuid.uuid4().hex[:10]; JOBS[jid] = dict(status='jalan', persen=0, pesan='Mulai')
    threading.Thread(target=_scrape_lalu_analisis, daemon=True,
                     args=(jid, url, halaman, request.form.get('tampil', '1') == '1', mesin, request.form.get('duplikat', '1') == '1')).start()
    return jsonify(id=jid)


@app.get('/')
def index():
    return render_template('index.html', transformer=TRANSFORMER_AKTIF, default=DEFAULT_MESIN)


def _daftar_contoh():
    out = []
    for sub in ('data', 'data_contoh'):
        d = os.path.join(DIR, sub)
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.lower().endswith('.csv'):
                    out.append(dict(nama=f, jalur=sub + '/' + f, ukuran=os.path.getsize(os.path.join(d, f))))
    return out


@app.get('/api/contoh')
def contoh(): return jsonify(_daftar_contoh())


@app.post('/api/mulai')
def mulai():
    mesin = request.form.get('mesin', 'aturan')
    if mesin in ('transformer', 'gabungan') and not TRANSFORMER_AKTIF: mesin = 'aturan'
    dup = request.form.get('duplikat', '1') == '1'
    if 'file' in request.files and request.files['file'].filename:
        f = request.files['file']
        sumber = io.BytesIO(f.read()); nama = f.filename
    else:
        jalur = request.form.get('contoh', '')
        ok = {c['jalur']: c for c in _daftar_contoh()}
        if jalur not in ok: return jsonify(error='File tidak dipilih.'), 400
        sumber = os.path.join(DIR, jalur); nama = ok[jalur]['nama']
    return jsonify(id=_mulai(sumber, nama, mesin, dup))


@app.get('/api/status/<jid>')
def status(jid):
    j = JOBS.get(jid) or abort(404)
    return jsonify(j)


def _h(jid): return HASIL.get(jid) or abort(404)


@app.get('/api/hasil/<jid>')
def hasil(jid): return jsonify(_h(jid)['ringkasan'])


@app.get('/api/produk/<jid>')
def produk(jid):
    df = _h(jid)['df']
    g = df[df.produk == request.args.get('nama', '')]
    if g.empty: abort(404)
    return jsonify(ringkas(g, min_produk=1, top_produk=0))


def _filter(df):
    a = request.args
    if a.get('produk'): df = df[df.produk == a['produk']]
    if a.get('label'): df = df[df.label == a['label']]
    if a.get('aspek'):
        asp, lab = a['aspek'], a.get('sentimen_aspek')
        df = df[df.aspek.map(lambda s: any(x[0] == asp and (not lab or x[1] == lab) for x in json.loads(s)))]
    if a.get('konflik') == '1': df = df[df.konflik]
    if a.get('campuran') == '1': df = df[df.campuran]
    if a.get('rating'): df = df[df.Rating == float(a['rating'])]
    if a.get('q'): df = df[df.Ulasan.str.contains(a['q'], case=False, regex=False)]
    return df


@app.get('/api/ulasan/<jid>')
def ulasan(jid):
    h = _h(jid); df = _filter(h['df'])
    hal = max(1, int(request.args.get('hal', 1))); per = 25
    urut = request.args.get('urut', 'acak')
    if urut == 'skor_naik': df = df.sort_values('skor')
    elif urut == 'skor_turun': df = df.sort_values('skor', ascending=False)
    else: df = df.sample(frac=1, random_state=7) if len(df) < 20000 else df
    baris = df.iloc[(hal - 1) * per: hal * per]
    mesin = h['mesin']; out = []
    for _, r in baris.iterrows():
        d = dict(rid=int(r.rid), teks=r.Ulasan, rating=None if pd.isna(r.Rating) else int(r.Rating), label=r.label, skor=r.skor,
                 campuran=r.campuran, konflik=bool(r.konflik), produk=r.produk, aspek=json.loads(r.aspek))
        aturan = getattr(mesin, 'aturan', mesin)
        if h['ringkasan']['mesin'] in ('aturan', 'gabungan'):
            d['klausa'] = [dict(teks=k, pos=p, neg=n) for k, p, n in aturan.analisis(r.Ulasan)['klausa']]
        if 'p_pos' in r.index:
            d['bert'] = dict(pos=round(float(r.p_pos), 2), net=round(float(r.p_net), 2), neg=round(float(r.p_neg), 2))
        out.append(d)
    return jsonify(total=int(len(df)), hal=hal, per=per, baris=out)


@app.get('/api/ekspor/<jid>')
def ekspor(jid):
    df = _h(jid)['df'][['rid', 'produk', 'Ulasan', 'Rating', 'label', 'skor', 'campuran', 'konflik', 'aspek']]
    return Response('﻿' + df.to_csv(index=False), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=hasil_sentimen.csv'})


@app.post('/api/validasi/<jid>')
def validasi(jid):
    from sklearn.metrics import precision_recall_fscore_support, accuracy_score, confusion_matrix
    h = _h(jid); f = request.files.get('file')
    if f is None: return jsonify(error='Pilih file label manual (kolom Ulasan dan label_manual).'), 400
    g = pd.read_csv(io.BytesIO(f.read()), encoding='utf-8-sig')
    if not {'Ulasan', 'label_manual'} <= set(g.columns):
        return jsonify(error="File harus punya kolom 'Ulasan' dan 'label_manual' (Positif/Negatif/Netral)."), 400
    g = g[g.label_manual.isin(['Positif', 'Negatif', 'Netral'])].copy()
    if g.empty: return jsonify(error='Tidak ada baris berlabel Positif/Negatif/Netral.'), 400
    hasil = h['mesin'].analisis_banyak(g.Ulasan.astype(str).tolist())
    g['pred'] = [x['label'] for x in hasil]
    L = ['Positif', 'Netral', 'Negatif']
    p, r, f1, s = precision_recall_fscore_support(g.label_manual, g.pred, labels=L, zero_division=0)
    cm = confusion_matrix(g.label_manual, g.pred, labels=L).tolist()
    salah = g[g.label_manual != g.pred].head(30)
    return jsonify(n=int(len(g)), akurasi=round(float(accuracy_score(g.label_manual, g.pred)), 3),
                   macro_f1=round(float(f1.mean()), 3),
                   kelas=[dict(label=l, presisi=round(float(a), 2), recall=round(float(b), 2), f1=round(float(c), 2), n=int(d))
                          for l, a, b, c, d in zip(L, p, r, f1, s)],
                   matriks=cm, labels=L,
                   salah=[dict(teks=r.Ulasan, manual=r.label_manual, mesin=r.pred) for _, r in salah.iterrows()])


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--transformer', action='store_true', help='paksa tampilkan pilihan IndoBERT (otomatis bila torch+transformers terpasang)')
    ap.add_argument('--aturan', action='store_true', help='pakai mesin aturan saja (tanpa IndoBERT)')
    ap.add_argument('--port', type=int, default=5000)
    ap.add_argument('--tanpa-browser', action='store_true')
    a = ap.parse_args()
    import importlib.util as iu
    ada = all(iu.find_spec(m) for m in ('torch', 'transformers'))
    TRANSFORMER_AKTIF = (ada or a.transformer) and not a.aturan
    DEFAULT_MESIN = 'gabungan' if TRANSFORMER_AKTIF else 'aturan'
    print('  Mesin bawaan:', 'gabungan IndoBERT + aturan (torch + transformers terdeteksi)' if TRANSFORMER_AKTIF else 'aturan bahasa (pasang torch + transformers untuk IndoBERT)')
    if not a.tanpa_browser:
        threading.Timer(1.2, lambda: webbrowser.open(f'http://127.0.0.1:{a.port}')).start()
    print(f'\n  Buka http://127.0.0.1:{a.port}  (Ctrl+C untuk berhenti)\n')
    app.run(host='127.0.0.1', port=a.port, debug=False, threaded=True)
