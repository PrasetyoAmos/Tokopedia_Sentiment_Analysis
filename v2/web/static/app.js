'use strict';
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const id = n => Number(n).toLocaleString('id-ID');
const pct = n => (Number(n).toFixed(1)).replace('.', ',') + '%';
const tunggu = ms => new Promise(r => setTimeout(r, ms));
const hemat = matchMedia('(prefers-reduced-motion: reduce)').matches;

const S = { jid: null, r: null, tab: 'ringkasan', filter: {}, hal: 1, berkas: null, contoh: '' };

/* ---------- layar ---------- */
function layar(nama) {
  $('#awal').hidden = nama !== 'awal';
  $('#proses').hidden = nama !== 'proses';
  $('#app').hidden = nama !== 'app';
  $('#tab').hidden = $('#aksi').hidden = nama !== 'app';
  window.scrollTo(0, 0);
}

/* ---------- unggah ---------- */
const form = $('#form'), file = $('#file'), drop = $('#drop');
function pilihBerkas(f) {
  S.berkas = f; S.contoh = '';
  $$('#contoh .chip').forEach(c => c.setAttribute('aria-pressed', 'false'));
  tandai();
}
function tandai() {
  const nama = S.berkas ? S.berkas.name : S.contoh;
  drop.classList.toggle('terisi', !!nama);
  $('#drop-judul').textContent = nama || 'Tarik file CSV ke sini, atau klik untuk memilih';
  $('#drop-info').textContent = S.berkas ? (S.berkas.size / 1024 / 1024 > 1 ? (S.berkas.size / 1048576).toFixed(1) + ' MB' : Math.round(S.berkas.size / 1024) + ' KB') : (nama ? 'Dari folder data' : 'Kolom yang dibaca: Ulasan (wajib), Nama_Produk, Rating');
  segarkanTombol();
  $('#galat').hidden = true;
}
file.addEventListener('change', () => file.files[0] && pilihBerkas(file.files[0]));
drop.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); file.click(); } });
['dragenter', 'dragover'].forEach(t => drop.addEventListener(t, e => { e.preventDefault(); drop.classList.add('tarik'); }));
['dragleave', 'drop'].forEach(t => drop.addEventListener(t, e => { e.preventDefault(); drop.classList.remove('tarik'); }));
drop.addEventListener('drop', e => { const f = e.dataTransfer.files[0]; if (f) pilihBerkas(f); });

fetch('/api/contoh').then(r => r.json()).then(l => {
  if (!l.length) return;
  $('#contoh-wrap').hidden = false;
  $('#contoh').innerHTML = l.map(c => `<button type="button" class="chip" aria-pressed="false" data-j="${esc(c.jalur)}">${esc(c.nama.replace(/_\d{8}_\d{6}/, '').replace('.csv', ''))}</button>`).join('');
  $$('#contoh .chip').forEach(b => b.addEventListener('click', () => {
    S.berkas = null; file.value = ''; S.contoh = b.dataset.j;
    $$('#contoh .chip').forEach(c => c.setAttribute('aria-pressed', String(c === b)));
    tandai(); $('#drop-judul').textContent = b.textContent;
  }));
});

const mode = () => new FormData(form).get('mode');
$$('[name=mode]').forEach(r => r.addEventListener('change', () => {
  $('#mode-csv').hidden = mode() !== 'csv'; $('#mode-web').hidden = mode() !== 'web'; segarkanTombol();
}));
function segarkanTombol() {
  $('#btn-mulai').disabled = mode() === 'web' ? !/tokopedia\.com/i.test($('#url').value) : !(S.berkas || S.contoh);
  $('#btn-mulai').textContent = mode() === 'web' ? 'Ambil dan analisis' : 'Analisis ulasan';
}
$('#url').addEventListener('input', segarkanTombol);

form.addEventListener('submit', async e => {
  e.preventDefault();
  const web = mode() === 'web';
  const fd = new FormData();
  if (web) { fd.append('url', $('#url').value.trim()); fd.append('halaman', $('#halaman').value); fd.append('tampil', $('#tampil').checked ? '1' : '0'); }
  else if (S.berkas) fd.append('file', S.berkas); else fd.append('contoh', S.contoh);
  fd.append('mesin', (new FormData(form).get('mesin')) || 'aturan');
  fd.append('duplikat', $('#dup').checked ? '1' : '0');
  layar('proses'); setProses(2, web ? 'Menyiapkan Chrome' : 'Mengunggah');
  try {
    const r = await fetch(web ? '/api/scrape' : '/api/mulai', { method: 'POST', body: fd });
    const j = await r.json(); if (!r.ok) throw new Error(j.error || 'Gagal memulai.');
    S.jid = j.id;
    for (;;) {
      await tunggu(450);
      const s = await (await fetch('/api/status/' + S.jid)).json();
      if (s.status === 'gagal') throw new Error(s.pesan);
      setProses(s.persen, s.pesan);
      if (s.status === 'selesai') break;
    }
    S.r = await (await fetch('/api/hasil/' + S.jid)).json();
    await tunggu(250);
    tampilkan();
  } catch (err) {
    layar('awal'); const g = $('#galat'); g.textContent = err.message; g.hidden = false;
  }
});
function setProses(p, m) {
  $('#proses-garis').style.width = p + '%'; $('#proses-persen').textContent = Math.round(p); $('#proses-pesan').textContent = m;
}

/* ---------- komponen ---------- */
function batang(pos, net, neg, kecil) {
  return `<div class="batang ${kecil ? 'kecil-b' : ''}" role="img" aria-label="Positif ${pct(pos)}, netral ${pct(net)}, negatif ${pct(neg)}">
    <div class="p" data-w="${pos}"></div><div class="n" data-w="${net}"></div><div class="g" data-w="${neg}"></div></div>`;
}
function isiBatang(root) {
  const set = () => $$('[data-w]', root).forEach(e => e.style.width = e.dataset.w + '%');
  if (hemat) set(); else requestAnimationFrame(() => requestAnimationFrame(set));
}
function hitung(el, target, desimal) {
  if (hemat) { el.textContent = desimal ? pct(target) : id(target); return; }
  const t0 = performance.now(), d = 1100;
  (function f(t) {
    const k = Math.min(1, (t - t0) / d), e = 1 - Math.pow(1 - k, 3), v = target * e;
    el.textContent = desimal ? pct(v) : id(Math.round(v));
    if (k < 1) requestAnimationFrame(f);
  })(t0);
}
function diverging(aspek, tindak) {
  const maks = Math.max(1, ...aspek.map(a => Math.max(a.puji, a.keluh)));
  return `<div class="diver"><div class="dv-judul"><span></span><span>Dipuji</span><span>Dikeluhkan</span></div>` +
    aspek.map(a => `<button class="dv ${a.total ? '' : 'kosong'}" data-aspek="${esc(a.nama)}" ${tindak ? '' : 'disabled'}>
      <span class="dv-nama">${esc(a.nama)}</span>
      <span class="dv-sisi kiri"><span class="dv-n">${a.puji ? id(a.puji) : ''}</span><i class="dv-bar" data-dw="${(a.puji / maks) * 100}"></i></span>
      <span class="dv-sisi kanan"><i class="dv-bar" data-dw="${(a.keluh / maks) * 100}"></i><span class="dv-n">${a.keluh ? id(a.keluh) : ''}</span></span>
    </button>`).join('') + '</div>';
}
function isiDiver(root) {
  const set = () => $$('[data-dw]', root).forEach(e => e.style.width = (e.dataset.dw * 0.62) + '%');
  if (hemat) set(); else requestAnimationFrame(() => requestAnimationFrame(set));
}
function daftarKata(judul, warna, arr, filterLabel) {
  const m = Math.max(1, ...arr.map(k => k.jumlah));
  return `<div class="kata" style="--c:${warna}"><h3>${judul}</h3>` + arr.map(k =>
    `<div class="baris"><a data-cari="${esc(k.kata)}" data-label="${filterLabel}">${esc(k.kata)}</a><div class="rel"><i data-w="${(k.jumlah / m) * 100}"></i></div><b>${id(k.jumlah)}</b></div>`).join('') + '</div>';
}
function matriks(m) {
  return `<div class="mtx">` + m.filter(x => x.n).map(x => {
    const p = x.Positif / x.n * 100, n = x.Netral / x.n * 100, g = x.Negatif / x.n * 100;
    return `<div class="mtx-baris"><span>Bintang ${x.rating}</span>${batang(p, n, g)}<span>${id(x.n)}</span></div>`;
  }).join('') + `</div>`;
}

/* awan kata: tata letak spiral, tanpa pustaka */
function awan(arr, warna, filterLabel) {
  const W = 560, H = 300, kotak = [];
  const m = Math.max(1, ...arr.map(k => k.jumlah)), n0 = Math.min(...arr.map(k => k.jumlah));
  const tabrak = b => kotak.some(o => b.x < o.x + o.w && b.x + b.w > o.x && b.y < o.y + o.h && b.y + b.h > o.y);
  let out = '';
  arr.slice(0, 38).forEach((k, i) => {
    const t = m === n0 ? .5 : Math.log(k.jumlah / n0 + 1) / Math.log(m / n0 + 1);
    const fs = Math.round(15 + 31 * Math.pow(t, .9)), w = k.kata.length * fs * .6 + 6, h = fs * 1.05;
    for (let a = 0, r = 0; r < 320; a += .45, r += .9) {
      const x = W / 2 + r * 1.9 * Math.cos(a) - w / 2, y = H / 2 + r * Math.sin(a) - h / 2, b = { x, y, w, h };
      if (x < 2 || y < 2 || x + w > W - 2 || y + h > H - 2 || tabrak(b)) continue;
      kotak.push(b);
      out += `<text x="${(x + w / 2).toFixed(1)}" y="${(y + h * .8).toFixed(1)}" font-size="${fs}" fill="${warna}" text-anchor="middle" data-cari="${esc(k.kata)}" data-label="${filterLabel}" style="--d:${i * 45}ms;--t:${(3.2 + (i * 37 % 20) / 10).toFixed(1)}s;--dx:${((i * 53 % 80) - 40)}px;--dy:${((i * 31 % 80) - 40)}px;--rot:${((i * 17 % 40) - 20)}deg;--bx:${((i * 7 % 7) - 3)}px;--by:${((i * 11 % 7) - 3)}px"><title>${esc(k.kata)}: ${id(k.jumlah)} ulasan</title>${esc(k.kata)}</text>`;
      break;
    }
  });
  return `<svg class="awan" viewBox="0 0 ${W} ${H}" role="img" aria-label="Awan kata ${filterLabel}">${out}</svg>`;
}
function donut(aspek) {
  const tot = aspek.reduce((a, x) => a + x.total, 0) || 1;
  const wr = ['#3f50d4', '#168a6a', '#e0a526', '#d6453d', '#7b61c9', '#2b9bb8', '#8d96a8'];
  const R = 62, C = 2 * Math.PI * R; let off = 0;
  const arcs = aspek.filter(a => a.total).map((a, i) => {
    const len = a.total / tot * C, el = `<circle cx="85" cy="85" r="${R}" stroke="${wr[i % 7]}" stroke-dasharray="0 ${C}" data-dash="${Math.max(0, len - 2)} ${C}" stroke-dashoffset="${-off}" transform="rotate(-90 85 85)"/>`;
    off += len; return el;
  }).join('');
  const leg = aspek.filter(a => a.total).map((a, i) => `<div><i style="background:${wr[i % 7]}"></i>${esc(a.nama)}<b>${Math.round(a.total / tot * 100)}%</b></div>`).join('');
  return `<div class="donut-wrap"><svg class="donut" viewBox="0 0 170 170" role="img" aria-label="Porsi topik"><circle cx="85" cy="85" r="${R}" stroke="var(--net-l)"/>${arcs}
    <text x="85" y="86" text-anchor="middle" font-size="26">${id(tot)}</text><text x="85" y="106" text-anchor="middle" font-size="11" style="font-weight:500;fill:var(--ink3)">sebutan topik</text></svg><div class="donut-leg">${leg}</div></div>`;
}
function histogram(h) {
  const m = Math.max(1, ...h.map(b => b.n));
  const lab = x => x <= -4 ? '≤−4' : x >= 4 ? '≥4' : (x > 0 ? '+' : x < 0 ? '−' : '') + Math.abs(x);
  return `<div class="hist">${h.map(b => `<div>${b.n ? id(b.n) : ''}<i data-h="${b.n / m * 100}" style="background:${b.x < 0 ? 'var(--neg)' : b.x > 0 ? 'var(--pos)' : 'var(--net)'}"></i></div>`).join('')}</div>
    <div class="hist-x">${h.map(b => `<span>${lab(b.x)}</span>`).join('')}</div><div class="hist-sumbu"><span>← keluhan kuat</span><span>pujian kuat →</span></div>`;
}
function peta(prod) {
  const W = 1100, H = 340, L = 50, B = 46, mx = Math.max(10, ...prod.map(p => p.neg)) * 1.1, my = Math.max(...prod.map(p => p.n));
  const X = v => L + v / mx * (W - L - 12), Y = v => H - B - Math.sqrt(v / my) * (H - B - 14);
  const grid = [0, .25, .5, 1].map(f => { const v = my * f * f; return `<line x1="${L}" x2="${W}" y1="${Y(v)}" y2="${Y(v)}"/><text x="${L - 6}" y="${Y(v) + 4}" text-anchor="end">${Math.round(v)}</text>`; }).join('');
  const xs = [0, .25, .5, .75, 1].map(f => `<text x="${X(mx * f / 1.1 * 1.1)}" y="${H - 26}" text-anchor="middle">${Math.round(mx * f)}%</text>`).join('');
  const dots = prod.map(p => `<circle cx="${X(p.neg)}" cy="${Y(p.n)}" r="0" data-r="${6 + Math.sqrt(p.n / my) * 8}" fill="${p.neg >= 20 ? 'var(--neg)' : p.pos >= 70 ? 'var(--pos)' : 'var(--net)'}" data-nama="${esc(p.nama)}"><title>${esc(p.nama)}&#10;${id(p.n)} ulasan · ${pct(p.pos)} positif · ${pct(p.neg)} negatif</title></circle>`).join('');
  return `<svg class="peta" viewBox="0 0 ${W} ${H}" role="img" aria-label="Peta produk">${grid}${xs}${dots}<text x="${L}" y="8">ulasan ↑</text><text x="${W}" y="${H - 2}" text-anchor="end">% ulasan negatif →</text></svg>`;
}
function heatmap(aspek, baris, klik) {
  if (!baris.length) return '';
  const warna = (p, k) => {
    const t = p + k; if (!t) return null; const v = (p - k) / t, a = Math.min(1, .25 + Math.sqrt(t) / 9);
    return v >= 0 ? `color-mix(in srgb, var(--pos) ${Math.round((.2 + .8 * v) * a * 100)}%, var(--net-l))` : `color-mix(in srgb, var(--neg) ${Math.round((.2 + .8 * -v) * a * 100)}%, var(--net-l))`;
  };
  let h = `<div class="heat" style="grid-template-columns:minmax(120px,210px) repeat(${aspek.length},minmax(64px,1fr))"><span></span>${aspek.map(a => `<span class="kh">${esc(a)}</span>`).join('')}`;
  baris.forEach((b, i) => {
    h += `<span class="bh" title="${esc(b.nama)}"><span>${esc(b.nama)}</span></span>`;
    b.sel.forEach((c, j) => {
      const w = warna(c.puji, c.keluh), d = (i + j) * 55;
      h += w ? `<button class="sel" style="background:${w};--d:${d}ms" data-b="${esc(b.nama)}" data-a="${esc(aspek[j])}" title="${esc(b.nama)} · ${esc(aspek[j])}: ${c.puji} pujian, ${c.keluh} keluhan">${c.puji + c.keluh}</button>`
               : `<span class="sel kosong" style="--d:${d}ms">–</span>`;
    });
  });
  return h + `</div><div class="skala"><span>lebih banyak keluhan</span><i></i><span>lebih banyak pujian</span><span style="margin-left:auto">angka = jumlah sebutan</span></div>`;
}
function animasiGrafik(root) {
  const go = () => {
    $$('[data-dash]', root).forEach(c => c.setAttribute('stroke-dasharray', c.dataset.dash));
    $$('[data-h]', root).forEach(e => e.style.height = e.dataset.h + '%');
    $$('[data-r]', root).forEach(c => c.setAttribute('r', c.dataset.r));
  };
  if (hemat) go(); else requestAnimationFrame(() => requestAnimationFrame(go));
}

/* ---------- panel ---------- */
function tampilkan() {
  const r = S.r;
  $('#btn-ekspor').href = '/api/ekspor/' + S.jid;
  layar('app');
  panelRingkasan(); panelTopik(); panelProduk(); panelUlasan(); panelValidasi();
  pindah('ringkasan');
}
function panelRingkasan() {
  const r = S.r, p = $('#p-ringkasan');
  p.innerHTML = `
  <div class="vonis"><h1>${esc(r.judul)}</h1><p class="sub">${esc(r.subjudul)}</p>
    <p class="meta">${id(r.n)} ulasan dari ${id(r.n_produk)} produk &middot; dinilai dari kalimatnya, bukan bintang${r.duplikat ? ' &middot; ' + id(r.duplikat) + ' ulasan kembar dibuang' : ''} &middot; ${r.detik} detik &middot; ${esc(r.berkas)}</p></div>
  <div>${batang(r.pos_pct, r.net_pct, r.neg_pct)}
    <div class="legenda">
      <div class="p"><b data-hitung="${r.pos_pct}">0</b><span>positif &middot; ${id(r.pos)} ulasan</span></div>
      <div class="n"><b data-hitung="${r.net_pct}">0</b><span>netral &middot; ${id(r.net)} ulasan</span></div>
      <div class="g"><b data-hitung="${r.neg_pct}">0</b><span>negatif &middot; ${id(r.neg)} ulasan</span></div>
    </div></div>
  <div><div class="kepala-bagian"><h2 class="judul">Yang paling sering dibicarakan</h2><p class="sub">Kata yang paling membedakan ulasan positif dari negatif; makin besar makin khas. Klik kata untuk membaca ulasannya.</p></div>
    <div class="dua"><div class="awan-kotak" style="--c:var(--pos)"><div class="awan-kepala"><h3>Dalam ulasan positif</h3><button class="mini" data-ulang>Putar ulang</button></div>${awan(r.kata.Positif, 'var(--pos)', 'Positif')}</div>
      <div class="awan-kotak" style="--c:var(--neg)"><div class="awan-kepala"><h3>Dalam ulasan negatif</h3><button class="mini" data-ulang>Putar ulang</button></div>${r.kata.Negatif.length ? awan(r.kata.Negatif, 'var(--neg)', 'Negatif') : '<p class="kecil" style="padding:20px">Belum ada kata keluhan yang cukup sering muncul.</p>'}</div></div>
    <details class="daftar-kata" style="margin-top:18px"><summary>Lihat daftar dengan jumlahnya</summary><div class="dua">${daftarKata('Dalam ulasan positif', 'var(--pos)', r.kata.Positif.slice(0, 14), 'Positif')}${daftarKata('Dalam ulasan negatif', 'var(--neg)', r.kata.Negatif.slice(0, 14), 'Negatif')}</div></details></div>
  <div class="grafik-dua">
    <div class="kotak"><h3>Porsi topik</h3><p class="kecil">Seberapa sering tiap topik disebut</p>${donut(r.aspek)}</div>
    <div class="kotak"><h3>Seberapa kuat nada ulasannya</h3><p class="kecil">Jumlah ulasan menurut skor sentimen; 0 berarti netral</p>${histogram(r.hist)}</div></div>
  ${r.ada_rating ? `<div><div class="kepala-bagian"><h2 class="judul">Bintang vs isi kalimat</h2><p class="sub">Tiap baris: ulasan dengan bintang tersebut, dibagi menurut sentimen kalimatnya.</p></div>
    ${matriks(r.matriks)}
    <p class="catatan"><b>${id(r.konflik)} ulasan (${pct(r.konflik_pct)})</b> bintangnya bertentangan dengan isinya &mdash; misalnya bintang 5 tapi mengeluh, atau bintang 1&ndash;2 tapi memuji. Inilah yang tidak terlihat jika hanya memakai rating. <button data-konflik>Baca ulasannya</button></p></div>` : ''}`;
  $$('[data-hitung]', p).forEach(e => hitung(e, +e.dataset.hitung, true));
  isiBatang(p); animasiGrafik(p);
  $$('.kata .rel i', p).forEach(e => e.style.width = e.dataset.w + '%');
  $$('[data-cari]', p).forEach(a => a.onclick = () => bacaUlasan({ q: a.dataset.cari, label: a.dataset.label }));
  $$('[data-ulang]', p).forEach(b => b.onclick = () => { const sv = $('.awan', b.closest('.awan-kotak')); const c = sv.cloneNode(true); sv.replaceWith(c); $$('[data-cari]', c).forEach(a => a.onclick = () => bacaUlasan({ q: a.dataset.cari, label: a.dataset.label })); });
  const k = $('[data-konflik]', p); if (k) k.onclick = () => bacaUlasan({ konflik: '1' });
}
function panelTopik() {
  const r = S.r;
  $('#p-topik').innerHTML = `<div class="kepala-bagian"><h2 class="judul">Topik yang dibicarakan</h2>
    <p class="sub">Setiap kalimat dicocokkan ke topik, lalu dinilai sendiri-sendiri. Satu ulasan bisa memuji kemasan sekaligus mengeluhkan pengiriman. Klik topik untuk membaca ulasannya.</p></div>${diverging(r.aspek, true)}
    <p class="meta">Hanya kalimat yang jelas menyebut topik dan memuat nada positif atau negatif yang dihitung.</p>
    ${r.heat_produk.length ? `<div class="kotak"><h3>Topik di tiap produk</h3><p class="kecil">Warna hijau berarti topik itu lebih sering dipuji untuk produk tersebut, merah lebih sering dikeluhkan. Klik kotak untuk membaca ulasannya.</p><div style="margin-top:14px">${heatmap(r.heat_aspek, r.heat_produk)}</div></div>` : ''}
    ${r.heat_rating.length ? `<div class="kotak"><h3>Topik menurut bintang</h3><p class="kecil">Apa yang dibicarakan pembeli di tiap tingkat bintang.</p><div style="margin-top:14px">${heatmap(r.heat_aspek, r.heat_rating)}</div></div>` : ''}`;
  isiDiver($('#p-topik'));
  $$('#p-topik .dv').forEach(b => b.onclick = () => bacaUlasan({ aspek: b.dataset.aspek }));
  $$('#p-topik .sel[data-b]').forEach(b => b.onclick = () => {
    const rt = /^Bintang (\d)$/.exec(b.dataset.b);
    bacaUlasan(rt ? { rating: rt[1], aspek: b.dataset.a } : { produk: b.dataset.b, aspek: b.dataset.a });
  });
}
function panelProduk() {
  const r = S.r, p = $('#p-produk');
  if (r.produk.length < 1) { p.innerHTML = `<div class="kosongan">Tidak ada produk dengan cukup ulasan. File perlu kolom <code>Nama_Produk</code>.</div>`; return; }
  p.innerHTML = `<div class="kepala-bagian"><h2 class="judul">Per produk</h2><p class="sub">Produk dengan sedikitnya 8 ulasan, diurutkan dari yang paling banyak diulas. Klik judul kolom untuk mengurutkan, klik baris untuk melihat detail.</p></div>
  <div class="kotak"><h3>Peta produk</h3><p class="kecil">Tiap lingkaran satu produk: makin ke kanan makin banyak keluhan, makin ke atas makin banyak diulas. Hijau umumnya puas, merah ≥20% negatif. Klik untuk detail.</p>${peta(r.produk)}</div>
  <div class="tabel-wrap"><table><thead><tr><th data-k="nama">Produk</th><th data-k="n" aria-sort="descending">Ulasan</th><th data-k="pos">Sentimen</th><th data-k="pos">Positif</th><th data-k="neg">Negatif</th>${r.ada_rating ? '<th data-k="rating">Bintang</th>' : ''}<th>Topik utama</th></tr></thead><tbody></tbody></table></div>`;
  animasiGrafik(p); $$('.peta circle', p).forEach(c => c.onclick = () => laci(c.dataset.nama));
  let kunci = 'n', arah = -1;
  const gambar = () => {
    const d = [...r.produk].sort((a, b) => (typeof a[kunci] === 'string' ? a[kunci].localeCompare(b[kunci]) : (a[kunci] ?? 0) - (b[kunci] ?? 0)) * arah);
    $('tbody', p).innerHTML = d.map(x => `<tr data-nama="${esc(x.nama)}"><td class="nama">${esc(x.nama)}</td><td>${id(x.n)}</td><td>${batang(x.pos, x.net, x.neg, true)}</td><td>${pct(x.pos)}</td><td>${pct(x.neg)}</td>${r.ada_rating ? `<td>${x.rating ?? '–'}</td>` : ''}
      <td>${x.puji.map(a => `<span class="tag p">${esc(a)}</span>`).join('')}${x.keluh.map(a => `<span class="tag g">${esc(a)}</span>`).join('')}</td></tr>`).join('');
    isiBatang(p);
    $$('tbody tr', p).forEach(tr => tr.onclick = () => laci(tr.dataset.nama));
  };
  $$('th[data-k]', p).forEach(th => th.onclick = () => {
    const k = th.dataset.k; arah = (kunci === k) ? -arah : (k === 'nama' ? 1 : -1); kunci = k;
    $$('th', p).forEach(t => t.removeAttribute('aria-sort')); th.setAttribute('aria-sort', arah < 0 ? 'descending' : 'ascending'); gambar();
  });
  gambar();
}
async function laci(nama) {
  const L = $('#laci'); L.hidden = false; $('#laci-konten').innerHTML = '<p class="kecil">Memuat…</p>';
  const d = await (await fetch('/api/produk/' + S.jid + '?nama=' + encodeURIComponent(nama))).json();
  const c = $('#laci-konten');
  c.innerHTML = `<div><h2>${esc(nama)}</h2><p class="meta">${id(d.n)} ulasan${d.rating ? ' · rata-rata bintang ' + d.rating : ''}</p></div>
    <div><p class="sub" style="font-size:16px;color:var(--ink);font-weight:600">${esc(d.judul)}</p><p class="sub">${esc(d.subjudul)}</p></div>
    <div>${batang(d.pos_pct, d.net_pct, d.neg_pct)}<div class="legenda"><div class="p"><b>${pct(d.pos_pct)}</b><span>positif</span></div><div class="n"><b>${pct(d.net_pct)}</b><span>netral</span></div><div class="g"><b>${pct(d.neg_pct)}</b><span>negatif</span></div></div></div>
    <div><div class="kepala-bagian"><h2 class="judul" style="font-size:17px">Topik</h2></div>${diverging(d.aspek, true)}</div>
    <div class="kata-laci">${d.kata.Negatif.length ? daftarKata('Kata dalam ulasan negatif', 'var(--neg)', d.kata.Negatif.slice(0, 8), 'Negatif') : ''}</div>
    <button class="tombol" id="laci-baca">Baca ulasan produk ini</button>`;
  isiDiver(c); isiBatang(c); $$('.kata .rel i', c).forEach(e => e.style.width = e.dataset.w + '%');
  $$('.dv', c).forEach(b => b.onclick = () => { tutupLaci(); bacaUlasan({ produk: nama, aspek: b.dataset.aspek }); });
  $$('[data-cari]', c).forEach(a => a.onclick = () => { tutupLaci(); bacaUlasan({ produk: nama, q: a.dataset.cari, label: 'Negatif' }); });
  $('#laci-baca').onclick = () => { tutupLaci(); bacaUlasan({ produk: nama }); };
}
const tutupLaci = () => $('#laci').hidden = true;
$$('[data-tutup]').forEach(e => e.onclick = tutupLaci);
document.addEventListener('keydown', e => { if (e.key === 'Escape') tutupLaci(); });

/* ulasan */
function bacaUlasan(f) { S.filter = f; S.hal = 1; pindah('ulasan'); renderFilter(); muatUlasan(); }
function panelUlasan() {
  const r = S.r, p = $('#p-ulasan');
  const prod = r.produk.map(x => `<option value="${esc(x.nama)}">${esc(x.nama.slice(0, 60))}</option>`).join('');
  p.innerHTML = `<div class="kepala-bagian"><h2 class="judul">Baca ulasan</h2><p class="sub">Buka “Mengapa label ini?” pada ulasan mana pun untuk melihat bagian kalimat yang menentukan hasilnya.</p></div>
  <div class="saring">
    <input type="search" id="f-q" placeholder="Cari kata…" aria-label="Cari kata">
    <select id="f-label" aria-label="Sentimen"><option value="">Semua sentimen</option><option>Positif</option><option>Netral</option><option>Negatif</option></select>
    <select id="f-aspek" aria-label="Topik"><option value="">Semua topik</option>${r.aspek.map(a => `<option>${esc(a.nama)}</option>`).join('')}</select>
    ${r.produk.length ? `<select id="f-produk" aria-label="Produk"><option value="">Semua produk</option>${prod}</select>` : ''}
    <select id="f-urut" aria-label="Urutan"><option value="acak">Acak</option><option value="skor_naik">Paling negatif dulu</option><option value="skor_turun">Paling positif dulu</option></select>
    ${r.ada_rating ? `<label class="centang"><input type="checkbox" id="f-konflik"><span>Bintang bertentangan</span></label>` : ''}
  </div>
  <p class="kecil" id="u-info"></p><div class="daftar" id="u-daftar"></div><div class="halaman" id="u-hal"></div>`;
  let t; const ubah = () => { clearTimeout(t); t = setTimeout(() => { ambilFilter(); S.hal = 1; muatUlasan(); }, 250); };
  $$('.saring input,.saring select', p).forEach(e => e.addEventListener('input', ubah));
}
function renderFilter() {
  const f = S.filter;
  const set = (i, v) => { const e = $(i); if (e) e.value = v || ''; };
  set('#f-q', f.q); set('#f-label', f.label); set('#f-aspek', f.aspek); set('#f-produk', f.produk); set('#f-urut', f.urut || 'acak');
  const k = $('#f-konflik'); if (k) k.checked = f.konflik === '1';
}
function ambilFilter() {
  const v = i => ($(i) || {}).value || '';
  S.filter = { q: v('#f-q'), label: v('#f-label'), aspek: v('#f-aspek'), produk: v('#f-produk'), urut: v('#f-urut'), konflik: ($('#f-konflik') || {}).checked ? '1' : '' };
}
async function muatUlasan() {
  const q = new URLSearchParams(); Object.entries(S.filter).forEach(([k, v]) => v && q.set(k, v)); q.set('hal', S.hal);
  const d = await (await fetch(`/api/ulasan/${S.jid}?` + q)).json();
  $('#u-info').textContent = `${id(d.total)} ulasan cocok`;
  $('#u-daftar').innerHTML = d.baris.length ? d.baris.map(u => `
    <article class="ul ${u.label}"><div class="ul-kepala"><span class="pil ${u.label}">${u.label}</span>${u.campuran ? '<span class="pil k">memuat pujian & keluhan</span>' : ''}
      ${u.rating ? `<span>Bintang ${u.rating}</span>` : ''}${u.konflik ? '<span class="pil k">bintang bertentangan</span>' : ''}<span>${esc(u.produk.slice(0, 48))}</span></div>
      <p>${esc(u.teks)}</p>
      ${u.klausa ? `<details><summary>Mengapa label ini?</summary><div class="klausa">${u.klausa.map(k => `<span>${esc(k.teks)}</span><em>${k.pos ? `<span class="ps">+${k.pos}</span> ` : ''}${k.neg ? `<span class="ng">−${k.neg}</span>` : ''}${!k.pos && !k.neg ? '<span class="kecil">netral</span>' : ''}</em>`).join('')}
        <span class="kecil">Skor total ${u.skor > 0 ? '+' : ''}${u.skor}; di atas +0,6 positif, di bawah −0,6 negatif</span><span></span></div></details>` : ''}
    </article>`).join('') : `<div class="kosongan">Tidak ada ulasan yang cocok. Longgarkan salah satu penyaring.</div>`;
  const maks = Math.ceil(d.total / d.per);
  $('#u-hal').innerHTML = maks > 1 ? `<button class="tombol sekunder" ${S.hal <= 1 ? 'disabled' : ''} id="h-mun">Sebelumnya</button><span class="kecil">Halaman ${S.hal} dari ${id(maks)}</span><button class="tombol sekunder" ${S.hal >= maks ? 'disabled' : ''} id="h-maj">Berikutnya</button>` : '';
  const m = $('#h-mun'), n = $('#h-maj');
  if (m) m.onclick = () => { S.hal--; muatUlasan(); window.scrollTo(0, 0); };
  if (n) n.onclick = () => { S.hal++; muatUlasan(); window.scrollTo(0, 0); };
}

/* validasi */
function panelValidasi() {
  const p = $('#p-validasi');
  p.innerHTML = `<div class="kepala-bagian"><h2 class="judul">Seberapa benar mesin ini?</h2>
    <p class="sub">Unggah CSV berisi ulasan yang sudah Anda beri label sendiri (kolom <code>Ulasan</code> dan <code>label_manual</code>: Positif, Netral, atau Negatif). Angka di bawah dihitung langsung dari file itu, bukan angka tetap. Contoh format ada di <code>data_contoh/sampel_uji_awal.csv</code>.</p></div>
  <div class="val-form"><input type="file" id="v-file" accept=".csv"><button class="tombol" id="v-jalan">Hitung ketepatan</button><span class="galat" id="v-galat" hidden></span></div>
  <div id="v-hasil"></div>`;
  $('#v-jalan').onclick = async () => {
    const f = $('#v-file').files[0], g = $('#v-galat'); g.hidden = true;
    if (!f) { g.textContent = 'Pilih file dulu.'; g.hidden = false; return; }
    const fd = new FormData(); fd.append('file', f);
    const r = await fetch('/api/validasi/' + S.jid, { method: 'POST', body: fd }), d = await r.json();
    if (!r.ok) { g.textContent = d.error; g.hidden = false; return; }
    const w = v => v >= .75 ? 'var(--pos-l)' : v >= .5 ? 'var(--net-l)' : 'var(--neg-l)';
    $('#v-hasil').innerHTML = `<div class="skor"><div><b>${pct(d.akurasi * 100)}</b><span>akurasi, dari ${id(d.n)} ulasan</span></div><div><b>${d.macro_f1.toFixed(2).replace('.', ',')}</b><span>macro-F1 (rata-rata adil antar kelas)</span></div></div>
    <div class="dua" style="margin-top:36px"><div><h3 class="judul" style="font-size:16px;margin-bottom:10px">Per kelas</h3><div class="tabel-wrap"><table><thead><tr><th>Kelas</th><th>Presisi</th><th>Recall</th><th>F1</th><th>Jumlah</th></tr></thead><tbody>
      ${d.kelas.map(k => `<tr style="cursor:default"><td><b>${k.label}</b></td><td>${k.presisi}</td><td>${k.recall}</td><td style="background:${w(k.f1)}">${k.f1}</td><td>${k.n}</td></tr>`).join('')}</tbody></table></div>
      <p class="kecil" style="margin-top:8px">Recall rendah pada Negatif berarti keluhan ada yang lolos dari mesin.</p></div>
    <div><h3 class="judul" style="font-size:16px;margin-bottom:10px">Tebakan mesin vs label Anda</h3><div class="cm"><div class="h"></div>${d.labels.map(l => `<div class="h">${l}</div>`).join('')}
      ${d.matriks.map((b, i) => `<div class="r">${d.labels[i]}</div>` + b.map((v, j) => `<div class="c" style="background:${i === j ? 'var(--pos-l)' : v ? 'var(--neg-l)' : 'var(--net-l)'}">${v}</div>`).join('')).join('')}</div></div></div>
    ${d.salah.length ? `<div style="margin-top:36px"><h3 class="judul" style="font-size:16px;margin-bottom:10px">Yang salah ditebak (maks. 30)</h3><div class="daftar">${d.salah.map(s => `<article class="ul ${s.manual}"><div class="ul-kepala"><span>Label Anda</span><span class="pil ${s.manual}">${s.manual}</span><span>Mesin</span><span class="pil ${s.mesin}">${s.mesin}</span></div><p>${esc(s.teks)}</p></article>`).join('')}</div></div>` : ''}`;
  };
}

/* tab & tombol */
function pindah(t) {
  S.tab = t;
  $$('#tab button').forEach(b => b.setAttribute('aria-selected', String(b.dataset.tab === t)));
  $$('.panel').forEach(p => p.hidden = p.id !== 'p-' + t);
  if (t === 'ringkasan' || t === 'topik' || t === 'produk') { isiBatang($('#p-' + t)); isiDiver($('#p-' + t)); animasiGrafik($('#p-' + t)); }
  window.scrollTo(0, 0);
}
$$('#tab button').forEach(b => b.onclick = () => { if (b.dataset.tab === 'ulasan' && !$('#u-daftar').children.length) { S.filter = {}; renderFilter(); muatUlasan(); } pindah(b.dataset.tab); });
$('#btn-baru').onclick = () => { S.berkas = null; S.contoh = ''; file.value = ''; $$('#contoh .chip').forEach(c => c.setAttribute('aria-pressed', 'false')); tandai(); layar('awal'); };
$('#btn-cetak').onclick = () => window.print();
