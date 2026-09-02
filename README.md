# neuronusa

**Jaringan syaraf tiruan yang gradiennya bisa dilihat satu per satu — dan
dibuktikan benar.** Mesinnya Python asli, dijalankan di dalam peramban lewat
Brython. Tidak ada server, tidak ada API, tidak ada satu bita pun yang
dikirim ke mana pun.

🔗 **[xyb3rpunq.github.io/neuronusa](https://xyb3rpunq.github.io/neuronusa/)**

Situs keempat dari empat yang dibangun dari materi kuliah IND323 Kecerdasan
Buatan. Ketiga saudaranya:
[ai-atlas](https://xyb3rpunq.github.io/ai-atlas/) (Rust → WebAssembly),
[kecerdasan-buatan](https://xyb3rpunq.github.io/kecerdasan-buatan/) (Lua),
[ind323-ai-lab](https://xyb3rpunq.github.io/ind323-ai-lab/) (Swift).

---

## Kenapa proyek ini ada

Hampir setiap demo jaringan syaraf memperlihatkan kurva galat yang menurun,
lalu berhenti di situ.

**Kurva galat tidak membuktikan apa pun.** Jaringan yang perambatan baliknya
salah tetap sering "belajar" — hanya lebih lambat dan berhenti di tempat yang
keliru — dan kurvanya tetap terlihat menurun dengan meyakinkan. Tanda gradien
yang terbalik pada satu bobot, faktor dua yang hilang, turunan aktivasi yang
tertukar: seluruhnya menghasilkan gambar yang sama meyakinkannya dengan
gambar yang benar.

Yang membedakan proyek ini: setiap turunan dihitung ulang dengan selisih
hingga, lalu ditampilkan berdampingan dengan hasil perambatan balik beserta
galat relatifnya. Itu satu-satunya cara memisahkan perambatan balik yang benar
dari yang kebetulan bekerja.

```
LOLOS   Galat relatif terburuk 2.803e-08 pada 17 parameter. Ambangnya 1e-5.

parameter      nilai       perambatan balik    selisih hingga     galat relatif
bias L0 n0     0.31842     0.00000086          0.00000086         2.80e-08
w L0 n3←2     -0.72119     0.00002257          0.00002257         2.77e-09
...
```

---

## Yang bisa dilakukan di halamannya

| Modul | Yang diperlihatkan |
|---|---|
| **Masalah** | XOR, AND, dan cincin. Setel neuron tersembunyi ke nol pada XOR dan lihat sendiri batas Minsky–Papert, alih-alih membaca kutipannya. |
| **Bentuk jaringan** | Jumlah neuron tersembunyi, empat aktivasi, dan benih bobot awal. Benih yang sama menghasilkan pelatihan yang sama persis. |
| **Kurva galat** | Galat tiap epoch, dengan sumbu yang berskala pada rentang yang benar-benar dicapai. |
| **Batas keputusan** | Tebakan jaringan di seluruh bidang, digambar dengan mencacah 484 titik. Perceptron tanpa lapis tersembunyi hanya bisa menarik garis lurus; di sinilah itu terlihat. |
| **Peta bobot** | Tebal garis menyatakan besarnya, warnanya menyatakan tandanya — lengkap dengan tabel nilai tepatnya. |
| **Langkah demi langkah** | Satu contoh melewati jaringan, maju lalu balik: keluaran tiap neuron, delta tiap neuron, dan gradien tiap bias. |
| **Pemeriksaan gradien** | Seluruh turunan dihitung ulang dengan selisih tengah, ditampilkan berdampingan dan diurutkan dari galat terbesar. |
| **Konformansi** | Tombol yang menjalankan ulang 3.796 pernyataan lintas bahasa di peramban Anda, sekarang, dengan bilah kemajuan. |
| **Catatan dan definisi** | Sebelas istilah, ditulis untuk dibaca orang yang belum paham. |

Setiap gambar punya keterangan yang menjelaskan **apa yang harus dilihat**,
bukan hanya menamai sumbunya. Gambar tanpa penjelasan hanya berguna bagi yang
sudah paham isinya, dan pembaca yang paling butuh gambar justru yang belum.

---

## Enam bahasa, angka yang sama persis

Algoritma inti proyek ini — certainty factor, Bayes, himpunan kabur, entropi,
gini, perolehan informasi, dan pembangkit acak SplitMix64 — sudah ditulis
**enam kali dalam enam bahasa**: Rust, Go, PL/SQL Oracle, Lua, Swift, dan
Python. Masing-masing ditulis dari rumusnya, bukan diterjemahkan dari yang
lain; salinan mewarisi seluruh cacat aslinya, sehingga mengadu salinan dengan
sumbernya tidak membuktikan apa pun.

Keenamnya diadu terhadap berkas vektor yang sama:

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
==========================================================================
Seluruh 3796 pernyataan cocok antara Python dan Rust.
```

Angkanya berpindah antar bahasa sebagai **pola bit heksadesimal 16 digit**,
bukan sebagai desimal. Desimal tidak memenuhi syarat: pengukuran pada proyek
pendahulunya menemukan sebuah pengurai desimal yang salah membulat sebesar
1 ULP pada 27.548 dari 200.000 nilai uji. Menulis `0.42000000000000004` lalu
membacanya kembali bisa menghasilkan `0.42` — angka yang berbeda.

**Empat tingkat keterbandingan**, karena "sama" bukan satu pertanyaan:

- `BitExact` — cocok sampai bit terakhir. Berlaku untuk apa pun yang hanya
  memakai operasi yang IEEE-754 wajibkan dibulatkan dengan benar.
- `NearlyEqual(n)` — kelonggaran *n* ULP pada hasilnya. Untuk perhitungan yang
  menyentuh `exp`, `log`, atau `pow`; ketiganya memang tidak diwajibkan
  dibulatkan dengan benar oleh standar mana pun.
- `CancellingDifference(n)` — kelonggaran *n* ULP diukur pada **skala
  masukan**, bukan pada hasilnya. Perolehan informasi adalah selisih dua
  entropi yang hampir sama besar; pengurangan seperti itu memperbesar galat
  relatifnya sampai puluhan kali. Menuntut ketepatan pada hasil akhir adalah
  menuntut sesuatu yang tidak dimiliki angka mana pun di sana.
- `PropertyOnly` — hanya sifatnya yang diperiksa, bukan nilainya.

---

## Konformansi yang dijalankan di peramban

Halaman ini punya tombol yang menjalankan ulang **seluruh 3.796 pernyataan
itu di peramban pengunjung**, terhadap berkas vektor yang sama persis dengan
yang dipakai CI. Sekitar 2,2 detik, dipecah menjadi potongan 40 milidetik
supaya halamannya tidak membeku.

Itu bukan hiasan, dan bukan gagasan yang kedengarannya bagus. **Dua cacat
sungguhan di proyek ini hanya muncul di peramban dan tidak bisa ditangkap uji
CPython mana pun:**

**1. Brython salah memformat `%e`.**

```python
'%.3e' % 2.803e-08        # → '0.000e+00'      salah
'%.3e' % 1.5e+300         # → '1.5e+300e+00'   salah
'%.2e' % -3.5e-9          # → '-0.00e+00'      salah
format(2.803e-08, '.3e')  # → '2.803e-08'      benar
```

Akibatnya pemeriksa gradien melaporkan galat relatif `0.000e+00` untuk
**setiap** parameter — angka yang membuat hasilnya tampak jauh lebih
meyakinkan daripada yang sebenarnya. Cacat yang membuat sesuatu terlihat
*lebih* benar adalah cacat yang paling lama bertahan.

**2. Brython melempar `OverflowError` pada `math.ldexp(x, 1074)`.**

Ia menerjemahkannya menjadi perkalian dengan `2**n`, dan `2**1074` sendiri
sudah tak hingga sebagai `float` — padahal `ldexp(5e-324, 1074)` sama sekali
tidak meluap; hasilnya 1,0. Akibatnya pola bit subnormal tidak bisa disandi
sama sekali. Penskalaannya kini dipecah menjadi beberapa tahap.

Keduanya ditemukan dengan menjalankan konformansi di dalam peramban. CI
menjalankan CPython; pengunjung menjalankan Brython. Keduanya Python, dan
keduanya tidak sama.

Hasil di peramban juga memperlihatkan sesuatu yang jujur: `fuzzy_transcendental.tsv`
menunjukkan **ULP maks 2**, bukan 0 seperti di CPython. Brython menghitung
`exp` dan `log` lewat pustaka matematika JavaScript, yang menempuh jalan
berbeda dari pustaka C. Selisihnya jauh di dalam batas 4 ULP yang sudah
dinyatakan di muka untuk berkas itu — dan seluruh berkas `BitExact` tetap nol.
Tingkat `NearlyEqual(4)` ternyata memang bekerja, bukan hiasan.

---

## Menjalankan sendiri

```bash
npm install
npm run dev
```

| Perintah | Yang dilakukan |
|---|---|
| `npm run dev` | Kemas mesin Python, lalu jalankan server pengembangan di `:5176`. |
| `npm run build` | Kemas, lalu bangun ke `dist/`. |
| `npm test` | 58 uji mesin Python (CPython). |
| `npm run conform` | Adu Python lawan 3.796 vektor Rust. |
| `npm run budget` | Anggaran ukuran berkas terbitan. |
| `npm run kemasan` | Pastikan kemasan sepadan dengan sumbernya, bita demi bita. |
| `npm run audit:all` | Seluruhnya, berurutan. |

Python 3.10 atau lebih baru. Mesinnya **tidak memakai satu pun modul di luar
`math`** — bukan `numpy`, bukan `decimal`, bukan `random`, bukan `struct` —
karena seluruhnya harus jalan di Brython juga. CI menolak impor terlarang
sebelum sempat terbit.

---

## Susunan

```
py/nusa/          mesin — dijalankan CPython saat uji, Brython di peramban
  fx.py           pertukaran pecahan bit-eksak, disandi tanpa struct
  inti.py         algoritma yang diadu lintas bahasa
  jaringan.py     jaringan syaraf, gradien, dan pemeriksa gradien
  konform.py      pemeriksa konformansi, bisa dijalankan bertahap
py/uji/           58 uji
conformance/
  vectors/        9 berkas vektor yang dihasilkan Rust
  jalankan.py     pembungkus baris perintah
src/
  app.py          seluruh antarmuka, ditulis dalam Python
  nyalakan.ts     satu-satunya TypeScript yang terbit — 110 baris
  gaya.css        gaya, ditulis tangan
scripts/
  salin-py.mjs        kemas mesin Python menjadi mesin virtual Brython
  ekstrak-stdlib.mjs  pangkas pustaka standar Brython 4,6 MB → 89 KB
  budget.mjs          anggaran ukuran
  periksa-kemasan.mjs pastikan yang terbit sama dengan sumbernya
```

### Kenapa mesin virtual, bukan `pythonpath`

Brython mengimpor modul dengan XMLHttpRequest **sinkron**. Setiap `import`
karena itu memblokir utas tampilan selama satu perjalanan pulang-pergi
jaringan; enam modul berarti enam kali membeku berturut-turut sebelum sebaris
pun antarmuka tergambar. Mengambilnya lebih dulu dengan `fetch` tidak
menolong, karena Brython menempelkan `?v=<waktu sekarang>` pada tiap URL modul
sehingga permintaannya tidak pernah cocok dengan apa pun di singgahan.

Jalan yang benar adalah yang dipakai pustaka standar Brython sendiri: seluruh
modul dititipkan lewat `update_VFS`, dan `import` menemukannya di memori. Satu
permintaan, nol XHR sinkron.

### Kenapa pustaka standarnya dipangkas

`brython_stdlib.js` berukuran 4,6 MB. Situs ini memakai lima modul dari
dalamnya — `math`, `browser`, `browser.svg`, `browser.timer`, `_svg` — yang
seluruhnya 89 KB. Sisanya tidak pernah disentuh.

Itu juga alasan `fx.py` menyandi IEEE-754 sendiri alih-alih memakai `struct`:
di Brython, `struct` menarik `_struct`, yang menarik `re` — mesin ekspresi
reguler yang ditulis dalam Python. Berat, untuk satu panggilan pengemasan
bilangan.

---

## Berat dan kelancaran

| Berkas | gzip |
|---|---|
| `brython.min.js` | 256,5 KB |
| `brython_stdlib_mini.js` | 24,3 KB |
| `nusa_vfs.js` (mesin) | 31,0 KB |
| halaman, gaya, penyala | 7,9 KB |
| **muat pertama** | **320,7 KB** |
| `vektor_vfs.js` | 23,8 KB — diambil hanya kalau tombol konformansi ditekan |

Dua ratus lima puluh enam kilobyte dari angka itu adalah penerjemah Python
yang utuh, dan bukan sesuatu yang bisa dikecilkan tanpa berhenti menjadi situs
Python.

Kelancarannya diukur, bukan diperkirakan. Bentuk pertama menggambar ulang
seluruh keluaran dalam **637 milidetik** per bingkai — cukup lama untuk
membuat setiap langkah pelatihan tersendat terlihat. Yang mengubahnya:

| Perubahan | Hasil |
|---|---|
| Batas keputusan dipindah dari 677 elemen SVG ke kanvas | 606 → 173 ms |
| `bidang_keputusan` menyusun ulang perulangannya per lapis, memakai ulang suku `w₀x` dan `w₁y` | 129 → 39 ms |
| `math.tanh` dipakai langsung, tanpa pembungkus | pemanggilan fungsi Brython ±1,2 µs per neuron dihemat |
| Petak sebaris yang sewarna digabung; metode kanvas diambil ke nama lokal | 82 → 47 ms |
| Penggambaran dipisah murah/mahal, dengan gelang berbasis anggaran waktu | bingkai lazim **8,5 ms**, penuh **74 ms** |
| `langkah(hitung_galat=False)` di gelang pelatihan | epoch 8,3 → 4,5 ms |

Susunan ulang perhitungan itu **bit-eksak** terhadap jalur lambatnya —
`test_bidang_keputusan_sama_persis` membandingkan pola bitnya di empat
aktivasi dan empat bentuk jaringan. Merapikan `(bias + w₀x) + w₁y` menjadi
`w₀x + w₁y + bias` akan menghasilkan pembulatan yang berbeda, dan gambar yang
tidak lagi sepadan dengan angka di sebelahnya.

---

## Yang diuji, dan kenapa

58 uji, ditulis untuk gagal ketika sesuatu memang salah:

- **`test_pemeriksa_gradien_menangkap_gradien_yang_dirusak`** — merusak satu
  gradien dengan sengaja, lalu menuntut pemeriksanya gagal. Pemeriksa yang
  selalu lolos tidak memeriksa apa pun.
- **`test_xor_tidak_bisa_dipelajari_tanpa_lapis_tersembunyi`** — memverifikasi
  Minsky–Papert alih-alih mengutipnya.
- **`test_telusuri_sama_dengan_gradien`** — membandingkan angka yang
  ditampilkan dengan angka yang dipakai melatih, **pola bit demi pola bit**.
  Uji ini menemukan bahwa keduanya berbeda pada nol negatif: `gradien`
  menjumlahkan dari `0.0`, jadi `-0.0` di sana selalu menjadi `+0.0`.
- **`test_galat_terkurung_walau_lajunya_sangat_besar`** — menahan penjelasan
  di halaman tetap benar. Peringatan aslinya berbunyi bahwa laju besar membuat
  pelatihan "meledak"; pengukuran terhadap tiga aktivasi dan dua kumpulan
  data, sampai laju efektif 20.000, tidak pernah sekali pun menghasilkan NaN.
  Lapis keluarannya sigmoid, sehingga galatnya terkurung. Cara gagalnya bukan
  peledakan melainkan kejenuhan — dan teksnya sudah diperbaiki.
- **`test_setelan_bawaan_halaman_benar_benar_belajar_xor`** — setelan yang
  dilihat pengunjung pertama kali wajib berhasil.
- **`test_potongan_kecil_sama_dengan_sekaligus`** — konformansi bertahap wajib
  memberi hasil identik dengan yang sekaligus, pada tiga ukuran potongan.
- **`test_laporan_kosong_tidak_dianggap_lolos`** — laporan tanpa satu pun
  pernyataan bukan keberhasilan melainkan tanda vektornya tidak terbaca.

---

## Keamanan

Kebijakan isi halaman ini mengunci semuanya kecuali yang memang dibutuhkan:

```
default-src 'none'; script-src 'self' 'unsafe-eval'; style-src 'self';
img-src 'self' data:; font-src 'self'; connect-src 'self';
base-uri 'none'; form-action 'none'; object-src 'none'
```

`'unsafe-eval'` ada karena Brython memang membutuhkannya: ia menerjemahkan
Python menjadi JavaScript lalu menjalankannya dengan `new Function`. Itu inti
cara kerjanya, bukan kecerobohan yang bisa ditambal.

Tidak ada satu pun berkas diambil dari CDN. Mesin yang menjalankan kode di
peramban pengguna tidak pantas diambil dari tempat yang bisa berubah tanpa
sepengetahuan siapa pun.

---

## Lisensi

[MIT](LICENSE) — Daniel Hutajulu (`.Deckyx`), 2026.
