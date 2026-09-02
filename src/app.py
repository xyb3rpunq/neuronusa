"""Antarmuka neuronusa, ditulis dalam Python dan dijalankan Brython.

Tidak ada JavaScript sama sekali di berkas ini. Yang dipakai hanya ``browser``
dari Brython, yang memetakan DOM ke Python. Itu bukan pameran: seluruh mesin
jaringan syarafnya sudah Python, dan menuliskan antarmukanya dalam bahasa lain
berarti setiap angka harus menyeberang batas bahasa dua kali per bingkai.

# Kenapa pelatihannya dipecah menjadi potongan

Brython adalah penerjemah Python di atas JavaScript, dan JavaScript berjalan
di utas yang sama dengan tampilan. Melatih tiga ribu epoch dalam satu
panggilan akan membekukan halaman sampai selesai — pengguna tidak bisa
menghentikannya, dan peramban akan menawarkan menutup tab. Karena itu
pelatihannya dipecah menjadi potongan kecil yang dijadwalkan lewat
``set_timeout``, sehingga tampilan tetap hidup dan tombol berhenti tetap bisa
ditekan.

.Deckyx
"""

import math

from browser import document, html, timer, window
from browser import svg as gambar_svg

from nusa import data as pengurai_data
from nusa import ekspor, fx, tautan
from nusa.jaringan import AKTIVASI, CACAT, DATASET, Jaringan

# ---------------------------------------------------------------------------
# Bantuan tampilan
# ---------------------------------------------------------------------------



def n(x, digit=4):
    """Angka untuk ditampilkan; dibulatkan pada tampilan saja."""
    if isinstance(x, float):
        if math.isnan(x):
            return "—"
        if math.isinf(x):
            return "∞" if x > 0 else "-∞"
    # ``format`` dan bukan ``%``: lihat catatan panjang di :func:`ilmiah`
    # tentang pemformatan Brython. ``%f`` sendiri terukur benar, tetapi memakai
    # dua jalan berbeda untuk pekerjaan yang sama hanya menyisakan satu jalan
    # yang tidak pernah diperiksa siapa pun.
    s = format(float(x), "." + str(digit) + "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def ilmiah(x, digit=2):
    """Angka dalam bentuk ilmiah, untuk galat yang sangat kecil.

    Memakai ``format`` dan **bukan** ``"%.3e" % x``. Keduanya setara di
    CPython; di Brython yang kedua rusak.

    Cacatnya ditemukan lewat halaman ini sendiri: pemeriksa gradien melaporkan
    galat relatif terburuk ``0.000e+00`` untuk setiap parameter, angka yang
    membuat hasilnya tampak jauh lebih meyakinkan daripada yang sebenarnya.
    Nilai sesungguhnya sekitar ``2.8e-08``. Diukur di peramban:

        '%.3e' % 2.803e-08   → '0.000e+00'     (salah)
        '%.3e' % 1.5e+300    → '1.5e+300e+00'  (salah)
        '%.2e' % -3.5e-9     → '-0.00e+00'     (salah)
        format(2.803e-08, '.3e') → '2.803e-08'  (benar)

    Uji di CPython tidak bisa menangkap ini, karena di CPython keduanya benar.
    Yang menangkapnya adalah pemeriksaan konformansi yang dijalankan di dalam
    peramban — dan itulah sebabnya tombolnya ada di halaman ini.
    """
    if x == 0.0:
        return "0"
    if math.isnan(x):
        return "—"
    if math.isinf(x):
        return "∞" if x > 0 else "-∞"
    return format(x, "." + str(digit) + "e")


def svg(tag, **atribut):
    """Membuat simpul SVG.

    Simpul SVG **wajib** dibuat pada ruang namanya sendiri. Dibuat dengan
    ``document.createElement`` seperti simpul HTML biasa, hasilnya adalah
    elemen bernama sama yang sah menurut DOM tetapi tidak pernah tergambar
    sepiksel pun — dan kegagalannya senyap: tidak ada galat, tidak ada
    peringatan, hanya kotak kosong.

    Atributnya dipasang lewat ``setAttribute``, bukan lewat argumen kata kunci
    modul ``browser.svg``. Alasannya: argumen kata kunci hanya mengganti
    garis bawah **pertama** menjadi tanda hubung, dan nama atribut SVG
    peka huruf besar-kecil sehingga ``Class`` tidak pernah cocok dengan
    pemilih CSS ``.kelas``.
    """
    simpul = getattr(gambar_svg, tag)()
    for k, v in atribut.items():
        simpul.setAttribute(k.replace("_", "-"), str(v))
    return simpul


def kosongkan(simpul):
    simpul.clear()


def kartu(judul, *anak):
    k = html.SECTION(Class="kartu")
    if judul:
        k <= html.H2(judul, Class="kartu__judul")
    for a in anak:
        k <= a
    return k


def bingkai(judul, terang, isi, kunci=None):
    """Bingkai gambar: judul, isi, keterangan simbol, dan penjelasannya.

    ``terang`` wajib. Gambar tanpa penjelasan hanya berguna bagi yang sudah
    paham isinya, dan pengguna yang paling butuh gambar justru yang belum
    paham. Teks itu sekaligus menjadi label bagi pembaca layar, yang tidak
    bisa melihat gambarnya sama sekali.
    """
    f = html.FIGURE(Class="viz")
    f <= html.H3(judul, Class="viz__judul")
    isi.setAttribute("class", "viz__svg")
    isi.setAttribute("role", "img")
    isi.setAttribute("aria-label", "%s. %s" % (judul, terang))
    f <= isi
    if kunci:
        u = html.UL(Class="viz__kunci")
        for warna, label in kunci:
            li = html.LI()
            s = html.SPAN(Class="viz__contoh")
            s.style.background = warna
            s.setAttribute("aria-hidden", "true")
            li <= s
            li <= html.SPAN(label)
            u <= li
        f <= u
    f <= html.FIGCAPTION(terang, Class="viz__terang")
    return f


def gambar(judul, terang, isi_svg, lebar, tinggi, kunci=None):
    """Bingkai untuk isi berupa SVG, lengkap dengan kotak pandangnya."""
    isi_svg.setAttribute("viewBox", "0 0 %d %d" % (lebar, tinggi))
    return bingkai(judul, terang, isi_svg, kunci)


def warna_tema(nama):
    """Nilai sebuah token warna CSS, seperti yang berlaku sekarang.

    Kanvas menyimpan piksel, bukan rujukan. Ia tidak ikut berubah saat tema
    peramban berpindah terang-gelap, jadi warnanya harus dibaca ulang setiap
    kali digambar — bukan disimpan di tetapan Python.
    """
    return window.getComputedStyle(document.body).getPropertyValue(nama).strip()


# ---------------------------------------------------------------------------
# Tautan yang bisa dibagikan
# ---------------------------------------------------------------------------
#
# Penyandian dan pemeriksaannya ada di ``nusa.tautan``, bukan di sini. Yang
# tersisa di berkas ini hanya lem ke peramban: membaca ``location.hash`` dan
# menulis kembali lewat ``replaceState``.
#
# Pemisahan itu bukan kerapian melainkan syarat: isi sebuah alamat ditulis
# orang lain, dan kode yang memeriksa masukan luar wajib punya uji. Selama ia
# tinggal di berkas yang mengimpor ``browser``, CPython tidak bisa mengimpornya
# sama sekali dan karena itu tidak bisa mengujinya sama sekali.


def baca_tautan():
    """Setelan yang sah dari alamat sekarang."""
    return tautan.baca(window.location.hash)


def tulis_tautan():
    """Menyelaraskan alamat dengan setelan sekarang.

    Memakai ``replaceState`` dan bukan menyetel ``location.hash`` langsung:
    yang terakhir menambah satu entri riwayat setiap kali sebuah penggeser
    digerakkan, sehingga tombol kembali peramban harus ditekan puluhan kali
    untuk keluar dari halaman ini. ``replaceState`` juga tidak memicu
    ``hashchange``, sehingga penulisan ini tidak memanggil balik
    :func:`terapkan_tautan`.
    """
    setelan = {nama: getattr(K, nama) for nama, _kunci in tautan.KUNCI}
    # Keadaan riwayat yang ada diteruskan apa adanya, bukan ``None``.
    #
    # Brython memetakan ``None`` menjadi objek Python, bukan menjadi ``null``
    # JavaScript, dan ``replaceState`` menolaknya dengan "could not be cloned".
    # Menyerahkan kembali ``history.state`` selalu aman: apa pun isinya, ia
    # sudah pernah melewati pengklonan itu sekali.
    window.history.replaceState(
        window.history.state, "", "#" + tautan.tulis(setelan)
    )


def terapkan_tautan(_ev=None):
    """Menerapkan setelan dari alamat ke halaman yang sudah terbuka.

    Dipanggil saat alamatnya berubah tanpa halaman dimuat ulang: tombol
    kembali peramban, atau tautan yang ditempel ke bilah alamat sementara
    halaman ini sudah terbuka. Tanpa ini, menempel tautan hanya mengubah
    tulisan di bilah alamat dan tidak mengubah apa pun di layar — kegagalan
    yang membuat seluruh gagasan tautan-yang-bisa-dibagikan tidak berguna
    justru bagi orang yang paling sering memakainya.
    """
    setelan = baca_tautan()
    if not setelan:
        return
    K.melatih = False
    for nama, nilai in setelan.items():
        setattr(K, nama, nilai)
    K.bangun()
    gambar_kontrol()
    gambar_ulang()


def salin_tautan(_ev=None):
    """Menyalin alamat sekarang ke papan klip."""
    wadah = document["kabar-tautan"]
    kosongkan(wadah)

    def berhasil(_hasil):
        wadah <= html.SPAN("Tautan disalin.", Class="kabar kabar--benar")

    def gagal(_galat):
        # Papan klip bisa ditolak peramban, dan itu bukan kesalahan yang perlu
        # ditutupi. Alamat di bilah alamat sudah benar; pengguna tinggal
        # menyalinnya sendiri.
        wadah <= html.SPAN(
            "Peramban menolak akses papan klip \u2014 salin saja alamat di bilah "
            "alamat, isinya sudah tepat.",
            Class="kabar",
        )

    try:
        window.navigator.clipboard.writeText(window.location.href).then(berhasil, gagal)
    except Exception:  # noqa: BLE001 - API-nya tidak ada di sebagian peramban
        gagal(None)


# ---------------------------------------------------------------------------
# Tema
# ---------------------------------------------------------------------------

#: Ketiga pilihan tema. "sistem" berarti tidak memasang atribut apa pun,
#: sehingga ``prefers-color-scheme`` yang menentukan.
TEMA = [("sistem", "Ikut sistem"), ("terang", "Terang"), ("gelap", "Gelap")]

_KUNCI_TEMA = "neuronusa:tema"


def tema_tersimpan():
    try:
        nilai = window.localStorage.getItem(_KUNCI_TEMA)
    except Exception:  # noqa: BLE001 - penyimpanan bisa dimatikan sama sekali
        return "sistem"
    return nilai if nilai in [k for k, _ in TEMA] else "sistem"


def pasang_tema(nama, gambar_lagi=True):
    akar = document.documentElement
    if nama == "sistem":
        akar.removeAttribute("data-tema")
    else:
        akar.setAttribute("data-tema", nama)
    try:
        window.localStorage.setItem(_KUNCI_TEMA, nama)
    except Exception:  # noqa: BLE001 - jendela penyamaran, dll.
        pass
    K.tema = nama
    if gambar_lagi:
        # Kanvas menyimpan piksel, bukan rujukan warna. Ia tidak ikut berubah
        # saat tema berpindah, jadi ia harus digambar ulang — tidak seperti
        # SVG di sekelilingnya, yang mengikuti CSS dengan sendirinya.
        gambar_kontrol()
        gambar_ulang()


# ---------------------------------------------------------------------------
# Keadaan aplikasi
# ---------------------------------------------------------------------------


class Keadaan:
    def __init__(self):
        self.dataset = "xor"
        self.tersembunyi = 4
        self.aktivasi = "tanh"
        self.laju = 0.5
        self.momentum = 0.9
        self.benih = 7
        self.epoch = 0
        self.riwayat = []
        self.melatih = False
        self.jaringan = None
        self._data = None
        self.pesan = None
        # Kapan bagian yang mahal terakhir digambar. Nol berarti "belum
        # pernah", sehingga penggambaran pertama selalu lengkap.
        self.gambar_berat_terakhir = 0.0
        # Contoh data mana yang sedang ditelusuri langkah demi langkah.
        self.titik_jejak = 0
        self.cacat = "tidak_ada"
        # Data tempelan pengguna, kalau ada. Disimpan terurai supaya tidak
        # diurai ulang di tiap bingkai gambar.
        self.data_sendiri = None
        self.skala_sendiri = []
        self.catatan_data = []
        self.teks_data = ""
        # Jaringan pembanding yang perambatan baliknya benar, dilatih
        # berdampingan dengan benih dan setelan yang sama persis. Hanya ada
        # saat sebuah cacat menyala; tanpa pembanding, kurva galat jaringan
        # yang rusak tidak berarti apa-apa — dan justru itulah yang mau
        # diperlihatkan.
        self.bayangan = None
        self.riwayat_bayangan = []
        self.tema = "sistem"

        # Setelan dari alamat diterapkan **sebelum** jaringannya dibangun.
        # Menerapkannya sesudah berarti membangun satu jaringan yang langsung
        # dibuang, dan pada kumpulan cincin itu berarti membangkitkan empat
        # puluh titik dua kali sebelum sebaris pun tergambar.
        for nama, nilai in baca_tautan().items():
            setattr(self, nama, nilai)

        self.bangun()

    def data(self):
        # Disimpan, tidak dibangkitkan ulang tiap dipanggil. Kumpulan cincin
        # membangkitkan empat puluh titik lewat PRNG; memanggilnya ulang belasan
        # kali per bingkai gambar tidak mengubah hasilnya sedikit pun, hanya
        # membuang waktu di penerjemah yang sudah lambat.
        if self._data is None:
            if self.dataset == "sendiri":
                # Tautan bisa menyebut "sendiri" tanpa membawa datanya —
                # datanya jauh terlalu besar untuk sebuah alamat. Jatuh ke XOR
                # alih-alih menabrak: pembaca tautan tidak melakukan kesalahan
                # apa pun, ia hanya menerima tautan yang tidak lengkap.
                if not self.data_sendiri:
                    self.dataset = "xor"
                    self._data = DATASET["xor"][1]()
                else:
                    self._data = self.data_sendiri
            else:
                self._data = DATASET[self.dataset][1]()
        return self._data

    def bangun(self):
        self._data = None
        self.pesan = None
        ukuran = [2, 1] if self.tersembunyi == 0 else [2, self.tersembunyi, 1]
        self.jaringan = Jaringan(ukuran, aktivasi=self.aktivasi, benih=self.benih)
        self.jaringan.atur_cacat(self.cacat)
        self.epoch = 0
        self.riwayat = [self.jaringan.galat(self.data())]

        if self.cacat == "tidak_ada":
            self.bayangan = None
            self.riwayat_bayangan = []
        else:
            # Benih yang sama berarti bobot awal yang sama persis, jadi apa pun
            # yang membedakan kedua kurva nanti hanyalah cacatnya — bukan
            # keberuntungan titik awal.
            self.bayangan = Jaringan(ukuran, aktivasi=self.aktivasi, benih=self.benih)
            self.riwayat_bayangan = [self.bayangan.galat(self.data())]

    def maju_satu_epoch(self):
        """Satu langkah untuk jaringan utama, dan untuk bayangannya bila ada."""
        data = self.data()
        self.jaringan.langkah(
            data, laju=self.laju, momentum=self.momentum, hitung_galat=False
        )
        if self.bayangan is not None:
            self.bayangan.langkah(
                data, laju=self.laju, momentum=self.momentum, hitung_galat=False
            )
        self.epoch += 1

    def catat_riwayat(self):
        """Menyimpan galat sekarang, dan memangkas riwayat bila sudah panjang."""
        data = self.data()
        self.riwayat.append(self.jaringan.galat(data))
        if self.bayangan is not None:
            self.riwayat_bayangan.append(self.bayangan.galat(data))
        if len(self.riwayat) > BATAS_RIWAYAT:
            # Kedua riwayat dipangkas dengan cara yang sama persis, kalau tidak
            # keduanya tidak lagi sepadan indeks demi indeks dan kurvanya
            # bergeser satu terhadap yang lain.
            self.riwayat = self.riwayat[::2]
            self.riwayat_bayangan = self.riwayat_bayangan[::2]


K = Keadaan()


# ---------------------------------------------------------------------------
# Gambar: kurva galat
# ---------------------------------------------------------------------------


def gambar_galat():
    L, T = 640, 200
    pad_kiri, pad_bawah, pad_atas = 52, 28, 14
    s = svg("svg")

    riwayat = K.riwayat
    if len(riwayat) < 2:
        return s, "Belum ada langkah pelatihan."

    bayangan = K.riwayat_bayangan if K.bayangan is not None else []
    # Kedua kurva berbagi satu sumbu. Menskalakannya sendiri-sendiri akan
    # membuat dua kurva yang nilainya jauh berbeda terlihat berimpit — persis
    # kesimpulan terbalik dari yang ingin diperlihatkan.
    semua = riwayat + bayangan
    terbesar = max(semua)
    terkecil = min(semua)
    if terbesar <= terkecil:
        terbesar = terkecil + 1e-9

    def px(i):
        return pad_kiri + (i / (len(riwayat) - 1)) * (L - pad_kiri - 16)

    def py(v):
        bagian = (v - terkecil) / (terbesar - terkecil)
        return pad_atas + (1.0 - bagian) * (T - pad_atas - pad_bawah)

    for bagian in (0.0, 0.5, 1.0):
        y = pad_atas + bagian * (T - pad_atas - pad_bawah)
        garis = svg("line", x1=pad_kiri, y1=y, x2=L - 16, y2=y, stroke="var(--garis)")
        s <= garis
        nilai = terbesar - bagian * (terbesar - terkecil)
        t = svg("text", x=pad_kiri - 8, y=y + 4, text_anchor="end", font_size=9, fill="var(--tinta-3)")
        t.textContent = ilmiah(nilai, 1)
        s <= t

    def jalur(nilai):
        potong = []
        for i, v in enumerate(nilai):
            potong.append("%s %.2f %.2f" % ("M" if i == 0 else "L", px(i), py(v)))
        return " ".join(potong)

    if bayangan:
        # Digambar lebih dulu supaya kurva yang rusak berada di atasnya.
        s <= svg(
            "path",
            d=jalur(bayangan),
            fill="none",
            stroke="var(--tinta-3)",
            stroke_width=2,
            stroke_dasharray="5 4",
        )
    s <= svg("path", d=jalur(riwayat), fill="none", stroke="var(--aksen)", stroke_width=2)

    t = svg("text", x=pad_kiri, y=T - 8, font_size=9, fill="var(--tinta-3)")
    t.textContent = "epoch 0"
    s <= t
    t2 = svg("text", x=L - 16, y=T - 8, text_anchor="end", font_size=9, fill="var(--tinta-3)")
    t2.textContent = "epoch %d" % K.epoch
    s <= t2

    arah = "menurun" if riwayat[-1] < riwayat[0] else "TIDAK menurun"
    terang = (
        "Galat %s dari %s menjadi %s setelah %d epoch. "
        "Sumbu tegaknya berskala dari nilai terkecil sampai terbesar yang pernah "
        "dicapai, jadi kurva yang terlihat curam belum tentu turun banyak — "
        "perhatikan angka di sumbunya, bukan kemiringannya."
        % (arah, ilmiah(riwayat[0], 2), ilmiah(riwayat[-1], 2), K.epoch)
    )
    if bayangan:
        terang += (
            " Garis putus-putus adalah jaringan pembanding dengan bobot awal yang "
            "sama persis dan perambatan balik yang benar. Perhatikan berapa "
            "banyak — atau berapa sedikit — keduanya berbeda: %s berbanding %s."
            % (ilmiah(riwayat[-1], 2), ilmiah(bayangan[-1], 2))
        )
    return s, terang


# ---------------------------------------------------------------------------
# Gambar: batas keputusan
# ---------------------------------------------------------------------------


#: Sisi kosong di sekeliling bidang batas keputusan, dalam piksel gambar.
#:
#: Bukan hiasan. Data XOR duduk tepat di keempat sudut bidang satuan, jadi
#: tanpa sisa ruang ini separuh setiap lingkaran terpotong tepi gambar —
#: dan yang terpotong justru titik-titik yang paling menentukan.
PADDING_BATAS = 12

#: Sisi bidang batas keputusan dalam piksel CSS.
SISI_BATAS = 300

#: Berapa tingkat buram yang dibedakan saat menggabung petak sebaris.
#:
#: Makin banyak tingkat, makin halus gradasinya dan makin sedikit petak yang
#: bisa digabung. 24 sudah lebih halus daripada yang bisa dibedakan mata pada
#: warna setransparan ini.
TINGKAT_BURAM = 24

#: Halus kasarnya bidang: berapa petak per sisi.
#:
#: Tiap petak berarti satu perambatan maju, jadi angkanya berbanding lurus
#: dengan biaya menggambar — dua kali lipat sisinya berarti empat kali biayanya.
#: 22 memberi 484 titik, sekitar 14 piksel per petak pada gambar 300 piksel:
#: cukup halus untuk memperlihatkan batas yang melengkung, cukup murah untuk
#: digambar ulang beberapa kali per detik di penerjemah Python.
KISI_BATAS = 22


def gambar_batas():
    """Bidang keputusan, digambar di atas kanvas dan bukan SVG.

    # Kenapa kanvas, padahal gambar lain di halaman ini SVG

    Karena yang digambar di sini bukan struktur melainkan piksel. SVG unggul
    untuk hal yang punya makna satuan — sebuah neuron, sebuah sisi, sebuah
    label — karena tiap bagiannya bisa diberi nama, ditata lewat CSS, dan
    dibacakan pembaca layar. Bidang keputusan tidak punya bagian bernama; ia
    ratusan petak warna yang hanya berarti secara keseluruhan.

    Perbedaannya terukur, bukan selera. Bentuk SVG-nya membuat 677 elemen DOM
    tiap kali digambar dan memakan **606 milidetik** di peramban — cukup lama
    untuk membuat setiap langkah pelatihan tersendat terlihat. Ratusan simpul
    DOM yang tidak satu pun bisa diberi nama adalah harga tanpa imbalan.

    Kanvas memang tidak bisa dibaca pembaca layar. Karena itu keterangan di
    bawah gambar menyebutkan angkanya — berapa titik yang benar dari berapa
    — dan bukan sekadar mengatakan "lihat gambar di atas".
    """
    dpr = window.devicePixelRatio or 1
    piksel = int(SISI_BATAS * dpr)
    kanvas = html.CANVAS(width=piksel, height=piksel)
    kanvas.style.aspectRatio = "1 / 1"
    ctx = kanvas.getContext("2d")

    skala = piksel / SISI_BATAS
    dalam = (SISI_BATAS - 2 * PADDING_BATAS) * skala
    tepi = PADDING_BATAS * skala

    def ke_layar(x, y):
        return tepi + x * dalam, tepi + (1.0 - y) * dalam

    # Satu resolusi gaya, empat pembacaan — bukan empat resolusi. Kanvas
    # menyimpan piksel, bukan rujukan, jadi warnanya harus dibaca ulang tiap
    # kali digambar supaya ikut berpindah saat tema peramban berubah.
    gaya = window.getComputedStyle(document.body)
    warna_a = gaya.getPropertyValue("--kelas-a").strip()
    warna_b = gaya.getPropertyValue("--kelas-b").strip()
    warna_garis = gaya.getPropertyValue("--garis-tegas").strip()
    warna_tinta = gaya.getPropertyValue("--tinta").strip()

    ctx.clearRect(0, 0, piksel, piksel)

    kisi = KISI_BATAS
    bidang = K.jaringan.bidang_keputusan(kisi)
    sisi = dalam / kisi

    # Tingkat buram tiap petak dihitung sekali di sini, bukan dua kali di dalam
    # pencarian lari di bawah. Tiap petak diperiksa dua kali — sekali sebagai
    # awal lari, sekali sebagai calon lanjutannya — dan menghitung ulang
    # ``int(min(abs(v - 0.5) * 2, 1) * 24)`` di kedua tempat berarti menjalankan
    # lima operasi Python dua kali untuk setiap petak.
    tingkatan = []
    atasan = []
    for v in bidang:
        tingkatan.append(int(min(abs(v - 0.5) * 2.0, 1.0) * TINGKAT_BURAM))
        atasan.append(v >= 0.5)

    # Metode konteks kanvas diambil sekali ke nama lokal. Tiap pencarian
    # atribut pada objek JavaScript menyeberangi batas bahasa, dan penyeberangan
    # itu jauh lebih mahal daripada pemanggilannya sendiri.
    isi_persegi = ctx.fillRect

    # Petak sebaris yang sewarna dan setingkat buram digabung menjadi satu
    # persegi.
    #
    # Bukan penghematan piksel melainkan penghematan panggilan. Tiap panggilan
    # ke konteks kanvas terukur sekitar 30 mikrodetik — puluhan kali lebih
    # mahal daripada aritmetika di sisi Python. Bidang keputusan berubah mulus,
    # jadi petak bersebelahan hampir selalu jatuh di tingkat yang sama, dan
    # penggabungan ini menurunkan jumlah panggilannya sampai sekitar seperlima
    # tanpa mengubah satu piksel pun yang terlihat.
    for ky in range(kisi):
        y = tepi + dalam - (ky + 1) * sisi
        dasar = ky * kisi
        kx = 0
        while kx < kisi:
            tingkat = tingkatan[dasar + kx]
            atas = atasan[dasar + kx]
            akhir_lari = kx + 1
            while (
                akhir_lari < kisi
                and atasan[dasar + akhir_lari] is atas
                and tingkatan[dasar + akhir_lari] == tingkat
            ):
                akhir_lari += 1

            # Buramnya mengikuti seberapa jauh keluarannya dari 0,5. Jaringan
            # yang belum belajar apa pun menjawab 0,5 di mana-mana, dan bidang
            # yang pucat rata itu memang gambaran yang jujur.
            ctx.globalAlpha = 0.10 + 0.72 * tingkat / TINGKAT_BURAM
            ctx.fillStyle = warna_b if atas else warna_a
            # Setengah piksel ditambahkan supaya persegi bersebelahan bertindih
            # sedikit. Tanpa itu pembulatan sub-piksel meninggalkan garis latar
            # tipis di antaranya, dan garis-garis itu terbaca seperti pola yang
            # berarti padahal bukan.
            isi_persegi(
                tepi + kx * sisi,
                y,
                (akhir_lari - kx) * sisi + 0.5,
                sisi + 0.5,
            )
            kx = akhir_lari

    ctx.globalAlpha = 1.0
    ctx.strokeStyle = warna_garis
    ctx.lineWidth = skala
    ctx.strokeRect(tepi, tepi, dalam, dalam)

    for x, t in K.data():
        cx, cy = ke_layar(x[0], x[1])
        ctx.beginPath()
        ctx.arc(cx, cy, 6 * skala, 0, 2 * math.pi)
        ctx.fillStyle = warna_b if t[0] >= 0.5 else warna_a
        ctx.fill()
        ctx.lineWidth = 1.6 * skala
        ctx.strokeStyle = warna_tinta
        ctx.stroke()

    benar = sum(1 for x, t in K.data() if round(K.jaringan.ramal(x)[0]) == int(t[0]))
    total = len(K.data())
    terang = (
        "Warna latar adalah tebakan jaringan di setiap titik bidang; makin pekat "
        "makin yakin. Lingkaran adalah data latihnya. Saat ini %d dari %d titik "
        "diramalkan benar. Perhatikan bentuk batasnya: perceptron tanpa lapis "
        "tersembunyi hanya bisa menarik garis lurus, dan itulah sebabnya XOR "
        "mustahil baginya." % (benar, total)
    )
    return kanvas, terang


# ---------------------------------------------------------------------------
# Gambar: bobot jaringan
# ---------------------------------------------------------------------------


def gambar_jaringan():
    ukuran = K.jaringan.ukuran
    L = 420
    T = max(180, max(ukuran) * 44 + 40)
    s = svg("svg")

    def titik(lap, j):
        x = 40 + lap * (L - 80) / max(1, len(ukuran) - 1)
        banyak = ukuran[lap]
        y = T / 2 + (j - (banyak - 1) / 2.0) * 42
        return x, y

    terbesar = 1e-9
    for lap in K.jaringan.bobot:
        for baris in lap:
            for w in baris:
                terbesar = max(terbesar, abs(w))

    for lap in range(len(K.jaringan.bobot)):
        for j, baris in enumerate(K.jaringan.bobot[lap]):
            for k, w in enumerate(baris):
                x1, y1 = titik(lap, k)
                x2, y2 = titik(lap + 1, j)
                tebal = 0.5 + 3.5 * abs(w) / terbesar
                # Tanda bobot dibedakan warnanya, bukan hanya tebalnya. Bobot
                # negatif dan positif berperan berlawanan, dan menyamakan
                # warnanya menyembunyikan justru struktur yang dipelajari.
                warna = "var(--positif)" if w >= 0 else "var(--negatif)"
                g = svg(
                    "line",
                    x1=x1, y1=y1, x2=x2, y2=y2,
                    stroke=warna,
                    stroke_width="%.2f" % tebal,
                    opacity=0.75,
                )
                s <= g

    for lap in range(len(ukuran)):
        for j in range(ukuran[lap]):
            x, y = titik(lap, j)
            c = svg("circle", cx=x, cy=y, r=13, fill="var(--latar-3)", stroke="var(--garis-tegas)", stroke_width=1.4)
            s <= c
            t = svg("text", x=x, y=y + 4, text_anchor="middle", font_size=9, fill="var(--tinta-3)")
            t.textContent = str(j + 1)
            s <= t

    nama = ["masukan"] + ["tersembunyi"] * (len(ukuran) - 2) + ["keluaran"]
    for lap in range(len(ukuran)):
        x, _ = titik(lap, 0)
        t = svg("text", x=x, y=T - 8, text_anchor="middle", font_size=9, fill="var(--tinta-3)")
        t.textContent = nama[lap]
        s <= t

    terang = (
        "Tebal garis menyatakan besar bobotnya, warnanya menyatakan tandanya. "
        "Bobot negatif dan positif berperan berlawanan, jadi menyamakan warnanya "
        "akan menyembunyikan struktur yang justru sedang dipelajari jaringan. "
        "Nilai tepatnya ada di tabel di bawah — bukan sebagai gelembung yang "
        "muncul saat disentuh tetikus, karena gelembung itu tidak pernah muncul "
        "di layar sentuh dan tidak pernah terbaca pembaca layar."
    )
    return s, terang


# ---------------------------------------------------------------------------
# Penggambaran halaman
# ---------------------------------------------------------------------------


def gambar_ulang(berat=True):
    """Menggambar ulang keluaran.

    Dipecah menjadi dua bagian karena biayanya jauh berbeda. Ringkasan dan
    kurva galat memakan beberapa milidetik; bidang keputusan, peta bobot, dan
    kedua tabel memakan puluhan. Menggambar semuanya di tiap potongan
    pelatihan membuat halaman tersendat tanpa menambah apa pun yang bisa
    dilihat — bidang keputusan tidak berubah kentara dalam sepersepuluh detik.
    """
    data = K.data()
    galat = K.jaringan.galat(data)
    benar = sum(1 for x, t in data if round(K.jaringan.ramal(x)[0]) == int(t[0]))

    ringkas = document["keluaran-ringkas"]
    kosongkan(ringkas)

    if K.pesan:
        ringkas <= html.P(K.pesan, Class="galat")

    kotak = html.DIV(Class="hasil")
    kotak <= html.DIV("Galat kuadrat rata-rata", Class="hasil__label")
    kotak <= html.DIV(ilmiah(galat, 4), Class="hasil__nilai")
    kotak <= html.DIV(
        "%d dari %d titik diramalkan benar setelah %d epoch — %d parameter dilatih."
        % (benar, len(data), K.epoch, K.jaringan.jumlah_parameter()),
        Class="hasil__tafsir",
    )
    macet = diagnosa_macet(data, benar)
    if macet:
        kotak <= html.DIV(macet, Class="hasil__tafsir")

    if K.cacat != "tidak_ada" and K.bayangan is not None:
        kotak <= html.DIV(banding_cacat(data, galat, benar), Class="hasil__tafsir hasil__tafsir--cacat")

    ringkas <= kotak

    s_galat, t_galat = gambar_galat()
    kunci_galat = None
    if K.bayangan is not None:
        kunci_galat = [
            ("var(--aksen)", "jaringan yang disabotase"),
            ("var(--tinta-3)", "pembanding yang benar (putus-putus)"),
        ]
    ringkas <= kartu(
        "Kurva galat",
        gambar("Galat tiap epoch", t_galat, s_galat, 640, 200, kunci_galat),
    )

    if not berat:
        return

    wadah = document["keluaran-berat"]
    kosongkan(wadah)

    s_batas, t_batas = gambar_batas()
    wadah <= kartu(
        "Batas keputusan",
        bingkai(
            "Tebakan jaringan di seluruh bidang",
            t_batas,
            s_batas,
            [("var(--kelas-a)", "kelas 0"), ("var(--kelas-b)", "kelas 1")],
        ),
    )

    s_jar, t_jar = gambar_jaringan()
    wadah <= kartu(
        "Bobot yang dipelajari",
        gambar(
            "Peta bobot jaringan",
            t_jar,
            s_jar,
            420,
            max(180, max(K.jaringan.ukuran) * 44 + 40),
            [("var(--positif)", "bobot positif"), ("var(--negatif)", "bobot negatif")],
        ),
        tabel_bobot(),
    )

    wadah <= kartu("Ramalan tiap titik data", tabel_ramalan(data))

    # Jejaknya ikut bagian yang mahal: ia menuntut satu perambatan maju dan
    # balik penuh, dan angkanya berubah setiap epoch — tetapi tidak ada yang
    # bisa dibaca dari angka yang berganti tiga puluh kali sedetik.
    gambar_langkah()


#: Berapa banyak epoch terakhir yang diperiksa untuk menyatakan pelatihan macet.
JENDELA_MACET = 12

#: Perubahan galat di bawah ini, sepanjang jendela di atas, dianggap mandek.
AMBANG_MACET = 1e-7


def banding_cacat(data, galat, benar):
    """Membandingkan jaringan yang disabotase dengan pembandingnya.

    Kalimatnya dirakit dari angka yang ada, bukan ditulis di muka.

    Bentuk pertamanya berbunyi "selisihnya sekecil itu" tanpa melihat
    selisihnya sama sekali. Situs yang sudah terbit membantahnya dalam satu
    kali coba: pada cacat "faktor dua", jaringan yang rusak berada di
    1,1e-02 dengan empat titik benar sementara pembandingnya di 6,8e-02
    dengan tiga. Selisihnya enam kali lipat, dan yang rusak justru yang
    terlihat lebih baik. Kalimat yang mengasumsikan salah satu arah akan
    salah separuh waktu.
    """
    label, _tempat, tertangkap, _p = CACAT[K.cacat]
    galat_benar = K.bayangan.galat(data)
    benar_bayangan = sum(1 for x, t in data if round(K.bayangan.ramal(x)[0]) == int(t[0]))

    teks = "Cacat menyala: %s. Yang disabotase ada di %s dengan %d dari %d titik benar; pembanding yang benar di %s dengan %d. " % (
        label,
        ilmiah(galat, 4),
        benar,
        len(data),
        ilmiah(galat_benar, 4),
        benar_bayangan,
    )

    if K.epoch == 0:
        teks += "Keduanya belum dilatih — tekan Latih."
    elif galat < galat_benar:
        teks += (
            "Yang disabotase justru berakhir LEBIH RENDAH. Itu bukan "
            "kebetulan yang lucu melainkan seluruh maksud halaman ini."
        )
    elif galat_benar < galat and benar >= benar_bayangan:
        teks += "Keduanya sama-sama menurun, dan keduanya menjawab sama banyak."
    else:
        teks += "Yang disabotase tertinggal — tetapi tetap menurun."

    teks += (
        "  Pemeriksa gradien menangkap cacat ini."
        if tertangkap
        else "  Pemeriksa gradien tidak bisa menangkap yang ini."
    )
    return teks


def diagnosa_macet(data, benar):
    """Menjelaskan pelatihan yang berhenti sebelum benar — kalau memang begitu.

    Ini pengukuran, bukan tebakan. Yang dilihat adalah galat sungguhan pada
    beberapa epoch terakhir dan ramalan sungguhan pada tiap titik; kalau
    keduanya menunjukkan jaringan berhenti bergerak tanpa menyelesaikan
    masalahnya, barulah keterangannya muncul.

    Membedakan dua sebab yang gejalanya mirip di kurva galat tetapi obatnya
    berlawanan: jaringan yang terlalu kecil untuk masalahnya, dan jaringan
    yang cukup besar tetapi neuronnya sudah jenuh atau mati.
    """
    if K.epoch < 200 or benar >= len(data) or len(K.riwayat) < JENDELA_MACET:
        return None
    jendela = K.riwayat[-JENDELA_MACET:]
    if max(jendela) - min(jendela) > AMBANG_MACET:
        return None

    tetap = len({round(K.jaringan.ramal(x)[0]) for x, _ in data}) == 1

    if K.tersembunyi == 0 and K.dataset in ("xor", "lingkaran"):
        return (
            "Pelatihan berhenti bergerak. Ini bukan setelan yang salah melainkan "
            "batas yang sesungguhnya: tanpa lapis tersembunyi jaringan ini cuma "
            "bisa menarik satu garis lurus, dan tidak ada garis lurus yang "
            "memisahkan masalah ini. Tambahkan neuron tersembunyi."
        )
    if tetap:
        return (
            "Pelatihan berhenti bergerak, dan jaringan menjawab sama untuk setiap "
            "masukan — neuronnya jenuh atau mati, sehingga turunannya nyaris nol "
            "dan tidak ada lagi yang mendorongnya. Kecilkan laju efektifnya, atau "
            "ganti aktivasinya; relu paling sering mati begini."
        )
    return (
        "Pelatihan berhenti bergerak sebelum seluruh titik benar. Coba tambah "
        "neuron tersembunyi, atau ganti benih bobot awal — sebagian titik awal "
        "memang berakhir di lembah yang bukan yang terdalam."
    )


def tabel_bobot():
    """Seluruh bobot dan bias sebagai angka.

    Gambar memperlihatkan polanya, tabel memperlihatkan nilainya. Keduanya
    dibutuhkan: pola tanpa angka tidak bisa diperiksa, angka tanpa pola tidak
    bisa dibaca sekilas.
    """
    bungkus = html.DIV(Class="gulir-x")
    t = html.TABLE()
    kepala = html.TR()
    for h in ("parameter", "nilai"):
        kepala <= html.TH(h)
    t <= html.THEAD(kepala)
    isi = html.TBODY()
    for lap in range(len(K.jaringan.bobot)):
        for j, baris_bobot in enumerate(K.jaringan.bobot[lap]):
            for k, w in enumerate(baris_bobot):
                baris = html.TR()
                baris <= html.TD("w  L%d  n%d ← %d" % (lap, j + 1, k + 1))
                baris <= html.TD(n(w, 6), Class="num")
                isi <= baris
        for j, b in enumerate(K.jaringan.bias[lap]):
            baris = html.TR()
            baris <= html.TD("bias  L%d  n%d" % (lap, j + 1))
            baris <= html.TD(n(b, 6), Class="num")
            isi <= baris
    t <= isi
    bungkus <= t
    return bungkus


def tabel_ramalan(data):
    bungkus = html.DIV(Class="gulir-x")
    t = html.TABLE()
    kepala = html.TR()
    for h in ("x₁", "x₂", "sasaran", "keluaran", "galat", "benar"):
        kepala <= html.TH(h)
    t <= html.THEAD(kepala)
    isi = html.TBODY()
    for x, sasaran in data[:16]:
        y = K.jaringan.ramal(x)[0]
        cocok = round(y) == int(sasaran[0])
        baris = html.TR()
        baris <= html.TD(n(x[0], 3), Class="num")
        baris <= html.TD(n(x[1], 3), Class="num")
        baris <= html.TD(n(sasaran[0], 0), Class="num")
        baris <= html.TD(n(y, 4), Class="num")
        baris <= html.TD(n(abs(y - sasaran[0]), 4), Class="num")
        baris <= html.TD("ya" if cocok else "—")
        isi <= baris
    t <= isi
    bungkus <= t
    return bungkus


# ---------------------------------------------------------------------------
# Pemeriksaan gradien
# ---------------------------------------------------------------------------


def tafsir_pemeriksaan(hasil):
    """Menghubungkan hasil pemeriksaan dengan cacat yang sedang menyala.

    Tanpa ini, seorang pengunjung yang menyalakan cacat "bias beku" lalu
    melihat LOLOS akan menyimpulkan pemeriksanya rusak. Yang benar justru
    sebaliknya: pemeriksa gradien memang tidak bisa menangkapnya, dan
    mengetahui batas sebuah alat adalah bagian dari memakainya.
    """
    if K.cacat == "tidak_ada":
        if hasil["lolos"]:
            return html.P(
                "Tidak ada cacat yang menyala, dan pemeriksanya lolos — seperti "
                "seharusnya. Untuk membuktikan pemeriksa ini benar-benar "
                "memeriksa sesuatu, nyalakan salah satu cacat di panel Sabotase "
                "lalu tekan tombol ini lagi.",
                Class="catatan",
            )
        return html.P(
            "Tidak ada cacat yang menyala, tetapi pemeriksanya gagal. Ini tidak "
            "diharapkan terjadi; kalau Anda melihatnya, ada yang salah di mesin "
            "ini dan bukan di setelan Anda.",
            Class="galat",
        )

    label, _tempat, tertangkap, _penjelasan = CACAT[K.cacat]
    if tertangkap and not hasil["lolos"]:
        return html.P(
            "Cacat \u201c%s\u201d menyala, dan pemeriksanya menangkapnya. Perhatikan "
            "kurva galat di sebelah: ia tetap menurun. Tidak ada satu pun angka "
            "di kurva itu yang bisa memberi tahu Anda hal yang baru saja "
            "diberitahukan tabel ini." % label,
            Class="catatan",
        )
    if not tertangkap and hasil["lolos"]:
        return html.P(
            "Cacat \u201c%s\u201d menyala, dan pemeriksanya LOLOS. Itu bukan kegagalan "
            "pemeriksanya melainkan batasnya: ia memeriksa apakah turunannya "
            "benar, bukan apakah turunannya dipakai. Cacat ini bekerja pada "
            "langkah pembaruan, jauh setelah gradiennya selesai dihitung. "
            "Alat yang batasnya tidak diketahui lebih berbahaya daripada tidak "
            "punya alat." % label,
            Class="catatan",
        )
    return html.P(
        "Cacat \u201c%s\u201d menyala dan hasilnya tidak seperti yang diperkirakan "
        "katalog cacatnya. Ini tidak diharapkan terjadi." % label,
        Class="galat",
    )


def jalankan_periksa_gradien(_ev=None):
    wadah = document["gradien"]
    kosongkan(wadah)
    wadah <= html.P("Menghitung ulang setiap turunan dengan selisih hingga…", Class="catatan")

    def kerjakan():
        hasil = K.jaringan.periksa_gradien(K.data())
        # Disimpan supaya laporan CSV bisa menyertakannya. Menjalankannya ulang
        # saat mengekspor akan memakan waktu yang sama lagi, dan lebih buruk:
        # hasilnya bisa berbeda dari yang tertera di layar kalau pelatihannya
        # sempat berlanjut di antara keduanya.
        _KONFORM["gradien_terakhir"] = hasil
        kosongkan(wadah)

        lencana = html.SPAN(
            "LOLOS" if hasil["lolos"] else "GAGAL",
            Class="lencana lencana--%s" % ("benar" if hasil["lolos"] else "salah"),
        )
        ringkas = html.P()
        ringkas <= lencana
        ringkas <= html.SPAN(
            "  Galat relatif terburuk %s pada %d parameter. Ambangnya 1e-5."
            % (ilmiah(hasil["terburuk"], 3), len(hasil["rincian"]))
        )
        wadah <= ringkas

        wadah <= html.P(
            "Perambatan balik menghitung turunan dengan aturan rantai; selisih "
            "hingga menghitungnya dengan menggeser bobotnya sedikit lalu melihat "
            "galatnya berubah berapa. Keduanya harus sepakat. Kalau tidak, "
            "perambatan baliknya salah — dan jaringan yang gradiennya salah tetap "
            "sering terlihat belajar, hanya berhenti di tempat yang keliru.",
            Class="catatan",
        )

        wadah <= tafsir_pemeriksaan(hasil)

        bungkus = html.DIV(Class="gulir-x")
        t = html.TABLE()
        kepala = html.TR()
        for h in ("parameter", "nilai", "perambatan balik", "selisih hingga", "galat relatif"):
            kepala <= html.TH(h)
        t <= html.THEAD(kepala)
        isi = html.TBODY()
        # Diurutkan menurut galat relatif menurun: kalau ada yang meleset,
        # ia harus muncul di baris pertama, bukan tenggelam di tengah daftar.
        rincian = sorted(hasil["rincian"], key=lambda r: -r["relatif"])
        for r in rincian[:14]:
            nama = (
                "bias L%d n%d" % (r["lapis"], r["ke"])
                if r["jenis"] == "bias"
                else "w L%d n%d←%d" % (r["lapis"], r["ke"], r["dari"])
            )
            baris = html.TR()
            baris <= html.TD(nama)
            baris <= html.TD(n(r["nilai"], 5), Class="num")
            baris <= html.TD(n(r["analitik"], 8), Class="num")
            baris <= html.TD(n(r["numerik"], 8), Class="num")
            baris <= html.TD(ilmiah(r["relatif"], 2), Class="num")
            isi <= baris
        t <= isi
        bungkus <= t
        wadah <= bungkus

        if len(rincian) > 14:
            wadah <= html.P(
                "Menampilkan 14 dari %d parameter, diurutkan dari galat terbesar."
                % len(rincian),
                Class="catatan",
            )

    # Dijadwalkan supaya pesan "menghitung" sempat tergambar lebih dulu.
    timer.set_timeout(kerjakan, 20)


# ---------------------------------------------------------------------------
# Perambatan maju dan balik, langkah demi langkah
# ---------------------------------------------------------------------------


def _bobot_terbesar():
    terbesar = 1e-12
    for lap in K.jaringan.bobot:
        for baris in lap:
            for w in baris:
                if abs(w) > terbesar:
                    terbesar = abs(w)
    return terbesar


def gambar_jejak(jejak):
    """Aliran satu contoh melewati jaringan, maju lalu balik.

    Dua arah digambar dalam satu bidang karena keduanya memang menempuh jalur
    yang sama. Itulah seluruh gagasan perambatan balik: bobot yang dipakai
    meneruskan sinyal ke depan adalah bobot yang sama yang dipakai meneruskan
    galat ke belakang. Menggambarnya sebagai dua diagram terpisah menyembunyikan
    justru hubungan yang paling perlu dilihat.
    """
    ukuran = K.jaringan.ukuran
    L = 620
    T = max(230, max(ukuran) * 62 + 80)
    s = svg("svg")

    def titik(lap, j):
        x = 70 + lap * (L - 150) / max(1, len(ukuran) - 1)
        banyak = ukuran[lap]
        y = 40 + (T - 100) / 2 + (j - (banyak - 1) / 2.0) * 60
        return x, y

    delta_terbesar = 1e-12
    for lap_delta in jejak["delta"]:
        for d in lap_delta:
            if abs(d) > delta_terbesar:
                delta_terbesar = abs(d)
    terbesar_w = _bobot_terbesar()

    # Sisi digambar lebih dulu supaya lingkaran neuron menutupinya, bukan
    # sebaliknya.
    for lap in range(len(K.jaringan.bobot)):
        for j, baris in enumerate(K.jaringan.bobot[lap]):
            for k, w in enumerate(baris):
                x1, y1 = titik(lap, k)
                x2, y2 = titik(lap + 1, j)
                s <= svg(
                    "line",
                    x1="%.1f" % x1,
                    y1="%.1f" % y1,
                    x2="%.1f" % x2,
                    y2="%.1f" % y2,
                    stroke="var(--positif)" if w >= 0 else "var(--negatif)",
                    stroke_width="%.2f" % (0.4 + 2.6 * abs(w) / terbesar_w),
                    opacity="0.5",
                )

    nama_lapis = ["masukan"] + ["tersembunyi"] * (len(ukuran) - 2) + ["keluaran"]
    for lap in range(len(ukuran)):
        x, _ = titik(lap, 0)
        t = svg("text", x="%.1f" % x, y=20, text_anchor="middle", font_size=10,
                fill="var(--tinta-3)")
        t.textContent = nama_lapis[lap]
        s <= t

        for j in range(ukuran[lap]):
            cx, cy = titik(lap, j)
            s <= svg(
                "circle",
                cx="%.1f" % cx,
                cy="%.1f" % cy,
                r=19,
                fill="var(--latar-3)",
                stroke="var(--garis-tegas)",
                stroke_width=1.4,
            )
            t = svg("text", x="%.1f" % cx, y="%.1f" % (cy + 4), text_anchor="middle",
                    font_size=10, fill="var(--tinta)")
            t.textContent = n(jejak["aktivasi"][lap][j], 3)
            s <= t

            # Delta hanya ada untuk lapis yang punya bobot masuk. Lapis masukan
            # tidak punya, dan menggambar nol di sana akan menyiratkan galatnya
            # sudah habis di situ padahal ia memang tidak pernah sampai ke sana.
            if lap > 0:
                d = jejak["delta"][lap - 1][j]
                jari = 3 + 9 * abs(d) / delta_terbesar
                s <= svg(
                    "circle",
                    cx="%.1f" % cx,
                    cy="%.1f" % (cy + 30),
                    r="%.1f" % jari,
                    fill="var(--negatif)" if d < 0 else "var(--aksen)",
                    opacity="0.8",
                )
                td = svg("text", x="%.1f" % cx, y="%.1f" % (cy + 34 + jari + 7),
                         text_anchor="middle", font_size=8, fill="var(--tinta-3)")
                td.textContent = ilmiah(d, 1)
                s <= td

    terang = (
        "Angka di dalam lingkaran adalah keluaran neuron itu pada perambatan "
        "maju. Bulatan di bawahnya adalah delta \u2014 bagian galat yang sampai ke "
        "neuron itu pada perambatan balik; makin besar bulatannya makin besar "
        "pengaruhnya, dan warnanya menyatakan arahnya. Garis di antara neuron "
        "adalah bobot yang sama untuk kedua arah, dan justru itulah seluruh "
        "gagasan perambatan balik."
    )
    return s, terang, T


def tabel_jejak(jejak):
    """Angka yang sama dengan gambarnya, dalam bentuk yang bisa dibaca teliti."""
    bungkus = html.DIV(Class="gulir-x")
    t = html.TABLE()
    kepala = html.TR()
    for h in ("neuron", "jumlah berbobot z", "keluaran a = f(z)", "delta", "gradien bias"):
        kepala <= html.TH(h)
    t <= html.THEAD(kepala)
    isi = html.TBODY()
    for lap in range(len(K.jaringan.bobot)):
        for j in range(len(K.jaringan.bobot[lap])):
            baris = html.TR()
            baris <= html.TD("L%d n%d" % (lap, j + 1))
            baris <= html.TD(n(jejak["pra"][lap][j], 6), Class="num")
            baris <= html.TD(n(jejak["aktivasi"][lap + 1][j], 6), Class="num")
            baris <= html.TD(ilmiah(jejak["delta"][lap][j], 3), Class="num")
            baris <= html.TD(ilmiah(jejak["gradien_b"][lap][j], 3), Class="num")
            isi <= baris
    t <= isi
    bungkus <= t
    return bungkus


#: Berapa banyak titik data yang ditawarkan sebagai tombol pilihan.
#:
#: Kumpulan cincin punya empat puluh titik. Empat puluh tombol bukan pilihan
#: melainkan dinding, dan delapan sudah cukup memperlihatkan bahwa jejaknya
#: berbeda dari satu contoh ke contoh lain.
BATAS_PILIHAN_TITIK = 8


def gambar_langkah(_ev=None):
    wadah = document["langkah"]
    kosongkan(wadah)

    data = K.data()
    if not data:
        return
    indeks = K.titik_jejak % len(data)
    x, sasaran = data[indeks]
    jejak = K.jaringan.telusuri(x, sasaran)

    pemilih = html.DIV(Class="baris")
    for i in range(min(len(data), BATAS_PILIHAN_TITIK)):
        xi, ti = data[i]
        b = html.BUTTON(
            "(%s, %s) \u2192 %s" % (n(xi[0], 2), n(xi[1], 2), n(ti[0], 0)),
            Class="tombol",
            type="button",
        )
        b.setAttribute("aria-pressed", "true" if i == indeks else "false")

        def buat(k):
            def klik(_e):
                K.titik_jejak = k
                gambar_langkah()

            return klik

        b.bind("click", buat(i))
        pemilih <= b
    wadah <= pemilih

    wadah <= html.P(
        "Masukan (%s, %s), sasaran %s, ramalan %s \u2014 galat contoh ini %s."
        % (
            n(x[0], 3),
            n(x[1], 3),
            n(sasaran[0], 0),
            n(jejak["keluaran"][0], 6),
            ilmiah(jejak["galat"], 3),
        ),
        Class="catatan",
    )

    s_jejak, t_jejak, tinggi = gambar_jejak(jejak)
    wadah <= gambar(
        "Satu contoh melewati jaringan, maju lalu balik",
        t_jejak,
        s_jejak,
        620,
        tinggi,
        [
            ("var(--positif)", "bobot positif"),
            ("var(--negatif)", "bobot negatif / delta negatif"),
            ("var(--aksen)", "delta positif"),
        ],
    )
    wadah <= tabel_jejak(jejak)
    wadah <= html.P(
        "Angka-angka ini bukan tiruan yang dihitung khusus untuk ditampilkan. "
        "Uji test_telusuri_sama_dengan_gradien membandingkannya dengan gradien "
        "yang benar-benar dipakai melatih \u2014 pola bit demi pola bit, pada empat "
        "aktivasi dan empat bentuk jaringan. Termasuk membedakan nol positif "
        "dari nol negatif, yang pernah membuat keduanya berbeda.",
        Class="catatan",
    )


# ---------------------------------------------------------------------------
# Konformansi lintas bahasa, dijalankan di peramban
# ---------------------------------------------------------------------------

#: Berapa baris diperiksa sekali jalan sebelum jam ditengok lagi.
#:
#: Butir terkecil pekerjaannya, bukan besar potongannya. Menengok jam tiap
#: baris akan menambah satu penyeberangan ke JavaScript per baris.
BARIS_SEKALI_JALAN = 20

#: Berapa lama satu potongan konformansi boleh menahan utas tampilan, dalam ms.
#:
#: Diukur di Brython, seluruh 3.796 pernyataannya memakan sekitar 2,4 detik.
#: Dijalankan sekaligus, itu berarti halaman membeku selama 2,4 detik: tombol
#: tidak bisa ditekan, dan sebagian peramban menawarkan menutup tabnya.
ANGGARAN_KONFORM_MS = 40.0

#: Anggaran yang dipakai saat tabnya tidak terlihat.
#:
#: Peramban membatasi ``setTimeout`` di tab tersembunyi menjadi sekitar sekali
#: sedetik. Dengan anggaran 40 milidetik itu berarti 40 milidetik pekerjaan per
#: detik, dan pemeriksaan yang mestinya 2,4 detik berubah menjadi satu menit.
#:
#: Di tab tersembunyi tidak ada tampilan yang perlu dijaga tetap lancar, jadi
#: potongannya diperbesar. Nilainya tetap di bawah ambang "skrip tidak
#: merespons" mana pun, dan kembali mengecil begitu tabnya dilihat lagi.
ANGGARAN_KONFORM_SEMBUNYI_MS = 600.0

_KONFORM = {"jalan": False, "vektor_siap": False}


def jalankan_konformansi(_ev=None):
    """Menjalankan ulang seluruh vektor uji Rust di dalam peramban ini.

    # Kenapa ini ada di halaman dan bukan hanya di CI

    Karena CI menjalankan CPython, dan yang dipakai pengunjung adalah Brython.
    Keduanya Python; keduanya tidak sama. Dua cacat sungguhan di halaman ini
    hanya muncul di peramban dan tidak bisa ditangkap uji CPython mana pun:

    * ``'%.3e' % 2.803e-08`` menghasilkan ``'0.000e+00'`` — yang membuat
      pemeriksa gradien melaporkan galat nol untuk setiap parameter, jauh
      lebih meyakinkan daripada yang sebenarnya;
    * ``math.ldexp(x, 1074)`` melempar ``OverflowError`` untuk subnormal,
      sehingga pola bit terkecil tidak bisa disandi sama sekali.

    Keduanya ditemukan dengan menjalankan pemeriksaan ini di sini. Itulah
    seluruh alasannya: klaim "enam bahasa sepakat sampai ke bit terakhir" tidak
    boleh menjadi kalimat yang harus dipercaya, kalau ia bisa menjadi tombol
    yang bisa ditekan.
    """
    if _KONFORM["jalan"]:
        return
    _KONFORM["jalan"] = True

    wadah = document["konformansi"]
    kosongkan(wadah)
    wadah <= html.P("Mengambil berkas vektor…", Class="catatan")

    # Vektornya diambil sekarang, bukan saat halaman dibuka.
    #
    # Berkasnya 55 KB setelah dimampatkan — seperempat berat halaman ini — dan
    # tidak sebaris pun dibutuhkan sampai tombol tadi ditekan. Memuatnya di muka
    # berarti setiap pengunjung membayar ongkos sebuah tombol yang mungkin tidak
    # pernah ia tekan.
    muat_vektor_lalu(mulai_pemeriksaan)


def muat_vektor_lalu(lanjut):
    """Memastikan mesin virtual vektor sudah dimuat, lalu memanggil ``lanjut``.

    Berkasnya menitipkan modulnya lewat ``update_VFS``, mekanisme yang sama
    dengan pustaka standar Brython. Karena itu ia harus selesai dijalankan
    sebelum ``import nusa.vektor`` dicoba — dan pemuatan skrip bersifat
    asinkron, jadi tidak ada jalan lain selain menunggu peristiwanya.
    """
    if _KONFORM.get("vektor_siap"):
        lanjut()
        return

    # Alamatnya dibaca dari <meta>, bukan ditulis di sini. Perkakas build
    # menempelkan sidik isi pada URL berkas vendor supaya penerbitan baru tidak
    # pernah berpasangan dengan berkas lama yang masih tersimpan di singgahan
    # peramban — dan yang tahu sidik itu hanya perkakas build.
    penunjuk = document.select_one('meta[name="neuronusa-vektor"]')
    rujukan = penunjuk.attrs["content"] if penunjuk else "vendor/vektor_vfs.js"
    alamat = window.URL.new(rujukan, document.baseURI).href
    skrip = document.createElement("script")
    skrip.src = alamat

    def sudah(_ev):
        _KONFORM["vektor_siap"] = True
        lanjut()

    def gagal(_ev):
        _KONFORM["jalan"] = False
        wadah = document["konformansi"]
        kosongkan(wadah)
        wadah <= html.P(
            "Berkas vektor gagal diambil, jadi tidak ada yang bisa diperiksa. "
            "Periksa sambungan jaringan lalu coba lagi.",
            Class="galat",
        )

    skrip.bind("load", sudah)
    skrip.bind("error", gagal)
    document.body.appendChild(skrip)


def mulai_pemeriksaan():
    wadah = document["konformansi"]
    kosongkan(wadah)

    from nusa import konform
    from nusa.vektor import DATA

    bertahap = konform.Bertahap(lambda nama: DATA[nama])
    mulai = window.performance.now()

    batang = html.DIV(Class="kemajuan")
    isi_batang = html.DIV(Class="kemajuan__isi")
    batang <= isi_batang
    batang.setAttribute("role", "progressbar")
    batang.setAttribute("aria-valuemin", "0")
    batang.setAttribute("aria-valuemax", "100")
    batang.setAttribute("aria-valuenow", "0")
    keterangan = html.P("Memeriksa…", Class="catatan")
    wadah <= keterangan
    wadah <= batang

    def potongan():
        anggaran = (
            ANGGARAN_KONFORM_SEMBUNYI_MS if document.hidden else ANGGARAN_KONFORM_MS
        )
        mulai_potongan = window.performance.now()
        dikerjakan = 0
        while True:
            maju = bertahap.kerjakan(BARIS_SEKALI_JALAN)
            dikerjakan += maju
            if maju == 0:
                break
            if window.performance.now() - mulai_potongan >= anggaran:
                break

        if dikerjakan:
            total = bertahap.total_baris
            # Total baris belum diketahui sampai berkas terakhir dibuka, jadi
            # yang ditampilkan adalah kemajuan terhadap yang sudah terlihat.
            # Menampilkannya sebagai persen yang bisa mundur akan lebih
            # membingungkan daripada menampilkan cacahnya.
            persen = int(100 * bertahap.baris_selesai / total) if total else 0
            isi_batang.style.width = "%d%%" % persen
            batang.setAttribute("aria-valuenow", str(persen))
            keterangan.text = "Memeriksa… %d baris vektor, %d pernyataan." % (
                bertahap.baris_selesai,
                bertahap.laporan.total,
            )
            timer.set_timeout(potongan, 0)
            return

        _KONFORM["jalan"] = False
        lama_ms = window.performance.now() - mulai
        tampilkan_konformansi(bertahap.laporan, lama_ms)

    timer.set_timeout(potongan, 0)


def tampilkan_konformansi(laporan, lama_ms):
    wadah = document["konformansi"]
    kosongkan(wadah)

    lolos = laporan.lolos
    ringkas = html.P()
    ringkas <= html.SPAN(
        "COCOK" if lolos else "TIDAK COCOK",
        Class="lencana lencana--%s" % ("benar" if lolos else "salah"),
    )
    ringkas <= html.SPAN(
        "  %d pernyataan diperiksa di peramban ini dalam %s detik, %d tidak cocok."
        % (laporan.total, n(lama_ms / 1000.0, 2), laporan.total_gagal)
    )
    wadah <= ringkas

    for pesan in laporan.galat_muat:
        wadah <= html.P("Vektor tidak terbaca — " + pesan, Class="galat")

    bungkus = html.DIV(Class="gulir-x")
    t = html.TABLE()
    kepala = html.TR()
    for h in ("berkas vektor", "pernyataan", "keterbandingan", "ULP maks", "hasil"):
        kepala <= html.TH(h)
    t <= html.THEAD(kepala)
    isi = html.TBODY()
    for b in laporan.berkas:
        baris = html.TR()
        baris <= html.TD(b.nama)
        baris <= html.TD(str(b.diperiksa), Class="num")
        baris <= html.TD(b.tingkat)
        baris <= html.TD(str(b.ulp_maks), Class="num")
        baris <= html.TD("cocok" if b.lolos else "%d GAGAL" % b.gagal)
        isi <= baris
    t <= isi
    bungkus <= t
    wadah <= bungkus

    if laporan.ketidakcocokan:
        wadah <= html.P(
            "Pola bit yang berbeda — harapan diambil dari vektor Rust:",
            Class="catatan",
        )
        bungkus2 = html.DIV(Class="gulir-x")
        t2 = html.TABLE()
        kepala2 = html.TR()
        for h in ("baris", "yang diuji", "harap", "dapat", "ULP"):
            kepala2 <= html.TH(h)
        t2 <= html.THEAD(kepala2)
        isi2 = html.TBODY()
        for k in laporan.ketidakcocokan:
            baris = html.TR()
            baris <= html.TD("%s:%d" % (k.berkas, k.nomor))
            baris <= html.TD(k.konteks)
            baris <= html.TD(k.harap, Class="num")
            baris <= html.TD(k.dapat, Class="num")
            baris <= html.TD("—" if k.ulp is None else str(k.ulp), Class="num")
            isi2 <= baris
        t2 <= isi2
        bungkus2 <= t2
        wadah <= bungkus2

    # Selisih ULP yang bukan nol dijelaskan, bukan disembunyikan — dan
    # dijelaskan **terpisah menurut tingkatnya**, karena angka yang sama
    # berarti hal yang berbeda di tingkat yang berbeda.
    #
    # Bentuk pertama catatan ini menyatakan seluruh selisih "jauh di dalam
    # batas 4 ULP". Itu salah, dan situs yang sudah terbit yang
    # membuktikannya: ml_gain.tsv di peramban menunjukkan 64 ULP. Ia tetap
    # lolos, karena toleransi CancellingDifference memang tidak diukur pada
    # hasilnya. Menyebut 64 sebagai "di dalam batas 4" adalah menutupi
    # perbedaan yang justru paling menarik di seluruh tabel ini.
    ulp_bit = max([b.ulp_maks for b in laporan.berkas if b.tingkat == "BitExact"] or [0])
    ulp_dekat = max(
        [b.ulp_maks for b in laporan.berkas if b.tingkat.startswith("NearlyEqual")] or [0]
    )
    ulp_batal = max(
        [
            b.ulp_maks
            for b in laporan.berkas
            if b.tingkat.startswith("CancellingDifference")
        ]
        or [0]
    )

    if ulp_bit == 0 and (ulp_dekat or ulp_batal):
        wadah <= html.P(
            "Perhatikan kolom ULP maks. Seluruh berkas BitExact nol \u2014 di situ "
            "memang tidak boleh ada selisih sedikit pun, dan tidak ada. Yang "
            "bukan nol semuanya jatuh di berkas yang tingkat keterbandingannya "
            "sudah menyatakan kelonggaran di muka.",
            Class="catatan",
        )

    if ulp_dekat:
        wadah <= html.P(
            "Berkas NearlyEqual(4) meleset sampai %d ULP. IEEE-754 mewajibkan "
            "penjumlahan, pengurangan, perkalian, pembagian, dan akar kuadrat "
            "dibulatkan dengan benar \u2014 tetapi tidak exp, log, maupun pow. Python "
            "di peramban menghitung ketiganya lewat pustaka matematika "
            "JavaScript, yang menempuh jalan berbeda dari pustaka C yang dipakai "
            "CPython di CI. Di CI angka ini nol; di sini tidak. Keduanya benar."
            % ulp_dekat,
            Class="catatan",
        )

    if ulp_batal:
        wadah <= html.P(
            "Dan perhatikan ml_gain.tsv: %d ULP, jauh di luar empat \u2014 tetapi "
            "tetap cocok. Bukan kelonggaran yang dilebarkan diam-diam. "
            "CancellingDifference mengukur toleransinya pada skala masukan, "
            "bukan pada hasil. Perolehan informasi adalah selisih dua entropi "
            "yang hampir sama besar; pengurangan seperti itu membuang digit "
            "berarti di depan dan memperbesar galat relatifnya berlipat-lipat, "
            "sampai puluhan kali. Menuntut ketepatan pada hasilnya adalah "
            "menuntut sesuatu yang tidak dimiliki angka mana pun di sana. Angka "
            "%d inilah pembalikan yang paling jelas: di CPython ia nol, dan "
            "tingkat keterbandingan ini yang membuat perbedaannya terlihat "
            "sebagai keterangan alih-alih sebagai kegagalan."
            % (ulp_batal, ulp_batal),
            Class="catatan",
        )

    wadah <= html.P(
        "Angkanya berpindah antar bahasa sebagai pola bit heksadesimal 16 digit, "
        "bukan sebagai desimal. “BitExact” menuntut kecocokan sampai bit "
        "terakhir. “NearlyEqual(4)” memberi kelonggaran empat ULP, dan hanya "
        "untuk perhitungan yang menyentuh exp atau log — IEEE-754 memang tidak "
        "mewajibkan keduanya dibulatkan dengan benar. "
        "“CancellingDifference(4)” mengukur kelonggarannya pada skala masukan, "
        "bukan pada hasil: perolehan informasi adalah selisih dua entropi yang "
        "hampir sama besar, dan pengurangan seperti itu memperbesar galat "
        "relatifnya berlipat-lipat.",
        Class="catatan",
    )


# ---------------------------------------------------------------------------
# Pelatihan
# ---------------------------------------------------------------------------

#: Berapa lama satu potongan pelatihan boleh menahan utas tampilan, dalam ms.
#:
#: Bukan jumlah epoch tetap. Satu epoch memakan waktu yang jauh berbeda antara
#: XOR dengan empat titik dan cincin dengan empat puluh, antara empat neuron
#: tersembunyi dan delapan, antara telepon dan meja kerja. Jumlah tetap yang
#: mulus di satu keadaan akan membekukan halaman di keadaan lain, dan yang
#: sebenarnya dijaga memang waktunya — jadi waktulah yang diukur.
ANGGARAN_HITUNG_MS = 24.0

#: Jarak terpendek antara dua penggambaran bagian yang mahal, dalam ms.
#:
#: Bidang keputusan berubah pelan. Menggambarnya tiga kali sedetik tidak
#: memperlihatkan apa pun yang tidak terlihat pada satu setengah kali sedetik,
#: tetapi menahan utas tampilan tiga kali lebih lama.
JEDA_BERAT_MS = 700.0

#: Panjang riwayat galat yang disimpan.
#:
#: Kurva dengan sepuluh ribu titik tidak lebih informatif daripada kurva dengan
#: tiga ratus, tetapi menggambarnya ulang tiap potongan membuat halaman
#: tersendat.
BATAS_RIWAYAT = 300


def satu_potongan():
    if not K.melatih:
        return
    data = K.data()
    mulai = window.performance.now()
    # Sekurang-kurangnya satu epoch tiap potongan, supaya pelatihan tetap maju
    # bahkan pada perangkat yang satu epochnya saja sudah melewati anggaran.
    while True:
        K.maju_satu_epoch()
        if window.performance.now() - mulai >= ANGGARAN_HITUNG_MS:
            break

    K.catat_riwayat()
    galat = K.riwayat[-1]

    if math.isnan(galat) or math.isinf(galat):
        K.melatih = False
        # Penjaga, bukan gejala yang diharapkan. Lapis keluaran sigmoid
        # mengurung galat di bawah 0,25, jadi sejauh yang terukur cabang ini
        # tidak pernah tercapai. Ia tetap ada karena berhenti dengan pesan
        # yang jujur lebih baik daripada menggambar NaN di setiap gambar.
        K.pesan = (
            "Pelatihan menghasilkan nilai yang tidak berhingga pada epoch %d dan "
            "dihentikan. Ini tidak diharapkan terjadi pada arsitektur ini — "
            "kalau Anda melihatnya, setelan yang Anda pakai menemukan sesuatu "
            "yang belum pernah terukur. Ulang dari awal untuk melanjutkan."
            % K.epoch
        )
        perbarui_tombol()
        gambar_ulang()
        return

    sekarang = window.performance.now()
    berat = sekarang - K.gambar_berat_terakhir >= JEDA_BERAT_MS
    if berat:
        K.gambar_berat_terakhir = sekarang
    gambar_ulang(berat)

    timer.set_timeout(satu_potongan, 0)


def perbarui_tombol():
    document["mulai"].text = "Berhenti" if K.melatih else "Latih"


def toggle_latih(_ev):
    K.melatih = not K.melatih
    perbarui_tombol()
    if K.melatih:
        satu_potongan()
    else:
        # Menggambar penuh saat berhenti. Selama melatih bagian yang mahal
        # sengaja dilewati, jadi tanpa ini yang tertinggal di layar adalah
        # bidang keputusan dari beberapa ratus milidetik yang lalu — tidak
        # sepadan dengan angka di sebelahnya.
        gambar_ulang()


def ulang(_ev):
    K.melatih = False
    perbarui_tombol()
    K.bangun()
    gambar_ulang()
    kosongkan(document["gradien"])


def satu_epoch(_ev):
    K.maju_satu_epoch()
    K.catat_riwayat()
    gambar_ulang()


# ---------------------------------------------------------------------------
# Kontrol
# ---------------------------------------------------------------------------


def bidang_geser(label, minimum, maksimum, langkah, nilai, bantuan, saat_ubah, format_nilai=None):
    if format_nilai is None:
        format_nilai = lambda v: n(v, 2)  # noqa: E731
    bungkus = html.LABEL(Class="bidang")
    baris = html.SPAN(Class="bidang__label")
    baris <= html.SPAN(label)
    pembacaan = html.SPAN(format_nilai(nilai), Class="bidang__nilai")
    baris <= pembacaan
    bungkus <= baris
    isian = html.INPUT(type="range", min=minimum, max=maksimum, step=langkah, value=nilai)

    def ubah(ev):
        v = float(ev.target.value)
        pembacaan.text = format_nilai(v)
        saat_ubah(v)

    isian.bind("input", ubah)
    bungkus <= isian
    if bantuan:
        bungkus <= html.SPAN(bantuan, Class="bidang__bantuan")
    return bungkus


def tombol_pilihan(label, pilihan, terpilih, saat_pilih):
    bungkus = html.DIV(Class="bidang")
    bungkus <= html.SPAN(label, Class="bidang__label")
    baris = html.DIV(Class="baris")
    for nilai, teks in pilihan:
        b = html.BUTTON(teks, Class="tombol", type="button")
        b.setAttribute("aria-pressed", "true" if nilai == terpilih else "false")

        def buat(v):
            def klik(_ev):
                saat_pilih(v)
            return klik

        b.bind("click", buat(nilai))
        baris <= b
    bungkus <= baris
    return bungkus


def gambar_kontrol():
    kontrol = document["kontrol"]
    kosongkan(kontrol)

    def set_dataset(v):
        K.dataset = v
        tulis_tautan()
        K.bangun()
        gambar_kontrol()
        gambar_ulang()

    def set_aktivasi(v):
        K.aktivasi = v
        tulis_tautan()
        K.bangun()
        gambar_kontrol()
        gambar_ulang()

    def set_tersembunyi(v):
        K.tersembunyi = int(v)
        tulis_tautan()
        K.bangun()
        gambar_kontrol()
        gambar_ulang()

    def set_laju(v):
        K.laju = v
        tulis_tautan()
        perbarui_peringatan()

    def set_momentum(v):
        K.momentum = v
        tulis_tautan()
        perbarui_peringatan()

    def set_benih(v):
        K.benih = int(v)
        tulis_tautan()
        K.bangun()
        gambar_ulang()

    kontrol <= kartu(
        "Masalah",
        tombol_pilihan(
            "Kumpulan data",
            [(k, v[0]) for k, v in DATASET.items()]
            + ([("sendiri", "Data sendiri")] if K.data_sendiri else []),
            K.dataset,
            set_dataset,
        ),
        html.P(
            "XOR dan cincin tidak terpisahkan garis lurus mana pun. Setel neuron "
            "tersembunyi ke nol pada keduanya, dan perhatikan jaringannya berhenti "
            "di sekitar setengah — itulah temuan Minsky dan Papert yang "
            "menghentikan penelitian bidang ini hampir dua dekade.",
            Class="catatan",
        ),
    )

    kontrol <= kartu_data_sendiri()

    kontrol <= kartu(
        "Bentuk jaringan",
        bidang_geser(
            "Neuron tersembunyi", 0, 8, 1, K.tersembunyi,
            "Nol berarti perceptron satu lapis, tanpa lapis tersembunyi sama sekali.",
            set_tersembunyi, lambda v: str(int(v)),
        ),
        tombol_pilihan(
            "Aktivasi lapis tersembunyi",
            [(k, k) for k in AKTIVASI],
            K.aktivasi,
            set_aktivasi,
        ),
        bidang_geser(
            "Benih bobot awal", 1, 200, 1, K.benih,
            "Benih yang sama menghasilkan bobot awal yang sama persis, sehingga hasil pelatihannya bisa diulang dan dibandingkan.",
            set_benih, lambda v: str(int(v)),
        ),
    )

    def set_cacat(v):
        K.cacat = v
        tulis_tautan()
        K.bangun()
        gambar_kontrol()
        gambar_ulang()

    kartu_cacat = kartu(
        "Sabotase",
        html.P(
            "Halaman ini menyatakan bahwa jaringan yang gradiennya salah tetap "
            "sering terlihat belajar. Jangan percayai itu — nyalakan salah "
            "satu cacat di bawah, latih, lalu perhatikan kurva galatnya.",
            Class="catatan",
        ),
        tombol_pilihan(
            "Cacat perambatan balik",
            [(k, v[0]) for k, v in CACAT.items()],
            K.cacat,
            set_cacat,
        ),
    )
    label, tempat, tertangkap, penjelasan = CACAT[K.cacat]
    kartu_cacat <= html.P(penjelasan, Class="catatan")
    if K.cacat != "tidak_ada":
        kartu_cacat <= html.P(
            "Pemeriksa gradien %s cacat ini."
            % ("MENANGKAP" if tertangkap else "TIDAK BISA menangkap"),
            Class="lencana lencana--%s" % ("benar" if tertangkap else "salah"),
        )
        kartu_cacat <= html.P(
            "Sebuah jaringan pembanding dengan bobot awal yang sama persis dan "
            "perambatan balik yang benar ikut dilatih berdampingan. Ia muncul "
            "sebagai garis putus-putus di kurva galat.",
            Class="catatan",
        )
    kontrol <= kartu_cacat

    kontrol <= kartu(
        "Pelatihan",
        bidang_geser("Laju belajar", 0.01, 5.0, 0.01, K.laju, None, set_laju),
        bidang_geser(
            "Momentum", 0.0, 0.99, 0.01, K.momentum,
            "Momentum menjumlahkan langkah sebelumnya, sehingga langkah tunaknya laju ÷ (1 − momentum).",
            set_momentum,
        ),
        html.DIV(id="peringatan"),
    )

    kontrol <= kartu_berbagi()

    baris = html.DIV(Class="baris")
    b_mulai = html.BUTTON("Latih", Class="tombol tombol--utama", type="button", id="mulai")
    b_mulai.bind("click", toggle_latih)
    baris <= b_mulai
    b_satu = html.BUTTON("Satu epoch", Class="tombol", type="button")
    b_satu.bind("click", satu_epoch)
    baris <= b_satu
    b_ulang = html.BUTTON("Ulang dari awal", Class="tombol", type="button")
    b_ulang.bind("click", ulang)
    baris <= b_ulang
    kontrol <= baris

    perbarui_peringatan()


#: Laju efektif yang, pada arsitektur ini, mulai membuat pelatihan macet.
#:
#: Angkanya diukur, bukan ditebak. Menjalankan XOR dan cincin pada tanh,
#: sigmoid, dan relu memperlihatkan bahwa laju efektif sampai sekitar 50 masih
#: melatih dengan baik pada tanh dan sigmoid, sementara di atas sekitar 200
#: keduanya berhenti di keluaran tetap. Batasnya bergantung aktivasi, jadi
#: angka ini disebut ambang perhatian, bukan ambang kegagalan.
AMBANG_LAJU = 100.0


def kartu_data_sendiri():
    """Menempelkan kumpulan data sendiri.

    Tiga kumpulan bawaan cukup untuk menjelaskan gagasannya dan tidak cukup
    untuk menjawab pertanyaan yang sebenarnya dibawa orang ke halaman seperti
    ini: *apakah ini bekerja pada data saya.* Menjawab pertanyaan itu menuntut
    data mereka, bukan data kami.
    """
    k = kartu("Data sendiri")
    k <= html.P(
        "Tempelkan tiga kolom: dua angka masukan dan satu kelas (0 atau 1). "
        "Pemisahnya boleh koma, titik koma, tab, atau spasi \u2014 dan koma "
        "desimal gaya Indonesia diterima. Angkanya akan diskalakan ke rentang "
        "0 sampai 1, dan rentang aslinya diberitahukan.",
        Class="catatan",
    )

    kotak = html.TEXTAREA(K.teks_data, id="data-sendiri", rows=7)
    kotak.setAttribute("spellcheck", "false")
    kotak.setAttribute(
        "placeholder", "165; 55,0; 0\n170; 60,5; 0\n175; 72,0; 1\n180; 85,5; 1"
    )
    kotak.setAttribute("aria-label", "Tempelkan data Anda di sini")
    k <= kotak

    baris = html.DIV(Class="baris")
    b_pakai = html.BUTTON("Pakai data ini", Class="tombol tombol--utama", type="button")
    b_pakai.bind("click", pakai_data_sendiri)
    baris <= b_pakai
    b_contoh = html.BUTTON("Isi contoh", Class="tombol", type="button")
    b_contoh.bind("click", isi_contoh_data)
    baris <= b_contoh
    k <= baris

    k <= html.DIV(id="kabar-data", Class="kabar-wadah")
    return k


def isi_contoh_data(_ev=None):
    document["data-sendiri"].value = pengurai_data.CONTOH
    kosongkan(document["kabar-data"])
    document["kabar-data"] <= html.SPAN(
        "Contoh diisi \u2014 tekan \u201cPakai data ini\u201d.", Class="kabar"
    )


def pakai_data_sendiri(_ev=None):
    wadah = document["kabar-data"]
    kosongkan(wadah)
    teks = document["data-sendiri"].value

    try:
        hasil = pengurai_data.urai(teks)
    except pengurai_data.Galat as galat:
        # Pesannya memang ditulis untuk dibaca pengguna, jadi ditampilkan apa
        # adanya. Menggantinya dengan "data tidak sah" akan membuang satu-
        # satunya keterangan yang bisa menolong.
        wadah <= html.P(str(galat), Class="galat")
        return

    K.melatih = False
    perbarui_tombol()
    K.teks_data = teks
    K.data_sendiri = hasil["data"]
    K.skala_sendiri = hasil["skala"]
    K.catatan_data = hasil["catatan"]
    K.dataset = "sendiri"
    tulis_tautan()
    K.bangun()
    gambar_kontrol()
    gambar_ulang()

    kabar = document["kabar-data"]
    kabar <= html.P(
        "%d baris dipakai." % len(hasil["data"]),
        Class="kabar kabar--benar",
    )
    for c in hasil["catatan"]:
        kabar <= html.P(c, Class="catatan")


# ---------------------------------------------------------------------------
# Ekspor
# ---------------------------------------------------------------------------


def unduh(nama, teks, jenis):
    """Menyerahkan sebuah berkas kepada pengguna.

    Memakai objek URL dan bukan ``data:`` URI. Yang terakhir dibatasi panjang
    di sebagian peramban, dan laporan dengan empat ratus baris data melewati
    batas itu tanpa memberi tanda apa pun \u2014 unduhannya sekadar tidak terjadi.

    Objek URL-nya dilepas segera setelah dipakai. Yang tidak dilepas menahan
    seluruh isi berkasnya di memori sampai tabnya ditutup.
    """
    gumpal = window.Blob.new([teks], {"type": jenis})
    alamat = window.URL.createObjectURL(gumpal)
    tautan_unduh = document.createElement("a")
    tautan_unduh.href = alamat
    tautan_unduh.download = nama
    document.body.appendChild(tautan_unduh)
    tautan_unduh.click()
    document.body.removeChild(tautan_unduh)
    window.URL.revokeObjectURL(alamat)


def unduh_csv(_ev=None):
    wadah = document["kabar-ekspor"]
    kosongkan(wadah)
    try:
        baris = ekspor.laporan_baris(K, _KONFORM.get("gradien_terakhir"))
        nama = ekspor.nama_berkas(K, "csv")
        unduh(nama, ekspor.csv(baris), "text/csv;charset=utf-8")
        wadah <= html.SPAN("Diunduh: %s" % nama, Class="kabar kabar--benar")
    except Exception as galat:  # noqa: BLE001 - unduhan bisa ditolak peramban
        wadah <= html.SPAN(
            "Peramban menolak unduhan: %s" % galat, Class="kabar"
        )


def cetak(_ev=None):
    """Membuka dialog cetak peramban, yang juga bisa menyimpan sebagai PDF.

    # Kenapa bukan pustaka PDF

    Karena menyusun PDF di peramban menuntut pustaka berukuran ratusan
    kilobyte \u2014 lebih besar daripada seluruh mesin jaringan syaraf di proyek
    ini, dan hanya untuk menghasilkan berkas yang sudah bisa dihasilkan
    peramban itu sendiri.

    Dialog cetak juga memberi pengguna hal yang tidak diberikan pustaka mana
    pun: ukuran kertas, orientasi, dan pratayang sebelum berkasnya jadi.
    """
    window.print()


def kartu_berbagi():
    """Tautan yang bisa dibagikan, dan pemilih tema.

    Keduanya di satu kartu karena keduanya menjawab pertanyaan yang sama:
    bagaimana keadaan halaman ini bertahan di luar sesi sekarang.
    """
    k = kartu("Bagikan dan tampilan")
    k <= html.P(
        "Alamat di bilah alamat selalu mencerminkan setelan sekarang. Siapa pun "
        "yang membukanya akan mendapat jaringan yang sama persis \u2014 benih yang "
        "sama berarti bobot awal yang sama, dan pelatihan yang sama bisa diulang. "
        "Itu bukan kenyamanan tambahan melainkan syarat: hasil yang tidak bisa "
        "diulang tidak bisa diperiksa siapa pun.",
        Class="catatan",
    )
    b = html.BUTTON("Salin tautan setelan ini", Class="tombol", type="button")
    b.bind("click", salin_tautan)
    k <= b
    k <= html.DIV(id="kabar-tautan", Class="kabar-wadah")

    k <= html.P(
        "Unduh seluruh hasilnya \u2014 setelan, ramalan tiap titik, bobot, kurva "
        "galat, dan pemeriksaan gradien kalau sudah dijalankan \u2014 sebagai satu "
        "berkas yang bisa dibuka Excel, atau cetak halamannya menjadi PDF.",
        Class="catatan",
    )
    baris_ekspor = html.DIV(Class="baris")
    b_csv = html.BUTTON("Unduh CSV (Excel)", Class="tombol", type="button")
    b_csv.bind("click", unduh_csv)
    baris_ekspor <= b_csv
    b_cetak = html.BUTTON("Cetak / simpan PDF", Class="tombol", type="button")
    b_cetak.bind("click", cetak)
    baris_ekspor <= b_cetak
    k <= baris_ekspor
    k <= html.DIV(id="kabar-ekspor", Class="kabar-wadah")

    def set_tema(v):
        pasang_tema(v)

    k <= tombol_pilihan("Tema", TEMA, K.tema, set_tema)
    return k


def perbarui_peringatan():
    wadah = document["peringatan"]
    kosongkan(wadah)
    efektif = K.jaringan.laju_efektif(K.laju, K.momentum)
    teks = "Laju efektif %s = %s ÷ (1 − %s)." % (n(efektif, 3), n(K.laju, 2), n(K.momentum, 2))
    if efektif > AMBANG_LAJU:
        # Perhatikan yang **tidak** dikatakan di sini: bahwa angkanya meluap.
        # Lapis keluaran jaringan ini sigmoid, sehingga galatnya terkurung di
        # bawah 0,25 dan tidak pernah bisa meledak menjadi tak hingga. Cara
        # gagalnya berbeda, dan menyebut cara gagal yang keliru membuat
        # pembaca mencari gejala yang tidak akan pernah muncul.
        wadah <= html.P(
            teks + " Sebesar ini pelatihan biasanya tidak meledak melainkan macet: "
            "keluarannya jenuh di 0 atau 1, turunan sigmoidnya nyaris nol, dan "
            "galatnya berhenti di satu angka sambil jaringan menjawab sama untuk "
            "setiap masukan. Jalankan dan perhatikan — kurvanya mendatar, bukan "
            "meroket.",
            Class="galat",
        )
    else:
        wadah <= html.P(teks, Class="catatan")


# ---------------------------------------------------------------------------
# Penyalaan
# ---------------------------------------------------------------------------


def mulai():
    document["memuat"].style.display = "none"
    # Atribut ``hidden`` dilepas, bukan ditimpa dengan ``style.display``.
    # Menimpanya memang berhasil menampilkan elemennya, tetapi meninggalkan
    # ``hidden`` yang tetap terbaca pembaca layar sebagai "tersembunyi" —
    # tampilan dan makna jadi bertentangan.
    document["aplikasi"].removeAttribute("hidden")
    # Tema dipasang sebelum apa pun tergambar, supaya kanvas membaca warna yang
    # benar sejak gambar pertama alih-alih berkedip sekali. Kanvas menyimpan
    # piksel; SVG di sekelilingnya mengikuti CSS dengan sendirinya.
    pasang_tema(tema_tersimpan(), gambar_lagi=False)
    tulis_tautan()
    gambar_kontrol()
    gambar_ulang()
    document["periksa"].bind("click", jalankan_periksa_gradien)
    document["jalankan-konformansi"].bind("click", jalankan_konformansi)
    window.addEventListener("hashchange", terapkan_tautan)
    # Angka ini dihitung, bukan diketik: kalau modul fx berubah dan pola bitnya
    # bergeser, teks di halaman ikut bergeser dan perbedaannya terlihat.
    document["bukti-bit"].text = fx.ke_hex(0.1)


mulai()
