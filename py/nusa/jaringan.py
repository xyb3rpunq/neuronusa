"""Jaringan syaraf tiruan dengan gradien yang bisa dilihat dan diperiksa.

# Kenapa modul ini ada, padahal proyek lain sudah punya jaringan syaraf

Karena yang ditampilkan di sana adalah kurva galat, dan kurva galat tidak
membuktikan apa pun. Jaringan yang gradiennya salah tetap sering "belajar" —
hanya lebih lambat dan berhenti di tempat yang keliru — dan kurvanya tetap
terlihat menurun dengan meyakinkan.

Yang membedakan modul ini: **gradiennya bisa dilihat satu per satu, dan bisa
dibuktikan benar**. :func:`periksa_gradien` menghitung ulang setiap turunan
dengan selisih hingga, lalu melaporkan galat relatifnya per bobot. Itu satu-
satunya cara memisahkan perambatan balik yang benar dari yang kebetulan
bekerja.

# Catatan Brython

Seluruh isi berkas ini berjalan di peramban. Karena itu ia memakai daftar Python
biasa, bukan ``numpy`` yang tidak tersedia di sana. Ukuran jaringannya sengaja
kecil — beberapa lusin bobot — supaya satu langkah pelatihan tetap selesai
dalam hitungan milidetik meski dijalankan penerjemah di atas JavaScript.

.Deckyx
"""

import math

from .inti import SplitMix64

# Diambil sekali di sini, bukan dicari lewat ``math.`` di dalam perulangan.
#
# Di CPython selisihnya tidak berarti. Di Brython terukur: satu pencarian
# atribut ~1,6 mikrodetik dan satu pemanggilan fungsi Python ~1,2 mikrodetik,
# sementara aritmetikanya sendiri hampir gratis. Pada bidang keputusan
# 26 × 26 dengan empat neuron tersembunyi itu berarti ribuan pencarian per
# gambar — dan gambarnya digambar ulang beberapa kali per detik.
_exp = math.exp
_tanh = math.tanh
_sqrt = math.sqrt

# ---------------------------------------------------------------------------
# Fungsi aktivasi
# ---------------------------------------------------------------------------


def _sigmoid(x):
    # Dipisah menurut tanda agar ``exp`` tidak pernah meluap. Bentuk naif
    # ``1/(1+exp(-x))`` menghasilkan inf untuk x sangat negatif, dan inf yang
    # muncul di tengah pelatihan menyebar menjadi NaN di seluruh bobot.
    if x >= 0.0:
        return 1.0 / (1.0 + _exp(-x))
    e = _exp(x)
    return e / (1.0 + e)


def _turunan_sigmoid(y):
    # Diturunkan dari keluarannya, bukan dari masukannya: ``σ'(x) = σ(x)(1−σ(x))``.
    # Menghitung ulang σ(x) di sini akan memanggil ``exp`` dua kali per bobot
    # tanpa alasan.
    return y * (1.0 - y)


def _turunan_tanh(y):
    return 1.0 - y * y


def _relu(x):
    return x if x > 0.0 else 0.0


def _turunan_relu(y):
    # Turunan di titik nol tidak terdefinisi secara matematis. Dipilih nol,
    # bukan satu, karena itu yang membuat neuron yang sudah mati tetap mati
    # alih-alih berdenyut oleh derau numerik.
    return 1.0 if y > 0.0 else 0.0


def _linear(x):
    return x


def _turunan_linear(_y):
    return 1.0


#: Aktivasi berikut turunannya.
#:
#: ``tanh`` memakai ``math.tanh`` langsung, bukan pembungkus ``def _tanh(x):
#: return math.tanh(x)`` seperti bentuk pertamanya. Pembungkus itu tidak
#: mengubah hasilnya sedikit pun — ia hanya menambah satu pemanggilan fungsi
#: Python di setiap neuron, di setiap titik, di setiap gambar.
AKTIVASI = {
    "sigmoid": (_sigmoid, _turunan_sigmoid),
    "tanh": (_tanh, _turunan_tanh),
    "relu": (_relu, _turunan_relu),
    "linear": (_linear, _turunan_linear),
}


# ---------------------------------------------------------------------------
# Jaringan
# ---------------------------------------------------------------------------


class Jaringan:
    """Jaringan syaraf maju berlapis, dilatih dengan perambatan balik.

    ``ukuran`` adalah daftar jumlah neuron tiap lapis, termasuk masukan dan
    keluaran. ``[2, 4, 1]`` berarti dua masukan, satu lapis tersembunyi berisi
    empat neuron, dan satu keluaran.
    """

    def __init__(self, ukuran, aktivasi="tanh", benih=42):
        if len(ukuran) < 2:
            raise ValueError("jaringan perlu minimal lapis masukan dan keluaran")
        if aktivasi not in AKTIVASI:
            raise ValueError("aktivasi tidak dikenal: %r" % aktivasi)

        self.ukuran = list(ukuran)
        self.nama_aktivasi = aktivasi
        self.f, self.df = AKTIVASI[aktivasi]
        # Lapis keluaran selalu sigmoid: keluarannya ditafsirkan sebagai
        # peluang kelas, dan aktivasi yang bisa negatif membuat tafsir itu
        # tidak berlaku.
        self.f_keluaran, self.df_keluaran = AKTIVASI["sigmoid"]
        self.benih = benih
        self.acak_ulang(benih)

    # -- bobot --------------------------------------------------------------

    def acak_ulang(self, benih=None):
        """Mengisi ulang bobot dengan nilai acak yang deterministik.

        Memakai penskalaan Xavier: rentangnya menyempit seiring bertambahnya
        masukan tiap neuron. Tanpa itu, jumlah berbobot di lapis lebar langsung
        jatuh di daerah datar sigmoid, turunannya nyaris nol, dan jaringannya
        praktis tidak pernah mulai belajar.
        """
        if benih is not None:
            self.benih = benih
        r = SplitMix64(self.benih)
        self.bobot = []
        self.bias = []
        for i in range(len(self.ukuran) - 1):
            masuk = self.ukuran[i]
            keluar = self.ukuran[i + 1]
            batas = _sqrt(6.0 / (masuk + keluar))
            self.bobot.append(
                [[r.rentang(-batas, batas) for _ in range(masuk)] for _ in range(keluar)]
            )
            self.bias.append([0.0 for _ in range(keluar)])

    def jumlah_parameter(self):
        """Banyaknya bobot dan bias yang dilatih."""
        n = 0
        for w in self.bobot:
            n += len(w) * len(w[0])
        for b in self.bias:
            n += len(b)
        return n

    # -- maju ---------------------------------------------------------------

    def maju(self, x):
        """Menjalankan jaringan dan mengembalikan keluaran tiap lapis.

        Keluaran antara ikut dikembalikan karena perambatan balik
        membutuhkannya. Menghitungnya ulang saat mundur akan menggandakan
        seluruh biaya pelatihan tanpa alasan.
        """
        aktif = [list(x)]
        akhir = len(self.bobot) - 1
        for lap in range(len(self.bobot)):
            f = self.f_keluaran if lap == akhir else self.f
            sebelum = aktif[-1]
            keluar = []
            for j, baris in enumerate(self.bobot[lap]):
                jumlah = self.bias[lap][j]
                for k, w in enumerate(baris):
                    jumlah += w * sebelum[k]
                keluar.append(f(jumlah))
            aktif.append(keluar)
        return aktif

    def ramal(self, x):
        """Keluaran akhir jaringan untuk satu masukan."""
        return self.maju(x)[-1]

    def bidang_keputusan(self, kisi):
        """Keluaran jaringan pada kisi ``kisi`` × ``kisi`` di bidang satuan.

        Hasilnya senarai datar sepanjang ``kisi * kisi``, disusun baris demi
        baris dari ``y = 0`` ke ``y = 1``, tiap baris dari ``x = 0`` ke
        ``x = 1``. Titik yang dihitung adalah titik tengah tiap petak.

        # Kenapa ini ada dan bukan sekadar memanggil :meth:`ramal` berulang

        Karena memanggilnya berulang **memang** yang dilakukan bentuk pertama,
        dan pengukuran di peramban memberi 606 milidetik untuk satu gambar —
        cukup lama untuk membuat setiap langkah pelatihan tersendat terlihat.
        Biayanya bukan aritmetikanya melainkan tata cara Python di sekelilingnya:
        satu pemanggilan fungsi, satu senarai masukan, dan satu senarai keluaran
        per lapis, dikalikan ratusan titik.

        Yang dimanfaatkan di sini: masukannya selalu dua, dan pada kisi teratur
        suku ``w₀·x`` hanya punya ``kisi`` nilai berbeda — begitu pula ``w₁·y``.
        Keduanya dihitung sekali lalu dipakai ulang, sehingga perkalian di lapis
        pertama turun dari ``kisi² × 2`` menjadi ``kisi × 2``.

        # Kenapa urutan penjumlahannya ditiru persis

        ``maju`` menjumlahkan mulai dari bias lalu menambahkan tiap suku sesuai
        urutan masukan. Bentuk di sini menghitung ``(bias + w₀x) + w₁y`` —
        urutan yang sama persis, sehingga hasilnya sama sampai ke bit terakhir.
        Merapikannya menjadi ``w₀x + w₁y + bias`` akan menghasilkan pembulatan
        yang berbeda, dan gambar yang tidak lagi sepadan dengan angka yang
        ditampilkan di sebelahnya. Uji ``test_bidang_keputusan_sama_persis``
        menahannya tetap begitu.
        """
        if self.ukuran[0] != 2:
            raise ValueError("bidang keputusan hanya untuk jaringan dua masukan")
        if kisi < 1:
            raise ValueError("kisi harus positif")

        titik = [(i + 0.5) / kisi for i in range(kisi)]
        akhir = len(self.bobot) - 1
        cacah = kisi * kisi

        # Lapis pertama, dihitung neuron demi neuron.
        #
        # ``bsx`` menyimpan ``bias + w0*x`` untuk tiap kolom, ``sy`` menyimpan
        # ``w1*y`` untuk tiap baris. Perulangan dalamnya karena itu tinggal
        # satu penjumlahan dan satu aktivasi per titik — dan urutannya,
        # ``(bias + w0*x) + w1*y``, sama persis dengan urutan di :meth:`maju`.
        w0 = self.bobot[0]
        b0 = self.bias[0]
        f0 = self.f_keluaran if akhir == 0 else self.f
        lapisan = []
        for j, baris in enumerate(w0):
            bsx = [b0[j] + baris[0] * x for x in titik]
            sy = [baris[1] * y for y in titik]
            kolom = []
            tambah = kolom.append
            for y in sy:
                for v in bsx:
                    tambah(f0(v + y))
            lapisan.append(kolom)

        # Lapis berikutnya, tetap neuron demi neuron dan bukan titik demi
        # titik: menukar urutan perulangannya memindahkan seluruh pencarian
        # bobot ke luar perulangan terdalam.
        for lap in range(1, len(self.bobot)):
            f = self.f_keluaran if lap == akhir else self.f
            bobot_lap = self.bobot[lap]
            bias_lap = self.bias[lap]
            baru = []
            for j, baris in enumerate(bobot_lap):
                bj = bias_lap[j]
                # Bobot dipasangkan dengan senarai aktivasi sumbernya sekali
                # saja; tanpa ini keduanya dicari ulang di tiap titik.
                pasangan = list(zip(baris, lapisan))
                kolom = []
                tambah = kolom.append
                for p in range(cacah):
                    jumlah = bj
                    for w, sumber in pasangan:
                        jumlah += w * sumber[p]
                    tambah(f(jumlah))
                baru.append(kolom)
            lapisan = baru

        return lapisan[0]

    # -- galat --------------------------------------------------------------

    def galat(self, data):
        """Galat kuadrat rata-rata pada seluruh data.

        ``data`` berupa daftar pasangan ``(masukan, sasaran)``.
        """
        if not data:
            return 0.0
        jumlah = 0.0
        for x, t in data:
            y = self.ramal(x)
            for j in range(len(t)):
                d = y[j] - t[j]
                jumlah += d * d
        return jumlah / (2.0 * len(data))

    # -- mundur -------------------------------------------------------------

    def gradien(self, data):
        """Gradien galat terhadap setiap bobot dan bias.

        Dikembalikan dalam bentuk yang sama dengan ``self.bobot`` dan
        ``self.bias``, sehingga bisa dibandingkan berdampingan dengan gradien
        numerik.
        """
        gw = [[[0.0] * len(baris) for baris in lap] for lap in self.bobot]
        gb = [[0.0] * len(lap) for lap in self.bias]
        if not data:
            return gw, gb

        akhir = len(self.bobot) - 1
        for x, t in data:
            aktif = self.maju(x)

            # Delta lapis keluaran: turunan galat kuadrat dikali turunan
            # aktivasinya. Inilah satu-satunya tempat sasaran ikut dihitung.
            keluaran = aktif[-1]
            delta = [
                (keluaran[j] - t[j]) * self.df_keluaran(keluaran[j])
                for j in range(len(keluaran))
            ]

            for lap in range(akhir, -1, -1):
                sebelum = aktif[lap]
                for j in range(len(self.bobot[lap])):
                    gb[lap][j] += delta[j]
                    for k in range(len(self.bobot[lap][j])):
                        gw[lap][j][k] += delta[j] * sebelum[k]

                if lap > 0:
                    # Delta lapis sebelumnya: bobot yang sama dipakai mundur,
                    # dan itulah seluruh gagasan perambatan balik.
                    baru = []
                    for k in range(len(sebelum)):
                        jumlah = 0.0
                        for j in range(len(self.bobot[lap])):
                            jumlah += self.bobot[lap][j][k] * delta[j]
                        baru.append(jumlah * self.df(sebelum[k]))
                    delta = baru

        n = float(len(data))
        for lap in range(len(gw)):
            for j in range(len(gw[lap])):
                gb[lap][j] /= n
                for k in range(len(gw[lap][j])):
                    gw[lap][j][k] /= n
        return gw, gb

    def telusuri(self, x, sasaran):
        """Satu perambatan maju dan balik, dengan seluruh nilai antaranya.

        Mengembalikan jumlah berbobot sebelum aktivasi, keluaran tiap lapis,
        delta tiap lapis, dan gradien tiap bobot — untuk **satu** contoh.

        # Kenapa terpisah dari :meth:`gradien`

        Karena keduanya menjawab pertanyaan berbeda. :meth:`gradien` menjawab
        "ke arah mana bobotnya harus digeser", dan untuk itu nilai antaranya
        adalah sampah yang dibuang begitu terpakai. Fungsi ini menjawab
        "kenapa", dan untuk itu justru nilai antaranya yang penting.

        Menyatukan keduanya akan membuat pelatihan menyimpan dan membuang
        selusin senarai per contoh per epoch, demi tampilan yang hanya dilihat
        satu contoh sekali waktu.

        Hasilnya wajib sama persis dengan :meth:`gradien` atas data satu
        contoh; ``test_telusuri_sama_dengan_gradien`` menahannya tetap begitu.
        """
        akhir = len(self.bobot) - 1

        pra = []
        aktif = [list(x)]
        for lap in range(len(self.bobot)):
            f = self.f_keluaran if lap == akhir else self.f
            sebelum = aktif[-1]
            jumlah_lapis = []
            keluar = []
            for j, baris in enumerate(self.bobot[lap]):
                jumlah = self.bias[lap][j]
                for k, w in enumerate(baris):
                    jumlah += w * sebelum[k]
                jumlah_lapis.append(jumlah)
                keluar.append(f(jumlah))
            pra.append(jumlah_lapis)
            aktif.append(keluar)

        keluaran = aktif[-1]
        delta = [
            (keluaran[j] - sasaran[j]) * self.df_keluaran(keluaran[j])
            for j in range(len(keluaran))
        ]

        # Disusun dari belakang lalu dibalik, supaya indeksnya sepadan dengan
        # ``self.bobot`` alih-alih terbalik terhadapnya.
        delta_lapis = [None] * len(self.bobot)
        gw = [[[0.0] * len(baris) for baris in lap] for lap in self.bobot]
        gb = [[0.0] * len(lap) for lap in self.bias]

        for lap in range(akhir, -1, -1):
            delta_lapis[lap] = list(delta)
            sebelum = aktif[lap]
            for j in range(len(self.bobot[lap])):
                # Ditambahkan ke nol, bukan diisikan langsung.
                #
                # Kelihatannya sama; tidak sama. ``gradien`` menjumlahkan
                # seluruh contoh mulai dari 0,0, jadi hasil yang kebetulan
                # −0,0 di sana selalu menjadi ``0.0 + (-0.0)`` — yaitu +0,0.
                # Mengisikannya langsung di sini menyimpan −0,0 apa adanya,
                # dan kedua fungsi lalu melaporkan pola bit berbeda untuk
                # bilangan yang tampak sama di layar.
                #
                # Enam dari tujuh belas parameter pada jaringan XOR bawaan
                # kena persis ini. Tanpa penjumlahan itu, tabel di halaman
                # akan memperlihatkan "-0" di sebelah "0" tanpa penjelasan.
                gb[lap][j] = 0.0 + delta[j]
                for k in range(len(self.bobot[lap][j])):
                    gw[lap][j][k] = 0.0 + delta[j] * sebelum[k]

            if lap > 0:
                baru = []
                for k in range(len(sebelum)):
                    jumlah = 0.0
                    for j in range(len(self.bobot[lap])):
                        jumlah += self.bobot[lap][j][k] * delta[j]
                    baru.append(jumlah * self.df(sebelum[k]))
                delta = baru

        galat = 0.0
        for j in range(len(sasaran)):
            d = keluaran[j] - sasaran[j]
            galat += d * d
        galat /= 2.0

        return {
            "aktivasi": aktif,
            "pra": pra,
            "delta": delta_lapis,
            "gradien_w": gw,
            "gradien_b": gb,
            "keluaran": keluaran,
            "galat": galat,
        }

    # -- pelatihan ----------------------------------------------------------

    def langkah(self, data, laju=0.5, momentum=0.0, hitung_galat=True):
        """Satu langkah pelatihan penuh.

        Mengembalikan galat sebelum langkah, atau ``None`` bila
        ``hitung_galat`` dimatikan.

        Parameter itu ada karena menghitung galat menuntut satu perambatan maju
        penuh atas seluruh data — pekerjaan yang sama besarnya dengan seperempat
        langkah pelatihan itu sendiri. Gelang pelatihan di halaman ini
        menjalankan puluhan langkah di antara dua penggambaran dan hanya
        memerlukan galat yang terakhir; membuang sisanya berarti membuang
        seperempat waktu tanpa satu pun angka yang berubah.
        """
        if not hasattr(self, "_kecepatan_w") or self._kecepatan_w is None:
            self.reset_momentum()

        sebelum = self.galat(data) if hitung_galat else None
        gw, gb = self.gradien(data)
        for lap in range(len(self.bobot)):
            for j in range(len(self.bobot[lap])):
                self._kecepatan_b[lap][j] = (
                    momentum * self._kecepatan_b[lap][j] - laju * gb[lap][j]
                )
                self.bias[lap][j] += self._kecepatan_b[lap][j]
                for k in range(len(self.bobot[lap][j])):
                    self._kecepatan_w[lap][j][k] = (
                        momentum * self._kecepatan_w[lap][j][k] - laju * gw[lap][j][k]
                    )
                    self.bobot[lap][j][k] += self._kecepatan_w[lap][j][k]
        return sebelum

    def reset_momentum(self):
        """Mengosongkan penyangga momentum.

        Wajib dipanggil setelah bobotnya diganti dari luar. Momentum lama yang
        tertinggal akan mendorong bobot baru ke arah yang tidak ada
        hubungannya, dan gejalanya terlihat seperti pelatihan yang tiba-tiba
        divergen tanpa sebab.
        """
        self._kecepatan_w = [[[0.0] * len(b) for b in lap] for lap in self.bobot]
        self._kecepatan_b = [[0.0] * len(lap) for lap in self.bias]

    def laju_efektif(self, laju, momentum):
        """Laju belajar setelah diperbesar momentum.

        Momentum menjumlahkan langkah sebelumnya, sehingga langkah tunaknya
        adalah ``laju / (1 - momentum)``. Nilai 0,5 dengan momentum 0,9 setara
        dengan laju 5 tanpa momentum — dan itulah sebabnya menyalakan momentum
        pada laju yang sudah besar hampir selalu membuat pelatihannya meledak.
        """
        if momentum >= 1.0:
            return float("inf")
        return laju / (1.0 - momentum)

    # -- pemeriksaan gradien ------------------------------------------------

    def periksa_gradien(self, data, h=1e-5):
        """Membandingkan gradien perambatan balik dengan selisih hingga.

        Inilah uji yang membedakan perambatan balik yang benar dari yang
        kebetulan bekerja. Jaringan yang gradiennya salah tetap sering
        "belajar", hanya lebih lambat dan berhenti di tempat yang keliru —
        dan kurva galatnya tetap terlihat menurun dengan meyakinkan.

        Memakai selisih tengah ``(f(w+h) − f(w−h)) / 2h``, bukan selisih maju.
        Selisih maju galatnya sebanding dengan ``h``; selisih tengah sebanding
        dengan ``h²``, dan perbedaannya cukup besar untuk menentukan apakah
        cacat sungguhan bisa dibedakan dari derau pembulatan.

        Mengembalikan daftar rincian per bobot beserta galat relatif
        terbesarnya.
        """
        gw, gb = self.gradien(data)
        rincian = []
        terburuk = 0.0

        for lap in range(len(self.bobot)):
            for j in range(len(self.bobot[lap])):
                for k in range(len(self.bobot[lap][j])):
                    asli = self.bobot[lap][j][k]

                    self.bobot[lap][j][k] = asli + h
                    naik = self.galat(data)
                    self.bobot[lap][j][k] = asli - h
                    turun = self.galat(data)
                    self.bobot[lap][j][k] = asli

                    numerik = (naik - turun) / (2.0 * h)
                    analitik = gw[lap][j][k]
                    penyebut = max(abs(numerik), abs(analitik), 1e-12)
                    relatif = abs(numerik - analitik) / penyebut
                    terburuk = max(terburuk, relatif)

                    rincian.append(
                        {
                            "jenis": "bobot",
                            "lapis": lap,
                            "ke": j,
                            "dari": k,
                            "nilai": asli,
                            "analitik": analitik,
                            "numerik": numerik,
                            "relatif": relatif,
                        }
                    )

        for lap in range(len(self.bias)):
            for j in range(len(self.bias[lap])):
                asli = self.bias[lap][j]
                self.bias[lap][j] = asli + h
                naik = self.galat(data)
                self.bias[lap][j] = asli - h
                turun = self.galat(data)
                self.bias[lap][j] = asli

                numerik = (naik - turun) / (2.0 * h)
                analitik = gb[lap][j]
                penyebut = max(abs(numerik), abs(analitik), 1e-12)
                relatif = abs(numerik - analitik) / penyebut
                terburuk = max(terburuk, relatif)

                rincian.append(
                    {
                        "jenis": "bias",
                        "lapis": lap,
                        "ke": j,
                        "dari": None,
                        "nilai": asli,
                        "analitik": analitik,
                        "numerik": numerik,
                        "relatif": relatif,
                    }
                )

        return {"rincian": rincian, "terburuk": terburuk, "lolos": terburuk < 1e-5}


# ---------------------------------------------------------------------------
# Kumpulan data
# ---------------------------------------------------------------------------


def data_xor():
    """XOR: kasus terkenal yang tidak terpisahkan secara linear.

    Temuan Minsky dan Papert bahwa perceptron satu lapis tidak bisa
    memisahkannya menghentikan penelitian jaringan syaraf hampir dua dekade.
    """
    return [
        ([0.0, 0.0], [0.0]),
        ([0.0, 1.0], [1.0]),
        ([1.0, 0.0], [1.0]),
        ([1.0, 1.0], [0.0]),
    ]


def data_and():
    """AND: terpisahkan secara linear, jadi perceptron satu lapis cukup."""
    return [
        ([0.0, 0.0], [0.0]),
        ([0.0, 1.0], [0.0]),
        ([1.0, 0.0], [0.0]),
        ([1.0, 1.0], [1.0]),
    ]


def data_lingkaran(jumlah=40, benih=7):
    """Dua kelas berbentuk cincin: yang di dalam dan yang di luar.

    Tidak terpisahkan garis lurus mana pun, sehingga ia menuntut lapis
    tersembunyi persis seperti XOR — tetapi dengan cukup banyak titik untuk
    memperlihatkan batas keputusannya melengkung.
    """
    r = SplitMix64(benih)
    data = []
    for i in range(jumlah):
        dalam = i % 2 == 0
        jari = r.rentang(0.0, 0.35) if dalam else r.rentang(0.6, 0.95)
        sudut = r.rentang(0.0, 2.0 * math.pi)
        data.append(
            (
                [0.5 + jari * math.cos(sudut) * 0.5, 0.5 + jari * math.sin(sudut) * 0.5],
                [0.0 if dalam else 1.0],
            )
        )
    return data


DATASET = {
    "xor": ("XOR", data_xor),
    "and": ("AND", data_and),
    "lingkaran": ("Cincin", data_lingkaran),
}
