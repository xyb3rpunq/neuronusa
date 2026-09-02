"""Menyandi dan membaca setelan halaman dari alamat.

# Kenapa ini modul mesin dan bukan bagian dari antarmuka

Karena isinya memeriksa masukan yang datang dari luar. Setiap nilai di sebuah
alamat ditulis orang lain — pengirim tautan, atau siapa pun yang menempelkan
sesuatu ke bilah alamat. Nilai yang tidak diperiksa akan sampai ke
:class:`~nusa.jaringan.Jaringan` apa adanya: aktivasi yang tidak ada melempar,
jumlah neuron negatif menghasilkan senarai kosong, laju berupa NaN merusak
seluruh bobot dalam satu langkah.

Kode yang memeriksa masukan luar wajib punya uji. Selama ia tinggal di berkas
antarmuka yang mengimpor ``browser``, ia tidak bisa diimpor CPython sama
sekali dan karena itu tidak bisa diuji sama sekali.

.Deckyx
"""

from .jaringan import AKTIVASI, CACAT, DATASET

#: Peta antara nama setelan dan kunci pendeknya di dalam alamat.
#:
#: Dipendekkan supaya alamatnya masih bisa dibaca manusia dan masih muat di
#: satu baris pesan. Kuncinya ditulis tetap, bukan diturunkan dari nama
#: atributnya: mengganti nama sebuah atribut Python tidak boleh diam-diam
#: mematikan setiap tautan yang sudah pernah dibagikan orang.
KUNCI = [
    ("dataset", "d"),
    ("tersembunyi", "h"),
    ("aktivasi", "a"),
    ("benih", "s"),
    ("laju", "l"),
    ("momentum", "m"),
    ("cacat", "c"),
]

#: Batas tiap setelan angka, sepadan dengan penggeser di antarmuka.
#:
#: Ditulis di sini dan bukan di antarmuka supaya batas yang diperiksa dan
#: batas yang bisa digeser tidak pernah menyimpang. Penggeser yang mengizinkan
#: nilai yang ditolak pemeriksa akan menghasilkan tautan yang tidak bisa
#: dibuka kembali oleh pembuatnya sendiri.
BATAS = {
    "tersembunyi": (0, 8),
    "benih": (1, 200),
    "laju": (0.01, 5.0),
    "momentum": (0.0, 0.99),
}


def _bulat(teks, nama):
    kecil, besar = BATAS[nama]
    try:
        v = int(teks)
    except (TypeError, ValueError):
        return None
    return v if kecil <= v <= besar else None


def _pecahan(teks, nama):
    kecil, besar = BATAS[nama]
    try:
        v = float(teks)
    except (TypeError, ValueError):
        return None
    # NaN gagal setiap perbandingan, jadi ia lolos begitu saja dari
    # pemeriksaan rentang yang ditulis sebagai ``if v < kecil: tolak``.
    # Ditulis sebagai "harus di dalam", bukan "tolak yang di luar".
    if not (kecil <= v <= besar):
        return None
    return v


#: Pemeriksa untuk tiap setelan. Kembalikan nilai bersih, atau None bila tolak.
PEMERIKSA = {
    # "sendiri" sah sebagai nama, tetapi datanya tidak pernah ikut ke alamat:
    # empat ratus baris angka tidak muat di sana, dan memaksanya muat akan
    # menghasilkan tautan yang tidak bisa dikirim lewat pesan mana pun.
    # Halaman yang menerimanya jatuh ke XOR, bukan menabrak.
    "dataset": lambda t: t if t in DATASET or t == "sendiri" else None,
    "aktivasi": lambda t: t if t in AKTIVASI else None,
    "cacat": lambda t: t if t in CACAT else None,
    "tersembunyi": lambda t: _bulat(t, "tersembunyi"),
    "benih": lambda t: _bulat(t, "benih"),
    "laju": lambda t: _pecahan(t, "laju"),
    "momentum": lambda t: _pecahan(t, "momentum"),
}


def baca(tanda):
    """Setelan yang sah dari sebuah tanda alamat, sebagai kamus.

    ``tanda`` boleh diawali ``#`` atau tidak.

    Yang tidak sah dibuang diam-diam dan sisanya tetap dipakai. Menolak
    seluruh tautan karena satu nilai keliru akan menghukum pembaca atas
    kesalahan pengirimnya, dan hasilnya halaman kosong alih-alih halaman yang
    hampir benar.
    """
    keluar = {}
    if not tanda:
        return keluar
    if tanda.startswith("#"):
        tanda = tanda[1:]
    if not tanda:
        return keluar

    pendek = {kunci: nama for nama, kunci in KUNCI}
    for bagian in tanda.split("&"):
        kunci, ada_sama_dengan, nilai = bagian.partition("=")
        if not ada_sama_dengan:
            continue
        nama = pendek.get(kunci)
        if nama is None:
            continue
        bersih = PEMERIKSA[nama](nilai)
        if bersih is not None:
            keluar[nama] = bersih
    return keluar


def tulis(setelan, format_pecahan=None):
    """Tanda alamat untuk sekumpulan setelan, tanpa ``#`` di depan.

    ``format_pecahan`` mengubah pecahan menjadi teks; bawaannya memangkas nol
    di belakang supaya alamatnya tetap pendek dan bisa dibaca.
    """
    if format_pecahan is None:
        format_pecahan = _pecahan_ringkas
    bagian = []
    for nama, kunci in KUNCI:
        if nama not in setelan:
            continue
        nilai = setelan[nama]
        teks = format_pecahan(nilai) if isinstance(nilai, float) else str(nilai)
        bagian.append("%s=%s" % (kunci, teks))
    return "&".join(bagian)


def _pecahan_ringkas(v):
    teks = format(float(v), ".4f")
    if "." in teks:
        teks = teks.rstrip("0").rstrip(".")
    return teks or "0"
