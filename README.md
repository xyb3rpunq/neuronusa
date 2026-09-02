<div align="center">

# neuronusa

**Jaringan syaraf yang gradiennya bisa dilihat satu per satu — dan dibuktikan benar.**
<br>
*A neural network whose gradients you can see one by one — and prove correct.*

[![CI](https://github.com/xyb3rpunq/neuronusa/actions/workflows/ci.yml/badge.svg)](https://github.com/xyb3rpunq/neuronusa/actions/workflows/ci.yml)
[![Live](https://img.shields.io/badge/live-xyb3rpunq.github.io%2Fneuronusa-0d9488)](https://xyb3rpunq.github.io/neuronusa/)
[![Lisensi](https://img.shields.io/badge/lisensi-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/Python-di%20peramban-3776ab?logo=python&logoColor=white)](https://brython.info/)
[![Uji](https://img.shields.io/badge/uji-108-brightgreen)](py/uji/test_nusa.py)
[![Bahasa](https://img.shields.io/badge/bahasa-ID%20%2B%20EN-blue)](py/nusa/bahasa.py)
[![Konformansi](https://img.shields.io/badge/konformansi-3.796%20pernyataan-brightgreen)](conformance/)

**[🔗 Buka situsnya / Open the site](https://xyb3rpunq.github.io/neuronusa/)**

[🇮🇩 Bahasa Indonesia](#-bahasa-indonesia) · [🇬🇧 English](#-english)

</div>

---

## 🇮🇩 Bahasa Indonesia

### Ini apa, sih?

Bayangkan kamu mengajari anak kecil membedakan kucing dan anjing. Tiap kali dia
salah, kamu bilang "bukan, itu salah" — dan dia sedikit mengubah cara
menebaknya. Ribuan kali. Lama-lama dia jarang salah.

Jaringan syaraf tiruan belajar persis seperti itu. Yang memberitahunya harus
berubah ke arah mana disebut **gradien** — semacam petunjuk arah: *"kalau angka
ini digeser sedikit ke kanan, tebakanmu jadi lebih benar sebanyak sekian."*

Masalahnya: **petunjuk arahnya bisa salah, dan tetap kelihatan berhasil.**
Seperti orang yang salah membaca peta tapi kebetulan tetap sampai ke kota —
hanya lebih lama, lewat jalan yang aneh, dan berhenti di alamat yang keliru.

Situs ini memperlihatkan petunjuk arah itu satu per satu, lalu **menghitungnya
ulang dengan cara yang sama sekali berbeda** dan menunjukkan apakah keduanya
sepakat. Supaya kamu tidak perlu percaya begitu saja, ada tombol untuk
**merusaknya dengan sengaja** — biar kamu lihat sendiri pemeriksanya memang
bekerja.

Semua perhitungannya berjalan **di dalam peramban kamu**. Tidak ada server,
tidak ada data yang dikirim ke mana pun.

### Kenapa ini penting

Hampir setiap demo jaringan syaraf memperlihatkan kurva galat yang menurun,
lalu berhenti di situ. **Kurva galat tidak membuktikan apa pun.** Tanda gradien
yang terbalik pada satu bobot, faktor dua yang hilang, turunan aktivasi yang
tertukar — seluruhnya menghasilkan grafik yang sama meyakinkannya dengan
grafik yang benar.

Yang membedakan proyek ini: setiap turunan dihitung ulang dengan **selisih
hingga**, lalu ditampilkan berdampingan dengan hasil perambatan balik beserta
galat relatifnya.

```
LOLOS   Galat relatif terburuk 2.803e-08 pada 17 parameter. Ambangnya 1e-5.

parameter      nilai       perambatan balik    selisih hingga     galat relatif
bias L0 n0     0.31842     0.00000086          0.00000086         2.80e-08
w L0 n3←2     -0.72119     0.00002257          0.00002257         2.77e-09
```

### Apa saja yang bisa dilakukan

| Modul | Yang diperlihatkan |
|---|---|
| **Masalah** | XOR, AND, cincin. Setel neuron tersembunyi ke nol pada XOR, dan lihat sendiri batas Minsky–Papert alih-alih membaca kutipannya. |
| **Data sendiri** | Tempel data kamu — tiga kolom, pemisah apa pun, koma desimal Indonesia diterima. Diskalakan otomatis, rentang aslinya diberitahukan. |
| **Bentuk jaringan** | Jumlah neuron tersembunyi, empat aktivasi, benih bobot awal. |
| **Sabotase** | Empat cacat perambatan balik yang bisa dinyalakan, dengan jaringan pembanding yang benar dilatih berdampingan. |
| **Kurva galat** | Galat tiap epoch, sumbunya berskala pada rentang yang benar-benar dicapai. |
| **Batas keputusan** | Tebakan jaringan di seluruh bidang, dicacah 484 titik di atas kanvas. |
| **Peta bobot** | Tebal garis = besarnya, warna = tandanya, plus tabel nilai tepatnya. |
| **Langkah demi langkah** | Satu contoh melewati jaringan, maju lalu balik: keluaran, delta, dan gradien tiap neuron. |
| **Pemeriksaan gradien** | Seluruh turunan dihitung ulang dengan selisih tengah, diurutkan dari galat terbesar. |
| **Konformansi** | Tombol yang menjalankan ulang 3.796 pernyataan lintas bahasa di peramban kamu, sekarang. |
| **Ekspor** | Unduh seluruh hasilnya sebagai CSV yang rapi di Excel, atau cetak jadi PDF. |
| **Bagikan** | Alamatnya selalu mencerminkan setelan; membukanya di tempat lain menghasilkan jaringan yang sama persis. |
| **Dwibahasa** | Seluruh isinya ada dalam Bahasa Indonesia dan Inggris, berganti seketika. Prosa tetap dipilih CSS, bukan Python — belasan kilobyte teks tidak layak disusun ulang penerjemah. |

Setiap gambar punya keterangan yang menjelaskan **apa yang harus dilihat**,
bukan sekadar menamai sumbunya.

### Sabotase: membantah klaim situs ini sendiri

Sebuah pemeriksa yang tidak pernah gagal tidak memeriksa apa pun. Panel
*Sabotase* memasang empat cacat sungguhan — kesalahan yang benar-benar sering
ditulis orang, bukan derau acak. Derau acak langsung merusak pelatihan dan
karena itu tidak mengajarkan apa pun; yang berbahaya justru cacat yang
membiarkan segalanya tampak baik-baik saja.

Diukur pada XOR, benih 7, empat neuron tersembunyi, 3.000 epoch:

| Cacat | Bekerja di | Pemeriksa gradien | Galat akhir | Titik benar |
|---|---|---|---|---|
| *(tidak ada)* | — | LOLOS | 4,34e-05 | 4/4 |
| Satu tanda terbalik | gradien | **GAGAL** | **4,24e-05** | 4/4 |
| Turunan aktivasi tidak dikalikan | gradien | **GAGAL** | 1,25e-01 | 3/4 |
| Faktor dua tertinggal | gradien | **GAGAL** | **2,11e-05** | 4/4 |
| Bias tidak pernah diperbarui | pembaruan | **LOLOS** | 3,13e-02 | 4/4 |

Baca baris kedua sekali lagi. Perambatan balik yang **salah tandanya** pada
satu bobot berakhir di galat yang *lebih rendah* daripada yang benar, dan
menjawab keempat titik XOR dengan benar. Baris keempat lebih buruk: cacatnya
menyamar sebagai perbaikan, karena menggandakan seluruh gradien setara dengan
menggandakan laju belajar.

Saat sebuah cacat menyala, jaringan pembanding dengan **bobot awal yang sama
persis** ikut dilatih berdampingan dan muncul sebagai garis putus-putus di
kurva galat. Benih yang sama itu yang membuat perbandingannya bermakna.

**Baris terakhir yang paling penting.** `Bias tidak pernah diperbarui` *lolos*
pemeriksaan, dan memang harus. Pemeriksa gradien memeriksa apakah turunannya
*benar*, bukan apakah turunannya *dipakai*. Alat yang batasnya tidak diketahui
lebih berbahaya daripada tidak punya alat.

Seluruh angka di tabel itu dikunci uji — termasuk yang kontraintuitif.

### Enam bahasa, angka yang sama persis

Algoritma inti proyek ini sudah ditulis **enam kali dalam enam bahasa**: Rust,
Go, PL/SQL Oracle, Lua, Swift, dan Python. Masing-masing ditulis dari rumusnya,
bukan diterjemahkan — salinan mewarisi seluruh cacat aslinya, sehingga mengadu
salinan dengan sumbernya tidak membuktikan apa pun.

```
bayes.tsv                   2187 diperiksa  BitExact                ULP maks   0  ok
certainty.tsv                680 diperiksa  BitExact                ULP maks   0  ok
fuzzy_linear.tsv             520 diperiksa  BitExact                ULP maks   0  ok
fuzzy_transcendental.tsv     222 diperiksa  NearlyEqual(4)          ULP maks   0  ok
fx.tsv                        14 diperiksa  BitExact                ULP maks   0  ok
ml_entropy.tsv                 7 diperiksa  NearlyEqual(4)          ULP maks   0  ok
ml_exact.tsv                  18 diperiksa  BitExact                ULP maks   0  ok
ml_gain.tsv                    4 diperiksa  CancellingDifference(4) ULP maks   0  ok
rng.tsv                      144 diperiksa  BitExact                ULP maks   0  ok
Seluruh 3796 pernyataan cocok antara Python dan Rust.
```

Angkanya berpindah sebagai **pola bit heksadesimal 16 digit**, bukan desimal.
Pengukuran pada proyek pendahulunya menemukan pengurai desimal yang salah
membulat 1 ULP pada 27.548 dari 200.000 nilai uji: menulis
`0.42000000000000004` lalu membacanya kembali bisa menghasilkan `0.42`.

**Empat tingkat keterbandingan**, karena "sama" bukan satu pertanyaan:

- `BitExact` — cocok sampai bit terakhir.
- `NearlyEqual(n)` — kelonggaran *n* ULP pada hasilnya, untuk `exp`/`log`/`pow`
  yang memang tidak diwajibkan dibulatkan benar oleh standar mana pun.
- `CancellingDifference(n)` — kelonggaran diukur pada **skala masukan**.
  Perolehan informasi adalah selisih dua entropi yang hampir sama besar, dan
  pengurangan seperti itu memperbesar galat relatifnya puluhan kali.
- `PropertyOnly` — hanya sifatnya yang diperiksa, bukan nilainya.

### Konformansi yang dijalankan di peramban

Tombol di halaman menjalankan ulang **seluruh 3.796 pernyataan itu di peramban
pengunjung** — sekitar 2,2 detik, dipecah menjadi potongan 40 milidetik supaya
halamannya tidak membeku.

Itu bukan hiasan. **Dua cacat sungguhan hanya muncul di peramban dan tidak bisa
ditangkap uji CPython mana pun:**

```python
# 1. Brython salah memformat %e
'%.3e' % 2.803e-08        # → '0.000e+00'      SALAH
format(2.803e-08, '.3e')  # → '2.803e-08'      benar

# 2. Brython melempar OverflowError pada ldexp untuk subnormal
math.ldexp(5e-324, 1074)  # → OverflowError, padahal jawabannya 1.0
```

Cacat pertama membuat pemeriksa gradien melaporkan galat relatif `0.000e+00`
untuk **setiap** parameter — jauh lebih meyakinkan daripada yang sebenarnya.
Cacat yang membuat sesuatu terlihat *lebih* benar adalah cacat yang paling lama
bertahan.

Hasil di peramban juga berbeda dari CI, persis seperti yang diramalkan
rancangannya:

| berkas | tingkat | ULP di CPython | ULP di Brython |
|---|---|---|---|
| seluruh berkas `BitExact` | `BitExact` | 0 | **0** |
| `fuzzy_transcendental.tsv` | `NearlyEqual(4)` | 0 | **2** |
| `ml_gain.tsv` | `CancellingDifference(4)` | 0 | **64** |

Enam puluh empat ULP, dan tetap cocok — karena `CancellingDifference` mengukur
toleransinya pada skala masukan, bukan pada hasil. Angka itu tidak pernah
muncul di CI, dan hanya terlihat kalau tombolnya benar-benar ditekan.

### Menjalankan sendiri

```bash
npm install
npm run dev
```

| Perintah | Yang dilakukan |
|---|---|
| `npm run dev` | Kemas mesin Python, jalankan server di `:5176`. |
| `npm run build` | Kemas, lalu bangun ke `dist/`. |
| `npm test` | 108 uji mesin Python (CPython). |
| `npm run conform` | Adu Python lawan 3.796 vektor Rust. |
| `npm run typecheck` | Periksa tipe TypeScript. |
| `npm run budget` | Anggaran ukuran berkas terbitan. |
| `npm run kemasan` | Pastikan kemasan sepadan dengan sumbernya, bita demi bita. |
| `npm run audit:all` | Seluruhnya, berurutan. |

Butuh Python 3.10+ dan Node 22+. Mesinnya **tidak memakai satu pun modul di
luar `math`** — bukan `numpy`, bukan `decimal`, bukan `random`, bukan `struct`
— karena seluruhnya harus jalan di Brython juga. CI menolak impor terlarang
sebelum sempat terbit.

### Susunan

```
py/nusa/            mesin — CPython saat uji, Brython di peramban
  fx.py             pertukaran pecahan bit-eksak, disandi tanpa struct
  inti.py           algoritma yang diadu lintas bahasa
  jaringan.py       jaringan syaraf, gradien, pemeriksa gradien, katalog cacat
  konform.py        pemeriksa konformansi, bisa dijalankan bertahap
  tautan.py         penyandi setelan ke alamat, dengan pemeriksaan masukan
  data.py           pengurai data tempelan pengguna
  ekspor.py         penyusun laporan CSV
  bahasa.py         kamus dwibahasa Indonesia dan Inggris
py/uji/             108 uji
conformance/        9 berkas vektor yang dihasilkan Rust
src/
  app.py            seluruh antarmuka, ditulis dalam Python
  nyalakan.ts       satu-satunya TypeScript yang terbit — 110 baris
  gaya.css          gaya, ditulis tangan
scripts/            pengemas, pemangkas pustaka, anggaran, pemeriksa kemasan
```

**Kenapa mesin virtual, bukan `pythonpath`.** Brython mengimpor modul dengan
XMLHttpRequest **sinkron**; setiap `import` memblokir utas tampilan selama satu
perjalanan jaringan. Prapengambilan `fetch` tidak menolong karena Brython
menempelkan `?v=<waktu>` pada tiap URL modul. Seluruh modul dititipkan lewat
`update_VFS` — satu permintaan, nol XHR sinkron.

**Kenapa pustaka standarnya dipangkas.** `brython_stdlib.js` 4,6 MB; situs ini
memakai lima modul dari dalamnya, yang seluruhnya 89 KB. Itu juga alasan
`fx.py` menyandi IEEE-754 sendiri: di Brython, `struct` menarik `_struct`, yang
menarik `re` — mesin regex yang ditulis dalam Python.

### Berat dan kelancaran

| Berkas | gzip |
|---|---|
| `brython.min.js` | 256,5 KB |
| `brython_stdlib_mini.js` | 24,3 KB |
| `nusa_vfs.js` (mesin) | 37,2 KB |
| halaman, gaya, penyala | 8,0 KB |
| **muat pertama** | **≈ 326 KB** |
| `vektor_vfs.js` | 28,8 KB — hanya kalau tombol konformansi ditekan |

Kelancarannya **diukur**, bukan diperkirakan. Bentuk pertama menggambar ulang
seluruh keluaran dalam 637 milidetik per bingkai:

| Perubahan | Hasil |
|---|---|
| Batas keputusan dari 677 elemen SVG ke kanvas | 606 → 173 ms |
| `bidang_keputusan` disusun ulang per lapis, memakai ulang suku `w₀x`/`w₁y` | 129 → 39 ms |
| `math.tanh` dipakai langsung, tanpa pembungkus | −1,2 µs per neuron |
| Petak sebaris digabung; metode kanvas ke nama lokal | 82 → 47 ms |
| Penggambaran dipisah murah/mahal, gelang berbasis anggaran waktu | **8,5 ms** lazim, 74 ms penuh |
| `langkah(hitung_galat=False)` | epoch 8,3 → 4,5 ms |

Biaya per operasi di Brython yang mendasari semua itu: pemanggilan fungsi
Python **±1,2 µs**, pencarian atribut **±1,6 µs**, satu panggilan menyeberang
ke JavaScript **±30 µs**. Aritmetikanya sendiri hampir gratis.

Susunan ulang perhitungannya **bit-eksak** terhadap jalur lambatnya —
`test_bidang_keputusan_sama_persis` membandingkan pola bitnya di empat
aktivasi dan empat bentuk jaringan.

### Yang diuji, dan kenapa

108 uji, ditulis untuk gagal ketika sesuatu memang salah:

- **`test_pemeriksa_gradien_menangkap_gradien_yang_dirusak`** — merusak satu
  gradien dengan sengaja, lalu menuntut pemeriksanya gagal.
- **`test_xor_tidak_bisa_dipelajari_tanpa_lapis_tersembunyi`** — memverifikasi
  Minsky–Papert alih-alih mengutipnya.
- **`test_telusuri_sama_dengan_gradien`** — membandingkan angka yang
  ditampilkan dengan angka yang dipakai melatih, **pola bit demi pola bit**.
  Uji ini menemukan keduanya berbeda pada nol negatif.
- **`test_setiap_cacat_tetap_terlihat_belajar`** — menuntut galat *menurun*
  pada keempat cacat; kalau ada yang tidak, halaman tidak boleh memakainya
  sebagai contoh.
- **`test_bias_beku_tidak_bisa_ditangkap_pemeriksa_gradien`** — mengunci
  *batas* alatnya, bukan kemampuannya.
- **`test_pemisah_dipilih_dari_seluruh_teks_bukan_baris_pertama`** — mengunci
  cacat pengurai data yang salah membaca `165;55,0;0`.
- **`test_nan_dan_takhingga_ditolak_walau_perbandingannya_aneh`** — `NaN`
  gagal setiap perbandingan, termasuk yang dipakai menolaknya.
- **`test_laporan_kosong_tidak_dianggap_lolos`** — laporan tanpa satu pun
  pernyataan bukan keberhasilan melainkan tanda vektornya tidak terbaca.

### Keamanan

```
default-src 'none'; script-src 'self' 'unsafe-eval'; style-src 'self';
img-src 'self' data:; font-src 'self'; connect-src 'self';
base-uri 'none'; form-action 'none'; object-src 'none'
```

`'unsafe-eval'` ada karena Brython memang membutuhkannya: ia menerjemahkan
Python menjadi JavaScript lalu menjalankannya dengan `new Function`. Itu inti
cara kerjanya, bukan kecerobohan yang bisa ditambal. Tidak ada satu pun berkas
diambil dari CDN — mesin yang menjalankan kode di peramban pengguna tidak
pantas diambil dari tempat yang bisa berubah tanpa sepengetahuan siapa pun.

---

## 🇬🇧 English

### What is this?

Imagine teaching a child to tell cats from dogs. Each time they get it wrong,
you say "no, that's wrong" — and they adjust their guessing a little. Thousands
of times. Eventually they rarely miss.

Artificial neural networks learn exactly like that. What tells them which way
to adjust is called a **gradient** — a direction hint: *"nudge this number
slightly right and your guess improves by this much."*

The problem: **the direction hint can be wrong and still look like it works.**
Like someone misreading a map who happens to reach the city anyway — just
slower, by a strange route, stopping at the wrong address.

This site shows those hints one by one, then **recomputes them a completely
different way** and reports whether the two agree. And so you needn't take that
on faith, there is a button to **break it on purpose** — so you can watch the
checker actually catch it.

Everything runs **inside your browser**. No server, no data leaves your machine.

### Why it matters

Almost every neural-network demo shows a descending error curve and stops
there. **An error curve proves nothing.** A flipped gradient sign on one
weight, a missing factor of two, a swapped activation derivative — each yields
a chart just as convincing as the correct one.

What sets this project apart: every derivative is recomputed with **finite
differences** and displayed side by side with the backpropagated value and its
relative error.

### Sabotage: letting visitors refute the site's own claim

A checker that never fails checks nothing. The *Sabotage* panel installs four
real defects — mistakes people genuinely write, not random noise. Random noise
breaks training immediately and therefore teaches nothing; the dangerous
defects are the ones that let everything keep looking fine.

Measured on XOR, seed 7, four hidden neurons, 3,000 epochs:

| Defect | Acts on | Gradient check | Final error | Points correct |
|---|---|---|---|---|
| *(none)* | — | PASS | 4.34e-05 | 4/4 |
| One sign flipped | gradient | **FAIL** | **4.24e-05** | 4/4 |
| Activation derivative dropped | gradient | **FAIL** | 1.25e-01 | 3/4 |
| Factor of two left out | gradient | **FAIL** | **2.11e-05** | 4/4 |
| Bias never updated | update step | **PASS** | 3.13e-02 | 4/4 |

Read the second row again. Backpropagation with a **flipped sign** on one
weight ends at a *lower* error than the correct version, and answers all four
XOR points correctly. The fourth row is worse: the defect masquerades as an
improvement, because doubling every gradient is equivalent to doubling the
learning rate.

When a defect is active, a reference network with **bit-identical initial
weights** trains alongside it and appears as a dashed line on the error curve.
That shared seed is what makes the comparison mean anything.

**The last row matters most.** `Bias never updated` *passes* the check, and it
must. Gradient checking verifies whether the derivative is *right*, not whether
it is *used*. A tool whose limits are unknown is more dangerous than no tool.

### Six languages, bit-identical numbers

The core algorithms have been written **six times in six languages**: Rust, Go,
Oracle PL/SQL, Lua, Swift, and Python — each from the formulas, never
translated, because a copy inherits every defect of its original. All 3,796
assertions match to the last bit.

Numbers cross language boundaries as **16-digit hexadecimal bit patterns**, not
decimal. Measurement on a predecessor project found a decimal parser
mis-rounding by 1 ULP on 27,548 of 200,000 test values.

Four comparability tiers exist because "equal" is not one question:

- `BitExact` — identical to the last bit.
- `NearlyEqual(n)` — *n* ULP of slack on the result, for `exp`/`log`/`pow`,
  which no standard requires to be correctly rounded.
- `CancellingDifference(n)` — slack measured at the **input** scale.
  Information gain is the difference of two nearly equal entropies, and such a
  subtraction amplifies relative error by tens of times.
- `PropertyOnly` — only the property is checked, not the value.

### In-browser conformance

A button reruns **all 3,796 assertions in the visitor's browser** — about 2.2
seconds, sliced into 40 ms chunks so the page never freezes.

This is not decoration. **Two real defects appear only in the browser and no
CPython test could have caught them:**

```python
# 1. Brython formats %e incorrectly
'%.3e' % 2.803e-08        # → '0.000e+00'      WRONG
format(2.803e-08, '.3e')  # → '2.803e-08'      correct

# 2. Brython raises OverflowError from ldexp on subnormals
math.ldexp(5e-324, 1074)  # → OverflowError, though the answer is 1.0
```

The first made the gradient checker report `0.000e+00` for **every** parameter
— far more convincing than the truth. A defect that makes something look *more*
correct is the kind that survives longest.

Browser results also differ from CI, exactly as the design predicted:

| file | tier | ULP in CPython | ULP in Brython |
|---|---|---|---|
| all `BitExact` files | `BitExact` | 0 | **0** |
| `fuzzy_transcendental.tsv` | `NearlyEqual(4)` | 0 | **2** |
| `ml_gain.tsv` | `CancellingDifference(4)` | 0 | **64** |

Sixty-four ULP, and still a match — because `CancellingDifference` measures its
tolerance at the input scale, not on the result. That number never appears in
CI, and shows up only when the button is actually pressed.

### Running it

```bash
npm install
npm run dev        # http://localhost:5176/neuronusa/
npm run audit:all  # tests, conformance, typecheck, build, budget, bundle check
```

| Command | What it does |
|---|---|
| `npm run dev` | Bundle the Python engine, serve on `:5176`. |
| `npm run build` | Bundle, then build to `dist/`. |
| `npm test` | 108 engine tests (CPython). |
| `npm run conform` | Check Python against 3,796 Rust vectors. |
| `npm run typecheck` | TypeScript type check. |
| `npm run budget` | Published-size budget. |
| `npm run kemasan` | Verify the bundle matches its sources byte for byte. |

Python 3.10+ and Node 22+. The engine imports **nothing beyond `math`** —
no `numpy`, `decimal`, `random`, or `struct` — because it must also run under
Brython. CI rejects forbidden imports before they can ship.

### Architecture notes

**Why a virtual filesystem, not `pythonpath`.** Brython imports modules with
**synchronous** XMLHttpRequest; every `import` blocks the UI thread for one
network round trip. Prefetching with `fetch` does not help, because Brython
appends `?v=<now>` to each module URL. All modules are registered through
`update_VFS` instead — one request, zero synchronous XHR.

**Why the standard library is trimmed.** `brython_stdlib.js` is 4.6 MB; this
site uses five modules from it, totalling 89 KB. It is also why `fx.py` encodes
IEEE-754 by hand: under Brython, `struct` pulls in `_struct`, which pulls in
`re` — a regex engine written in Python.

### Weight and smoothness

First load is ≈ 326 KB gzip, of which 256.5 KB is the Python interpreter
itself. Conformance vectors (28.8 KB) load only when the button is pressed.

Frame cost was **measured**, not estimated: full redraw went from 637 ms to
8.5 ms on the common path, by moving the decision field from 677 SVG elements
to a canvas, reorganising the field computation per layer, and splitting cheap
redraws from expensive ones under a time budget. The reorganisation is
bit-exact against the slow path, and a test compares bit patterns across four
activations and four network shapes to keep it that way.

Per-operation cost in Brython, which drove all of it: a Python function call
≈ 1.2 µs, an attribute lookup ≈ 1.6 µs, one crossing into JavaScript ≈ 30 µs.
The arithmetic itself is nearly free.

### Security

```
default-src 'none'; script-src 'self' 'unsafe-eval'; style-src 'self';
img-src 'self' data:; font-src 'self'; connect-src 'self';
base-uri 'none'; form-action 'none'; object-src 'none'
```

`'unsafe-eval'` is present because Brython requires it: it translates Python to
JavaScript and runs it with `new Function`. That is how it works, not an
oversight to be patched. Nothing is loaded from a CDN.

---

<div align="center">

**Bagian dari empat situs IND323** · *Part of the four IND323 sites*

[ai-atlas](https://xyb3rpunq.github.io/ai-atlas/) (Rust → WASM) ·
[kecerdasan-buatan](https://xyb3rpunq.github.io/kecerdasan-buatan/) (Lua) ·
[ind323-ai-lab](https://xyb3rpunq.github.io/ind323-ai-lab/) (Swift) ·
**neuronusa** (Brython)

[MIT](LICENSE) — Daniel Hutajulu (`.Deckyx`), 2026

</div>
