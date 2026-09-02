"""Menyusun hasil menjadi berkas yang bisa dibuka di luar halaman ini.

# Kenapa CSV dan bukan XLSX

Karena XLSX adalah arsip ZIP berisi beberapa berkas XML, dan menyusunnya di
peramban menuntut pustaka berukuran ratusan kilobyte — lebih besar daripada
seluruh mesin jaringan syaraf di proyek ini. CSV dibuka Excel, LibreOffice,
Google Sheets, pandas, dan R tanpa satu bita pun tambahan.

Yang tidak boleh dilewatkan agar CSV itu benar-benar terbuka rapi di Excel:

1. **Tanda urutan bita (BOM) UTF-8 di depan.** Tanpa itu Excel di Windows
   membaca berkasnya sebagai ANSI, dan setiap huruf beraksen berubah menjadi
   sampah.
2. **Baris ``sep=,`` di baris pertama.** Excel dengan pengaturan wilayah
   Indonesia memakai titik koma sebagai pemisah, dan tanpa petunjuk ini
   seluruh baris masuk ke satu kolom. Baris itu resmi dikenali Excel dan
   diabaikan pembaca CSV lain yang melewati baris pertama sebagai judul.
3. **Akhir baris CRLF**, seperti yang dituntut RFC 4180.

# Kenapa isinya ikut berganti bahasa

Karena berkas yang diunduh adalah bagian dari situs ini, bukan lampiran yang
kebetulan menempel. Sebelumnya seluruh laporan ditulis dalam bahasa Indonesia
saja, sehingga pengunjung yang membaca situs ini dalam bahasa Inggris
mengunduh berkas yang tidak bisa ia baca — dan tidak akan pernah
melaporkannya, karena ia hanya akan menyimpulkan berkasnya memang begitu.

Kunci-kuncinya berawalan ``eks_`` di :mod:`nusa.bahasa`, dan diuji dengan
aturan yang sama seperti untai antarmuka: kedua bahasa wajib ada, wajib
berbeda, dan wajib dipakai.

.Deckyx
"""

from . import bahasa
from .jaringan import DATASET

_CR = chr(13)
_LF = chr(10)
_BARIS = _CR + _LF
_BOM = "﻿"


def _sel(nilai):
    """Satu sel CSV, dikutip bila perlu.

    Angka ditulis apa adanya dengan titik desimal. Excel berwilayah Indonesia
    membaca ``0.5`` sebagai teks, bukan angka — tetapi menuliskannya sebagai
    ``0,5`` akan bertabrakan dengan pemisah kolom, dan berkas yang kolomnya
    bergeser jauh lebih merepotkan daripada angka yang perlu sekali klik
    "ubah ke angka". Pilihan ini disebut di catatan kaki berkasnya.
    """
    if isinstance(nilai, bool):
        teks = "1" if nilai else "0"
    elif isinstance(nilai, float):
        teks = repr(nilai)
    else:
        teks = str(nilai)
    if any(c in teks for c in (',', '"', _CR, _LF)):
        teks = '"' + teks.replace('"', '""') + '"'
    return teks


def csv(baris):
    """Menyusun daftar baris menjadi teks CSV yang siap diunduh."""
    isi = [_BOM + "sep=,"]
    for b in baris:
        isi.append(",".join(_sel(sel) for sel in b))
    return _BARIS.join(isi) + _BARIS


def laporan_baris(K, hasil_gradien=None):
    """Seluruh isi laporan sebagai daftar baris, siap diubah menjadi CSV.

    Disusun sebagai beberapa blok bertajuk alih-alih satu tabel lebar. Satu
    tabel yang memuat setelan, ramalan, bobot, dan gradien sekaligus akan
    punya kolom yang berarti berbeda di tiap baris — bentuk yang menyulitkan
    dibaca manusia maupun mesin.

    Seluruh labelnya mengikuti bahasa yang sedang aktif. Bahasanya sendiri
    dicatat di kepala berkas, supaya laporan yang beredar lepas dari
    halamannya tetap bisa ditelusuri asalnya.
    """
    t = bahasa.t
    jar = K.jaringan
    data = K.data()
    baris = []

    baris.append([t("eks_judul")])
    baris.append([t("eks_dihasilkan"), t("eks_sumber")])
    baris.append([t("eks_bahasa_berkas"), bahasa.sekarang()])
    baris.append([])

    baris.append([t("eks_setelan")])
    baris.append([t("eks_kumpulan_data"), t("data_nama_" + K.dataset)
                  if K.dataset in DATASET else t("data_sendiri")])
    baris.append([t("eks_tersembunyi"), K.tersembunyi])
    # Nama aktivasi tidak diterjemahkan: "tanh" dan "relu" adalah nama fungsi,
    # bukan kata, dan menerjemahkannya akan membuat laporannya justru lebih
    # sulit dicocokkan dengan pustaka mana pun.
    baris.append([t("eks_aktivasi"), K.aktivasi])
    baris.append([t("eks_benih"), K.benih])
    baris.append([t("eks_laju"), K.laju])
    baris.append([t("eks_momentum_baris"), K.momentum])
    baris.append([t("eks_laju_efektif"), jar.laju_efektif(K.laju, K.momentum)])
    baris.append([t("eks_cacat"), t("cacat_nama_" + K.cacat)])
    baris.append([t("eks_epoch"), K.epoch])
    baris.append([t("eks_parameter"), jar.jumlah_parameter()])
    baris.append([])

    galat = jar.galat(data)
    benar = sum(1 for x, sasaran in data if round(jar.ramal(x)[0]) == int(sasaran[0]))
    baris.append([t("eks_hasil")])
    baris.append([t("eks_galat_rata"), galat])
    baris.append([t("eks_titik_benar"), benar])
    baris.append([t("eks_titik_semua"), len(data)])
    if K.bayangan is not None:
        baris.append([t("eks_galat_pembanding"), K.bayangan.galat(data)])
    baris.append([])

    baris.append([t("eks_ramalan")])
    baris.append(
        ["x1", "x2", t("eks_kol_sasaran"), t("eks_kol_keluaran"),
         t("eks_kol_selisih"), t("eks_kol_benar")]
    )
    for x, sasaran in data:
        y = jar.ramal(x)[0]
        baris.append(
            [x[0], x[1], sasaran[0], y, abs(y - sasaran[0]), round(y) == int(sasaran[0])]
        )
    baris.append([])

    baris.append([t("eks_bobot")])
    baris.append(
        [t("eks_kol_parameter"), t("eks_kol_lapis"), t("eks_kol_ke"),
         t("eks_kol_dari"), t("eks_kol_nilai")]
    )
    for lap in range(len(jar.bobot)):
        for j, baris_bobot in enumerate(jar.bobot[lap]):
            for k, w in enumerate(baris_bobot):
                baris.append([t("eks_bobot_nama"), lap, j + 1, k + 1, w])
        for j, b in enumerate(jar.bias[lap]):
            baris.append([t("eks_bias_nama"), lap, j + 1, "", b])
    baris.append([])

    baris.append([t("eks_kurva")])
    baris.append([t("eks_kol_riwayat"), t("eks_kol_galat")])
    for i, v in enumerate(K.riwayat):
        baris.append([i, v])
    baris.append([])

    if hasil_gradien:
        baris.append([t("eks_gradien")])
        baris.append(
            [t("eks_hasil_periksa"),
             t("eks_lolos") if hasil_gradien["lolos"] else t("eks_gagal")]
        )
        baris.append([t("eks_terburuk"), hasil_gradien["terburuk"]])
        baris.append([t("eks_ambang"), 1e-5])
        baris.append([])
        baris.append(
            [t("eks_kol_parameter"), t("eks_kol_lapis"), t("eks_kol_ke"),
             t("eks_kol_dari"), t("eks_kol_nilai"), t("eks_kol_analitik"),
             t("eks_kol_numerik"), t("eks_kol_relatif")]
        )
        for r in sorted(hasil_gradien["rincian"], key=lambda x: -x["relatif"]):
            jenis = t("eks_bobot_nama") if r["jenis"] == "bobot" else t("eks_bias_nama")
            baris.append(
                [jenis, r["lapis"], r["ke"] + 1,
                 "" if r["dari"] is None else r["dari"] + 1,
                 r["nilai"], r["analitik"], r["numerik"], r["relatif"]]
            )
        baris.append([])

    baris.append([t("eks_catatan")])
    baris.append([t("eks_catatan_mesin")])
    baris.append([t("eks_catatan_desimal")])
    baris.append([t("eks_catatan_skala")])
    return baris


def nama_berkas(K, akhiran="csv"):
    """Nama berkas yang menyebutkan setelannya, bukan sekadar tanggal.

    Sebuah unduhan bernama ``laporan (3).csv`` tidak bisa dibedakan dari
    tetangganya seminggu kemudian. Nama yang memuat setelannya bisa.
    """
    bagian = [
        "neuronusa",
        str(K.dataset),
        "h%d" % K.tersembunyi,
        str(K.aktivasi),
        "s%d" % K.benih,
        "e%d" % K.epoch,
    ]
    if K.cacat != "tidak_ada":
        bagian.append(K.cacat)
    return "-".join(bagian) + "." + akhiran
