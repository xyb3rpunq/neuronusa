/**
 * Anggaran ukuran berkas terbitan.
 *
 * Brython adalah penerjemah Python yang utuh, jadi anggarannya jauh lebih
 * longgar daripada tiga situs pendahulunya — dan itu memang harganya. Yang
 * dijaga anggaran ini bukan supaya ia kecil, melainkan supaya ia tidak
 * pelan-pelan membesar tanpa ada yang menyadarinya.
 *
 * .Deckyx
 */

import { gzipSync } from "node:zlib";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, extname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const AKAR = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const DIST = join(AKAR, "dist");

// Angkanya diikat ke ukuran sekarang plus sedikit ruang, bukan dipilih
// longgar. Anggaran yang jauh di atas kenyataan tidak pernah gagal, dan
// anggaran yang tidak pernah gagal tidak mengukur apa pun.
const ANGGARAN = { ".js": 285, ".css": 9, ".html": 14 };

// Yang dihitung hanya berkas yang benar-benar diambil saat halaman dibuka.
// vektor_vfs.js sengaja tidak termasuk: ia baru diambil kalau pengunjung
// menekan tombol konformansi, dan memasukkannya ke anggaran halaman akan
// menghukum sebuah berkas justru karena ia berhasil dibuat malas.
const DIKECUALIKAN = new Set(["vendor/vektor_vfs.js"]);
// 256 KB dari angka ini adalah brython.min.js sendiri — penerjemah Python yang
// utuh, dan bukan sesuatu yang bisa dikecilkan tanpa berhenti menjadi situs
// Python. Sisanya sekitar 65 KB: pustaka standar yang sudah dipangkas dari
// 4,6 MB, mesin jaringan syarafnya, dan halamannya sendiri.
//
// Angkanya diikat sedikit di atas kenyataan sekarang, bukan dipilih longgar.
// Anggaran yang tidak pernah gagal tidak mengukur apa pun. Ia dinaikkan hanya
// bersama perubahan yang memang menambah kemampuan — terakhir saat pengurai
// data tempelan dan penyusun laporan CSV masuk.
const ANGGARAN_TOTAL = 360;

function semuaBerkas(dir) {
  const keluar = [];
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const jalur = join(dir, e.name);
    if (e.isDirectory()) keluar.push(...semuaBerkas(jalur));
    else keluar.push(jalur);
  }
  return keluar;
}

const baris = [];
let total = 0;
let terlampaui = 0;

for (const jalur of semuaBerkas(DIST).sort()) {
  if (jalur.endsWith(".map")) continue;
  const nama = relative(DIST, jalur).split("\\").join("/");
  const kb = gzipSync(readFileSync(jalur), { level: 9 }).length / 1024;
  const batas = ANGGARAN[extname(jalur)];
  const lewat = batas !== undefined && kb > batas;
  if (lewat) terlampaui += 1;
  if (!DIKECUALIKAN.has(nama)) total += kb;
  baris.push({
    berkas: nama,
    gzip: `${kb.toFixed(1)} KB`,
    anggaran: batas === undefined ? "—" : `${batas} KB`,
    status: DIKECUALIKAN.has(nama)
      ? "malas"
      : batas === undefined
        ? "—"
        : lewat
          ? "LEWAT"
          : "ok",
  });
}

console.table(baris);
const totalLewat = total > ANGGARAN_TOTAL;
console.log(
  `\nTotal seluruh berkas: ${total.toFixed(1)} KB  (anggaran ${ANGGARAN_TOTAL} KB) — ` +
    (totalLewat ? "LEWAT" : "ok"),
);

if (baris.length === 0) {
  console.error("Tidak ada satu pun berkas di dist/. Build tidak berjalan.");
  process.exit(2);
}
if (terlampaui > 0 || totalLewat) {
  console.error(`\nAnggaran terlampaui pada ${terlampaui} berkas.`);
  process.exit(1);
}
console.log("Seluruh anggaran terpenuhi.");

// Berkas wajib. Mesin Python yang hilang dari hasil build tidak akan
// menggagalkan build maupun uji mana pun; halamannya hanya akan berhenti di
// layar "memuat" selamanya.
//
// Isi nusa_vfs.js ikut diperiksa, bukan hanya keberadaannya: berkas yang
// dihasilkan dari direktori kosong tetap sah sebagai JavaScript, tetap lolos
// pemeriksaan ukuran, dan tetap menghasilkan halaman yang mati.
for (const wajib of [
  "index.html", "404.html", "robots.txt",
  "vendor/brython.min.js", "vendor/brython_stdlib_mini.js",
  "vendor/nusa_vfs.js", "vendor/vektor_vfs.js",
]) {
  try {
    statSync(join(DIST, wajib));
  } catch {
    console.error(`Berkas wajib hilang dari hasil build: ${wajib}`);
    process.exit(3);
  }
}
// Modul yang wajib ada di muatan pertama. `nusa.konform` sengaja tidak di
// sini: ia ikut berkas yang malas bersama vektornya, karena hanya tombol
// konformansi yang membutuhkannya.
const WAJIB_AWAL = [
  "nusa", "nusa.fx", "nusa.inti", "nusa.jaringan",
  "nusa.tautan", "nusa.data", "nusa.ekspor", "nusa.bahasa", "app",
];
const WAJIB_MALAS = ["nusa.konform", "nusa.vektor"];

const vfs = readFileSync(join(DIST, "vendor", "nusa_vfs.js"), "utf8");
for (const modul of WAJIB_AWAL) {
  if (!vfs.includes(`"${modul}":`)) {
    console.error(`Modul '${modul}' tidak ada di dalam vendor/nusa_vfs.js`);
    process.exit(3);
  }
}
const vfsMalas = readFileSync(join(DIST, "vendor", "vektor_vfs.js"), "utf8");
for (const modul of WAJIB_MALAS) {
  if (!vfsMalas.includes(`"${modul}":`)) {
    console.error(`Modul '${modul}' tidak ada di dalam vendor/vektor_vfs.js`);
    process.exit(3);
  }
}
// Yang malas tidak boleh ikut ke muatan pertama; kalau ikut, penundaannya
// tidak menghemat apa pun dan hanya menambah satu berkas.
for (const modul of WAJIB_MALAS) {
  if (vfs.includes(`"${modul}":`)) {
    console.error(`Modul '${modul}' seharusnya malas, tetapi ada di muatan pertama.`);
    process.exit(3);
  }
}
console.log(
  `Seluruh berkas wajib ada: ${WAJIB_AWAL.length} modul di muatan pertama, ` +
    `${WAJIB_MALAS.length} ditunda.`,
);
