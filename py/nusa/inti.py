"""Algoritma inti yang diadu lintas bahasa.

Ditulis ulang dari rumusnya, bukan diterjemahkan dari kelima implementasi lain.
Salinan mewarisi seluruh cacat aslinya, sehingga mengadu salinan dengan
sumbernya tidak membuktikan apa pun.

# Kenapa urutan operasinya tidak boleh dirapikan

``a + b * (1 - a)`` tidak boleh disederhanakan menjadi ``a + b - a * b``
sekalipun keduanya setara secara aljabar. Pada aritmetika IEEE-754 keduanya
menghasilkan bit yang berbeda, dan perbedaan itulah yang sedang diukur.

.Deckyx
"""

import math

EPS = 1e-9

# ---------------------------------------------------------------------------
# Pembangkit acak
# ---------------------------------------------------------------------------

_TOPENG = 0xFFFFFFFFFFFFFFFF
_GAMMA = 0x9E3779B97F4A7C15
_MIX1 = 0xBF58476D1CE4E5B9
_MIX2 = 0x94D049BB133111EB


class SplitMix64:
    """Pembangkit acak deterministik.

    Dipakai membangkitkan bobot awal jaringan. Benih yang sama wajib
    menghasilkan bobot yang sama persis: pelatihan yang tidak bisa diulang
    tidak bisa dipelajari, dan pembaca yang melihat kurva galat berbeda tiap
    kali halamannya dimuat tidak akan pernah tahu mana yang disebabkan
    perubahan setelan dan mana yang disebabkan keberuntungan.
    """

    __slots__ = ("keadaan",)

    def __init__(self, benih=0):
        self.keadaan = benih & _TOPENG

    def u64(self):
        """Bilangan bulat 64-bit berikutnya."""
        self.keadaan = (self.keadaan + _GAMMA) & _TOPENG
        z = self.keadaan
        z = ((z ^ (z >> 30)) * _MIX1) & _TOPENG
        z = ((z ^ (z >> 27)) * _MIX2) & _TOPENG
        return (z ^ (z >> 31)) & _TOPENG

    def f64(self):
        """Pecahan berikutnya di rentang setengah terbuka ``[0, 1)``.

        Memakai 53 bit teratas, yaitu tepat sebanyak bit mantissa ``float``.
        Mengambil lebih banyak tidak menambah ketelitian; mengambil lebih
        sedikit meninggalkan celah yang tidak pernah terpilih.
        """
        return (self.u64() >> 11) * (1.0 / 9007199254740992.0)

    def rentang(self, lo, hi):
        """Pecahan di rentang tertentu."""
        return lo + self.f64() * (hi - lo)


# ---------------------------------------------------------------------------
# Certainty factor
# ---------------------------------------------------------------------------


def _periksa(v, lo, hi, nama):
    if not math.isfinite(v) or v < lo - EPS or v > hi + EPS:
        raise ValueError("%s harus di rentang %g sampai %g, diberi %r" % (nama, lo, hi, v))
    return min(max(v, lo), hi)


def cf_dari_mb_md(mb, md):
    """``CF = MB - MD``."""
    return _periksa(mb, 0.0, 1.0, "MB") - _periksa(md, 0.0, 1.0, "MD")


def cf_gabung_paralel(cf1, cf2):
    """Menggabungkan dua CF dari bukti berbeda untuk hipotesis yang sama."""
    a = _periksa(cf1, -1.0, 1.0, "CF pertama")
    b = _periksa(cf2, -1.0, 1.0, "CF kedua")
    if a >= 0.0 and b >= 0.0:
        hasil = a + b * (1.0 - a)
    elif a <= 0.0 and b <= 0.0:
        hasil = a + b * (1.0 + a)
    else:
        penyebut = 1.0 - min(abs(a), abs(b))
        # Bukti berlawanan penuh (+1 lawan -1) saling meniadakan.
        hasil = 0.0 if abs(penyebut) < EPS else (a + b) / penyebut
    return min(max(hasil, -1.0), 1.0)


def cf_gabung_berantai(cf_aturan, cf_bukti):
    """CF kesimpulan = CF aturan dikali CF bukti.

    Bukti dengan CF negatif tidak menyalakan aturan, jadi hasilnya nol.
    """
    r = _periksa(cf_aturan, -1.0, 1.0, "CF aturan")
    e = _periksa(cf_bukti, -1.0, 1.0, "CF bukti")
    return min(max(r * max(e, 0.0), -1.0), 1.0)


def cf_premis_dan(a, b):
    """CF gabungan premis yang dihubungkan DAN — diambil nilai terkecil."""
    return min(_periksa(a, -1.0, 1.0, "premis"), _periksa(b, -1.0, 1.0, "premis"))


def cf_premis_atau(a, b):
    """CF gabungan premis yang dihubungkan ATAU — diambil nilai terbesar."""
    return max(_periksa(a, -1.0, 1.0, "premis"), _periksa(b, -1.0, 1.0, "premis"))


# ---------------------------------------------------------------------------
# Bayesian
# ---------------------------------------------------------------------------


def bayes_bukti(prior, kemungkinan_h, kemungkinan_bukan_h):
    """Peluang munculnya bukti, ``P(E)``."""
    p_h = _periksa(prior, 0.0, 1.0, "P(H)")
    p_e_h = _periksa(kemungkinan_h, 0.0, 1.0, "P(E|H)")
    p_e_n = _periksa(kemungkinan_bukan_h, 0.0, 1.0, "P(E|~H)")
    p_nh = 1.0 - p_h
    ev = p_h * p_e_h + p_nh * p_e_n
    if ev < EPS:
        raise ValueError("P(E) nol: posterior tidak terdefinisi")
    return ev


def bayes_posterior(prior, kemungkinan_h, kemungkinan_bukan_h):
    """Posterior ``P(H|E)``."""
    p_h = _periksa(prior, 0.0, 1.0, "P(H)")
    p_e_h = _periksa(kemungkinan_h, 0.0, 1.0, "P(E|H)")
    ev = bayes_bukti(prior, kemungkinan_h, kemungkinan_bukan_h)
    return min(max(p_e_h * p_h / ev, 0.0), 1.0)


def bayes_rasio(kemungkinan_h, kemungkinan_bukan_h):
    """Rasio kemungkinan ``P(E|H) / P(E|~H)``."""
    a = _periksa(kemungkinan_h, 0.0, 1.0, "P(E|H)")
    b = _periksa(kemungkinan_bukan_h, 0.0, 1.0, "P(E|~H)")
    if b < EPS:
        return 0.0 if a < EPS else float("inf")
    return a / b


# ---------------------------------------------------------------------------
# Keanggotaan kabur
# ---------------------------------------------------------------------------


def _batasi01(v):
    return min(max(v, 0.0), 1.0)


def kabur_segitiga(a, b, c, x):
    """Keanggotaan segitiga.

    Puncak diperiksa **sebelum** tepi. Kalau tidak, segitiga berkaki berimpit
    seperti ``(0, 0, 15)`` bernilai nol tepat di tempat ia seharusnya bernilai
    satu — bentuk yang justru paling lazim dipakai di tepi semesta.
    """
    if abs(x - b) < EPS:
        v = 1.0
    elif x <= a or x >= c:
        v = 0.0
    elif x < b:
        v = 1.0 if abs(b - a) < EPS else (x - a) / (b - a)
    elif abs(c - b) < EPS:
        v = 1.0
    else:
        v = (c - x) / (c - b)
    return _batasi01(v)


def kabur_trapesium(a, b, c, d, x):
    """Keanggotaan trapesium; bahu datar diperiksa sebelum tepi."""
    if b <= x <= c:
        v = 1.0
    elif x <= a or x >= d:
        v = 0.0
    elif x < b:
        v = 1.0 if abs(b - a) < EPS else (x - a) / (b - a)
    elif abs(d - c) < EPS:
        v = 1.0
    else:
        v = (d - x) / (d - c)
    return _batasi01(v)


def kabur_gauss(rerata, sigma, x):
    """Kurva Gauss berpusat ``rerata`` dengan lebar ``sigma``."""
    s = EPS if abs(sigma) < EPS else abs(sigma)
    z = (x - rerata) / s
    return _batasi01(math.exp(-0.5 * z * z))


def kabur_sigmoid(a, c, x):
    """Kurva sigmoid dengan kecuraman ``a`` dan titik tengah ``c``."""
    return _batasi01(1.0 / (1.0 + math.exp(-a * (x - c))))


# ---------------------------------------------------------------------------
# Jarak dan ketakmurnian
# ---------------------------------------------------------------------------


def euclidean(a, b):
    """Jarak lurus."""
    jumlah = 0.0
    for i in range(min(len(a), len(b))):
        d = a[i] - b[i]
        jumlah += d * d
    return math.sqrt(jumlah)


def manhattan(a, b):
    """Jumlah selisih tiap sumbu."""
    jumlah = 0.0
    for i in range(min(len(a), len(b))):
        jumlah += abs(a[i] - b[i])
    return jumlah


def chebyshev(a, b):
    """Selisih terbesar di antara semua sumbu."""
    maks = 0.0
    for i in range(min(len(a), len(b))):
        maks = max(maks, abs(a[i] - b[i]))
    return maks


def _cacah(label):
    """Frekuensi tiap label, dikembalikan berurutan menaik.

    Urutan menaik bukan demi kerapian: penjumlahan pecahan tidak asosiatif,
    sehingga urutan yang berbeda menghasilkan bit terakhir yang berbeda.
    Implementasi Rust yang menjadi acuan memakai peta terurut, jadi urutan itu
    bagian dari spesifikasinya.
    """
    jumlah = {}
    for l in label:
        jumlah[l] = jumlah.get(l, 0) + 1
    return [(k, jumlah[k]) for k in sorted(jumlah)]


def entropi(label):
    """Entropi Shannon sebuah sebaran label, dalam bit."""
    if not label:
        return 0.0
    n = float(len(label))
    akum = 0.0
    for _, c in _cacah(label):
        p = c / n
        akum += p * math.log2(p)
    return -akum


def gini(label):
    """Ketakmurnian Gini.

    Berbeda dengan entropi, Gini hanya memakai perkalian dan pengurangan,
    sehingga hasilnya wajib identik bit demi bit di bahasa mana pun.
    """
    if not label:
        return 0.0
    n = float(len(label))
    akum = 0.0
    for _, c in _cacah(label):
        p = c / n
        akum += p * p
    return 1.0 - akum


def perolehan_informasi(nilai, label):
    """Perolehan informasi bila data dipecah menurut sebuah atribut."""
    if len(nilai) != len(label) or not label:
        return 0.0
    sebelum = entropi(label)
    n = float(len(label))
    kelompok = {}
    for v, l in zip(nilai, label):
        kelompok.setdefault(v, []).append(l)
    sesudah = 0.0
    for v in sorted(kelompok):
        g = kelompok[v]
        sesudah += (len(g) / n) * entropi(g)
    return sebelum - sesudah
