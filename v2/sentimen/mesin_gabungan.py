"""Mesin gabungan: IndoBERT + aturan bahasa.

Alasannya, kedua mesin salah di tempat berbeda (hasil uji di laptop):
- IndoBERT peka terhadap keluhan (recall Negatif 1,00) tetapi lemah di Netral dan jarang menandai ulasan campuran.
- Aturan bahasa teliti (presisi Negatif 0,96), bisa menjelaskan alasannya per kalimat, dan menangkap campuran,
  tetapi hanya mengenal kata yang ada di kamus.

Cara kerja per ulasan:
1. Teks dinormalkan (slang, singkatan, salah ketik) lalu diberikan ke IndoBERT, sehingga 'mntappppp' dibaca 'mantap'.
2. Aturan memberi skor kata (sr, -1..+1 lewat tanh), IndoBERT memberi sb = P(positif) - P(negatif).
3. Skor gabungan s = w*sr + (1-w)*sb. Bila aturan tidak menemukan kata sentimen sama sekali, IndoBERT yang menentukan.
4. s >= ambang -> Positif, s <= -ambang -> Negatif, selain itu Netral. IndoBERT yakin 'netral' dan aturan tidak
   menemukan bukti -> Netral.
5. Ditandai campuran bila aturan menemukan pujian dan keluhan sekaligus, atau kedua mesin berlawanan arah dengan yakin."""
import math
from .normalisasi import normalisasi
from .mesin_aturan import MesinAturan


class MesinGabungan:
    def __init__(self, transformer=None, aturan=None, bobot_aturan=0.45, ambang=0.3, **kw_transformer):
        if transformer is None:
            from .mesin_transformer import MesinTransformer
            transformer = MesinTransformer(**kw_transformer)
        self.transformer = transformer
        self.aturan = aturan or MesinAturan()
        self.w = bobot_aturan
        self.ambang = ambang

    def _gabung(self, r, b):
        sr = math.tanh(r['skor'] / 2)
        p = b['prob']; sb = p['Positif'] - p['Negatif']
        ada_bukti = (r['positif'] + r['negatif']) >= 0.3
        s = (self.w * sr + (1 - self.w) * sb) if ada_bukti else sb
        if not ada_bukti and p['Netral'] >= 0.55:
            label = 'Netral'
        elif s >= self.ambang: label = 'Positif'
        elif s <= -self.ambang: label = 'Negatif'
        else: label = 'Netral'
        berlawanan = abs(sr) > 0.5 and abs(sb) > 0.5 and (sr > 0) != (sb > 0)
        campuran = bool(r['campuran'] or (p['Positif'] > 0.3 and p['Negatif'] > 0.3) or berlawanan)
        return dict(label=label, skor=round(s * 3, 2), positif=r['positif'], negatif=r['negatif'], campuran=campuran,
                    klausa=r['klausa'], bert=p, skor_aturan=r['skor'])

    def analisis_banyak(self, daftar):
        daftar = [str(t) for t in daftar]
        hr = [self.aturan.analisis(t) for t in daftar]
        hb = self.transformer.analisis_banyak([normalisasi(t) or '-' for t in daftar])
        return [self._gabung(r, b) for r, b in zip(hr, hb)]

    def analisis(self, teks):
        return self.analisis_banyak([teks])[0]

    def prediksi(self, teks):
        return self.analisis(teks)['label']
