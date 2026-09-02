"""Menjalankan konformansi dari baris perintah.

Logika pemeriksanya ada di ``nusa.konform``, bukan di sini, karena pemeriksaan
yang sama juga dijalankan di dalam peramban. Berkas ini hanya membaca cakram
dan mencetak.

Keluar dengan kode bukan nol bila ada satu pun ketidakcocokan, sehingga CI
gagal alih-alih hanya mencetak peringatan yang tidak dibaca siapa pun.

.Deckyx
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "py"))

from nusa import konform  # noqa: E402

DASAR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vectors")


def muat(nama):
    with open(os.path.join(DASAR, nama), "r", encoding="utf-8") as f:
        return f.read()


def main():
    laporan = konform.jalankan(muat)

    print("Konformansi Python terhadap vektor Rust — neuronusa .Deckyx")
    print("=" * 74)
    for b in laporan.berkas:
        status = "ok" if b.lolos else "%d GAGAL" % b.gagal
        print(
            "%-26s%6d diperiksa  %-24sULP maks %3d  %s"
            % (b.nama, b.diperiksa, b.tingkat, b.ulp_maks, status)
        )
    print("=" * 74)

    for pesan in laporan.galat_muat:
        print("Vektor tidak terbaca: %s" % pesan, file=sys.stderr)
    if laporan.galat_muat:
        return 2

    if laporan.total_gagal:
        print(
            "%d ketidakcocokan (paling banyak %d baris pertama):"
            % (laporan.total_gagal, konform.BATAS_KETIDAKCOCOKAN)
        )
        for k in laporan.ketidakcocokan:
            ekor = "  ULP %s" % k.ulp if k.ulp is not None else ""
            print(
                "  %-26s%-30sharap %s  dapat %s%s"
                % ("%s:%d" % (k.berkas, k.nomor), k.konteks, k.harap, k.dapat, ekor)
            )
        return 1

    if laporan.total == 0:
        print("Tidak ada satu pun pernyataan yang diperiksa.", file=sys.stderr)
        return 2

    print("Seluruh %d pernyataan cocok antara Python dan Rust." % laporan.total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
