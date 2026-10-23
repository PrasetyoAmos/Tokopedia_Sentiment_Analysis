"""Penanganan slang, singkatan, dan salah ketik bahasa Indonesia sebelum ulasan dinilai.

Tiga lapis, dari yang paling pasti:
1. KAMUS    - slang/singkatan yang sudah dikenal ('gaosah' -> 'tidak usah', 'satset' -> 'cepat').
2. RANGKA   - singkatan tanpa vokal ('mntp' -> 'mantap', 'bgs' -> 'bagus', 'kwlts' -> 'kualitas'),
              dipakai hanya bila rangka konsonannya cocok dengan tepat satu kata kamus sentimen/topik.
3. MIRIP    - salah ketik ('kwalitas' -> 'kualitas', 'kendall' -> 'kendala'), dipakai hanya bila
              kemiripan huruf tinggi dan huruf pertama sama.
Kata yang sudah dikenal tidak pernah diubah, kata pendek (<4 huruf) tidak ditebak."""
import re
from difflib import get_close_matches

KAMUS = {
    # pujian
    'satset': 'cepat', 'sat-set': 'cepat', 'kenceng': 'cepat', 'gercep': 'cepat', 'wuzz': 'cepat',
    'gokil': 'bagus', 'kece': 'bagus', 'ciamik': 'bagus', 'paten': 'mantap', 'markotop': 'mantap', 'sipp': 'bagus', 'siplah': 'bagus',
    'cakeup': 'bagus', 'cwakep': 'bagus', 'cwakepp': 'bagus', 'cakepp': 'bagus', 'kecee': 'bagus', 'kerenn': 'keren',
    'pwoll': 'pol', 'pwol': 'pol', 'poll': 'pol', 'mantapp': 'mantap', 'mantabb': 'mantap', 'mantaps': 'mantap', 'mantull': 'mantap',
    'pwas': 'puas', 'puass': 'puas', 'worthit': 'worth', 'wortit': 'worth', 'worthed': 'worth', 'oke': 'oke', 'okeh': 'oke', 'okelah': 'oke',
    'hamdalah': 'alhamdulillah', 'hamdllah': 'alhamdulillah', 'hamdulillah': 'alhamdulillah', 'alhamdulilah': 'alhamdulillah',
    'alhamdullilah': 'alhamdulillah', 'alhamdulillahh': 'alhamdulillah', 'alhmdllh': 'alhamdulillah',
    'kualitasss': 'kualitas', 'kwalitas': 'kualitas', 'kwalitasnya': 'kualitas', 'perfoma': 'performa', 'perform': 'performa',
    'gaosah': 'tidak usah', 'gausah': 'tidak usah', 'gaperlu': 'tidak perlu', 'ganyesel': 'tidak nyesel', 'gapernah': 'tidak pernah',
    'gakecewa': 'tidak kecewa', 'gaada': 'tidak ada', 'gadaa': 'tidak ada', 'gamuat': 'tidak muat', 'gapapa': 'tidak apa-apa', 'gpp': 'tidak apa-apa',
    'ditanyak': 'ditanya', 'diragukan': 'diragukan', 'selamatt': 'selamat', 'selamatsemoga': 'selamat semoga',
    # keluhan
    'dibales': 'dibalas', 'dibls': 'dibalas', 'dbales': 'dibalas', 'kesel': 'kesal', 'kzl': 'kesal', 'bete': 'kesal', 'dongkol': 'kesal',
    'ngecewain': 'mengecewakan', 'ngecewakan': 'mengecewakan', 'kecewaa': 'kecewa', 'zonkk': 'zonk', 'apes': 'sial',
    'nyesell': 'nyesel', 'nyesal': 'menyesal', 'bapuk': 'jelek', 'burik': 'jelek', 'amsyong': 'rusak', 'ancurr': 'ancur',
    'ngadat': 'rusak', 'ngehang': 'macet', 'ngelag': 'ngelag', 'lemott': 'lemot', 'lelett': 'lambat',
    'jamuran': 'berjamur', 'ketuker': 'tertukar', 'ketukar': 'tertukar', 'ketuker2': 'tertukar', 'salahkirim': 'salah kirim',
    'gkbisa': 'tidak bisa', 'gabisaa': 'tidak bisa', 'gbsa': 'tidak bisa', 'tdak': 'tidak', 'tidk': 'tidak', 'tdk': 'tidak',
    'kgk': 'tidak', 'kaga': 'tidak', 'kagak': 'tidak', 'nggk': 'tidak', 'ngk': 'tidak', 'gx': 'tidak', 'gaa': 'tidak', 'gda': 'tidak ada',
    'rekomended': 'recommended', 'rekomendid': 'recommended', 'recomend': 'recommended', 'recommended': 'recommended', 'rekomen': 'recommended',
    'recomendedd': 'recommended', 'rcmnd': 'recommended',
    # umum
    'gmn': 'bagaimana', 'gimana': 'bagaimana', 'gm': 'bagaimana', 'kyk': 'seperti', 'kaya': 'seperti', 'kayak': 'seperti', 'spt': 'seperti',
    'bgt': 'banget', 'bgtt': 'banget', 'bngtt': 'banget', 'bgd': 'banget', 'bet': 'banget', 'abis': 'habis', 'doang': 'saja', 'aja': 'saja', 'ajah': 'saja',
    'dr': 'dari', 'dri': 'dari', 'sampe': 'sampai', 'sampek': 'sampai', 'smpe': 'sampai', 'smp': 'sampai', 'dtg': 'datang', 'dateng': 'datang',
    'kirimnya': 'kirim', 'dikirimnya': 'dikirim', 'pengirimn': 'pengiriman', 'pengirimannya': 'pengiriman', 'pcking': 'packing', 'pecking': 'packing',
    'pakingnya': 'packing', 'paking': 'packing', 'packing': 'packing', 'pckg': 'packing', 'dus': 'dus', 'ekspedisinya': 'ekspedisi',
    'pesen': 'pesan', 'psn': 'pesan', 'pesenan': 'pesanan', 'pesenannya': 'pesanan', 'brgnya': 'barang', 'brng': 'barang', 'barng': 'barang',
    'seller': 'seller', 'sllr': 'seller', 'penjualx': 'penjual', 'tokped': 'tokopedia', 'tokpedia': 'tokopedia',
    'dapet': 'dapat', 'dpt': 'dapat', 'dpet': 'dapat', 'bikin': 'membuat', 'bnyk': 'banyak', 'sdkt': 'sedikit', 'dikit': 'sedikit', 'bgs': 'bagus',
    'mls': 'malas', 'bru': 'baru', 'lg': 'lagi', 'lgi': 'lagi', 'hrs': 'harus', 'skrg': 'sekarang', 'sblm': 'sebelum', 'stlh': 'setelah',
    'packaging': 'packing', 'packagingnya': 'packing', 'buble': 'bubble', 'ekspetasi': 'ekspektasi', 'diskripsi': 'deskripsi', 'kendall': 'kendala',
    'kemaren': 'kemarin', 'response': 'respon', 'respons': 'respon', 'kmrn': 'kemarin', 'bsk': 'besok', 'tmn': 'teman', 'kk': 'kakak', 'min': 'admin', 'gan': 'agan', 'sis': 'kakak',
}

# kata yang dianggap 'sudah benar' walau tidak ada di kamus sentimen, agar tidak salah dikoreksi
UMUM = set('''plus pass yang dan di ke dari ini itu untuk dengan ada saya sudah juga atau tapi karena pada akan bisa sama jadi lagi saja udah banget sekali
lebih sih deh dong kok tidak belum bukan barang produk beli pesan sampai kali lah nih ya kan mau kalau hanya cuma agak masih sangat semua setelah
sebelum dalam oleh seperti yaitu lain kakak toko seller penjual terima kasih kirim dikirim datang warna ukuran sepatu baju kaos celana tas hp
kabel charger ongkir pesanan model bahan harga stok varian paket kurir ekspedisi packing dus kardus plastik bubble wrap box foto gambar
deskripsi pakai dipakai dipakek pemakaian beberapa banyak sedikit kemarin besok nanti dulu terus tetap pernah kembali coba mencoba mau ingin
bahkan ternyata malah padahal walaupun meskipun supaya agar biar kalo klo kenapa gimana bagaimana dimana kapan siapa berapa'''.split())

_indeks = None


def _bangun():
    global _indeks
    from .mesin_aturan import POSITIF, NEGATIF, FRASA_POS, FRASA_NEG
    from .aspek import ASPEK
    kosa = set(POSITIF) | set(NEGATIF) | {k for ks in ASPEK.values() for k in ks}
    for f in list(FRASA_POS) + list(FRASA_NEG):
        kosa.update(f.split())
    kosa |= set(KAMUS.values())
    kosa = {k for k in kosa if re.fullmatch(r'[a-z]+', k)}
    rangka = {}
    for k in kosa:
        r = re.sub(r'[aeiou]', '', k)
        if len(r) >= 3 and len(k) >= 4:
            rangka.setdefault(r, set()).add(k)
    per_awal = {}
    for k in kosa:
        if len(k) >= 5:
            per_awal.setdefault(k[0], []).append(k)
    _indeks = dict(kosa=kosa, rangka={r: next(iter(v)) for r, v in rangka.items() if len(v) == 1}, per_awal=per_awal)


def koreksi(tok):
    """Kembalikan bentuk baku sebuah kata, atau kata itu sendiri bila tidak yakin."""
    if tok in KAMUS:
        return KAMUS[tok]
    if not re.fullmatch(r'[a-z]+', tok) or len(tok) < 4:
        return tok
    if _indeks is None:
        _bangun()
    if tok in _indeks['kosa'] or tok in UMUM:
        return tok
    # akhiran -nya dan huruf akhir ganda: periksa bentuk dasarnya dulu
    dasar = tok[:-3] if tok.endswith('nya') and len(tok) > 6 else tok
    if dasar != tok and (dasar in _indeks['kosa'] or dasar in UMUM):
        return tok
    if len(dasar) > 3 and dasar[-1] == dasar[-2] and dasar[:-1] in (_indeks['kosa'] | UMUM):
        return dasar[:-1]
    r = re.sub(r'[aeiou]', '', dasar)
    if len(r) >= 3 and r in _indeks['rangka'] and len(dasar) - len(r) <= 1 and len(dasar) < len(_indeks['rangka'][r]):  # hanya singkatan hampir tanpa vokal
        return _indeks['rangka'][r]
    if len(dasar) >= 7:
        m = get_close_matches(dasar, _indeks['per_awal'].get(dasar[0], []), n=1, cutoff=0.88)
        if m and abs(len(m[0]) - len(dasar)) <= 2:
            return m[0]
    return tok
