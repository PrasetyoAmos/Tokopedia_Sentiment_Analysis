"""Ambil ulasan dari halaman ulasan produk Tokopedia (Selenium).

Perbaikan dibanding v1 (lihat v1/docs/SCRAPER_AUDIT.md):
- teks asli disimpan (hanya spasi dirapikan), ulasan pendek tidak dibuang
- rating yang tidak terbaca dibiarkan kosong, bukan diisi 5
- setelah klik "Laman berikutnya", scraper memastikan isi halaman benar-benar berubah
- berhenti saat tombol berikutnya nonaktif / tidak ada lagi
- ulasan kembar (produk + rating + teks + tanggal sama) dibuang
- halaman di-scroll agar konten lazy-load ikut terbaca
Tidak perlu chromedriver.exe: Selenium 4.6+ mengunduh driver sendiri (butuh internet saat pertama kali)."""
import re, time
from bs4 import BeautifulSoup

TGL = re.compile(r'\b(hari ini|kemarin|\d+\s*(?:hari|minggu|bulan|tahun)\s*lalu)\b', re.I)


def _rapikan(t):
    return re.sub(r'\s+', ' ', t or '').strip()


def parse_halaman(html):
    """Kembalikan daftar dict ulasan dari HTML satu halaman."""
    soup = BeautifulSoup(html, 'html.parser')
    out = []
    for art in soup.find_all('article'):
        el = art.find('span', attrs={'data-testid': 'lblItemUlasan'})
        if not el:
            continue
        teks = _rapikan(el.get_text(' '))
        if not teks:
            continue
        a = art.find('a', class_='styProduct') or art.find('a', href=re.compile(r'/'))
        produk = _rapikan(a.get_text(' ')) if a else ''
        rating = None
        r = art.find(attrs={'data-testid': 'icnStarRating'}) or art.find(attrs={'aria-label': re.compile(r'Rating\s*\d')})
        if r:
            m = re.search(r'\d+', r.get('aria-label', ''))
            rating = int(m.group()) if m else None
        m = TGL.search(art.get_text(' '))
        out.append(dict(Ulasan=teks, Nama_Produk=produk, Rating=rating, Tanggal=m.group(1).lower() if m else ''))
    return out


def _tanda(daftar):
    return hash(tuple((d['Nama_Produk'], d['Ulasan']) for d in daftar[:6]))


def ambil(url, halaman=5, tampil_browser=True, cb=None, jeda=1.5):
    """Scrape `halaman` halaman ulasan. cb(persen, pesan). Mengembalikan list dict tanpa duplikat."""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    cb = cb or (lambda p, m: None)
    if 'tokopedia.com' not in url:
        raise ValueError('Link harus dari tokopedia.com (halaman ulasan produk).')
    opt = Options()
    for a in ('--no-sandbox', '--disable-dev-shm-usage', '--window-size=1366,900'):
        opt.add_argument(a)
    if not tampil_browser:
        opt.add_argument('--headless=new')
    cb(2, 'Membuka Chrome')
    try:
        drv = webdriver.Chrome(options=opt)
    except Exception as e:
        raise RuntimeError('Chrome tidak bisa dibuka. Pastikan Google Chrome terpasang dan komputer online '
                           '(Selenium mengunduh chromedriver sendiri). Detail: ' + str(e).splitlines()[0])
    data, lihat = [], set()
    try:
        drv.get(url); time.sleep(5)
        for i in range(halaman):
            cb(5 + int(33 * i / halaman), f'Membaca halaman {i + 1} dari {halaman} · {len(data)} ulasan')
            for y in (0.3, 0.6, 1.0):  # scroll agar lazy-load muncul
                drv.execute_script(f'window.scrollTo(0, document.body.scrollHeight*{y});'); time.sleep(.4)
            hal = parse_halaman(drv.page_source)
            if not hal and i == 0:
                raise RuntimeError('Tidak ada ulasan terbaca. Pastikan link adalah halaman ulasan produk dan tidak sedang tertahan captcha/login.')
            for d in hal:
                k = (d['Nama_Produk'], d['Rating'], d['Ulasan'], d['Tanggal'])
                if k not in lihat:
                    lihat.add(k); data.append(d)
            if i == halaman - 1:
                break
            try:
                tombol = WebDriverWait(drv, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label^='Laman berikutnya']")))
            except Exception:
                break  # tidak ada tombol berikutnya
            if tombol.get_attribute('disabled') or tombol.get_attribute('aria-disabled') == 'true':
                break
            sebelum = _tanda(hal)
            drv.execute_script('arguments[0].scrollIntoView({block:"center"});', tombol); time.sleep(.5)
            try: tombol.click()
            except Exception: drv.execute_script('arguments[0].click();', tombol)
            for _ in range(20):  # tunggu isi benar-benar berganti (maks ±10 dtk)
                time.sleep(.5)
                if _tanda(parse_halaman(drv.page_source)) != sebelum:
                    break
            else:
                break  # isi tidak berubah: sudah halaman terakhir
            time.sleep(jeda)
        return data
    finally:
        drv.quit()
