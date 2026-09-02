"""Mengadu mesin Python ini terhadap vektor uji yang dihasilkan Rust.

Python adalah implementasi keenam algoritma ini, setelah Rust, Go, PL/SQL
Oracle, Lua, dan Swift. Ditulis dari rumusnya, bukan diterjemahkan dari kode
mana pun: salinan mewarisi seluruh cacat aslinya, sehingga mengadu salinan
dengan sumbernya tidak membuktikan apa pun.

# Kenapa logikanya ada di sini dan bukan di skrip baris perintah

Karena pemeriksaan yang sama dijalankan di dua tempat: CPython saat CI, dan
Brython di dalam peramban pengunjung. Dua salinan logika pemeriksa akan
menyimpang, dan yang menyimpang akan menjadi yang di peramban — yang tidak
pernah dijalankan siapa pun sebelum terbit.

Modul ini tidak menyentuh berkas sama sekali. Isi vektornya diserahkan sebagai
teks oleh pemanggilnya: dari cakram di CPython, dari mesin virtual di peramban.

.Deckyx
"""

from . import fx, inti

#: Berkas vektor yang wajib ada, berikut urutan tampilnya.
#:
#: Ditulis tetap, bukan hasil pemindaian direktori. Berkas yang hilang harus
#: menggagalkan pemeriksaan, bukan diam-diam mengurangi jumlah pernyataan yang
#: diperiksa — dan pemindaian direktori tidak bisa membedakan keduanya.
BERKAS = [
    "bayes.tsv",
    "certainty.tsv",
    "fuzzy_linear.tsv",
    "fuzzy_transcendental.tsv",
    "fx.tsv",
    "ml_entropy.tsv",
    "ml_exact.tsv",
    "ml_gain.tsv",
    "rng.tsv",
]

_h = fx.dari_hex

# Ditulis lewat kode karakter, bukan sebagai escape di dalam untai. Berkas
# ini beberapa kali dihasilkan lewat perkakas yang menafsirkan escape-nya
# sendiri, dan sebuah escape yang berubah menjadi karakter sungguhan di
# tengah untai adalah galat sintaks yang penyebabnya tidak terlihat sama
# sekali di layar.
_CR = chr(13)
_TAB = chr(9)


def _pisah_koma(s):
    return [x for x in s.split(",") if x]


def _periksa_baris(nama, kol, nomor, nilai, nilai_teks):
    """Memeriksa satu baris vektor.

    ``nilai`` membandingkan dua pecahan menurut tingkat keterbandingan berkas
    itu; ``nilai_teks`` membandingkan dua untai apa adanya.
    """
    if nama == "fx.tsv":
        # Dibandingkan sebagai **teks**, bukan sebagai nilai. Membandingkan
        # nilai hasil bolak-balik dengan nilai asalnya adalah membandingkan
        # sesuatu dengan dirinya sendiri: kerusakan yang setangkup di kedua
        # arah — tanda nol negatif yang hilang saat dibaca dan karena itu tidak
        # pernah dituliskan kembali — akan lolos setiap kali. Cacat persis itu
        # pernah lolos di implementasi Lua proyek ini.
        nilai_teks(kol[1], fx.ke_hex(_h(kol[1])), "bolak-balik " + kol[0], nomor)

    elif nama == "rng.tsv":
        benih, indeks = int(kol[0]), int(kol[1])
        r = inti.SplitMix64(benih)
        u = 0
        for _ in range(indeks + 1):
            u = r.u64()
        nilai(_h(kol[2]), fx.dari_bits(u), "next_u64 benih %s indeks %d" % (kol[0], indeks), nomor)
        rf = inti.SplitMix64(benih)
        f = 0.0
        for _ in range(indeks + 1):
            f = rf.f64()
        nilai(_h(kol[3]), f, "next_f64 benih %s indeks %d" % (kol[0], indeks), nomor)

    elif nama == "certainty.tsv":
        a, b = _h(kol[1]), _h(kol[2])
        op = kol[0]
        fn = {
            "parallel": inti.cf_gabung_paralel,
            "sequential": inti.cf_gabung_berantai,
            "and": inti.cf_premis_dan,
            "or": inti.cf_premis_atau,
            "mb_md": inti.cf_dari_mb_md,
        }[op]
        nilai(_h(kol[3]), fn(a, b), "%s(%s, %s)" % (op, kol[1], kol[2]), nomor)

    elif nama == "bayes.tsv":
        prior, lh, lnh = _h(kol[0]), _h(kol[1]), _h(kol[2])
        nilai(_h(kol[3]), inti.bayes_bukti(prior, lh, lnh), "P(E)", nomor)
        nilai(_h(kol[4]), inti.bayes_posterior(prior, lh, lnh), "posterior", nomor)
        nilai(_h(kol[5]), inti.bayes_rasio(lh, lnh), "rasio kemungkinan", nomor)

    elif nama == "fuzzy_linear.tsv":
        p1, p2, p3, p4, x = (_h(kol[i]) for i in range(1, 6))
        dapat = (
            inti.kabur_segitiga(p1, p2, p3, x)
            if kol[0] == "triangular"
            else inti.kabur_trapesium(p1, p2, p3, p4, x)
        )
        nilai(_h(kol[6]), dapat, "%s di x=%s" % (kol[0], kol[5]), nomor)

    elif nama == "fuzzy_transcendental.tsv":
        p1, p2, x = _h(kol[1]), _h(kol[2]), _h(kol[3])
        dapat = (
            inti.kabur_gauss(p1, p2, x)
            if kol[0] == "gaussian"
            else inti.kabur_sigmoid(p1, p2, x)
        )
        nilai(_h(kol[4]), dapat, "%s di x=%s" % (kol[0], kol[3]), nomor)

    elif nama == "ml_exact.tsv":
        if kol[0] == "gini":
            nilai(_h(kol[5]), inti.gini(_pisah_koma(kol[1])), "gini " + kol[1], nomor)
        else:
            a = [_h(kol[1]), _h(kol[2])]
            b = [_h(kol[3]), _h(kol[4])]
            fn = {
                "euclidean": inti.euclidean,
                "manhattan": inti.manhattan,
                "chebyshev": inti.chebyshev,
            }[kol[0]]
            nilai(_h(kol[5]), fn(a, b), kol[0], nomor)

    elif nama == "ml_entropy.tsv":
        nilai(_h(kol[3]), inti.entropi(_pisah_koma(kol[1])), "entropi " + kol[1], nomor)

    elif nama == "ml_gain.tsv":
        label = _pisah_koma(kol[1])
        atribut, _, isi = kol[2].partition("=")
        # Kolom skala memuat entropi sebelum pemecahan, yaitu tempat
        # aritmetikanya sesungguhnya terjadi. Perolehan informasi adalah
        # selisih dua entropi yang hampir sama besar, dan pengurangan seperti
        # itu memperbesar galat relatif berlipat-lipat — sampai 64 kali pada
        # pengukuran proyek pendahulunya. Mengukur toleransinya pada hasil
        # akhir akan menuntut ketepatan yang tidak dimiliki angka mana pun di
        # sini; mengukurnya pada skala masukan adalah pertanyaan yang benar.
        nilai(
            _h(kol[4]),
            inti.perolehan_informasi(_pisah_koma(isi), label),
            "perolehan " + atribut,
            nomor,
            _h(kol[3]),
        )
    else:
        raise ValueError("tidak ada pemeriksa untuk %s" % nama)


class HasilBerkas:
    """Hasil pemeriksaan satu berkas vektor."""

    __slots__ = ("nama", "tingkat", "diperiksa", "gagal", "ulp_maks")

    def __init__(self, nama, tingkat, diperiksa, gagal, ulp_maks):
        self.nama = nama
        self.tingkat = tingkat
        self.diperiksa = diperiksa
        self.gagal = gagal
        self.ulp_maks = ulp_maks

    @property
    def lolos(self):
        return self.gagal == 0


class Ketidakcocokan:
    """Satu pernyataan yang tidak cocok, lengkap dengan pola bit keduanya."""

    __slots__ = ("berkas", "nomor", "konteks", "harap", "dapat", "ulp")

    def __init__(self, berkas, nomor, konteks, harap, dapat, ulp):
        self.berkas = berkas
        self.nomor = nomor
        self.konteks = konteks
        self.harap = harap
        self.dapat = dapat
        self.ulp = ulp


class Laporan:
    """Hasil seluruh pemeriksaan."""

    __slots__ = ("berkas", "ketidakcocokan", "total", "galat_muat", "pancar")

    def __init__(self):
        self.berkas = []
        self.ketidakcocokan = []
        self.total = 0
        self.galat_muat = []
        #: Pola bit tiap pernyataan, hanya terisi bila mode pancar menyala.
        #: Lihat :class:`Bertahap`.
        self.pancar = []

    @property
    def total_gagal(self):
        return sum(b.gagal for b in self.berkas)

    @property
    def lolos(self):
        # Jalan tanpa satu pun pernyataan bukan keberhasilan melainkan tanda
        # vektornya tidak terbaca. Tanpa syarat ``total > 0`` di sini, laporan
        # paling hijau yang mungkin dihasilkan justru laporan yang tidak
        # memeriksa apa pun.
        return not self.galat_muat and self.total > 0 and self.total_gagal == 0


#: Paling banyak ketidakcocokan yang disimpan, supaya laporan gagal tidak
#: berubah menjadi ribuan baris yang tidak dibaca siapa pun.
BATAS_KETIDAKCOCOKAN = 25

#: Nama kolom hasil di berkas vektornya, menurut urutan pelaporannya.
#:
#: Dipakai memancarkan pola bit untuk halaman "Enam bahasa, satu angka" di AI
#: ATLAS, yang memasangkan hasil tiap bahasa lewat kunci (berkas, baris,
#: kolom).
#:
#: Urutannya, bukan nama yang diserahkan tiap pemeriksa. Sebuah baris
#: ``rng.tsv`` selalu melaporkan bilangan bulatnya lebih dulu dan pecahannya
#: kemudian; menambahkan argumen ke seluruh cabang :func:`_periksa_baris`
#: hanya untuk menyebutkan urutan yang sudah tetap itu berarti sembilan tempat
#: baru yang bisa salah tulis.
KOLOM = {
    "fx.tsv": ("hex",),
    "rng.tsv": ("next_u64_hex", "next_f64_hex"),
    "bayes.tsv": ("evidence_hex", "posterior_hex", "likelihood_ratio_hex"),
    "certainty.tsv": ("result_hex",),
    "fuzzy_linear.tsv": ("degree_hex",),
    "fuzzy_transcendental.tsv": ("degree_hex",),
    "ml_exact.tsv": ("result_hex",),
    "ml_entropy.tsv": ("result_hex",),
    "ml_gain.tsv": ("result_hex",),
}


class Bertahap:
    """Pemeriksaan yang bisa dijalankan sepotong-sepotong.

    # Kenapa harus bisa dipotong

    Karena pemeriksaan yang sama dijalankan di dalam peramban, dan di sana ia
    berbagi satu utas dengan tampilan. Diukur di Brython, ketiga ribu tujuh
    ratus sembilan puluh enam pernyataannya memakan sekitar 2,4 detik — dan
    2,4 detik tanpa potongan berarti halaman yang membeku, tombol yang tidak
    bisa ditekan, dan peramban yang menawarkan menutup tab.

    Pemotongannya diukur dalam **baris**, bukan milidetik. Modul ini juga
    berjalan di CPython saat CI, dan CPython tidak punya ``window.performance``
    sementara ``time`` tidak ada di Brython yang dipangkas. Pemanggilnya yang
    tahu jam mana yang tersedia; kelas ini hanya tahu berapa banyak pekerjaan
    yang diminta.
    """

    def __init__(self, muat, berkas=None, pancar=False):
        self.laporan = Laporan()
        # ``pancar`` membuat pola bit tiap pernyataan ikut dikumpulkan di
        # ``laporan.pancar``. Angkanya sama persis dengan yang dibandingkan --
        # nilai yang sama, dari panggilan yang sama -- sehingga tidak mungkin
        # halaman menampilkan pola bit yang tidak pernah diperiksa siapa pun.
        self._pancar = pancar
        self._muat = muat
        # ``berkas is None`` dan ``berkas == []`` sengaja dibedakan. Yang
        # pertama berarti "seluruhnya", yang kedua berarti "tidak satu pun" —
        # dan menyamakan keduanya lewat ``berkas or BERKAS`` membuat permintaan
        # kosong diam-diam berubah menjadi permintaan penuh.
        self._antre = list(BERKAS if berkas is None else berkas)
        self._nama = None
        self._tingkat = None
        self._baris = []
        self._i = 0
        self._cacah = None

        # Jumlah baris seluruhnya dihitung di muka supaya kemajuannya bisa
        # ditampilkan sebagai pecahan, bukan sebagai angka yang naik terus
        # tanpa pengunjung tahu kapan berhentinya.
        self.total_baris = 0
        self.baris_selesai = 0

    @property
    def selesai(self):
        return not self._antre and self._nama is None

    def _buka_berikutnya(self):
        """Menyiapkan berkas berikutnya. Mengembalikan False bila habis."""
        while self._antre:
            nama = self._antre.pop(0)
            try:
                isi = self._muat(nama)
            except Exception as galat:  # noqa: BLE001 - sumbernya bisa apa saja
                self.laporan.galat_muat.append("%s: %s" % (nama, galat))
                continue

            tingkat = None
            baris_isi = []
            for baris in isi.splitlines():
                baris = baris.rstrip(_CR)
                if not baris:
                    continue
                if baris.startswith("#"):
                    komentar = baris[1:].strip()
                    if komentar.startswith("keterbandingan:"):
                        tingkat = fx.Keterbandingan.dari_penanda(
                            komentar[len("keterbandingan:") :]
                        )
                else:
                    baris_isi.append(baris.split(_TAB))

            if tingkat is None:
                self.laporan.galat_muat.append(
                    "%s: tidak menyebutkan tingkat keterbandingan" % nama
                )
                continue

            self._nama = nama
            self._tingkat = tingkat
            self._baris = baris_isi
            self._i = 0
            self._cacah = {"n": 0, "gagal": 0, "ulp": 0}
            self.total_baris += len(baris_isi)
            return True
        return False

    def _tutup_berkas(self):
        c = self._cacah
        self.laporan.total += c["n"]
        self.laporan.berkas.append(
            HasilBerkas(self._nama, self._tingkat.nama, c["n"], c["gagal"], c["ulp"])
        )
        self._nama = None
        self._tingkat = None
        self._baris = []
        self._cacah = None

    def kerjakan(self, batas_baris):
        """Memeriksa sampai ``batas_baris`` baris, lalu kembali.

        Mengembalikan jumlah baris yang benar-benar diperiksa; nol berarti
        seluruhnya sudah selesai.
        """
        dikerjakan = 0
        laporan = self.laporan

        while dikerjakan < batas_baris:
            if self._nama is None and not self._buka_berikutnya():
                break

            tingkat = self._tingkat
            cacah = self._cacah
            nama = self._nama

            # Argumen bawaan mengikat nilai sekarang. Tanpa itu penutupannya
            # akan menunjuk berkas yang sedang aktif saat ia dipanggil, bukan
            # saat ia dibuat — dan setiap berkas akan dinilai dengan tingkat
            # keterbandingan berkas terakhir.
            pancar = self.laporan.pancar if self._pancar else None
            urut = {"k": 0}
            kolom = KOLOM.get(nama, ())

            def catat(dapat_hex, konteks, nomor):
                urut["k"] += 1
                pancar.append(
                    {
                        "berkas": nama,
                        "baris": nomor,
                        "kolom": (
                            kolom[urut["k"] - 1] if urut["k"] <= len(kolom) else "result_hex"
                        ),
                        "hasil_hex": dapat_hex,
                        "konteks": konteks,
                    }
                )

            def nilai(harap, dapat, konteks, nomor, skala=None, _t=tingkat, _c=cacah, _n=nama):
                _c["n"] += 1
                if pancar is not None:
                    catat(fx.ke_hex(dapat), konteks, nomor)
                d = fx.jarak_ulp(harap, dapat)
                if d is not None and d > _c["ulp"]:
                    _c["ulp"] = d
                if not _t.terpenuhi(harap, dapat, skala):
                    _c["gagal"] += 1
                    if len(laporan.ketidakcocokan) < BATAS_KETIDAKCOCOKAN:
                        laporan.ketidakcocokan.append(
                            Ketidakcocokan(
                                _n, nomor, konteks, fx.ke_hex(harap), fx.ke_hex(dapat), d
                            )
                        )

            def nilai_teks(harap, dapat, konteks, nomor, _c=cacah, _n=nama):
                _c["n"] += 1
                if pancar is not None:
                    # ``dapat`` di sini sudah berupa teks heksadesimal, bukan
                    # pecahan: berkas fx memang dibandingkan sebagai teks.
                    catat(dapat, konteks, nomor)
                if harap != dapat:
                    _c["gagal"] += 1
                    if len(laporan.ketidakcocokan) < BATAS_KETIDAKCOCOKAN:
                        laporan.ketidakcocokan.append(
                            Ketidakcocokan(_n, nomor, konteks, harap, dapat, None)
                        )

            sisa = batas_baris - dikerjakan
            akhir = min(self._i + sisa, len(self._baris))
            for i in range(self._i, akhir):
                # Urutannya dihitung per baris: kolom keberapa sebuah nilai
                # dilaporkan hanya berarti di dalam barisnya sendiri.
                urut["k"] = 0
                _periksa_baris(nama, self._baris[i], i + 1, nilai, nilai_teks)
            dikerjakan += akhir - self._i
            self.baris_selesai += akhir - self._i
            self._i = akhir

            if self._i >= len(self._baris):
                self._tutup_berkas()

        return dikerjakan


def jalankan(muat, berkas=None, pancar=False):
    """Menjalankan seluruh pemeriksaan sekaligus.

    ``muat(nama)`` mengembalikan isi berkas vektor sebagai untai, atau
    melempar bila tidak ada. ``pancar`` mengisi ``laporan.pancar``.
    """
    bertahap = Bertahap(muat, berkas, pancar)
    while bertahap.kerjakan(100000):
        pass
    return bertahap.laporan
