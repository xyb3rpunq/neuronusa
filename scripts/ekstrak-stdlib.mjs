/**
 * Mengambil hanya modul pustaka standar Brython yang benar-benar dipakai.
 *
 * # Kenapa tidak menyalin brython_stdlib.js apa adanya
 *
 * Berkasnya 4,6 MB. Situs ini memakai tiga modul dari dalamnya — `_svg`,
 * `browser.svg`, dan `browser.timer` — yang seluruhnya berjumlah sekitar
 * 4 KB. Menyertakan sisanya berarti peramban mengunduh, mengurai, dan
 * menjalankan seribu kali lipat kode yang tidak pernah disentuh, pada
 * halaman yang justru dituntut ringan.
 *
 * Mesin Python di proyek ini sengaja tidak mengimpor apa pun selain `math`,
 * yang sudah ada di inti Brython. Itu bukan kebetulan: modul `struct` yang
 * dipakai bentuk pertama `fx.py` menarik `_struct`, yang menarik `re` — dan
 * `re` di Brython adalah mesin ekspresi reguler yang ditulis dalam Python.
 * Menghindarinya adalah alasan `fx.py` menyandi IEEE-754 sendiri.
 *
 * # Kenapa diekstrak, bukan disalin tangan
 *
 * Supaya `npm update brython` cukup dijalankan lalu skrip ini mengambil versi
 * barunya. Potongan yang disalin tangan akan tertinggal diam-diam, dan
 * ketertinggalan itu hanya terlihat saat halamannya rusak di produksi.
 *
 * .Deckyx
 */

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const AKAR = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const SUMBER = join(AKAR, "node_modules", "brython", "brython_stdlib.js");
const TUJUAN = join(AKAR, "public", "vendor", "brython_stdlib_mini.js");

/**
 * Modul yang diimpor langsung oleh kode kita. Kebergantungannya diikuti sendiri.
 *
 * `math` ada di daftar ini dan bukan di inti Brython — inti hanya menyimpan
 * *nama*-nya, lalu mengambil isinya dari berkas pustaka standar saat diimpor.
 * Menghilangkannya membuat `import math` gagal dengan
 * `SyntaxError: Unexpected token '<'`, karena yang terambil adalah halaman
 * 404 berbentuk HTML, bukan modulnya.
 */
const DIMINTA = ["math", "browser.svg", "browser.timer"];

const teks = readFileSync(SUMBER, "utf8");
const awal = teks.indexOf("var scripts = ");
if (awal < 0) throw new Error("format brython_stdlib.js berubah: 'var scripts =' tidak ada");
const tanda = teks.lastIndexOf("__BRYTHON__.update_VFS");
const vfs = JSON.parse(teks.slice(awal + "var scripts = ".length, teks.lastIndexOf("}", tanda) + 1));

// Penutupan kebergantungan. Ditelusuri, bukan diketik: daftar yang diketik
// tangan akan benar hari ini dan salah pada versi Brython berikutnya.
const perlu = new Set();
const antre = [...DIMINTA];
while (antre.length) {
  const nama = antre.pop();
  if (perlu.has(nama)) continue;
  const entri = vfs[nama];
  if (!entri) throw new Error(`modul '${nama}' tidak ada di brython_stdlib.js`);
  perlu.add(nama);
  for (const d of entri[2] ?? []) if (vfs[d] !== undefined) antre.push(d);
}

const kecil = { $timestamp: vfs.$timestamp };
for (const nama of [...perlu].sort()) kecil[nama] = vfs[nama];

const keluaran =
  "// Dihasilkan scripts/ekstrak-stdlib.mjs — jangan disunting tangan.\n" +
  "// Berisi hanya modul pustaka standar Brython yang dipakai neuronusa.\n" +
  "// .Deckyx\n" +
  "__BRYTHON__.use_VFS = true;\n" +
  `var scripts = ${JSON.stringify(kecil)}\n` +
  "__BRYTHON__.update_VFS(scripts)\n";

mkdirSync(dirname(TUJUAN), { recursive: true });
writeFileSync(TUJUAN, keluaran);

const kb = (n) => `${(n / 1024).toFixed(1)} KB`;
console.log(
  `Pustaka standar dipangkas: ${kb(teks.length)} \u2192 ${kb(keluaran.length)} ` +
    `(${perlu.size} modul: ${[...perlu].sort().join(", ")})`,
);
