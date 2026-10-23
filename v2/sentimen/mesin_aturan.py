"""Mesin sentimen berbasis aturan, hanya dari teks. Rating tidak dipakai sama sekali."""
import re
from .normalisasi import normalisasi, klausa, token

POSITIF = {
    'candu': 1.5, 'enak': 1.3, 'seenak': 1.0, 'alhamdulillah': 0.8, 'presisi': 1.2, 'profesional': 1.3, 'komunikatif': 1.3,
    'jelas': 1.0, 'ngefek': 1.0, 'efektif': 1.3, 'ampuh': 1.5, 'tajam': 0.3, 'jaya': 0.6, 'lumayan': 0.4,
    'bagus': 1.5, 'baik': 1.0, 'mantap': 2.0, 'jos': 1.5, 'keren': 1.8, 'puas': 2.0, 'memuaskan': 2.0, 'suka': 1.5,
    'senang': 1.5, 'recommended': 2.0, 'rekomendasi': 1.5, 'oke': 1.0, 'sesuai': 1.2, 'cocok': 1.2, 'pas': 1.0,
    'speechless': 1.5, 'cepat': 1.3, 'kilat': 1.8, 'aman': 1.2, 'rapi': 1.3, 'rapih': 1.3, 'awet': 1.5, 'original': 1.2, 'asli': 1.2,
    'murah': 1.3, 'worth': 1.8, 'sepadan': 1.5, 'nyaman': 1.5, 'halus': 1.2, 'lancar': 1.3, 'mulus': 1.5, 'tebal': 0.8,
    'ramah': 1.5, 'responsif': 1.5, 'fast': 1.3, 'respon': 0.3, 'terbaik': 2.0, 'sempurna': 2.0, 'luar biasa': 2.0,
    'cantik': 1.5, 'bersih': 1.2, 'wangi': 1.2, 'empuk': 1.2, 'kuat': 1.2, 'kokoh': 1.3, 'tangguh': 1.3, 'ngebut': 1.3,
    'terima kasih': 0.8, 'top': 1.5, 'the best': 2.0, 'best': 1.5, 'good': 1.3, 'nice': 1.3, 'great': 1.5, 'love': 1.8,
    'amanah': 1.5, 'terpercaya': 1.5, 'untung': 1.0, 'lengkap': 1.2, 'jernih': 1.3, 'ringan': 1.0, 'premium': 1.3,
    'sukses': 1.2, 'berfungsi': 0.8, 'normal': 0.8, 'tepat': 1.0, 'mulus': 1.5, 'lega': 1.0, 'adem': 1.0,
}
NEGATIF = {
    'patah': 1.8, 'busuk': 2.0, 'ruwet': 1.5, 'kacau': 2.0, 'cacad': 2.0, 'kelamaan': 1.6, 'kosong': 1.0, 'penipuan': 2.5,
    'kasar': 1.2, 'oblak': 1.0, 'putus': 1.3, 'scam': 2.5, 'abal': 1.5, 'ngeyel': 1.5, 'amburadul': 2.0, 'nipu': 2.4,
    'jelek': 2.0, 'buruk': 2.0, 'kecewa': 2.2, 'mengecewakan': 2.2, 'lambat': 1.5, 'rusak': 2.0, 'cacat': 2.0,
    'lecet': 1.5, 'penyok': 1.5, 'retak': 1.8, 'pecah': 1.8, 'bocor': 1.8, 'mati': 1.5, 'error': 1.8, 'lemot': 1.6,
    'panas': 1.0, 'boros': 1.5, 'mahal': 1.3, 'palsu': 2.2, 'fake': 2.2, 'kw': 1.8, 'bekas': 1.8, 'zonk': 2.2,
    'tipu': 2.4, 'penipu': 2.5, 'tertipu': 2.4, 'bohong': 2.0, 'nyesel': 2.2, 'menyesal': 2.2, 'parah': 2.0,
    'sampah': 2.5, 'ancur': 2.0, 'hancur': 2.0, 'bau': 1.3, 'kotor': 1.5, 'kecil': 0.6, 'kebesaran': 1.2, 'kekecilan': 1.2,
    'sempit': 1.0, 'longgar': 1.0, 'luntur': 1.5, 'kusut': 1.3, 'robek': 1.5, 'jebol': 1.6, 'rontok': 1.5,
    'telat': 1.5, 'terlambat': 1.5, 'nyasar': 1.8, 'hilang': 1.8, 'salah': 1.6, 'keliru': 1.5,
    'kurang': 0.8, 'masalah': 1.2, 'kendala': 1.2, 'komplain': 1.5, 'protes': 1.3, 'ribet': 1.3, 'susah': 1.3, 'sulit': 1.2,
    'bohongan': 2.0, 'jutek': 1.6, 'judes': 1.6, 'cuek': 1.5, 'lalai': 1.6, 'ngaco': 1.8, 'payah': 2.0, 'bad': 1.8,
    'terrible': 2.2, 'worst': 2.4, 'disappointed': 2.0, 'kapok': 2.4, 'drop': 1.2, 'ngelag': 1.5, 'lag': 1.2,
    'macet': 1.4, 'blank': 1.4, 'bootloop': 2.0, 'cacatnya': 2.0, 'kotor': 1.5, 'berdebu': 1.0, 'jangan': 1.5,
}
FRASA_POS = {
    'tahan lama': 1.6, 'awet tahan lama': 0.4,
    'tidak diragukan': 1.8, 'tidak pernah kecewa': 2.0, 'tidak ada kendala': 1.8,
    'sesuai deskripsi': 1.8, 'sesuai pesanan': 1.6, 'sesuai foto': 1.5, 'sesuai gambar': 1.5, 'sesuai ekspektasi': 1.6,
    'sesuai harga': 1.4, 'tidak mengecewakan': 2.0, 'tidak ada masalah': 1.8, 'tidak ada kendala': 1.8,
    'tidak ada cacat': 1.8, 'tidak ada lecet': 1.6, 'tidak ada minus': 1.8, 'tanpa kendala': 1.6, 'tidak buruk': 1.0,
    'tidak jelek': 1.0, 'kualitas bagus': 1.5, 'pengiriman cepat': 1.6, 'packing rapi': 1.6, 'packing aman': 1.6,
    'harga murah': 1.3, 'harga terjangkau': 1.3, 'pasti beli lagi': 2.0, 'beli lagi': 1.4, 'next order': 1.5, 'repeat order': 1.8,
    'sampai dengan selamat': 1.4, 'sampai dengan aman': 1.4, 'sampai dengan cepat': 1.5, 'barang sampai': 0.6, 'barang bagus': 1.8,
}
FRASA_NEG = {
    'tidak dikirim': 1.8, 'tidak merespon': 2.0, 'tidak merespons': 2.0, 'tidak sama': 1.5, 'mudah panas': 1.5, 'cepat habis': 1.5,
    'never received': 2.2, 'not received': 2.0, 'cuci tangan': 1.8, 'tidak mau membantu': 1.8, 'tidak diselotip': 1.2, 'tidak padat': 1.0,
    'tidak sesuai': 2.0, 'tidak sampai': 2.2, 'belum sampai': 1.6, 'belum diterima': 1.6, 'tidak berfungsi': 2.2,
    'tidak bisa': 1.4, 'tidak nyala': 2.0, 'tidak menyala': 2.0, 'tidak bagus': 1.8, 'tidak puas': 2.0, 'tidak recommended': 2.2,
    'tidak worth': 1.8, 'tidak ori': 2.0, 'tidak original': 2.0, 'tidak asli': 2.0, 'tidak responsif': 2.0, 'tidak ada respon': 2.0,
    'tidak dibalas': 1.8, 'tidak ditanggapi': 1.8, 'tidak amanah': 2.2, 'salah kirim': 2.2, 'salah ukuran': 2.0, 'salah warna': 2.0,
    'salah varian': 2.0, 'tidak lengkap': 1.8, 'kurang memuaskan': 1.8, 'kurang bagus': 1.6, 'kurang puas': 1.8, 'kurang sesuai': 1.6,
    'kurang rapi': 1.5, 'kurang cepat': 1.4, 'kurang responsif': 1.8, 'jangan beli': 2.6, 'jangan tertipu': 2.4, 'tidak akan beli lagi': 2.4,
    'tidak beli lagi': 2.2, 'pengiriman lama': 1.8, 'lama banget': 1.8, 'lama sekali': 1.8, 'barang jelek': 2.2, 'tidak layak': 2.0,
    'stok lama': 1.5, 'tidak mulus': 1.6, 'tidak segel': 1.8, 'segel rusak': 1.8, 'segel terbuka': 1.8, 'tidak original': 2.0,
}
NEGASI = {'tidak', 'bukan', 'belum', 'tanpa', 'jangan', 'kurang'}
# --- tambahan leksikon slang & keluhan umum ---
for _k, _v in {'sobek': 1.5, 'berjamur': 1.8, 'jamur': 1.3, 'tertukar': 1.8, 'sial': 1.5, 'kesal': 1.8, 'ngehang': 1.4, 'php': 1.8, 'ghosting': 1.8,
               'diabaikan': 1.5, 'berbeda': 1.0, 'broken': 2.0, 'damaged': 2.0, 'slow': 1.3, 'wrong': 1.6, 'shame': 1.5, 'kurang ajar': 2.0,
               'abal-abal': 1.8, 'seret': 1.2, 'rewel': 1.2, 'melenceng': 1.5, 'menyesal': 2.2, 'kelamaan': 1.6}.items():
    NEGATIF.setdefault(_k, _v)
for _k, _v in {'selamat': 0.8, 'alhamdulillah': 0.8, 'gercep': 1.3, 'ciamik': 1.6, 'markotop': 1.8, 'lancar jaya': 1.5, 'sip': 1.3,
               'puas banget': 0.5, 'mulus': 1.5, 'berkualitas': 1.5, 'tahan banting': 1.5, 'nagih': 1.5, 'betah': 1.3, 'pewe': 1.5,
               'trusted': 1.5, 'fast': 1.3, 'kece': 1.5, 'cakep': 1.5, 'mewah': 1.3, 'elegan': 1.3, 'ngadem': 1.0}.items():
    POSITIF.setdefault(_k, _v)
FRASA_NEG.update({'tidak dibalas': 1.8, 'tidak pernah dibalas': 2.0, 'tidak dibales': 1.8, 'tidak muat': 1.5, 'tidak sesuai': 1.8,
                  'tidak dikirim': 2.0, 'salah kirim': 2.0, 'tidak ada respon': 1.8, 'tidak ada balasan': 1.8, 'tidak seenak': 1.5,
                  'tidak seperti': 1.2, 'tidak sama': 1.2, 'tidak berfungsi': 2.0, 'tidak bisa dipakai': 2.0, 'tidak worth': 1.8,
                  'bukan original': 2.0, 'tidak recommended': 2.2, 'tidak nyesel': -1.0})
FRASA_POS.update({'tidak usah ditanya': 1.5, 'tidak perlu diragukan': 1.8, 'tidak usah diragukan': 1.8, 'tidak diragukan': 1.5,
                  'dengan selamat': 1.0, 'tidak ada kendala': 1.5, 'tidak ada masalah': 1.5, 'tidak nyesel': 1.8, 'tidak kecewa': 1.8,
                  'sesuai deskripsi': 1.5, 'sesuai pesanan': 1.3, 'sesuai gambar': 1.5, 'tidak mengecewakan': 1.8, 'ga nyesel': 1.8,
                  'pasti beli lagi': 2.0, 'beli lagi': 1.2, 'repeat order': 1.6, 'langganan': 1.0})
FRASA_NEG.pop('tidak nyesel', None)

HEDGE = {'agak', 'sedikit', 'dikit', 'lumayan'}
KONTEKS_TUNGGU = {'kirim', 'dikirim', 'pengiriman', 'sampai', 'sampe', 'nunggu', 'menunggu', 'tunggu', 'proses', 'diproses', 'packing',
                  'respon', 'balas', 'dibalas', 'datang', 'tiba', 'paket', 'kurir', 'ekspedisi', 'resi', 'antri', 'nungguin'}
INTENSIF = {'banget', 'sekali', 'sangat', 'super', 'parah', 'amat', 'bener', 'benar', 'bangeet', 'pol'}
NEGATIF_NETRAL = {'masalah', 'kendala', 'cacat', 'lecet', 'minus', 'kecewa', 'penyok', 'rusak', 'komplain'}  # "tidak ada X" => baik


class Hasil(dict):
    pass


class MesinAturan:
    """Memberi label Positif / Negatif / Netral dari teks. Mengembalikan juga skor dan penanda campuran."""

    def __init__(self, ambang=0.6):
        self.ambang = ambang
        self._emoji = self._muat_emoji()

    @staticmethod
    def _muat_emoji():
        return {'😍': 2.5, '🥰': 2.5, '❤': 2.0, '💖': 2.0, '😘': 2.0, '👍': 1.8, '👌': 1.5, '🙏': 1.0, '😊': 1.5, '😁': 1.5,
                '🔥': 1.2, '💯': 2.0, '⭐': 1.5, '🌟': 1.5, '✨': 1.0, '😎': 1.2, '🤩': 2.0, '😭': -1.5, '😡': -2.5, '😠': -2.5,
                '👎': -2.0, '😤': -1.8, '😢': -1.5, '😞': -1.5, '🤬': -2.8, '💔': -2.0, '🤮': -2.5, '😒': -1.5, '🙄': -1.0}

    # ---- skor satu klausa ----
    def skor_klausa(self, teks):
        toks = token(teks)
        s_pos = s_neg = 0.0
        terpakai = set()
        # frasa dulu (lebih spesifik)
        for kamus, tanda in ((FRASA_POS, 1), (FRASA_NEG, -1)):
            for f, w in kamus.items():
                if f in teks:
                    if tanda > 0: s_pos += w
                    else: s_neg += w
                    for t in f.split(): terpakai.add(t)
        # kata tunggal dengan negasi dan intensifier
        i = 0
        while i < len(toks):
            t = toks[i]
            if t in terpakai and t not in NEGASI:
                i += 1; continue
            if t == 'lama':  # 'lama' buruk hanya untuk pengiriman/menunggu; bukan 'tahan lama', 'sudah lama', 'berapa lama'
                sebelum = toks[i - 1] if i else ''
                if sebelum not in ('tahan', 'awet', 'sudah', 'udah', 'berapa', 'sejak', 'cukup') and 'berapa' not in toks and KONTEKS_TUNGGU & set(toks):
                    neg_lama = any(toks[j] in NEGASI for j in (i - 1, i - 2) if j >= 0)
                    if neg_lama: s_pos += 0.8
                    else: s_neg += 1.2 * (1.3 if (i + 1 < len(toks) and toks[i + 1] in INTENSIF) else 1)
                i += 1; continue
            dasar = t[:-3] if t.endswith('nya') and len(t) > 5 and t not in POSITIF and t not in NEGATIF else t
            if dasar not in POSITIF and dasar not in NEGATIF and len(dasar) > 3 and dasar[-1] == dasar[-2]:
                dasar = dasar[:-1]  # 'baguss' -> 'bagus', 'mantapp' -> 'mantap'
            nilai = POSITIF.get(dasar) or 0
            nilai_n = NEGATIF.get(dasar) or 0
            if nilai or nilai_n:
                bobot = nilai or nilai_n
                pos = bool(nilai)
                # intensifier setelah kata (bagus banget) atau sebelum (sangat bagus)
                if (i + 1 < len(toks) and toks[i + 1] in INTENSIF) or (i > 0 and toks[i - 1] in INTENSIF):
                    bobot *= 1.3
                # negasi dalam 2 token sebelumnya
                neg_sebelum = None
                for j in (i - 1, i - 2, i - 3):
                    if j < 0: break
                    if toks[j] in NEGASI:
                        neg_sebelum = toks[j]; break
                    if j < i - 1 and toks[j] not in ('di', 'ke', 'yang', 'terlalu', 'begitu', 'dengan', 'ter'):
                        break  # jarak 3 token hanya bila perantaranya kata sambung ('ga di packing rapi')
                if neg_sebelum:
                    # "tidak ada masalah/kendala" => baik; "kurang bagus" => buruk; "tidak buruk" => cukup baik
                    if not pos and t in NEGATIF_NETRAL and neg_sebelum in ('tidak', 'tanpa', 'belum'):
                        pos = True; bobot *= 0.9
                    else:
                        pos = not pos; bobot *= 0.8
                    if neg_sebelum == 'kurang' and pos is False and nilai == 0:
                        pass
                if t == 'kurang' and not neg_sebelum:
                    # 'kurang' sebagai kata negasi untuk kata berikutnya, bukan skor sendiri
                    if i + 1 < len(toks) and (toks[i + 1] in POSITIF):
                        i += 1; continue
                if i > 0 and toks[i - 1] in HEDGE: bobot *= 0.5  # 'agak sempit' lebih ringan dari 'sempit'
                if pos: s_pos += bobot
                else: s_neg += bobot
            i += 1
        # emoji
        for ch, w in self._emoji.items():
            n = teks.count(ch)
            if n:
                if w > 0: s_pos += w * min(n, 2) * 0.7
                else: s_neg += -w * min(n, 2) * 0.7
        return s_pos, s_neg

    def analisis(self, teks):
        norm = normalisasi(teks)
        ks = klausa(norm)
        pos = neg = 0.0
        detail = []
        for idx, k in enumerate(ks):
            p, n = self.skor_klausa(k)
            # klausa setelah kata kontras ("tapi", "cuma") lebih menentukan
            if re.match(r'^(tapi|cuma|namun|sayang|sayangnya|hanya saja|akan tetapi)\b', k) and (p or n):
                p *= 1.4; n *= 1.4
            pos += p; neg += n
            detail.append((k, round(p, 2), round(n, 2)))
        skor = pos - neg
        if skor >= self.ambang:
            label = 'Positif'
        elif skor <= -self.ambang:
            label = 'Negatif'
        else:
            label = 'Netral'
        campuran = pos >= 1.2 and neg >= 1.2
        return Hasil(label=label, skor=round(skor, 2), positif=round(pos, 2), negatif=round(neg, 2),
                     campuran=campuran, klausa=detail)

    def analisis_banyak(self, daftar):
        return [self.analisis(t) for t in daftar]

    def prediksi(self, teks):
        return self.analisis(teks)['label']
