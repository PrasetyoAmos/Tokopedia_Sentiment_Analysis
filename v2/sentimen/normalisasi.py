import re

SLANG = {
    'cakep': 'bagus', 'cakeup': 'bagus', 'cakepp': 'bagus',
    'gk': 'tidak', 'ga': 'tidak', 'gak': 'tidak', 'nggak': 'tidak', 'ngga': 'tidak', 'enggak': 'tidak', 'engga': 'tidak',
    'tdk': 'tidak', 'gx': 'tidak', 'tak': 'tidak', 'ndak': 'tidak', 'gada': 'tidak ada', 'gaada': 'tidak ada',
    'gabisa': 'tidak bisa', 'gbs': 'tidak bisa', 'blm': 'belum', 'udh': 'sudah', 'udah': 'sudah', 'sdh': 'sudah',
    'bgt': 'banget', 'bngt': 'banget', 'bgtt': 'banget', 'bangettt': 'banget', 'sgt': 'sangat',
    'mantul': 'mantap', 'mantab': 'mantap', 'mantep': 'mantap', 'josss': 'jos', 'joss': 'jos', 'sip': 'bagus', 'siip': 'bagus',
    'bgus': 'bagus', 'baguss': 'bagus', 'bagusss': 'bagus', 'rekomen': 'rekomendasi', 'recomended': 'recommended',
    'recomen': 'recommended', 'rekomended': 'recommended', 'rekomendasi': 'recommended', 'rec': 'recommended',
    'yg': 'yang', 'dgn': 'dengan', 'dg': 'dengan', 'utk': 'untuk', 'krn': 'karena', 'karna': 'karena', 'jg': 'juga',
    'tp': 'tapi', 'tapii': 'tapi', 'cuman': 'cuma', 'cm': 'cuma', 'lbh': 'lebih', 'sm': 'sama', 'trs': 'terus',
    'brg': 'barang', 'barangnya': 'barang', 'pengirimannya': 'pengiriman', 'kurirnya': 'kurir', 'packingnya': 'packing',
    'packagingnya': 'packing', 'sellernya': 'seller', 'penjualnya': 'penjual', 'tokonya': 'toko', 'hp': 'hp',
    'cpt': 'cepat', 'cepet': 'cepat', 'lama': 'lama', 'lmbat': 'lambat', 'lelet': 'lambat', 'jelek': 'jelek',
    'kecewaa': 'kecewa', 'thx': 'terima kasih', 'tq': 'terima kasih', 'makasih': 'terima kasih', 'thanks': 'terima kasih',
    'trims': 'terima kasih', 'trimakasih': 'terima kasih', 'terimakasih': 'terima kasih', 'ori': 'original', 'org': 'orang',
    'bs': 'bisa', 'recomend': 'recommended', 'recommendnya': 'recommended', 'rekomend': 'recommended', 'ok': 'oke', 'okey': 'oke', 'okay': 'oke', 'oke': 'oke', 'murce': 'murah', 'worth': 'worth', 'recommend': 'recommended',
}

_ULANG = re.compile(r'(.)\1{2,}')          # bagusss -> bagus, bangetttt -> banget
_KATA = re.compile(r"[a-z]+(?:-[a-z]+)?|\d+")


def normalisasi(teks: str) -> str:
    t = str(teks).lower()
    t = _ULANG.sub(r'\1', t)
    t = re.sub(r'\b(?:ga|gak|gk|nggak|tidak|tdk)\s+bisa\s+ber(?:word|kata)\S*(?:\s*-\s*kata)?', 'speechless', t)  # "ga bisa berkata-kata" = terpukau
    # pisahkan emoji dari kata agar tidak menempel
    t = re.sub(r'([^\w\s.,!?\-])', r' \1 ', t)
    out = []
    for tok in re.split(r'\s+', t):
        out.append(SLANG.get(tok, tok))
    return ' '.join(out)


def klausa(teks_norm: str):
    """Pecah ulasan menjadi klausa berdasarkan tanda baca dan kata kontras, kata kontras ikut klausa berikutnya."""
    bagian = re.split(r'[.!?\n;]+|\s,\s|,', teks_norm)
    hasil = []
    for b in bagian:
        for p in re.split(r'\b(?=(?:tapi|cuma|namun|sayang|sayangnya|hanya saja|akan tetapi|walaupun|meskipun|padahal)\b)', b):
            p = p.strip()
            if p:
                hasil.append(p)
    return hasil


def token(klausa_teks: str):
    return _KATA.findall(klausa_teks)
