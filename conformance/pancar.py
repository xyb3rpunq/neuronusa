"""Memancarkan pola bit yang dihitung mesin Python, satu baris per pernyataan.

Dipakai halaman "Enam bahasa, satu angka" di AI ATLAS. Kuncinya
(berkas, baris, kolom) sama persis dengan yang dipakai harness Go, PL/SQL,
Lua, dan Swift, sehingga keenam bahasa bisa disandingkan tanpa satu pun
penyesuaian.

Angkanya datang dari jalan konformansi yang sama, lewat panggilan yang sama.
Menghitungnya lagi di jalur terpisah akan membuat halaman menampilkan pola bit
yang tidak pernah dibandingkan dengan apa pun — tabel yang terlihat seperti
bukti padahal bukan.

.Deckyx
"""

import datetime
import os
import platform
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "py"))

from nusa import konform  # noqa: E402

DASAR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vectors")


def muat(nama):
    with open(os.path.join(DASAR, nama), "r", encoding="utf-8") as f:
        return f.read()


def main():
    if len(sys.argv) < 2:
        print("pemakaian: python conformance/pancar.py <berkas-keluaran.tsv>", file=sys.stderr)
        return 2

    laporan = konform.jalankan(muat, pancar=True)

    if laporan.galat_muat:
        for pesan in laporan.galat_muat:
            print("Vektor tidak terbaca: %s" % pesan, file=sys.stderr)
        return 2

    # Jalan yang gagal tetap dipancarkan: pola bit yang berbeda justru yang
    # paling layak dilihat. Yang tidak boleh dipancarkan adalah jalan yang
    # tidak memeriksa apa pun, karena berkasnya akan kosong tanpa alasan.
    if not laporan.pancar:
        print("tidak ada pola bit yang dipancarkan", file=sys.stderr)
        return 1

    waktu = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    baris = [
        "# neuronusa — pola bit yang dihitung Python",
        "# bahasa: python",
        "# versi: %s %s" % (platform.python_implementation(), platform.python_version()),
        "# dihasilkan: %s" % waktu,
        "# perintah: python conformance/pancar.py",
        "# kolom: berkas\tbaris\tkolom\thasil_hex\tkonteks",
    ]
    for p in laporan.pancar:
        baris.append(
            "\t".join(
                [p["berkas"], str(p["baris"]), p["kolom"], p["hasil_hex"], p["konteks"] or ""]
            )
        )

    with open(sys.argv[1], "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(baris) + "\n")

    print("Pola bit Python: %d pernyataan → %s" % (len(laporan.pancar), sys.argv[1]))
    if laporan.total_gagal:
        print("Catatan: %d pernyataan tidak cocok pada jalan ini." % laporan.total_gagal)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
