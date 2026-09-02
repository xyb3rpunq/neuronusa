"""Pertukaran bilangan pecahan secara bit-eksak.

# Kenapa modul ini ada

Algoritma di paket ini sudah pernah ditulis lima kali di tiga proyek lain —
Rust, Go, PL/SQL, Lua, dan Swift — dan kelimanya diadu memakai berkas vektor
yang sama. Implementasi Python ini menjadi yang keenam, dan perbandingan itu
hanya bermakna kalau angkanya berpindah tanpa berubah sedikit pun.

Desimal tidak memenuhi syarat itu. Pengukuran pada proyek pendahulunya
menemukan sebuah pengurai desimal yang salah membulat sebesar 1 ULP pada 27.548
dari 200.000 nilai uji. Menulis ``0.42000000000000004`` lalu membacanya kembali
bisa menghasilkan ``0.42`` — angka yang berbeda.

# Catatan Brython

Modul ini berjalan di dua tempat: CPython saat uji dan konformansi, dan Brython
di dalam peramban. Karena itu ia **hanya** memakai ``math``, dan tidak satu pun
modul lain.

Bentuk pertamanya memakai ``struct``. Itu ditinggalkan bukan karena salah,
melainkan karena harganya: ``struct`` di Brython menarik ``_struct``, yang
menarik ``re`` — mesin ekspresi reguler yang ditulis dalam Python — dan
seluruhnya hanya tersedia lewat berkas pustaka standar berukuran 4,6 MB. Empat
setengah megabyte untuk satu panggilan pengemasan bilangan, pada halaman yang
justru dituntut tidak boleh berat.

Penggantinya menyandi IEEE-754 biner-64 langsung dengan ``frexp`` dan
``ldexp``. Keduanya penskalaan pangkat dua, jadi tidak ada satu pun pembulatan
yang terjadi di sepanjang jalannya — dan 3.796 pernyataan konformansi terhadap
vektor Rust yang membuktikannya, bukan alasan di paragraf ini.

Jangan menambahkan ``numpy`` atau ``decimal`` di sini — keduanya tidak ada di
peramban, dan kegagalannya baru terlihat saat halamannya dibuka.

.Deckyx
"""

import math

#: Panjang representasi heksadesimal sebuah pecahan: 16 digit.
PANJANG_HEX = 16

#: Toleransi bawaan untuk perhitungan yang menyentuh fungsi transendental.
#:
#: IEEE-754 hanya mewajibkan penjumlahan, pengurangan, perkalian, pembagian,
#: akar kuadrat, dan perbandingan dibulatkan dengan benar. ``exp``, ``log``,
#: dan ``pow`` tidak termasuk.
ULP_TRANSENDENTAL = 4


#: Pola bit NaN tenang baku. Lihat catatan di :func:`bits`.
NAN_BAKU = 0x7FF8000000000000

#: Pangkas terbesar yang aman untuk satu kali penskalaan pangkat dua.
#:
#: Rentang pangkat sebuah ``float`` binary64 adalah −1074 sampai 1023, jadi
#: penskalaan sejauh 1074 tahap dibutuhkan untuk memindahkan subnormal terkecil
#: menjadi bilangan bulat. CPython menanganinya dalam satu langkah; Brython
#: tidak.
#:
#: Brython menerjemahkan ``ldexp(x, n)`` menjadi perkalian dengan ``2**n``, dan
#: ``2**1074`` sendiri sudah tak hingga sebagai ``float``. Hasilnya
#: ``OverflowError`` — bukan angka yang salah, melainkan kegagalan terang-
#: terangan, dan hanya di peramban.
#:
#: Cacat ini tidak ditemukan uji mana pun di CPython, karena di CPython tidak
#: ada cacatnya. Yang menemukannya adalah pemeriksaan konformansi yang
#: dijalankan di dalam peramban, pada baris ``subnormal`` di ``fx.tsv``.
_PANGKAS_SKALA = 500

_TOPENG64 = 0xFFFFFFFFFFFFFFFF
_TOPENG_MANTISSA = 0x000FFFFFFFFFFFFF
_TERSIRAT = 1 << 52


def _skala(x, n):
    """``x * 2**n``, dipecah menjadi beberapa langkah bila ``n`` terlalu besar.

    Setara ``math.ldexp(x, n)`` dan tepat sama hasilnya: penskalaan pangkat dua
    tidak membulatkan apa pun selama hasil antaranya tidak meluap atau menjadi
    subnormal — dan pemecahan inilah yang menjamin keduanya tidak terjadi.
    Alasan lengkapnya ada di :data:`_PANGKAS_SKALA`.
    """
    while n > _PANGKAS_SKALA:
        x = math.ldexp(x, _PANGKAS_SKALA)
        n -= _PANGKAS_SKALA
    while n < -_PANGKAS_SKALA:
        x = math.ldexp(x, -_PANGKAS_SKALA)
        n += _PANGKAS_SKALA
    return math.ldexp(x, n)


def bits(x):
    """Pola bit sebuah pecahan sebagai bilangan bulat tak bertanda 64-bit.

    Disandi langsung alih-alih lewat ``struct``; alasannya ada di kepala modul.

    Satu batasan yang disengaja: seluruh NaN disandi menjadi satu pola tenang
    baku, sehingga muatan dan tanda NaN tidak terbawa. Itu bukan kelalaian
    melainkan pilihan — Brython menjalankan pecahan di atas ``Number``
    JavaScript, yang tidak menyediakan cara membaca bit tanda sebuah NaN sama
    sekali. Menyimpan tanda NaN di CPython lalu kehilangannya di peramban akan
    menghasilkan dua implementasi yang tidak sepakat, dan itu jauh lebih buruk
    daripada satu implementasi yang tidak sepakat dengan dirinya sendiri secara
    terbuka. Seluruh vektor uji yang ada memakai NaN positif.
    """
    x = float(x)
    if x != x:
        return NAN_BAKU
    if x == 0.0:
        # ``x < 0`` tidak berlaku untuk nol negatif: −0.0 < 0.0 bernilai salah.
        # Tanpa ``copysign`` di sini, −0.0 akan disandi sebagai +0.0 — persis
        # cacat yang pernah lolos di implementasi Lua karena pemeriksanya
        # membandingkan sebuah nilai dengan hasil bolak-baliknya sendiri.
        return 0x8000000000000000 if math.copysign(1.0, x) < 0.0 else 0
    tanda = 0
    if x < 0.0:
        tanda = 0x8000000000000000
        x = -x
    if x == float("inf"):
        return tanda | 0x7FF0000000000000
    mantissa, pangkat = math.frexp(x)  # x == mantissa * 2**pangkat, 0,5 ≤ m < 1
    bidang = pangkat - 1 + 1023
    if bidang <= 0:
        # Subnormal: nilainya pecahan × 2⁻¹⁰⁷⁴ tanpa bit tersirat.
        return tanda | int(_skala(x, 1074))
    # ``ldexp(mantissa, 53)`` jatuh di ``[2⁵², 2⁵³)`` dan bulat persis, karena
    # mantissa sebuah binary64 memang tidak pernah lebih dari 53 bit.
    return tanda | (bidang << 52) | (int(_skala(mantissa, 53)) - _TERSIRAT)


def dari_bits(b):
    """Pecahan dari pola bitnya."""
    b &= _TOPENG64
    negatif = (b >> 63) != 0
    bidang = (b >> 52) & 0x7FF
    pecahan = b & _TOPENG_MANTISSA

    if bidang == 0x7FF:
        if pecahan:
            return float("nan")
        return float("-inf") if negatif else float("inf")

    if bidang == 0:
        nilai = _skala(float(pecahan), -1074)
    else:
        nilai = _skala(float(pecahan + _TERSIRAT), bidang - 1075)

    # ``copysign``, bukan ``-nilai``: pola bit 0x8000000000000000 harus kembali
    # menjadi −0.0, dan mengalikan nol dengan minus satu tidak menjaminnya di
    # setiap penerjemah.
    return math.copysign(nilai, -1.0 if negatif else 1.0)


def ke_hex(x):
    """Mengubah pecahan menjadi 16 digit heksadesimal huruf kecil.

    Memakai pola bit alih-alih ``float.hex()``: yang terakhir menghasilkan
    bentuk seperti ``0x1.999999999999ap-4`` yang benar tetapi bukan pola bit,
    dan tidak sepadan dengan kelima implementasi lain.
    """
    return "%016x" % bits(x)


def dari_hex(teks):
    """Membaca pecahan dari 16 digit heksadesimal.

    Menolak panjang yang salah alih-alih diam-diam menghasilkan angka lain:
    teks 14 digit adalah pola bit yang sah, hanya bukan yang dimaksud.
    """
    t = teks.strip()
    if len(t) != PANJANG_HEX:
        raise ValueError("panjang harus %d digit, diberi %d" % (PANJANG_HEX, len(t)))
    try:
        b = int(t, 16)
    except ValueError:
        raise ValueError("bukan digit heksadesimal: %r" % t) from None
    return dari_bits(b)


def sama_bit(a, b):
    """Apakah dua nilai identik pada tingkat bit, dengan NaN dianggap sama.

    Perbandingan ``==`` biasa menyatakan NaN tidak sama dengan dirinya sendiri,
    padahal untuk mengadu dua implementasi kita justru ingin "sama-sama
    menghasilkan NaN" dinilai lolos.
    """
    if math.isnan(a) and math.isnan(b):
        return True
    return bits(a) == bits(b)


def _kunci_urut(x):
    """Kunci terurut monoton dari pola bit.

    Pola bit dibaca sebagai bilangan bertanda, lalu yang negatif dicerminkan
    sehingga urutan bilangan bulatnya sepadan dengan urutan pecahannya.
    """
    b = bits(x)
    if b & 0x8000000000000000:
        # Nilai negatif: dicerminkan terhadap batas bawah bilangan bertanda.
        return -(b & 0x7FFFFFFFFFFFFFFF)
    return b


def jarak_ulp(a, b):
    """Jarak dua pecahan dalam satuan ULP, atau ``None`` bila tidak terdefinisi."""
    if math.isnan(a) or math.isnan(b):
        return None
    if a == b:
        return 0
    if math.isinf(a) or math.isinf(b):
        return None
    return abs(_kunci_urut(a) - _kunci_urut(b))


def langkah_ulp(x):
    """Jarak antara ``x`` dan pecahan berikutnya yang lebih besar nilai mutlaknya.

    Dipakai untuk menyatakan toleransi pada skala tempat aritmetikanya terjadi,
    bukan pada hasil akhirnya. Satu ULP pada 1024 seribu kali lebih besar
    daripada satu ULP pada 1.
    """
    if math.isnan(x) or math.isinf(x):
        return float("nan")
    a = abs(x)
    if a == 0.0:
        # Nol tidak punya ULP yang bermakna; dipakai bilangan subnormal
        # terkecil, yaitu langkah sesungguhnya dari nol.
        return dari_bits(1)
    return dari_bits(bits(a) + 1) - a


class Keterbandingan:
    """Seberapa jauh sebuah perhitungan bisa dituntut sama antarbahasa.

    Menyamakan hasil lintas bahasa hanya masuk akal bila targetnya ditetapkan
    lebih dulu. Menuntut yang mustahil hanya menghasilkan uji yang gagal
    berselang-seling tanpa ada yang benar-benar salah.
    """

    __slots__ = ("nama", "maks_ulp", "sifat_saja", "pakai_skala")

    def __init__(self, nama, maks_ulp=0, sifat_saja=False, pakai_skala=False):
        self.nama = nama
        self.maks_ulp = maks_ulp
        self.sifat_saja = sifat_saja
        self.pakai_skala = pakai_skala

    @staticmethod
    def dari_penanda(teks):
        """Menguraikan penanda dari kepala berkas vektor, atau ``None``."""
        t = teks.strip()
        if t == "BitExact":
            return Keterbandingan(t, 0)
        if t == "PropertyOnly":
            return Keterbandingan(t, 0, sifat_saja=True)
        for awalan, berskala in (("NearlyEqual", False), ("CancellingDifference", True)):
            if t.startswith(awalan + "(") and t.endswith(")"):
                isi = t[len(awalan) + 1 : -1]
                if isi.isdigit():
                    return Keterbandingan(t, int(isi), pakai_skala=berskala)
        return None

    def terpenuhi(self, a, b, skala=None):
        """Apakah dua nilai memenuhi tingkat keterbandingan ini.

        Pada tingkat bit-eksak yang dituntut adalah kesamaan **pola bit**, bukan
        jarak ULP nol. Keduanya terlihat sama tetapi tidak sama: IEEE-754
        menyatakan ``0.0 == -0.0`` bernilai benar sehingga jaraknya nol, padahal
        pola bitnya berbeda dan menyebar berbeda pula.
        """
        if self.sifat_saja:
            return True
        if sama_bit(a, b):
            return True
        if self.pakai_skala:
            # Tingkat berskala menuntut skala. Tanpa skala yang dikembalikan
            # adalah pemeriksaan paling ketat, bukan paling longgar: pemanggil
            # yang lupa memberinya melihat kegagalan, bukan kelolosan palsu.
            if skala is None or not math.isfinite(skala):
                return False
            if not (math.isfinite(a) and math.isfinite(b)):
                return False
            return abs(a - b) <= self.maks_ulp * langkah_ulp(skala)
        if self.maks_ulp == 0:
            return False
        d = jarak_ulp(a, b)
        return d is not None and d <= self.maks_ulp
