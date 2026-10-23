"""Mesin sentimen berbasis model terlatih (IndoBERT / IndoRoBERTa) dari Hugging Face.
Antarmukanya sama dengan MesinAturan: analisis(teks) dan analisis_banyak(daftar_teks).
Model diunduh otomatis saat pertama kali dipakai (lalu tersimpan di cache komputer Anda)."""
import re

MODEL_BAWAAN = 'w11wo/indonesian-roberta-base-sentiment-classifier'
# Cara membaca label tiap model. Nama label dibuat huruf kecil sebelum dicocokkan.
PETA_UMUM = {'positive': 'Positif', 'negative': 'Negatif', 'neutral': 'Netral',
             'positif': 'Positif', 'negatif': 'Negatif', 'netral': 'Netral', 'pos': 'Positif', 'neg': 'Negatif', 'neu': 'Netral'}
PETA_PER_MODEL = {
    # model ini mengeluarkan LABEL_0/1/2
    'mdhugol/indonesia-bert-sentiment-classification': {'label_0': 'Positif', 'label_1': 'Netral', 'label_2': 'Negatif'},
}


class MesinTransformer:
    def __init__(self, model=MODEL_BAWAAN, peta=None, batas_token=256, ukuran_batch=32, perangkat=None):
        try:
            from transformers import pipeline
        except ImportError as e:
            raise ImportError('Pasang dulu: pip install transformers torch') from e
        self.model = model
        self.peta = {**PETA_UMUM, **PETA_PER_MODEL.get(model, {}), **(peta or {})}
        self.batas = batas_token
        self.batch = ukuran_batch
        kw = {'device': perangkat} if perangkat is not None else {}
        self._nlp = pipeline('text-classification', model=model, top_k=None, truncation=True, max_length=batas_token, **kw)

    def _ke_label(self, nama):
        k = str(nama).strip().lower()
        if k not in self.peta:
            raise ValueError(f"Label model '{nama}' belum dikenal. Berikan peta label, mis. peta={{'{k}': 'Positif'}}.")
        return self.peta[k]

    @staticmethod
    def _bersih(t):
        t = re.sub(r'\s+', ' ', str(t)).strip()
        return t if t else '-'

    def analisis_banyak(self, daftar):
        teks = [self._bersih(t) for t in daftar]
        keluar = self._nlp(teks, batch_size=self.batch)
        hasil = []
        for baris in keluar:
            p = {'Positif': 0.0, 'Negatif': 0.0, 'Netral': 0.0}
            for item in baris:
                p[self._ke_label(item['label'])] += float(item['score'])
            label = max(p, key=p.get)
            hasil.append(dict(label=label, skor=round(p['Positif'] - p['Negatif'], 3), positif=round(p['Positif'], 3),
                              negatif=round(p['Negatif'], 3), campuran=bool(p['Positif'] > 0.3 and p['Negatif'] > 0.3), klausa=[]))
        return hasil

    def analisis(self, teks):
        return self.analisis_banyak([teks])[0]

    def prediksi(self, teks):
        return self.analisis(teks)['label']
