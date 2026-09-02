"""Uji mesin neuronusa.

Konformansi membuktikan angka Python sepadan dengan lima implementasi lain.
Uji di berkas ini membuktikan hal yang tidak bisa dibuktikan konformansi:
bahwa masukan tidak sah ditolak, bahwa perambatan baliknya benar, dan bahwa
sifat matematis yang seharusnya berlaku memang berlaku pada masukan mana pun.

Memakai ``unittest`` dari pustaka standar, bukan pytest. Alasannya sama dengan
alasan mesinnya tidak memakai numpy: paket ini harus bisa diuji di lingkungan
mana pun tanpa langkah pemasangan.

.Deckyx
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from nusa import data, ekspor, fx, inti, jaringan, konform, tautan  # noqa: E402

VEKTOR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "conformance", "vectors"
)


def muat_vektor(nama):
    with open(os.path.join(VEKTOR, nama), "r", encoding="utf-8") as f:
        return f.read()


class UjiFx(unittest.TestCase):
    def test_pola_bit_nilai_dikenal(self):
        self.assertEqual(fx.ke_hex(1.0), "3ff0000000000000")
        self.assertEqual(fx.ke_hex(0.1), "3fb999999999999a")
        self.assertEqual(fx.ke_hex(0.0), "0000000000000000")
        self.assertEqual(fx.ke_hex(float("inf")), "7ff0000000000000")

    def test_nol_negatif_bertahan(self):
        # Nol negatif adalah nilai yang paling sering hilang saat angka
        # berpindah bahasa. Oracle mengubahnya menjadi nol positif; Lua
        # kehilangannya lewat penambahan yang tampak tidak berbahaya.
        self.assertEqual(fx.ke_hex(-0.0), "8000000000000000")
        self.assertEqual(fx.ke_hex(fx.dari_hex("8000000000000000")), "8000000000000000")
        self.assertFalse(fx.sama_bit(0.0, -0.0))
        # Namun perbandingan biasa tetap menyatakan keduanya sama, dan itulah
        # sebabnya perbandingan bit-eksak tidak boleh memakai ``==``.
        self.assertTrue(0.0 == -0.0)

    def test_bolak_balik_nilai_batas(self):
        for hx in ("400921fb54442d18", "0000000000000001", "7fefffffffffffff", "fff0000000000000"):
            self.assertEqual(fx.ke_hex(fx.dari_hex(hx)), hx)

    def test_panjang_salah_ditolak(self):
        # Teks 14 digit adalah pola bit yang sah, hanya bukan yang dimaksud.
        with self.assertRaises(ValueError):
            fx.dari_hex("3ff00000000000")
        with self.assertRaises(ValueError):
            fx.dari_hex("3ff000000000000z")

    def test_jarak_ulp(self):
        a = fx.dari_hex("3fdae147ae147ae1")
        b = fx.dari_hex("3fdae147ae147ae2")
        self.assertEqual(fx.jarak_ulp(a, b), 1)
        self.assertEqual(fx.jarak_ulp(1.0, 2.0), 4503599627370496)
        self.assertEqual(fx.jarak_ulp(-0.0, 0.0), 0)
        self.assertIsNone(fx.jarak_ulp(float("nan"), 1.0))
        self.assertIsNone(fx.jarak_ulp(float("inf"), 1.0))

    def test_jarak_ulp_melintasi_nol(self):
        # Kunci terurutnya memetakan nilai negatif ke bilangan negatif, jadi
        # selisih dua nilai berlawanan tanda harus tetap positif.
        d = fx.jarak_ulp(-1.0, 1.0)
        self.assertIsNotNone(d)
        self.assertGreater(d, 0)

    def test_nan_sama_dengan_nan_pada_tingkat_bit(self):
        self.assertTrue(fx.sama_bit(float("nan"), float("nan")))
        self.assertFalse(float("nan") == float("nan"))

    def test_langkah_ulp(self):
        self.assertEqual(fx.langkah_ulp(1.0), sys.float_info.epsilon)
        self.assertEqual(fx.langkah_ulp(-1.0), sys.float_info.epsilon)
        self.assertEqual(fx.langkah_ulp(0.0), fx.dari_bits(1))
        # Satu ULP pada 1024 seribu kali lebih besar daripada pada 1. Justru
        # inilah alasan toleransi ULP harus disebut skalanya.
        self.assertGreater(fx.langkah_ulp(1024.0), fx.langkah_ulp(1.0) * 1000.0)
        self.assertTrue(math.isnan(fx.langkah_ulp(float("inf"))))


class UjiKeterbandingan(unittest.TestCase):
    def test_penanda_terbaca(self):
        self.assertEqual(fx.Keterbandingan.dari_penanda("BitExact").maks_ulp, 0)
        self.assertEqual(fx.Keterbandingan.dari_penanda("NearlyEqual(4)").maks_ulp, 4)
        self.assertTrue(fx.Keterbandingan.dari_penanda("CancellingDifference(4)").pakai_skala)
        self.assertTrue(fx.Keterbandingan.dari_penanda("PropertyOnly").sifat_saja)
        self.assertIsNone(fx.Keterbandingan.dari_penanda("Kira-kira sama"))
        self.assertIsNone(fx.Keterbandingan.dari_penanda("NearlyEqual"))

    def test_bit_eksak_menolak_beda_tanda_nol(self):
        # Nol positif dan negatif berjarak nol ULP tetapi berbeda pola bitnya.
        t = fx.Keterbandingan.dari_penanda("BitExact")
        self.assertFalse(t.terpenuhi(0.0, -0.0))
        self.assertTrue(t.terpenuhi(1.0, 1.0))

    def test_tingkat_berskala(self):
        t = fx.Keterbandingan.dari_penanda("CancellingDifference(4)")
        skala = 0.9402859586706311
        a = 0.02922256565895487
        self.assertTrue(t.terpenuhi(a, a + 2 * fx.langkah_ulp(skala), skala))
        self.assertFalse(t.terpenuhi(a, a + 5 * fx.langkah_ulp(skala), skala))
        # Galat yang sama berjarak puluhan ULP kalau diukur pada hasilnya.
        hampir = fx.Keterbandingan.dari_penanda("NearlyEqual(4)")
        self.assertFalse(hampir.terpenuhi(a, a + 2 * fx.langkah_ulp(skala)))

    def test_tanpa_skala_dinilai_paling_ketat(self):
        # Lupa memberi skala harus berujung kegagalan, bukan kelolosan palsu.
        t = fx.Keterbandingan.dari_penanda("CancellingDifference(4)")
        self.assertTrue(t.terpenuhi(1.0, 1.0))
        self.assertFalse(t.terpenuhi(1.0, 1.0 + sys.float_info.epsilon))
        self.assertFalse(t.terpenuhi(1.0, 2.0, float("nan")))


class UjiInti(unittest.TestCase):
    def test_certainty_factor(self):
        self.assertAlmostEqual(inti.cf_dari_mb_md(0.8, 0.01), 0.79, places=12)
        self.assertAlmostEqual(inti.cf_gabung_paralel(0.8, 0.6), 0.92, places=12)
        # Bukti berlawanan penuh saling meniadakan, bukan membagi dengan nol.
        self.assertEqual(inti.cf_gabung_paralel(1.0, -1.0), 0.0)
        # Bukti negatif tidak menyalakan aturan sama sekali. Tanda nolnya
        # mengikuti tanda CF aturannya, bukan tanda buktinya.
        self.assertTrue(fx.sama_bit(inti.cf_gabung_berantai(0.9, -0.5), 0.0))
        self.assertTrue(fx.sama_bit(inti.cf_gabung_berantai(-1.0, -1.0), -0.0))
        self.assertEqual(inti.cf_premis_dan(0.9, 0.3), 0.3)
        self.assertEqual(inti.cf_premis_atau(0.9, 0.3), 0.9)

    def test_certainty_komutatif_dan_terbatas(self):
        v = [i / 4.0 for i in range(-4, 5)]
        for a in v:
            for b in v:
                kiri = inti.cf_gabung_paralel(a, b)
                self.assertTrue(fx.sama_bit(kiri, inti.cf_gabung_paralel(b, a)))
                self.assertGreaterEqual(kiri, -1.0)
                self.assertLessEqual(kiri, 1.0)

    def test_certainty_menolak_di_luar_rentang(self):
        with self.assertRaises(ValueError):
            inti.cf_dari_mb_md(1.5, 0.0)
        with self.assertRaises(ValueError):
            inti.cf_gabung_paralel(float("nan"), 0.2)

    def test_bayes_tugas_pertemuan_5(self):
        self.assertAlmostEqual(inti.bayes_posterior(0.2, 0.9, 0.3), 3.0 / 7.0, places=12)
        self.assertAlmostEqual(inti.bayes_bukti(0.2, 0.9, 0.3), 0.42, places=12)
        self.assertAlmostEqual(inti.bayes_rasio(0.9, 0.3), 3.0, places=12)

    def test_bayes_posterior_dan_komplemen_berjumlah_satu(self):
        # Sifat yang paling sering dilanggar implementasi keliru, diperiksa
        # pada 729 kombinasi masukan alih-alih satu contoh.
        for a in range(1, 10):
            for b in range(1, 10):
                for c in range(1, 10):
                    p = inti.bayes_posterior(a / 10.0, b / 10.0, c / 10.0)
                    self.assertAlmostEqual(p + (1.0 - p), 1.0, places=12)
                    self.assertGreaterEqual(p, 0.0)
                    self.assertLessEqual(p, 1.0)

    def test_bayes_laju_dasar(self):
        self.assertLess(inti.bayes_posterior(0.001, 0.99, 0.05), 0.05)
        self.assertTrue(math.isinf(inti.bayes_rasio(0.5, 0.0)))
        self.assertEqual(inti.bayes_rasio(0.0, 0.0), 0.0)
        with self.assertRaises(ValueError):
            inti.bayes_posterior(0.0, 0.9, 0.0)

    def test_kabur_kaki_berimpit(self):
        # Bentuk yang paling gampang salah: kalau tepi diperiksa lebih dulu
        # daripada puncak, keduanya bernilai nol tepat di tempat mereka
        # seharusnya bernilai satu.
        self.assertEqual(inti.kabur_segitiga(0, 0, 15, 0), 1.0)
        self.assertEqual(inti.kabur_trapesium(5, 8, 10, 10, 10), 1.0)
        self.assertEqual(inti.kabur_segitiga(0, 5, 10, 5), 1.0)
        self.assertEqual(inti.kabur_segitiga(0, 10, 20, 5), 0.5)

    def test_kabur_selalu_dalam_rentang(self):
        for i in range(-50, 151):
            x = i / 2.0
            for v in (
                inti.kabur_segitiga(10, 20, 30, x),
                inti.kabur_trapesium(0, 0, 15, 20, x),
                inti.kabur_gauss(24, 3, x),
                inti.kabur_sigmoid(2, 5, x),
            ):
                self.assertGreaterEqual(v, 0.0)
                self.assertLessEqual(v, 1.0)

    def test_entropi_dan_gini(self):
        # Kelas tunggal menghasilkan nol negatif, bukan nol positif: hasilnya
        # negasi dari nol, dan itu yang dihasilkan kelima implementasi lain.
        self.assertTrue(fx.sama_bit(inti.entropi(["A"]), -0.0))
        self.assertEqual(inti.entropi(["A", "B"]), 1.0)
        self.assertEqual(inti.entropi(["A", "B", "C", "D"]), 2.0)
        self.assertEqual(inti.entropi([]), 0.0)
        self.assertEqual(inti.gini(["A", "B"]), 0.5)
        self.assertEqual(inti.gini(["A", "A"]), 0.0)

    def test_jarak(self):
        self.assertEqual(inti.euclidean([0, 0], [3, 4]), 5.0)
        self.assertEqual(inti.manhattan([0, 0], [3, 4]), 7.0)
        self.assertEqual(inti.chebyshev([0, 0], [3, 4]), 4.0)
        a, b, c = [0.0, 0.0], [1.0, 2.0], [3.0, 1.0]
        for ukur in (inti.euclidean, inti.manhattan, inti.chebyshev):
            self.assertAlmostEqual(ukur(a, b), ukur(b, a), places=12)
            self.assertLessEqual(ukur(a, c), ukur(a, b) + ukur(b, c) + 1e-12)
            self.assertEqual(ukur(a, a), 0.0)

    def test_perolehan_informasi_tenis(self):
        cuaca = ["Cerah", "Cerah", "Mendung", "Hujan", "Hujan", "Hujan", "Mendung",
                 "Cerah", "Cerah", "Hujan", "Cerah", "Mendung", "Mendung", "Hujan"]
        label = ["Tidak", "Tidak", "Ya", "Ya", "Ya", "Tidak", "Ya",
                 "Tidak", "Ya", "Ya", "Ya", "Ya", "Ya", "Tidak"]
        self.assertAlmostEqual(inti.entropi(label), 0.9402859586706311, places=12)
        self.assertAlmostEqual(
            inti.perolehan_informasi(cuaca, label), 0.24674981977443933, places=12
        )
        # Panjang yang tidak sepadan menghasilkan nol, bukan galat.
        self.assertEqual(inti.perolehan_informasi(["a"], label), 0.0)

    def test_splitmix64(self):
        r = inti.SplitMix64(0)
        self.assertEqual(fx.ke_hex(fx.dari_bits(r.u64())), "e220a8397b1dcdaf")
        self.assertEqual(fx.ke_hex(fx.dari_bits(r.u64())), "6e789e6aa1b965f4")
        a, b = inti.SplitMix64(42), inti.SplitMix64(42)
        for _ in range(50):
            self.assertEqual(a.u64(), b.u64())
        c = inti.SplitMix64(7)
        jumlah = 0.0
        for _ in range(2000):
            v = c.f64()
            self.assertGreaterEqual(v, 0.0)
            self.assertLess(v, 1.0)
            jumlah += v
        self.assertLess(abs(jumlah / 2000.0 - 0.5), 0.05)


class UjiJaringan(unittest.TestCase):
    """Uji jaringan syaraf.

    Yang paling menentukan di sini adalah pemeriksaan gradien. Jaringan yang
    gradiennya salah tetap sering "belajar" — hanya lebih lambat dan berhenti
    di tempat yang keliru — dan kurva galatnya tetap terlihat menurun dengan
    meyakinkan. Hanya perbandingan dengan selisih hingga yang bisa
    memisahkan perambatan balik yang benar dari yang kebetulan bekerja.
    """

    def test_bentuk_dan_jumlah_parameter(self):
        j = jaringan.Jaringan([2, 4, 1])
        # 2×4 + 4 bias, lalu 4×1 + 1 bias.
        self.assertEqual(j.jumlah_parameter(), 8 + 4 + 4 + 1)
        self.assertEqual(len(j.ramal([0.0, 0.0])), 1)

    def test_menolak_bentuk_dan_aktivasi_tidak_sah(self):
        with self.assertRaises(ValueError):
            jaringan.Jaringan([3])
        with self.assertRaises(ValueError):
            jaringan.Jaringan([2, 2, 1], aktivasi="ajaib")

    def test_benih_sama_menghasilkan_bobot_sama(self):
        a = jaringan.Jaringan([2, 3, 1], benih=99)
        b = jaringan.Jaringan([2, 3, 1], benih=99)
        self.assertEqual(a.bobot, b.bobot)
        c = jaringan.Jaringan([2, 3, 1], benih=100)
        self.assertNotEqual(a.bobot, c.bobot)

    def test_keluaran_selalu_di_dalam_nol_sampai_satu(self):
        # Lapis keluaran selalu sigmoid, jadi keluarannya bisa ditafsirkan
        # sebagai peluang kelas berapa pun aktivasi tersembunyinya.
        for akt in jaringan.AKTIVASI:
            j = jaringan.Jaringan([2, 5, 1], aktivasi=akt, benih=3)
            for x in ([0.0, 0.0], [1.0, 1.0], [-9.0, 9.0], [50.0, -50.0]):
                y = j.ramal(x)[0]
                self.assertGreaterEqual(y, 0.0)
                self.assertLessEqual(y, 1.0)

    def test_sigmoid_tidak_meluap_pada_masukan_ekstrem(self):
        # Bentuk naif 1/(1+exp(-x)) menghasilkan inf untuk x sangat negatif,
        # dan inf yang muncul di tengah pelatihan menyebar menjadi NaN.
        j = jaringan.Jaringan([1, 1, 1], aktivasi="sigmoid", benih=1)
        j.bobot[0][0][0] = 1000.0
        for x in ([1e3], [-1e3]):
            y = j.ramal(x)[0]
            self.assertTrue(math.isfinite(y))

    def test_gradien_cocok_dengan_selisih_hingga(self):
        # Inilah uji yang membedakan perambatan balik yang benar dari yang
        # kebetulan bekerja.
        for akt in ("tanh", "sigmoid", "linear"):
            for ukuran in ([2, 3, 1], [2, 4, 3, 1]):
                j = jaringan.Jaringan(ukuran, aktivasi=akt, benih=5)
                hasil = j.periksa_gradien(jaringan.data_xor())
                self.assertTrue(
                    hasil["lolos"],
                    "%s %s: galat relatif terburuk %g" % (akt, ukuran, hasil["terburuk"]),
                )
                self.assertEqual(len(hasil["rincian"]), j.jumlah_parameter())

    def test_pemeriksa_gradien_menangkap_gradien_yang_dirusak(self):
        # Pemeriksa yang selalu lolos tidak berguna. Sebuah gradien yang
        # sengaja dirusak harus tertangkap.
        j = jaringan.Jaringan([2, 3, 1], benih=5)
        data = jaringan.data_xor()
        asli = j.gradien

        def gradien_rusak(d):
            gw, gb = asli(d)
            gw[0][0][0] += 0.01
            return gw, gb

        j.gradien = gradien_rusak
        hasil = j.periksa_gradien(data)
        self.assertFalse(hasil["lolos"])
        self.assertGreater(hasil["terburuk"], 1e-5)

    def test_pemeriksa_gradien_tidak_mengubah_bobot(self):
        # Ia menggeser tiap bobot dua kali lalu mengembalikannya. Kalau
        # pengembaliannya meleset, pelatihan sesudahnya berangkat dari tempat
        # yang salah tanpa ada yang menyadarinya.
        j = jaringan.Jaringan([2, 3, 1], benih=11)
        sebelum = [[list(b) for b in lap] for lap in j.bobot]
        j.periksa_gradien(jaringan.data_xor())
        self.assertEqual(j.bobot, sebelum)

    def test_pelatihan_menurunkan_galat(self):
        j = jaringan.Jaringan([2, 4, 1], aktivasi="tanh", benih=7)
        data = jaringan.data_xor()
        awal = j.galat(data)
        for _ in range(400):
            j.langkah(data, laju=0.5, momentum=0.9)
        self.assertLess(j.galat(data), awal * 0.5)

    def test_xor_bisa_dipelajari_dengan_lapis_tersembunyi(self):
        j = jaringan.Jaringan([2, 4, 1], aktivasi="tanh", benih=7)
        data = jaringan.data_xor()
        for _ in range(3000):
            j.langkah(data, laju=0.5, momentum=0.9)
        for x, t in data:
            y = j.ramal(x)[0]
            self.assertEqual(round(y), int(t[0]), "XOR gagal pada %s" % x)

    def test_xor_tidak_bisa_dipelajari_tanpa_lapis_tersembunyi(self):
        # Temuan Minsky dan Papert, diperiksa alih-alih dikutip: perceptron
        # satu lapis hanya bisa menarik satu garis lurus.
        j = jaringan.Jaringan([2, 1], aktivasi="tanh", benih=7)
        data = jaringan.data_xor()
        for _ in range(3000):
            j.langkah(data, laju=0.5, momentum=0.9)
        benar = sum(1 for x, t in data if round(j.ramal(x)[0]) == int(t[0]))
        self.assertLessEqual(benar, 3)

    def test_and_bisa_dipelajari_tanpa_lapis_tersembunyi(self):
        # Pembanding yang menjaga uji sebelumnya bermakna: kalau AND pun gagal,
        # yang salah bukan keterpisahan liniernya melainkan pelatihannya.
        j = jaringan.Jaringan([2, 1], aktivasi="tanh", benih=7)
        data = jaringan.data_and()
        for _ in range(3000):
            j.langkah(data, laju=0.5, momentum=0.9)
        for x, t in data:
            self.assertEqual(round(j.ramal(x)[0]), int(t[0]))

    def test_laju_terlalu_besar_membuat_pelatihan_meledak(self):
        # Gejala khasnya: galat berhenti menurun lalu melompat-lompat, berbeda
        # dari laju terlalu kecil yang menurun tetapi lambat.
        j = jaringan.Jaringan([2, 4, 1], benih=7)
        data = jaringan.data_xor()
        awal = j.galat(data)
        for _ in range(200):
            j.langkah(data, laju=50.0, momentum=0.9)
        akhir = j.galat(data)
        self.assertTrue(akhir > awal or math.isnan(akhir) or akhir > 0.2)

    def test_laju_efektif(self):
        j = jaringan.Jaringan([2, 2, 1])
        # Momentum menjumlahkan langkah sebelumnya: langkah tunaknya
        # laju / (1 - momentum).
        self.assertAlmostEqual(j.laju_efektif(0.5, 0.9), 5.0, places=12)
        self.assertAlmostEqual(j.laju_efektif(0.1, 0.0), 0.1, places=12)
        self.assertTrue(math.isinf(j.laju_efektif(0.1, 1.0)))

    def test_reset_momentum_setelah_bobot_diganti(self):
        # Momentum lama yang tertinggal akan mendorong bobot baru ke arah yang
        # tidak ada hubungannya, dan gejalanya terlihat seperti pelatihan yang
        # tiba-tiba divergen tanpa sebab.
        j = jaringan.Jaringan([2, 3, 1], benih=7)
        data = jaringan.data_xor()
        for _ in range(50):
            j.langkah(data, laju=0.5, momentum=0.9)
        j.acak_ulang(123)
        j.reset_momentum()
        for lap in j._kecepatan_w:
            for baris in lap:
                for v in baris:
                    self.assertEqual(v, 0.0)

    def test_data_kosong_tidak_menabrak(self):
        j = jaringan.Jaringan([2, 3, 1])
        self.assertEqual(j.galat([]), 0.0)
        gw, gb = j.gradien([])
        self.assertEqual(gw[0][0][0], 0.0)
        self.assertEqual(gb[0][0], 0.0)

    def test_dataset_bawaan(self):
        self.assertEqual(len(jaringan.data_xor()), 4)
        self.assertEqual(len(jaringan.data_and()), 4)
        lingkaran = jaringan.data_lingkaran(40, benih=7)
        self.assertEqual(len(lingkaran), 40)
        # Benih tetap: dua pemanggilan wajib menghasilkan titik yang sama.
        self.assertEqual(lingkaran, jaringan.data_lingkaran(40, benih=7))
        kelas = {t[0] for _, t in lingkaran}
        self.assertEqual(kelas, {0.0, 1.0})
        for x, _ in lingkaran:
            self.assertEqual(len(x), 2)


class UjiCaraGagal(unittest.TestCase):
    """Mengunci **cara** pelatihan gagal, bukan hanya bahwa ia bisa gagal.

    Kelas ini ada karena antarmukanya pernah memuat peringatan yang salah.
    Peringatan itu berbunyi bahwa laju efektif di atas 1 membuat pelatihan
    "berayun alih-alih menurun" sampai angkanya meluap. Terdengar masuk akal,
    dan memang begitulah jaringan syaraf umumnya gagal — tetapi bukan yang
    ini. Pengukuran terhadap tiga aktivasi dan dua kumpulan data, sampai laju
    efektif 20.000, tidak pernah sekali pun menghasilkan NaN atau tak hingga.

    Sebabnya ada di arsitekturnya: lapis keluarannya sigmoid, sehingga
    ramalannya terkurung di ``(0, 1)`` dan galat kuadratnya terkurung di bawah
    0,5 berapa pun bobotnya. Yang terjadi bukan peledakan melainkan kejenuhan.

    Uji di bawah menahan penjelasan itu tetap benar. Kalau lapis keluarannya
    suatu hari diganti menjadi linear, ujinya gagal — dan teks di halaman
    memang harus ikut berubah saat itu.
    """

    #: Setelan paling ekstrem yang masih masuk akal untuk dicoba pengguna.
    LAJU_EKSTREM = 200.0
    MOMENTUM_EKSTREM = 0.99

    def test_galat_terkurung_walau_lajunya_sangat_besar(self):
        for aktivasi in ("tanh", "sigmoid", "relu"):
            for data in (jaringan.data_xor(), jaringan.data_lingkaran(20, benih=3)):
                j = jaringan.Jaringan([2, 4, 1], aktivasi=aktivasi, benih=7)
                for _ in range(400):
                    j.langkah(
                        data,
                        laju=self.LAJU_EKSTREM,
                        momentum=self.MOMENTUM_EKSTREM,
                    )
                    g = j.galat(data)
                    self.assertTrue(
                        math.isfinite(g),
                        "%s menghasilkan galat tak berhingga; lapis keluarannya "
                        "mungkin bukan sigmoid lagi" % aktivasi,
                    )
                    self.assertLess(g, 0.5)

    def test_ramalan_selalu_di_antara_nol_dan_satu(self):
        """Batas yang membuat galatnya terkurung, diuji langsung."""
        j = jaringan.Jaringan([2, 3, 1], aktivasi="relu", benih=11)
        # Bobot dibesarkan dengan tangan sampai jauh di luar apa pun yang bisa
        # dihasilkan pelatihan, supaya batasnya diuji dan bukan kebetulan.
        for lap in j.bobot:
            for baris in lap:
                for k in range(len(baris)):
                    baris[k] = 1e6 if k % 2 == 0 else -1e6
        for x in ([0.0, 0.0], [1.0, 1.0], [0.5, 0.25], [1e3, -1e3]):
            y = j.ramal(x)[0]
            self.assertTrue(math.isfinite(y))
            self.assertGreaterEqual(y, 0.0)
            self.assertLessEqual(y, 1.0)

    def test_laju_ekstrem_menjenuhkan_alih_alih_meledak(self):
        """Cara gagal yang sesungguhnya: keluaran tetap, sama untuk apa pun."""
        data = jaringan.data_xor()
        j = jaringan.Jaringan([2, 4, 1], aktivasi="tanh", benih=7)
        for _ in range(600):
            j.langkah(data, laju=self.LAJU_EKSTREM, momentum=self.MOMENTUM_EKSTREM)
        keluaran = [j.ramal(x)[0] for x, _ in data]
        for y in keluaran:
            self.assertTrue(math.isfinite(y))
        self.assertEqual(
            len({round(y) for y in keluaran}),
            1,
            "diharapkan jaringan jenuh menjawab sama untuk setiap masukan",
        )

    def test_setelan_bawaan_halaman_benar_benar_belajar_xor(self):
        """Setelan yang dilihat pengunjung pertama kali wajib berhasil.

        Halaman yang membuka dengan setelan yang tidak pernah menyelesaikan
        masalahnya mengajarkan hal yang keliru sejak layar pertama.
        """
        data = jaringan.data_xor()
        j = jaringan.Jaringan([2, 4, 1], aktivasi="tanh", benih=7)
        for _ in range(3000):
            j.langkah(data, laju=0.5, momentum=0.9)
        benar = sum(1 for x, t in data if round(j.ramal(x)[0]) == int(t[0]))
        self.assertEqual(benar, 4)
        self.assertLess(j.galat(data), 1e-3)


class UjiCacatYangBisaDinyalakan(unittest.TestCase):
    """Menahan seluruh klaim yang dibuat halaman tentang cacat perambatan balik.

    Setiap kalimat di antarmuka tentang cacat ini adalah pernyataan yang bisa
    salah, dan sebagian memang pernah salah. Kelas ini memeriksa keempatnya
    dengan menjalankannya, bukan dengan mempercayainya.

    Angka-angkanya diukur, bukan dikarang. Yang paling penting: cacat
    ``tanda_terbalik`` pada XOR dengan benih 7 berakhir di galat 4,24e-05 —
    **lebih rendah** daripada perambatan balik yang benar, yang berakhir di
    4,34e-05. Itu bukan kebetulan yang lucu melainkan seluruh alasan halaman
    ini ada: kurva galat tidak membuktikan apa pun.
    """

    EPOCH = 3000
    LAJU = 0.5
    MOMENTUM = 0.9

    def latih(self, cacat, data=None, tersembunyi=4, benih=7):
        data = data if data is not None else jaringan.data_xor()
        j = jaringan.Jaringan([2, tersembunyi, 1], aktivasi="tanh", benih=benih)
        j.atur_cacat(cacat)
        awal = j.galat(data)
        for _ in range(self.EPOCH):
            j.langkah(data, laju=self.LAJU, momentum=self.MOMENTUM, hitung_galat=False)
        return j, data, awal, j.galat(data)

    def test_katalog_lengkap_dan_konsisten(self):
        self.assertIn("tidak_ada", jaringan.CACAT)
        for nama, (label, tempat, tertangkap, penjelasan) in jaringan.CACAT.items():
            self.assertTrue(label and isinstance(label, str), nama)
            self.assertTrue(penjelasan and len(penjelasan) > 40, nama)
            if nama == "tidak_ada":
                self.assertIsNone(tempat)
                self.assertIsNone(tertangkap)
            else:
                self.assertIn(tempat, ("gradien", "langkah"), nama)
                self.assertIsInstance(tertangkap, bool)
                # Klaim yang menentukan: cacat pada gradien tertangkap
                # pemeriksa gradien, cacat pada pembaruan tidak. Uji di bawah
                # membuktikan keduanya dengan menjalankannya.
                self.assertEqual(tertangkap, tempat == "gradien", nama)

    def test_nama_cacat_yang_tidak_dikenal_ditolak(self):
        j = jaringan.Jaringan([2, 3, 1])
        with self.assertRaises(ValueError):
            j.atur_cacat("tidak-pernah-ada")
        # Yang lama harus tetap terpasang, bukan diam-diam terlepas.
        self.assertEqual(j.cacat, "tidak_ada")

    def test_pemeriksa_gradien_menangkap_yang_seharusnya_tertangkap(self):
        data = jaringan.data_xor()
        for nama, (_label, tempat, tertangkap, _p) in jaringan.CACAT.items():
            if nama == "tidak_ada":
                continue
            j = jaringan.Jaringan([2, 4, 1], aktivasi="tanh", benih=7)
            j.atur_cacat(nama)
            # Diperiksa setelah beberapa langkah, bukan pada bobot awal:
            # sebagian gradien awal cukup kecil untuk membuat galat relatif
            # apa pun terlihat besar, dan uji yang lolos karena itu tidak
            # memeriksa apa yang dikiranya diperiksa.
            for _ in range(50):
                j.langkah(data, laju=0.5, momentum=0.9, hitung_galat=False)
            hasil = j.periksa_gradien(data)
            self.assertEqual(
                hasil["lolos"],
                not tertangkap,
                "cacat %r: diharapkan pemeriksa gradien %s, ternyata %s "
                "(galat relatif terburuk %.3e)"
                % (
                    nama,
                    "GAGAL" if tertangkap else "LOLOS",
                    "LOLOS" if hasil["lolos"] else "GAGAL",
                    hasil["terburuk"],
                ),
            )

    def test_bias_beku_tidak_bisa_ditangkap_pemeriksa_gradien(self):
        """Batas alatnya, diuji langsung.

        Pemeriksa gradien memeriksa apakah turunannya benar, bukan apakah
        turunannya dipakai. Uji ini memastikan halaman tidak pernah menjanjikan
        yang pertama sebagai jaminan atas yang kedua.
        """
        data = jaringan.data_xor()
        j = jaringan.Jaringan([2, 4, 1], aktivasi="tanh", benih=7)
        j.atur_cacat("bias_beku")
        for _ in range(50):
            j.langkah(data, laju=0.5, momentum=0.9, hitung_galat=False)
        self.assertTrue(j.periksa_gradien(data)["lolos"])
        # Dan buktikan cacatnya memang terpasang: biasnya tidak bergerak.
        for lap in j.bias:
            for b in lap:
                self.assertEqual(b, 0.0)

    def test_setiap_cacat_tetap_terlihat_belajar(self):
        """Klaim inti halaman ini, diuji pada keempat cacat.

        Galatnya wajib **menurun** pada setiap cacat. Kalau ada yang tidak,
        kalimat "jaringan yang gradiennya salah tetap sering belajar" tidak
        berlaku untuk cacat itu, dan halaman tidak boleh memakainya sebagai
        contoh.
        """
        for nama in jaringan.CACAT:
            for label, data, tersembunyi in (
                ("XOR", jaringan.data_xor(), 4),
                ("cincin", jaringan.data_lingkaran(40, benih=7), 6),
            ):
                _j, _d, awal, akhir = self.latih(nama, data, tersembunyi)
                self.assertTrue(math.isfinite(akhir), "%s/%s" % (nama, label))
                self.assertLess(
                    akhir,
                    awal,
                    "cacat %r pada %s tidak membuat galatnya menurun sama "
                    "sekali (%.3e → %.3e); halaman tidak boleh memakainya "
                    "sebagai contoh 'tetap terlihat belajar'"
                    % (nama, label, awal, akhir),
                )

    def test_tanda_terbalik_tidak_bisa_dibedakan_dari_kurva_galatnya(self):
        """Kasus yang paling menohok, dikunci angkanya.

        Perambatan balik yang salah tandanya pada satu bobot berakhir dengan
        galat yang **lebih rendah** daripada yang benar, dan menjawab keempat
        titik XOR dengan benar. Tidak ada satu pun angka di kurva galat yang
        bisa membedakan keduanya. Yang bisa hanya pemeriksa gradien.
        """
        _jb, data, _a, benar_akhir = self.latih("tidak_ada")
        _jr, _d, _a2, rusak_akhir = self.latih("tanda_terbalik")

        self.assertLess(benar_akhir, 1e-4)
        self.assertLess(rusak_akhir, 1e-4)
        # Keduanya di bawah ambang yang sama; besarannya tidak terbedakan.
        self.assertLess(abs(math.log10(rusak_akhir) - math.log10(benar_akhir)), 0.5)

        jr = jaringan.Jaringan([2, 4, 1], aktivasi="tanh", benih=7)
        jr.atur_cacat("tanda_terbalik")
        for _ in range(self.EPOCH):
            jr.langkah(data, laju=self.LAJU, momentum=self.MOMENTUM, hitung_galat=False)
        benar = sum(1 for x, t in data if round(jr.ramal(x)[0]) == int(t[0]))
        self.assertEqual(benar, 4, "jaringan yang gradiennya salah tetap menjawab benar")
        self.assertFalse(jr.periksa_gradien(data)["lolos"])

    def test_faktor_dua_justru_terlihat_lebih_baik(self):
        """Cacat yang menyamar sebagai perbaikan.

        Menggandakan seluruh gradien setara dengan menggandakan laju belajar,
        dan pada masalah sekecil ini itu mempercepat. Galatnya berakhir lebih
        rendah daripada perambatan balik yang benar — dan tetap salah.
        """
        _jb, _d, _a, benar_akhir = self.latih("tidak_ada")
        _jr, _d2, _a2, rusak_akhir = self.latih("faktor_dua")
        self.assertLess(rusak_akhir, benar_akhir)

    def test_turunan_hilang_berhenti_di_tempat_yang_keliru(self):
        """Cacat yang berhenti sebelum selesai, tetapi tetap menurun.

        Inilah bentuk paling murni dari kalimat "lebih lambat dan berhenti di
        tempat yang keliru".
        """
        data = jaringan.data_xor()
        j, _d, awal, akhir = self.latih("turunan_hilang")
        self.assertLess(akhir, awal)
        benar = sum(1 for x, t in data if round(j.ramal(x)[0]) == int(t[0]))
        self.assertLess(benar, 4, "diharapkan tidak menyelesaikan XOR")

    def test_cacat_tidak_mengubah_perambatan_maju(self):
        """Cacatnya hanya di jalur mundur; ramalannya harus utuh.

        Kalau perambatan majunya ikut berubah, yang diperlihatkan bukan lagi
        "gradien yang salah pada jaringan yang sama" melainkan jaringan yang
        berbeda — dan perbandingannya kehilangan makna.
        """
        for nama in jaringan.CACAT:
            a = jaringan.Jaringan([2, 4, 1], aktivasi="tanh", benih=21)
            b = jaringan.Jaringan([2, 4, 1], aktivasi="tanh", benih=21)
            b.atur_cacat(nama)
            for x in ([0.0, 0.0], [0.3, 0.9], [1.0, 1.0]):
                self.assertEqual(
                    fx.bits(a.ramal(x)[0]), fx.bits(b.ramal(x)[0]), "%s %r" % (nama, x)
                )

    def test_telusuri_tetap_sepadan_dengan_gradien_di_setiap_cacat(self):
        """Angka yang ditampilkan wajib angka yang dipakai — juga saat rusak.

        Tampilan langkah-demi-langkah adalah tempat pengunjung melihat *di
        mana* cacatnya bekerja. Kalau jejaknya memakai jalur yang berbeda dari
        gradien sungguhan, yang diperlihatkan bukan cacatnya melainkan cacat
        lain.
        """
        for nama in jaringan.CACAT:
            j = jaringan.Jaringan([2, 4, 1], aktivasi="tanh", benih=11)
            j.atur_cacat(nama)
            for x, t in jaringan.data_xor():
                jejak = j.telusuri(x, t)
                gw, gb = j.gradien([(x, t)])
                for lap in range(len(gw)):
                    for a in range(len(gw[lap])):
                        self.assertEqual(
                            fx.bits(gb[lap][a]),
                            fx.bits(jejak["gradien_b"][lap][a]),
                            "%s bias L%d n%d" % (nama, lap, a),
                        )
                        for b in range(len(gw[lap][a])):
                            self.assertEqual(
                                fx.bits(gw[lap][a][b]),
                                fx.bits(jejak["gradien_w"][lap][a][b]),
                                "%s bobot L%d %d<-%d" % (nama, lap, a, b),
                            )


class UjiTelusur(unittest.TestCase):
    """Menahan jejak langkah-demi-langkah tetap sepadan dengan pelatihannya.

    Tampilan langkah-demi-langkah hanya berguna kalau angka yang ditampilkan
    memang angka yang dipakai. Jejak yang menyimpang dari gradien sungguhan
    justru lebih buruk daripada tidak ada tampilan sama sekali: ia mengajarkan
    perambatan balik yang salah dengan penuh keyakinan.
    """

    def test_telusuri_sama_dengan_gradien(self):
        for ukuran, aktivasi in (
            ([2, 4, 1], "tanh"),
            ([2, 1], "sigmoid"),
            ([2, 5, 3, 1], "relu"),
            ([2, 3, 1], "linear"),
        ):
            j = jaringan.Jaringan(ukuran, aktivasi=aktivasi, benih=11)
            for x, t in jaringan.data_xor() + jaringan.data_lingkaran(6, benih=2):
                jejak = j.telusuri(x, t)
                gw, gb = j.gradien([(x, t)])
                for lap in range(len(gw)):
                    for a in range(len(gw[lap])):
                        # Dibandingkan sebagai pola bit, bukan dengan ``==``.
                        # ``-0.0 == 0.0`` bernilai benar, dan justru selisih
                        # nol negatif itulah yang pernah membedakan keduanya.
                        self.assertEqual(
                            fx.bits(gb[lap][a]),
                            fx.bits(jejak["gradien_b"][lap][a]),
                            "bias lapis %d neuron %d, %s" % (lap, a, aktivasi),
                        )
                        for b in range(len(gw[lap][a])):
                            self.assertEqual(
                                fx.bits(gw[lap][a][b]),
                                fx.bits(jejak["gradien_w"][lap][a][b]),
                                "bobot L%d %d<-%d, %s" % (lap, a, b, aktivasi),
                            )
                self.assertEqual(fx.bits(jejak["galat"]), fx.bits(j.galat([(x, t)])))
                self.assertEqual(fx.bits(jejak["keluaran"][0]), fx.bits(j.ramal(x)[0]))

    def test_bentuk_jejak(self):
        j = jaringan.Jaringan([2, 5, 3, 1], aktivasi="tanh", benih=3)
        jejak = j.telusuri([0.25, 0.75], [1.0])
        self.assertEqual([len(a) for a in jejak["aktivasi"]], [2, 5, 3, 1])
        self.assertEqual([len(p) for p in jejak["pra"]], [5, 3, 1])
        self.assertEqual([len(d) for d in jejak["delta"]], [5, 3, 1])
        self.assertEqual(jejak["aktivasi"][0], [0.25, 0.75])

    def test_aktivasi_sepadan_dengan_pra_aktivasi(self):
        """Keluaran tiap neuron wajib benar-benar hasil aktivasi jumlahnya."""
        for aktivasi in ("tanh", "sigmoid", "relu", "linear"):
            j = jaringan.Jaringan([2, 4, 1], aktivasi=aktivasi, benih=9)
            jejak = j.telusuri([0.3, 0.8], [0.0])
            akhir = len(j.bobot) - 1
            for lap in range(len(j.bobot)):
                f = j.f_keluaran if lap == akhir else j.f
                for k, z in enumerate(jejak["pra"][lap]):
                    self.assertEqual(
                        fx.bits(f(z)),
                        fx.bits(jejak["aktivasi"][lap + 1][k]),
                        "%s lapis %d neuron %d" % (aktivasi, lap, k),
                    )


class UjiBidangKeputusan(unittest.TestCase):
    """Menahan jalur cepat bidang keputusan tetap sama dengan jalur lambatnya.

    :meth:`bidang_keputusan` menghitung ulang urutan operasinya untuk memakai
    kembali suku ``w0*x`` dan ``w1*y`` di seluruh kisi. Susunan itu hanya sah
    selama urutan penjumlahannya persis sama dengan :meth:`maju`; merapikannya
    menjadi ``w0x + w1y + bias`` akan menghasilkan pembulatan yang berbeda,
    dan gambar yang tidak lagi sepadan dengan tabel angka di sebelahnya.
    """

    def test_bidang_keputusan_sama_persis(self):
        kisi = 9
        for ukuran, aktivasi in (
            ([2, 4, 1], "tanh"),
            ([2, 1], "sigmoid"),
            ([2, 6, 3, 1], "relu"),
            ([2, 8, 1], "linear"),
        ):
            j = jaringan.Jaringan(ukuran, aktivasi=aktivasi, benih=5)
            cepat = j.bidang_keputusan(kisi)
            self.assertEqual(len(cepat), kisi * kisi)
            for ky in range(kisi):
                for kx in range(kisi):
                    lambat = j.ramal([(kx + 0.5) / kisi, (ky + 0.5) / kisi])[0]
                    self.assertEqual(
                        fx.bits(cepat[ky * kisi + kx]),
                        fx.bits(lambat),
                        "%s %s di (%d, %d)" % (ukuran, aktivasi, kx, ky),
                    )

    def test_menolak_jaringan_yang_masukannya_bukan_dua(self):
        j = jaringan.Jaringan([3, 4, 1])
        with self.assertRaises(ValueError):
            j.bidang_keputusan(8)

    def test_menolak_kisi_tidak_masuk_akal(self):
        j = jaringan.Jaringan([2, 4, 1])
        with self.assertRaises(ValueError):
            j.bidang_keputusan(0)


class UjiLangkahTanpaGalat(unittest.TestCase):
    """``hitung_galat=False`` hanya boleh menghemat waktu, bukan mengubah bobot."""

    def test_bobot_sama_persis_dengan_atau_tanpa_galat(self):
        data = jaringan.data_xor()
        a = jaringan.Jaringan([2, 4, 1], aktivasi="tanh", benih=13)
        b = jaringan.Jaringan([2, 4, 1], aktivasi="tanh", benih=13)
        for _ in range(50):
            hasil_a = a.langkah(data, laju=0.4, momentum=0.7)
            hasil_b = b.langkah(data, laju=0.4, momentum=0.7, hitung_galat=False)
            self.assertIsNotNone(hasil_a)
            self.assertIsNone(hasil_b)
        for lap in range(len(a.bobot)):
            for j in range(len(a.bobot[lap])):
                self.assertEqual(fx.bits(a.bias[lap][j]), fx.bits(b.bias[lap][j]))
                for k in range(len(a.bobot[lap][j])):
                    self.assertEqual(
                        fx.bits(a.bobot[lap][j][k]), fx.bits(b.bobot[lap][j][k])
                    )


class UjiUraiData(unittest.TestCase):
    """Menguji pengurai data tempelan.

    Isinya ditulis orang lain, ditempel dari Excel, Word, atau catatan sendiri.
    Setiap bentuk yang mungkin ditempel harus berakhir di salah satu dari dua
    tempat: kumpulan data yang bisa dilatih, atau pesan yang bisa dimengerti.
    Tidak ada tempat ketiga.
    """

    def test_bentuk_paling_sederhana(self):
        hasil = data.urai("0,0,0\n0,1,1\n1,0,1\n1,1,0")
        self.assertEqual(len(hasil["data"]), 4)
        self.assertEqual(hasil["data"][0], ([0.0, 0.0], [0.0]))
        self.assertEqual(hasil["data"][3], ([1.0, 1.0], [0.0]))

    def test_pemisah_yang_berbeda_beda(self):
        for pemisah in (",", ";", "\t", "|"):
            teks = "\n".join(
                pemisah.join(k) for k in (["0", "0", "0"], ["0", "1", "1"],
                                          ["1", "0", "1"], ["1", "1", "0"])
            )
            self.assertEqual(len(data.urai(teks)["data"]), 4, repr(pemisah))
        # Spasi saja juga diterima; itu bentuk yang keluar dari banyak alat.
        self.assertEqual(len(data.urai("0 0 0\n0 1 1\n1 0 1\n1 1 0")["data"]), 4)

    def test_pemisah_dipilih_dari_seluruh_teks_bukan_baris_pertama(self):
        """Cacat sungguhan yang pernah ada di sini, dikunci.

        Bentuk pertama pengurai ini memilih pemisah dengan mengambil tanda
        pertama yang ditemukan di sebuah baris. Pada data Indonesia yang
        paling lazim — tiga kolom dipisah titik koma, dengan koma desimal di
        salah satunya — koma ditemukan lebih dulu, barisnya terbelah menjadi
        empat, dan seluruh berkas ditolak dengan pesan yang membingungkan.
        """
        # Titik koma sebagai pemisah, koma sebagai desimal.
        hasil = data.urai("165;55,0;0\n170;60,5;0\n175;72,0;1\n180;85,5;1")
        self.assertEqual(len(hasil["data"]), 4)

        # Tab sebagai pemisah, koma sebagai desimal — bentuk yang keluar
        # dari menyalin tabel Excel berwilayah Indonesia.
        hasil = data.urai(
            "165\t55,0\t0\n170\t60,5\t0\n175\t72,0\t1\n180\t85,5\t1"
        )
        self.assertEqual(len(hasil["data"]), 4)

        # Koma sebagai pemisah, titik sebagai desimal — bentuk internasional.
        hasil = data.urai("165,55.0,0\n170,60.5,0\n175,72.0,1\n180,85.5,1")
        self.assertEqual(len(hasil["data"]), 4)

    def test_pemilih_pemisah_menilai_bukan_menghitung_kemunculan(self):
        """Tanda yang lebih sering muncul belum tentu pemisahnya.

        Koma muncul delapan kali di bawah, titik koma hanya tiga — tetapi
        hanya titik koma yang menghasilkan tiga kolom angka.
        """
        baris = ["1,5;2,5;0", "3,5;4,5;1", "5,5;6,5;0", "7,5;8,5;1"]
        self.assertEqual(data.pilih_pemisah(baris), ";")

    def test_koma_desimal_gaya_indonesia(self):
        hasil = data.urai("0,0;0,0;0\n0,0;1,0;1\n1,0;0,0;1\n1,0;1,0;0")
        self.assertEqual(len(hasil["data"]), 4)

    def test_judul_kolom_dilewati_sekali(self):
        hasil = data.urai("x1,x2,kelas\n0,0,0\n0,1,1\n1,0,1\n1,1,0")
        self.assertEqual(len(hasil["data"]), 4)
        self.assertTrue(any("judul kolom" in c for c in hasil["catatan"]))

    def test_baris_kosong_dan_komentar_dilewati(self):
        hasil = data.urai("# catatan\n0,0,0\n\n0,1,1\n\n1,0,1\n1,1,0\n")
        self.assertEqual(len(hasil["data"]), 4)

    def test_penskalaan_diberitahukan(self):
        hasil = data.urai(data.CONTOH)
        self.assertEqual(len(hasil["data"]), 8)
        for masukan, _sasaran in hasil["data"]:
            for v in masukan:
                self.assertGreaterEqual(v, 0.0)
                self.assertLessEqual(v, 1.0)
        # Rentang aslinya wajib tercatat, bukan dibuang diam-diam.
        self.assertEqual(hasil["skala"][0]["minimum"], 165.0)
        self.assertEqual(hasil["skala"][0]["maksimum"], 182.0)
        self.assertTrue(any("diskalakan" in c for c in hasil["catatan"]))

    def test_kolom_tetap_diberitahukan_dan_tidak_menabrak(self):
        hasil = data.urai("5,0,0\n5,1,1\n5,0,0\n5,1,1")
        self.assertTrue(any("tidak membedakan" in c for c in hasil["catatan"]))
        for masukan, _s in hasil["data"]:
            self.assertEqual(masukan[0], 0.5)

    def test_menolak_dengan_pesan_yang_bisa_dibaca(self):
        kasus = [
            ("", "belum ada data"),
            ("   \n\n", "belum ada data"),
            ("0,0,0\n0,1,1", "sekurang-kurangnya 4"),
            ("0,0\n0,1\n1,0\n1,1", "3"),
            ("0,0,0\n0,1,0\n1,0,0\n1,1,0", "satu kelas"),
            ("0,0,0\n0,1,1\n1,0,7\n1,1,0", "0 atau 1"),
            ("0,0,0\n0,1,1\nabc,def,1\n1,1,0", "bukan angka"),
        ]
        for teks, potongan in kasus:
            with self.assertRaises(data.Galat, msg=repr(teks)) as tangkap:
                data.urai(teks)
            self.assertIn(potongan, str(tangkap.exception), repr(teks))

    def test_menolak_yang_terlalu_banyak(self):
        besar = "\n".join(
            "%d,%d,%d" % (i, i * 2, i % 2) for i in range(data.BATAS_BARIS + 10)
        )
        with self.assertRaises(data.Galat) as tangkap:
            data.urai(besar)
        self.assertIn("lebih dari", str(tangkap.exception))

    def test_batasnya_sendiri_masih_diterima(self):
        pas = "\n".join("%d,%d,%d" % (i, i * 2, i % 2) for i in range(data.BATAS_BARIS))
        self.assertEqual(len(data.urai(pas)["data"]), data.BATAS_BARIS)

    def test_nan_dan_takhingga_ditolak(self):
        for buruk in ("nan", "inf", "-inf", "Infinity"):
            teks = "0,0,0\n0,1,1\n%s,0,1\n1,1,0" % buruk
            with self.assertRaises(data.Galat, msg=buruk):
                data.urai(teks)

    def test_contoh_bawaan_bisa_dilatih(self):
        """Contoh yang ditawarkan halaman wajib benar-benar bisa dipakai."""
        hasil = data.urai(data.CONTOH)
        j = jaringan.Jaringan([2, 4, 1], aktivasi="tanh", benih=7)
        awal = j.galat(hasil["data"])
        for _ in range(500):
            j.langkah(hasil["data"], laju=0.5, momentum=0.9, hitung_galat=False)
        self.assertLess(j.galat(hasil["data"]), awal)


class UjiEkspor(unittest.TestCase):
    """Menguji penyusun CSV.

    Berkas yang gagal terbuka rapi di Excel sama tidak bergunanya dengan
    berkas yang tidak pernah diunduh.
    """

    def _keadaan_palsu(self):
        class Palsu:
            pass

        K = Palsu()
        K.dataset = "xor"
        K.tersembunyi = 4
        K.aktivasi = "tanh"
        K.benih = 7
        K.laju = 0.5
        K.momentum = 0.9
        K.cacat = "tidak_ada"
        K.epoch = 120
        K.jaringan = jaringan.Jaringan([2, 4, 1], aktivasi="tanh", benih=7)
        K.bayangan = None
        K.riwayat = [0.125, 0.1, 0.05]
        K._data = jaringan.data_xor()
        K.data = lambda: K._data
        return K

    def test_csv_diawali_bom_dan_petunjuk_pemisah(self):
        teks = ekspor.csv([["a", "b"], [1, 2]])
        # BOM wajib pertama: tanpa itu Excel di Windows membaca berkasnya
        # sebagai ANSI dan setiap huruf beraksen berubah jadi sampah.
        self.assertTrue(teks.startswith("\ufeff"))
        self.assertIn("sep=,", teks.splitlines()[0])
        self.assertIn(chr(13) + chr(10), teks)

    def test_sel_yang_memuat_koma_atau_kutip_dikutip(self):
        teks = ekspor.csv([["ada, koma", 'ada "kutip"', "polos"]])
        baris = teks.splitlines()[1]
        self.assertIn('"ada, koma"', baris)
        self.assertIn('"ada ""kutip"""', baris)
        self.assertIn(",polos", baris)

    def test_baris_baru_di_dalam_sel_tidak_merusak_bentuknya(self):
        teks = ekspor.csv([["dua" + chr(10) + "baris", "x"]])
        # Selnya dikutip, jadi jumlah kutip ganda pada baris itu genap.
        self.assertEqual(teks.count('"') % 2, 0)
        self.assertIn('"dua', teks)

    def test_laporan_memuat_seluruh_bagian(self):
        K = self._keadaan_palsu()
        baris = ekspor.laporan_baris(K)
        tajuk = {b[0] for b in baris if len(b) == 1 and isinstance(b[0], str)}
        for wajib in ("SETELAN", "HASIL", "RAMALAN TIAP TITIK", "BOBOT DAN BIAS",
                      "KURVA GALAT", "CATATAN"):
            self.assertIn(wajib, tajuk, wajib)

    def test_laporan_memuat_pemeriksaan_gradien_bila_ada(self):
        K = self._keadaan_palsu()
        hasil = K.jaringan.periksa_gradien(K.data())
        baris = ekspor.laporan_baris(K, hasil)
        tajuk = {b[0] for b in baris if len(b) == 1 and isinstance(b[0], str)}
        self.assertIn("PEMERIKSAAN GRADIEN", tajuk)
        # Tiap parameter wajib punya satu baris; yang hilang berarti laporan
        # yang tampak lengkap padahal tidak.
        rincian = [b for b in baris if b and b[0] in ("bobot", "bias")]
        self.assertGreaterEqual(len(rincian), len(hasil["rincian"]))

    def test_setiap_baris_laporan_bisa_disusun_jadi_csv(self):
        K = self._keadaan_palsu()
        teks = ekspor.csv(ekspor.laporan_baris(K, K.jaringan.periksa_gradien(K.data())))
        self.assertGreater(len(teks), 800)
        # Tidak boleh ada baris yang jumlah kutipnya ganjil: itu tanda sel
        # yang terpotong, dan Excel akan menelan sisa berkasnya.
        for baris in teks.split(chr(13) + chr(10)):
            self.assertEqual(baris.count('"') % 2, 0, baris[:60])

    def test_nama_berkas_menyebutkan_setelannya(self):
        K = self._keadaan_palsu()
        nama = ekspor.nama_berkas(K)
        for potongan in ("neuronusa", "xor", "h4", "tanh", "s7", "e120", ".csv"):
            self.assertIn(potongan, nama)
        K.cacat = "tanda_terbalik"
        self.assertIn("tanda_terbalik", ekspor.nama_berkas(K))


class UjiTautan(unittest.TestCase):
    """Memeriksa penyandi setelan yang isinya datang dari luar.

    Setiap nilai di sebuah alamat ditulis orang lain. Yang tidak diperiksa
    akan sampai ke :class:`Jaringan` apa adanya, dan kegagalannya terjadi di
    peramban pembaca — bukan di mesin pengirim.
    """

    def test_bolak_balik_utuh(self):
        setelan = {
            "dataset": "lingkaran",
            "tersembunyi": 0,
            "aktivasi": "sigmoid",
            "benih": 42,
            "laju": 0.2,
            "momentum": 0.5,
            "cacat": "turunan_hilang",
        }
        kembali = tautan.baca("#" + tautan.tulis(setelan))
        self.assertEqual(kembali, setelan)

    def test_pecahan_ditulis_ringkas_dan_terbaca_kembali(self):
        """Alamatnya harus pendek, dan tetap membawa nilai yang sama.

        Bentuk ilmiah dilarang muncul: ``l=5e-01`` sah secara teknis tetapi
        membuat alamat yang tidak bisa dibaca sekilas oleh orang yang
        menerimanya, dan seluruh gunanya tautan ini adalah bisa dibaca.
        """
        for nama, nilai in (
            ("laju", 0.5),
            ("laju", 0.01),
            ("laju", 5.0),
            ("laju", 1.0),
            ("laju", 0.25),
            ("momentum", 0.0),
            ("momentum", 0.9),
            ("momentum", 0.99),
        ):
            teks = tautan.tulis({nama: nilai})
            self.assertNotIn("e", teks, teks)
            self.assertLessEqual(len(teks), 8, teks)
            self.assertEqual(tautan.baca(teks), {nama: nilai}, teks)

    def test_menolak_nilai_di_luar_rentang(self):
        for tanda, nama in (
            ("h=9", "tersembunyi"),
            ("h=-1", "tersembunyi"),
            ("s=0", "benih"),
            ("s=201", "benih"),
            ("l=5.01", "laju"),
            ("l=0", "laju"),
            ("m=1", "momentum"),
            ("m=-0.1", "momentum"),
        ):
            self.assertNotIn(nama, tautan.baca(tanda), tanda)

    def test_menolak_nilai_yang_tidak_dikenal(self):
        for tanda in ("d=segitiga", "a=selu", "c=tidak-pernah-ada"):
            self.assertEqual(tautan.baca(tanda), {}, tanda)

    def test_menolak_bukan_angka(self):
        for tanda in ("h=empat", "s=", "l=abc", "m=NaN", "l=nan", "m=inf", "l=-inf"):
            self.assertEqual(tautan.baca(tanda), {}, tanda)

    def test_nan_dan_takhingga_ditolak_walau_perbandingannya_aneh(self):
        """NaN gagal setiap perbandingan, termasuk yang dipakai menolaknya.

        Pemeriksa yang ditulis sebagai ``if v < kecil or v > besar: tolak``
        akan meloloskan NaN, karena kedua perbandingannya bernilai salah.
        Satu NaN yang lolos merusak seluruh bobot dalam satu langkah
        pelatihan.
        """
        for teks in ("nan", "NaN", "-nan", "inf", "-inf", "Infinity"):
            self.assertIsNone(tautan.PEMERIKSA["laju"](teks), teks)
            self.assertIsNone(tautan.PEMERIKSA["momentum"](teks), teks)

    def test_bagian_yang_rusak_tidak_membuang_bagian_yang_baik(self):
        hasil = tautan.baca("#d=xor&h=99&a=relu&z=1&rusak&s=12")
        self.assertEqual(
            hasil, {"dataset": "xor", "aktivasi": "relu", "benih": 12}
        )

    def test_tanda_kosong_menghasilkan_kamus_kosong(self):
        for tanda in ("", "#", None):
            self.assertEqual(tautan.baca(tanda), {})

    def test_kunci_pendek_unik_dan_lengkap(self):
        nama = [n for n, _k in tautan.KUNCI]
        kunci = [k for _n, k in tautan.KUNCI]
        self.assertEqual(len(set(kunci)), len(kunci), "kunci pendek bertabrakan")
        self.assertEqual(set(nama), set(tautan.PEMERIKSA), "pemeriksa tidak lengkap")

    def test_batas_sepadan_dengan_yang_bisa_dipakai_jaringan(self):
        """Batas di tautan harus benar-benar bisa dibangun jadi jaringan.

        Kalau batasnya lebih longgar daripada yang sanggup dibangun, sebuah
        tautan yang lolos pemeriksaan akan tetap merusak halaman saat dibuka.
        """
        for tersembunyi in (
            tautan.BATAS["tersembunyi"][0],
            tautan.BATAS["tersembunyi"][1],
        ):
            ukuran = [2, 1] if tersembunyi == 0 else [2, tersembunyi, 1]
            for aktivasi in jaringan.AKTIVASI:
                j = jaringan.Jaringan(ukuran, aktivasi=aktivasi, benih=1)
                for cacat in jaringan.CACAT:
                    j.atur_cacat(cacat)
                    j.langkah(
                        jaringan.data_xor(),
                        laju=tautan.BATAS["laju"][1],
                        momentum=tautan.BATAS["momentum"][1],
                        hitung_galat=False,
                    )
                self.assertTrue(math.isfinite(j.galat(jaringan.data_xor())))


class UjiKonformansiBertahap(unittest.TestCase):
    """Memeriksa bahwa memotong pekerjaan tidak mengubah hasilnya.

    Pemeriksaan konformansi dijalankan sepotong-sepotong di dalam peramban,
    supaya halamannya tidak membeku 2,4 detik. Pemotongan itu menyimpan
    keadaan di antara panggilan — berkas mana yang sedang dibuka, baris ke
    berapa, cacah mana yang sedang diisi — dan keadaan yang salah dipulihkan
    adalah cara paling mudah menghasilkan laporan hijau yang tidak memeriksa
    apa pun.
    """

    def test_potongan_kecil_sama_dengan_sekaligus(self):
        sekaligus = konform.jalankan(muat_vektor)
        for batas in (1, 7, 100):
            bertahap = konform.Bertahap(muat_vektor)
            putaran = 0
            while bertahap.kerjakan(batas):
                putaran += 1
                self.assertLess(putaran, 20000, "tidak pernah selesai")
            hasil = bertahap.laporan
            self.assertTrue(bertahap.selesai)
            self.assertEqual(hasil.total, sekaligus.total, "batas %d" % batas)
            self.assertEqual(hasil.total_gagal, 0)
            self.assertEqual(
                [(b.nama, b.diperiksa, b.tingkat, b.ulp_maks) for b in hasil.berkas],
                [(b.nama, b.diperiksa, b.tingkat, b.ulp_maks) for b in sekaligus.berkas],
                "batas %d" % batas,
            )

    def test_kemajuan_mencapai_seluruh_baris(self):
        bertahap = konform.Bertahap(muat_vektor)
        while bertahap.kerjakan(50):
            pass
        self.assertGreater(bertahap.baris_selesai, 0)
        self.assertEqual(bertahap.baris_selesai, bertahap.total_baris)

    def test_vektor_hilang_menggagalkan_dan_bukan_diam(self):
        """Berkas yang tidak terbaca wajib terlihat, bukan mengurangi cacah."""

        def muat_pincang(nama):
            if nama == "bayes.tsv":
                raise OSError("sengaja tidak ada")
            return muat_vektor(nama)

        laporan = konform.jalankan(muat_pincang)
        self.assertFalse(laporan.lolos)
        self.assertEqual(len(laporan.galat_muat), 1)
        self.assertIn("bayes.tsv", laporan.galat_muat[0])

    def test_laporan_kosong_tidak_dianggap_lolos(self):
        laporan = konform.jalankan(muat_vektor, berkas=[])
        self.assertEqual(laporan.total, 0)
        self.assertFalse(
            laporan.lolos,
            "laporan tanpa satu pun pernyataan tidak boleh dianggap berhasil",
        )


class UjiPortabilitasFx(unittest.TestCase):
    """Menahan penyandian IEEE-754 tetap benar di luar CPython.

    Kedua uji di bawah lahir dari cacat sungguhan yang hanya muncul di Brython
    dan tidak bisa ditangkap uji CPython mana pun — keduanya ditemukan dengan
    menjalankan konformansi ini di dalam peramban. Yang bisa diuji di sini
    adalah bentuk kodenya: bahwa penskalaan dipecah, dan bahwa pemformatan
    ilmiah tidak lagi lewat operator ``%``.
    """

    def test_penskalaan_dipecah_agar_tidak_meluap(self):
        """``ldexp`` sejauh 1074 tahap meluap di sebagian penerjemah.

        Brython menerjemahkannya menjadi perkalian dengan ``2**n``, dan
        ``2**1074`` sendiri sudah tak hingga sebagai ``float`` — padahal
        ``ldexp(5e-324, 1074)`` sama sekali tidak meluap, hasilnya 1,0.

        Perhatikan pasangan yang diuji: seluruhnya berujung pada nilai yang
        memang bisa diwakili. Menguji ``ldexp(1.0, 1074)`` tidak berarti apa-apa
        di sini, karena yang itu sungguh-sungguh meluap di CPython juga.
        """
        self.assertLessEqual(fx._PANGKAS_SKALA, 1000)
        self.assertGreater(fx._PANGKAS_SKALA, 0)

        pasangan = [
            (5e-324, 1074, 1.0),
            (5e-324, 1073, 0.5),
            (1.0, -1074, 5e-324),
            (4503599627370496.0, -1074, 2.2250738585072014e-308),  # 2**52 * 2**-1074
            (1.0, 0, 1.0),
            (1.0, 500, math.ldexp(1.0, 500)),
            (1.0, -500, math.ldexp(1.0, -500)),
            (1.0, 501, math.ldexp(1.0, 501)),
            (1.0, -1022, math.ldexp(1.0, -1022)),
            (2.0, 1022, math.ldexp(2.0, 1022)),
        ]
        for x, n, harap in pasangan:
            self.assertEqual(fx._skala(x, n), harap, "x=%r n=%d" % (x, n))

        # Yang memang harus meluap tetap meluap, dengan cara yang sama.
        for x, n in ((1.0, 1074), (4503599627370496.0, 1023)):
            with self.assertRaises(OverflowError):
                fx._skala(x, n)

    def test_subnormal_terkecil_bolak_balik(self):
        """Baris yang menyingkap cacat ``ldexp`` itu, diuji langsung."""
        for hex_ in ("0000000000000001", "0000000000000000", "8000000000000000",
                     "000fffffffffffff", "0010000000000000"):
            self.assertEqual(fx.ke_hex(fx.dari_hex(hex_)), hex_)


if __name__ == "__main__":
    unittest.main(verbosity=2)
