"""Membaca kumpulan data yang ditempel pengguna.

# Kenapa ini modul mesin dan bukan bagian dari antarmuka

Karena isinya mengurai teks yang ditulis orang lain. Teks yang ditempel bisa
apa saja: berkas CSV dari Excel dengan titik koma, salinan dari tabel Word
dengan tab, angka Indonesia dengan koma desimal, baris kosong, kolom judul,
atau tiga ribu baris yang akan membekukan halaman. Semuanya harus ditolak atau
diperbaiki dengan pesan yang bisa dimengerti — bukan dengan tumpukan galat.

Kode yang mengurai masukan luar wajib punya uji. Selama ia tinggal di berkas
antarmuka yang mengimpor ``browser``, ia tidak bisa diimpor CPython sama
sekali dan karena itu tidak bisa diuji sama sekali.

# Kenapa datanya dinormalkan, dan kenapa itu diberitahukan

Seluruh gambar di halaman ini menganggap masukannya berada di kotak satuan
nol sampai satu. Data sungguhan tidak pernah begitu: tinggi badan dalam
sentimeter, harga dalam rupiah, suhu dalam derajat. Menolak data seperti itu
berarti menolak hampir semua data sungguhan.

Jadi ia dinormalkan — dan pengguna **diberi tahu** angka yang dipakai
menormalkannya. Penskalaan diam-diam adalah cara paling mudah membuat
seseorang salah menafsirkan grafiknya sendiri.

.Deckyx
"""

#: Batas jumlah baris yang diterima.
#:
#: Bukan batas keamanan melainkan batas kejujuran. Pelatihan di penerjemah
#: Python di dalam peramban memakan sekitar satu milidetik per titik per
#: epoch; seribu titik berarti satu detik per epoch, dan halaman yang
#: mengiyakan permintaan seperti itu hanya akan terlihat rusak.
BATAS_BARIS = 400

#: Batas kolom yang dibaca. Kolom ketiga dan seterusnya diabaikan.
KOLOM = 3

#: Calon pemisah kolom, dari yang paling tidak meragukan.
#:
#: Koma ada di urutan terakhir dengan sengaja. Ia satu-satunya calon yang juga
#: dipakai sebagai pemisah desimal dalam penulisan Indonesia, sehingga baris
#: seperti ``165;55,0;0`` benar-benar bisa dibaca dua cara. Yang lain tidak
#: pernah bermakna ganda.
_PEMISAH = [";", "\t", "|", ","]


class Galat(Exception):
    """Kesalahan yang pesannya memang ditujukan untuk dibaca pengguna."""


def _angka(teks):
    """Membaca satu angka, memaklumi gaya penulisan Indonesia.

    ``3,5`` dan ``3.5`` keduanya diterima. Yang tidak diterima adalah
    ``1.234,5``: pemisah ribuan tidak bisa dibedakan dari desimal tanpa
    menebak, dan menebak angka milik orang lain bukan hal yang pantas
    dilakukan diam-diam.
    """
    t = teks.strip().replace(" ", "")
    if not t:
        raise Galat("ada sel yang kosong")
    if t.count(",") == 1 and t.count(".") == 0:
        t = t.replace(",", ".")
    try:
        nilai = float(t)
    except ValueError:
        raise Galat("bukan angka: %r" % teks.strip()[:20]) from None
    if nilai != nilai or nilai in (float("inf"), float("-inf")):
        raise Galat("angka tidak berhingga: %r" % teks.strip()[:20])
    return nilai


def _bisa_angka(teks):
    try:
        _angka(teks)
        return True
    except Galat:
        return False


def _nilai_pemisah(baris_isi, pemisah):
    """Berapa banyak baris yang terbaca rapi kalau pemisah ini yang dipakai.

    Yang dihitung bukan berapa kali tanda itu muncul melainkan berapa baris
    yang benar-benar menjadi tiga kolom angka karenanya. Tanda yang sering
    muncul tetapi tidak menghasilkan kolom yang masuk akal kalah dari tanda
    yang jarang muncul tetapi menghasilkan.
    """
    cocok = 0
    for baris in baris_isi:
        sel = baris.split(pemisah) if pemisah else baris.split()
        if len(sel) < KOLOM:
            continue
        if all(_bisa_angka(sel[i]) for i in range(KOLOM)):
            cocok += 1
    return cocok


def pilih_pemisah(baris_isi):
    """Memilih pemisah kolom dengan menilai seluruh teks, bukan satu baris.

    # Kenapa tidak cukup "tanda pertama yang ditemukan"

    Karena bentuk pertama fungsi ini memang begitu, dan ia salah membaca data
    Indonesia yang paling lazim. Pada baris ``165, 55,0, 0`` — tiga kolom
    dipisah koma, dengan koma desimal di kolom kedua — koma ditemukan lebih
    dulu, barisnya terbelah menjadi empat, dan seluruh berkas ditolak dengan
    pesan yang membingungkan.

    Menilai seluruh teks menyelesaikannya: pemisah yang benar menghasilkan
    tiga kolom angka pada hampir setiap baris, yang salah tidak menghasilkannya
    pada satu baris pun.
    """
    terbaik = None
    nilai_terbaik = 0
    # Termasuk ``None`` yang berarti dipisah spasi; itu bentuk yang keluar
    # dari banyak alat dan dari salinan tabel Word.
    for p in _PEMISAH + [None]:
        nilai = _nilai_pemisah(baris_isi, p)
        # Perbandingannya tegas ">": pada nilai yang sama, calon yang lebih
        # awal menang, dan urutan itu memang disusun dari yang paling tidak
        # meragukan.
        if nilai > nilai_terbaik:
            nilai_terbaik = nilai
            terbaik = p
    return terbaik


def _pisahkan(baris, pemisah):
    return baris.split(pemisah) if pemisah else baris.split()


def urai(teks):
    """Mengubah teks tempelan menjadi kumpulan data siap latih.

    Mengembalikan kamus berisi ``data`` (daftar pasangan masukan-sasaran),
    ``skala`` (rentang asli tiap kolom), dan ``catatan`` (hal yang perlu
    diketahui pengguna tentang apa yang baru saja dilakukan pada datanya).

    Melempar :class:`Galat` dengan pesan yang bisa dibaca kalau datanya tidak
    bisa dipakai sama sekali.
    """
    if not teks or not teks.strip():
        raise Galat("belum ada data yang ditempel")

    # Pemisahnya dipilih sekali untuk seluruh teks. Memilihnya per baris
    # berarti sebuah berkas bisa terbaca dengan dua aturan berbeda di dalam
    # dirinya sendiri, dan barisnya bergeser tanpa satu pun galat muncul.
    bersih = [
        b.strip()
        for b in teks.splitlines()
        if b.strip() and not b.strip().startswith("#")
    ]
    pemisah = pilih_pemisah(bersih)

    mentah = []
    dilewati_kepala = False
    for nomor, baris in enumerate(teks.splitlines(), start=1):
        baris = baris.strip()
        if not baris or baris.startswith("#"):
            continue

        sel = _pisahkan(baris, pemisah)
        if len(sel) < KOLOM:
            raise Galat(
                "baris %d hanya punya %d kolom; dibutuhkan 3 (x1, x2, kelas)"
                % (nomor, len(sel))
            )

        try:
            x1 = _angka(sel[0])
            x2 = _angka(sel[1])
            kelas = _angka(sel[2])
        except Galat as g:
            # Baris pertama yang tidak berupa angka dianggap judul kolom, dan
            # dilewati sekali saja. Menolak seluruh berkas karena barisnya
            # bernama "x1,x2,kelas" akan menolak hampir setiap ekspor Excel.
            if nomor == 1 and not dilewati_kepala:
                dilewati_kepala = True
                continue
            raise Galat("baris %d: %s" % (nomor, g)) from None

        if kelas not in (0.0, 1.0):
            raise Galat(
                "baris %d: kelas harus 0 atau 1, ditemukan %s" % (nomor, sel[2].strip()[:20])
            )
        mentah.append((x1, x2, kelas))

        if len(mentah) > BATAS_BARIS:
            raise Galat(
                "lebih dari %d baris. Python di dalam peramban tidak cukup "
                "cepat untuk itu, dan halaman yang menerimanya hanya akan "
                "terlihat rusak." % BATAS_BARIS
            )

    if len(mentah) < 4:
        raise Galat("dibutuhkan sekurang-kurangnya 4 baris, ditemukan %d" % len(mentah))

    kelas_ada = {k for _a, _b, k in mentah}
    if len(kelas_ada) < 2:
        raise Galat(
            "seluruh barisnya berkelas sama. Jaringan yang datanya satu kelas "
            "akan langsung 'benar' 100% dengan menjawab kelas itu terus, dan "
            "tidak ada yang bisa dipelajari darinya."
        )

    catatan = []
    if dilewati_kepala:
        catatan.append("Baris pertama dianggap judul kolom dan dilewati.")

    data, skala = _normalkan(mentah, catatan)
    return {"data": data, "skala": skala, "catatan": catatan}


def _normalkan(mentah, catatan):
    """Menskalakan kedua kolom masukan ke rentang nol sampai satu."""
    x1 = [a for a, _b, _k in mentah]
    x2 = [b for _a, b, _k in mentah]
    skala = []
    kolom = []

    for nama, nilai in (("x1", x1), ("x2", x2)):
        lo, hi = min(nilai), max(nilai)
        if hi - lo == 0:
            # Kolom tetap tidak membawa keterangan apa pun, tetapi juga tidak
            # merusak apa-apa. Ia dipetakan ke tengah supaya tidak menempel di
            # tepi gambar, dan itu diberitahukan.
            catatan.append(
                "Kolom %s bernilai sama di setiap baris, jadi ia tidak "
                "membedakan apa pun; digambar di tengah." % nama
            )
            kolom.append([0.5 for _ in nilai])
            skala.append({"nama": nama, "minimum": lo, "maksimum": hi, "tetap": True})
        else:
            kolom.append([(v - lo) / (hi - lo) for v in nilai])
            skala.append({"nama": nama, "minimum": lo, "maksimum": hi, "tetap": False})
            if lo < 0.0 or hi > 1.0:
                catatan.append(
                    "Kolom %s diskalakan dari rentang aslinya %g sampai %g "
                    "menjadi 0 sampai 1." % (nama, lo, hi)
                )

    data = [
        ([kolom[0][i], kolom[1][i]], [mentah[i][2]])
        for i in range(len(mentah))
    ]
    return data, skala


#: Contoh yang bisa ditempel pengguna untuk mencoba, dengan satuan sungguhan.
#:
#: Sengaja memakai angka di luar rentang nol sampai satu, dan koma desimal
#: gaya Indonesia, supaya penskalaan dan penguraiannya benar-benar terlihat
#: bekerja alih-alih hanya dijanjikan.
CONTOH = """# tinggi_cm; berat_kg; lolos_seleksi
165; 55,0; 0
170; 60,5; 0
175; 72,0; 1
180; 85,5; 1
168; 58,0; 0
178; 79,0; 1
172; 63,0; 0
182; 88,0; 1
"""
