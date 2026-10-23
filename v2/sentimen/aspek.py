"""Topik yang dibicarakan: aspek per klausa beserta sentimennya."""
import re
from .normalisasi import normalisasi, klausa, token
from .mesin_aturan import MesinAturan

ASPEK = {
    'Kualitas produk': ['kualitas', 'bahan', 'jahitan', 'awet', 'kokoh', 'material', 'finishing', 'warna', 'performa', 'layar',
                        'kamera', 'baterai', 'batre', 'sinyal', 'suara', 'speaker', 'cas', 'charger', 'ngelag', 'lemot', 'panas',
                        'cacat', 'rusak', 'lecet', 'penyok', 'retak', 'fungsi', 'berfungsi', 'nyala', 'hasil', 'tebal', 'halus', 'empuk'],
    'Ukuran & kesesuaian': ['ukuran', 'size', 'sizenya', 'pas', 'kebesaran', 'kekecilan', 'sempit', 'longgar', 'sesuai', 'deskripsi',
                            'foto', 'gambar', 'varian', 'pesanan', 'model', 'ekspektasi', 'beda'],
    'Pengiriman': ['kirim', 'pengiriman', 'kurir', 'sampai', 'ekspedisi', 'resi', 'jne', 'sicepat', 'jnt', 'gosend', 'grab',
                   'instan', 'nyasar', 'telat', 'terlambat', 'diterima', 'tiba', 'paket'],
    'Kemasan': ['packing', 'kemasan', 'bubble', 'wrap', 'dus', 'kardus', 'plastik', 'bungkus', 'dibungkus', 'segel', 'box'],
    'Penjual & layanan': ['seller', 'penjual', 'admin', 'respon', 'responsif', 'ramah', 'toko', 'chat', 'garansi', 'retur', 'refund',
                          'komplain', 'pelayanan', 'layanan', 'cs', 'dibalas', 'tanggap', 'amanah', 'cuek', 'judes', 'tokopedia'],
    'Harga': ['harga', 'murah', 'mahal', 'worth', 'promo', 'diskon', 'terjangkau', 'ongkir', 'sepadan', 'cashback', 'voucher'],
    'Keaslian': ['original', 'asli', 'palsu', 'fake', 'kw', 'ori', 'bekas', 'segel', 'resmi'],
}
_INDEKS = {}
for a, kata in ASPEK.items():
    for k in kata:
        _INDEKS.setdefault(k, []).append(a)

_mesin = MesinAturan()


def analisis_aspek(teks, mesin=None):
    """Kembalikan daftar (aspek, label, klausa) untuk tiap klausa yang menyebut aspek dan punya sentimen."""
    mesin = mesin or _mesin
    hasil = []
    ks = klausa(normalisasi(teks))
    for idx, k in enumerate(ks):
        toks = token(k)
        aspek = {a for t in toks for a in _INDEKS.get(t, [])}
        p, n = mesin.skor_klausa(k)
        if not aspek:
            continue
        # klausa tanpa kata sentimen mewarisi klausa sebelumnya/sesudahnya yang bersentimen (mis. "pengiriman, cepat")
        if abs(p - n) < mesin.ambang and idx + 1 < len(ks):
            p2, n2 = mesin.skor_klausa(ks[idx + 1])
            if not _INDEKS_ADA(ks[idx + 1]):
                p, n = p + p2, n + n2
        skor = p - n
        if skor >= mesin.ambang: lab = 'Positif'
        elif skor <= -mesin.ambang: lab = 'Negatif'
        else: continue
        for a in aspek:
            hasil.append((a, lab, k))
    return hasil


def _INDEKS_ADA(klausa_teks):
    return any(t in _INDEKS for t in token(klausa_teks))
