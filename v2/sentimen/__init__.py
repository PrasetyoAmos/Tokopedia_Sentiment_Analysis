"""Sentimen murni dari teks ulasan (tanpa rating)."""
from .mesin_aturan import MesinAturan
from .aspek import analisis_aspek, ASPEK


def buat_mesin(nama='aturan', **kw):
    """nama: 'aturan', 'transformer', atau 'gabungan' (IndoBERT + aturan)."""
    if nama == 'gabungan':
        from .mesin_gabungan import MesinGabungan
        return MesinGabungan(**kw)
    if nama == 'transformer':
        from .mesin_transformer import MesinTransformer
        return MesinTransformer(**kw)
    return MesinAturan()
