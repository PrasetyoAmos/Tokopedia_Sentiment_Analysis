"""Sentimen murni dari teks ulasan (tanpa rating)."""
from .mesin_aturan import MesinAturan
from .aspek import analisis_aspek, ASPEK


def buat_mesin(nama='aturan', **kw):
    """nama: 'aturan' atau 'transformer'."""
    if nama == 'transformer':
        from .mesin_transformer import MesinTransformer
        return MesinTransformer(**kw)
    return MesinAturan()
