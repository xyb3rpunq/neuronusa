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

.Deckyx
"""

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
    """
    jar = K.jaringan
    data = K.data()
    baris = []

    baris.append(["neuronusa — laporan pelatihan"])
    baris.append(["dihasilkan", "halaman neuronusa (.Deckyx)"])
    baris.append([])

    baris.append(["SETELAN"])
    baris.append(["kumpulan data", K.dataset])
    baris.append(["neuron tersembunyi", K.tersembunyi])
    baris.append(["aktivasi", K.aktivasi])
    baris.append(["benih bobot awal", K.benih])
    baris.append(["laju belajar", K.laju])
    baris.append(["momentum", K.momentum])
    baris.append(["laju efektif", jar.laju_efektif(K.laju, K.momentum)])
    baris.append(["cacat perambatan balik", K.cacat])
    baris.append(["epoch dijalankan", K.epoch])
    baris.append(["jumlah parameter", jar.jumlah_parameter()])
    baris.append([])

    galat = jar.galat(data)
    benar = sum(1 for x, t in data if round(jar.ramal(x)[0]) == int(t[0]))
    baris.append(["HASIL"])
    baris.append(["galat kuadrat rata-rata", galat])
    baris.append(["titik benar", benar])
    baris.append(["titik seluruhnya", len(data)])
    if K.bayangan is not None:
        baris.append(["galat pembanding tanpa cacat", K.bayangan.galat(data)])
    baris.append([])

    baris.append(["RAMALAN TIAP TITIK"])
    baris.append(["x1", "x2", "sasaran", "keluaran", "selisih", "benar"])
    for x, sasaran in data:
        y = jar.ramal(x)[0]
        baris.append(
            [x[0], x[1], sasaran[0], y, abs(y - sasaran[0]), round(y) == int(sasaran[0])]
        )
    baris.append([])

    baris.append(["BOBOT DAN BIAS"])
    baris.append(["parameter", "lapis", "ke", "dari", "nilai"])
    for lap in range(len(jar.bobot)):
        for j, baris_bobot in enumerate(jar.bobot[lap]):
            for k, w in enumerate(baris_bobot):
                baris.append(["bobot", lap, j + 1, k + 1, w])
        for j, b in enumerate(jar.bias[lap]):
            baris.append(["bias", lap, j + 1, "", b])
    baris.append([])

    baris.append(["KURVA GALAT"])
    baris.append(["titik riwayat", "galat"])
    for i, v in enumerate(K.riwayat):
        baris.append([i, v])
    baris.append([])

    if hasil_gradien:
        baris.append(["PEMERIKSAAN GRADIEN"])
        baris.append(["hasil", "LOLOS" if hasil_gradien["lolos"] else "GAGAL"])
        baris.append(["galat relatif terburuk", hasil_gradien["terburuk"]])
        baris.append(["ambang", 1e-5])
        baris.append([])
        baris.append(
            ["parameter", "lapis", "ke", "dari", "nilai", "perambatan balik",
             "selisih hingga", "galat relatif"]
        )
        for r in sorted(hasil_gradien["rincian"], key=lambda x: -x["relatif"]):
            baris.append(
                [r["jenis"], r["lapis"], r["ke"] + 1,
                 "" if r["dari"] is None else r["dari"] + 1,
                 r["nilai"], r["analitik"], r["numerik"], r["relatif"]]
            )
        baris.append([])

    baris.append(["CATATAN"])
    baris.append(
        ["Angka memakai titik sebagai pemisah desimal. Excel berwilayah "
         "Indonesia mungkin membacanya sebagai teks; ubah kolomnya menjadi "
         "angka lewat Data > Text to Columns bila perlu."]
    )
    baris.append(
        ["Nilai x1 dan x2 sudah dalam skala 0 sampai 1. Untuk data tempelan, "
         "rentang aslinya tercantum di halaman."]
    )
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
