"""Uji yang membaca antarmukanya sendiri dan menolak teks yang tidak lewat kamus.

# Kenapa memeriksa isi kamus saja tidak cukup

Uji kamus yang sudah ada memeriksa isi ``bahasa.TEKS``: tiap kunci punya dua
bahasa, keduanya terisi. Seluruhnya hijau — dan seluruhnya akan tetap hijau
sementara sebuah tombol di ``src/app.py`` bertuliskan ``"Latih"`` apa adanya,
karena teks itu memang bukan bagian dari kamus mana pun.

Kegagalan seperti itu tidak bisa dilihat dari dalam kamus. Yang bisa
melihatnya hanya pemeriksaan dari arah sebaliknya: baca berkas antarmukanya,
lalu tolak untai berbahasa Indonesia yang tidak melewati :func:`nusa.bahasa.t`.

# Kenapa lewat ``ast``, bukan pencarian teks

Karena pencarian teks tidak bisa membedakan untai di dalam ``tr("...")`` dari
untai yang berdiri sendiri, dan tidak bisa mengabaikan docstring — sedangkan
seluruh berkas ini memang berdokumentasi panjang dalam Bahasa Indonesia, dan
itu disengaja: yang membacanya pengembang, bukan pengunjung.

.Deckyx
"""

import ast
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
APP = AKAR / "src" / "app.py"
HALAMAN = AKAR / "index.html"

#: Kata Indonesia yang tidak mungkin muncul sebagai nama kelas atau atribut.
#:
#: Sengaja kata fungsi — kata sambung, kata depan, kata ganti. Kata benda
#: seperti "data" dan "kelas" dipakai sebagai nama peubah di seluruh berkas
#: ini, dan memasukkannya akan membuat ujinya berteriak pada kode yang benar.
KATA = re.compile(
    r"\b(yang|dengan|adalah|tidak|untuk|dari|pada|karena|jadi|bisa|akan|"
    r"sebuah|supaya|sehingga|kalau|tetapi|atau|dan|ini|itu|lebih|sudah|"
    r"masih|hanya|setiap|tiap|bila|juga|belum|harus)\b",
    re.IGNORECASE,
)


class PengumpulUntai(ast.NodeVisitor):
    """Mengumpulkan untai yang berdiri sendiri, di luar panggilan penerjemah.

    Docstring dilewati lewat :meth:`buang_docstring`, bukan dengan menebak dari
    isinya: sebuah docstring adalah untai yang menjadi pernyataan pertama
    sebuah modul, kelas, atau fungsi, dan itu bisa dikenali dengan pasti.
    """

    #: Nama fungsi yang isinya memang sudah diterjemahkan.
    PENERJEMAH = {"t", "tr"}

    def __init__(self):
        self.temuan = []
        self._lewati = set()

    def buang_docstring(self, simpul):
        badan = getattr(simpul, "body", None)
        if not badan:
            return
        pertama = badan[0]
        if isinstance(pertama, ast.Expr) and isinstance(pertama.value, ast.Constant):
            if isinstance(pertama.value.value, str):
                self._lewati.add(id(pertama.value))

    def visit_Module(self, simpul):
        self.buang_docstring(simpul)
        self.generic_visit(simpul)

    def visit_FunctionDef(self, simpul):
        self.buang_docstring(simpul)
        self.generic_visit(simpul)

    def visit_ClassDef(self, simpul):
        self.buang_docstring(simpul)
        self.generic_visit(simpul)

    def visit_Subscript(self, simpul):
        # ``r["dari"]`` adalah kunci kamus, bukan teks yang ditampilkan. Nama
        # kunci di berkas ini memang Bahasa Indonesia, dan itu disengaja: ia
        # nama bidang di dalam program, bukan kalimat.
        for anak in ast.walk(simpul.slice):
            if isinstance(anak, ast.Constant) and isinstance(anak.value, str):
                self._lewati.add(id(anak))
        self.generic_visit(simpul)

    def visit_Call(self, simpul):
        nama = simpul.func
        terjemah = (
            isinstance(nama, ast.Name)
            and nama.id in self.PENERJEMAH
            or isinstance(nama, ast.Attribute)
            and nama.attr in self.PENERJEMAH
        )
        if terjemah:
            # Argumennya kunci kamus, bukan teks yang ditampilkan.
            for arg in simpul.args:
                for anak in ast.walk(arg):
                    if isinstance(anak, ast.Constant) and isinstance(anak.value, str):
                        self._lewati.add(id(anak))
        self.generic_visit(simpul)

    def visit_Constant(self, simpul):
        if isinstance(simpul.value, str) and id(simpul) not in self._lewati:
            self.temuan.append((simpul.lineno, simpul.value))


def untai_berdiri_sendiri():
    pohon = ast.parse(APP.read_text(encoding="utf-8"))
    p = PengumpulUntai()
    # Dua lintasan: yang pertama menandai docstring dan argumen penerjemah,
    # yang kedua mengumpulkan sisanya. Satu lintasan tidak cukup karena
    # ``visit_Constant`` bisa dilalui sebelum ``visit_Call`` menandainya.
    p.visit(pohon)
    p.temuan = [(b, v) for b, v in p.temuan if id(v) or True]
    return p


class UjiProsaAntarmuka(unittest.TestCase):
    def test_pola_ujinya_sendiri_bisa_gagal(self):
        # Pemeriksaan yang tidak bisa gagal adalah kegagalan yang paling mahal,
        # karena ia terlihat persis seperti jaminan.
        self.assertTrue(KATA.search("mulai latihan dengan data ini"))
        self.assertFalse(KATA.search("kartu__judul"))
        # Tanpa batas kata, "dan" akan cocok di dalam "standar".
        self.assertFalse(KATA.search("standar deviasi"))

    def test_tidak_ada_kalimat_indonesia_di_luar_kamus(self):
        p = untai_berdiri_sendiri()
        bocor = [
            f"{APP.name}:{baris}  {nilai[:70]}"
            for baris, nilai in p.temuan
            if KATA.search(nilai)
        ]
        self.assertEqual(bocor, [], "\n".join(bocor))

    def test_pengumpulnya_memang_melihat_untai(self):
        # Kalau pengumpulnya tidak menemukan apa pun, ujinya di atas hijau
        # karena tidak memeriksa apa-apa — bukan karena berkasnya bersih.
        p = untai_berdiri_sendiri()
        self.assertGreater(len(p.temuan), 100)


if __name__ == "__main__":
    unittest.main()


class PembacaHalaman(HTMLParser):
    """Membaca teks statis ``index.html`` beserta bahasa yang menaunginya.

    Prosa tetap di halaman ini dipilih lewat CSS: dua salinan hidup
    berdampingan di dalam HTML, masing-masing bertanda ``lang``, dan yang tidak
    dipakai disembunyikan. Yang tidak punya tanda itu berarti hanya ada satu
    salinan — dan salinan tunggal berbahasa Indonesia akan tetap tampil di
    halaman berbahasa Inggris.
    """

    LEWATI = {"script", "style", "noscript", "svg", "template"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tumpukan = []
        self.dalam_lewati = 0
        #: ``(teks, bahasa_terdekat_atau_None)``
        self.teks = []

    def handle_starttag(self, tag, atribut):
        if tag in self.LEWATI:
            self.dalam_lewati += 1
        kamus = dict(atribut)
        # Tag yang menutup sendiri tidak pernah masuk tumpukan.
        if tag not in ("br", "hr", "img", "input", "meta", "link", "source"):
            self.tumpukan.append((tag, kamus.get("lang")))

    def handle_endtag(self, tag):
        if tag in self.LEWATI and self.dalam_lewati > 0:
            self.dalam_lewati -= 1
        for i in range(len(self.tumpukan) - 1, -1, -1):
            if self.tumpukan[i][0] == tag:
                del self.tumpukan[i:]
                break

    def handle_data(self, data):
        isi = data.strip()
        if not isi or self.dalam_lewati:
            return
        bahasa_terdekat = None
        for _, b in reversed(self.tumpukan):
            if b is not None:
                bahasa_terdekat = b
                break
        self.teks.append((isi, bahasa_terdekat))


class UjiHalamanStatis(unittest.TestCase):
    """Prosa tetap di ``index.html``, yang tidak pernah dilewati Python."""

    @classmethod
    def setUpClass(cls):
        p = PembacaHalaman()
        p.feed(HALAMAN.read_text(encoding="utf-8"))
        cls.teks = p.teks

    def test_pembacanya_memang_melihat_teks(self):
        # Pembaca yang tidak menemukan apa pun membuat uji di bawah hijau
        # karena tidak memeriksa apa-apa, bukan karena halamannya bersih.
        self.assertGreater(len(self.teks), 40)

    def test_prosa_indonesia_selalu_punya_penanda_bahasa(self):
        # Yang tanpa penanda hanya punya satu salinan, dan salinan tunggal
        # berbahasa Indonesia akan tetap tampil di halaman berbahasa Inggris.
        # Persis itu yang terjadi pada baris "IND323 · Kecerdasan Buatan".
        bocor = [
            f"{isi[:70]}"
            for isi, bahasa in self.teks
            if KATA.search(isi) and bahasa != "id"
        ]
        self.assertEqual(bocor, [], "\n".join(bocor))

    def test_tiap_salinan_indonesia_punya_pasangan_inggris(self):
        # Jumlahnya harus sama. Salinan Indonesia yang kehilangan pasangannya
        # menghasilkan lubang kosong di halaman berbahasa Inggris — dan lubang
        # kosong tidak menggagalkan pemeriksaan bocoran mana pun.
        halaman = HALAMAN.read_text(encoding="utf-8")
        id_ = len(re.findall(r'class="[^"]*\bbhs\b[^"]*"\s+lang="id"', halaman))
        en = len(re.findall(r'class="[^"]*\bbhs\b[^"]*"\s+lang="en"', halaman))
        self.assertGreater(id_, 10)
        self.assertEqual(id_, en)


class UjiKepalaDokumen(unittest.TestCase):
    def test_judul_tab_diterapkan_bersama_atribut_lang(self):
        # Judul tab tidak terlihat di halaman, jadi ia satu-satunya teks yang
        # bisa tertinggal berbulan-bulan tanpa ada yang menyadarinya. Yang
        # menjaganya bukan ingatan, melainkan letaknya: selama ia diterapkan di
        # fungsi yang sama dengan `lang`, tidak ada jalan mengganti bahasa yang
        # melewatinya.
        sumber = APP.read_text(encoding="utf-8")
        awal = sumber.index("def pasang_bahasa(")
        akhir = sumber.index("\ndef ", awal + 10)
        badan = sumber[awal:akhir]
        self.assertIn('setAttribute("lang"', badan)
        self.assertIn("document.title", badan)

        # Dan tidak ada tempat lain yang menyetel salah satunya sendirian.
        baris = [
            b.strip()
            for b in sumber.splitlines()
            if ("document.title" in b or 'setAttribute("lang"' in b)
            and not b.strip().startswith("#")
        ]
        self.assertEqual(len(baris), 2, "\n".join(baris))
