/**
 * Mengemas mesin Python menjadi satu berkas yang bisa diimpor Brython tanpa
 * satu pun permintaan jaringan tambahan.
 *
 * # Kenapa tidak menaruh berkas .py begitu saja lalu memakai `pythonpath`
 *
 * Karena Brython mengimpor modul dengan XMLHttpRequest **sinkron**, dan
 * setiap `import` karena itu memblokir utas tampilan selama satu perjalanan
 * pulang-pergi jaringan. Lima modul berarti lima kali membeku berturut-turut,
 * sebelum sebaris pun antarmuka tergambar.
 *
 * Mengambilnya lebih dulu dengan `fetch` tidak menolong: Brython menempelkan
 * `?v=<waktu sekarang>` pada setiap URL modul, sehingga permintaannya tidak
 * pernah cocok dengan apa pun yang sudah ada di singgahan. (Penempelan itu
 * bisa dimatikan dengan opsi `cache`, tetapi opsi yang sama menyalakan
 * singgahan indexedDB — dan modul lama yang tertinggal di sana setelah
 * penerbitan baru adalah cacat yang jauh lebih mahal daripada satu perjalanan
 * jaringan.)
 *
 * Jalan yang benar adalah yang dipakai pustaka standar Brython sendiri:
 * berkas mesin virtual. Seluruh modul dititipkan lewat `update_VFS`, dan
 * `import` menemukannya di memori.
 *
 * Hasilnya: satu permintaan, nol XHR sinkron, dan tidak ada 404 dari Brython
 * yang menjajal `nusa.py` sebelum `nusa/__init__.py`.
 *
 * # Sumber kebenarannya tetap py/nusa/
 *
 * Direktori itulah yang dipakai uji dan konformansi. Berkas di `public/`
 * dihasilkan, bukan disunting, dan diabaikan git supaya tidak ada dua tempat
 * yang harus dijaga tetap sepadan.
 *
 * .Deckyx
 */

import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const AKAR = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const PUBLIK = join(AKAR, "public");
const VENDOR = join(PUBLIK, "vendor");

mkdirSync(VENDOR, { recursive: true });

// ---------------------------------------------------------------------------
// Runtime Brython
// ---------------------------------------------------------------------------

// Disalin ke dalam repositori, bukan diambil dari CDN. Kebijakan keamanan
// situs ini membatasi script-src ke 'self', dan itu disengaja: mesin yang
// menjalankan kode Python di peramban pengguna tidak pantas diambil dari
// tempat yang bisa berubah tanpa sepengetahuan siapa pun.
const brython = join(AKAR, "node_modules", "brython", "brython.min.js");
writeFileSync(join(VENDOR, "brython.min.js"), readFileSync(brython));

// Pustaka standarnya dipangkas, bukan disalin utuh: 4,6 MB menjadi 89 KB.
// Alasan lengkapnya ada di scripts/ekstrak-stdlib.mjs.
execFileSync(process.execPath, [join(AKAR, "scripts", "ekstrak-stdlib.mjs")], {
  stdio: "inherit",
});

// ---------------------------------------------------------------------------
// Mesin Python kita sendiri
// ---------------------------------------------------------------------------

const PAKET = "nusa";

/**
 * Membaca kebergantungan sebuah modul dari pernyataan importnya.
 *
 * Sengaja hanya mengenali bentuk yang benar-benar dipakai paket ini —
 * `import x`, `from x import y`, dan `from .x import y` di margin kiri.
 * Pengurai yang lebih pintar akan lebih sering benar tetapi jauh lebih sulit
 * dipastikan benar; yang ini gagal dengan berisik lewat berkas yang tidak
 * bisa diimpor, bukan diam-diam.
 */
function bacaKebergantungan(sumber) {
  const keluar = new Set();
  for (const baris of sumber.split("\n")) {
    let cocok = /^import\s+([A-Za-z_][\w.]*)/.exec(baris);
    if (cocok) keluar.add(cocok[1]);
    cocok = /^from\s+(\.?)([A-Za-z_][\w.]*)\s+import\s/.exec(baris);
    if (cocok) keluar.add(cocok[1] ? `${PAKET}.${cocok[2]}` : cocok[2]);
  }
  return [...keluar].sort();
}

const vfs = {};

// Waktu berkas termuda dipakai sebagai cap waktu mesin virtual. Brython
// membandingkannya dengan cap waktu di singgahan untuk membuang modul basi;
// cap yang tidak pernah berubah akan membuat modul lama tetap dipakai setelah
// kode barunya terbit.
let capWaktu = 0;

const vfsMalas = {};

function tambah(namaModul, jalur, paket) {
  const sumber = readFileSync(jalur, "utf8");
  capWaktu = Math.max(capWaktu, Math.trunc(statSync(jalur).mtimeMs));
  const entri = [".py", sumber, bacaKebergantungan(sumber)];
  if (paket) entri.push(1);
  (MODUL_MALAS.has(namaModul) ? vfsMalas : vfs)[namaModul] = entri;
}

/**
 * Modul yang hanya dibutuhkan tombol konformansi.
 *
 * Ikut ke berkas yang malas bersama vektornya, bukan ke muatan pertama.
 * Aturannya sederhana dan bisa dinyatakan dalam satu kalimat: **berkas yang
 * malas berisi tepat apa yang dibutuhkan tombol konformansi, dan tidak ada
 * yang lain.** Pemeriksa gradien, pelatihan, dan seluruh gambar tidak pernah
 * menyentuhnya.
 */
const MODUL_MALAS = new Set(["nusa.konform"]);

const dirNusa = join(AKAR, "py", PAKET);
tambah(PAKET, join(dirNusa, "__init__.py"), true);

const modul = readdirSync(dirNusa)
  .filter((f) => f.endsWith(".py") && f !== "__init__.py")
  .sort();
for (const berkas of modul) {
  tambah(`${PAKET}.${basename(berkas, ".py")}`, join(dirNusa, berkas), false);
}

// Antarmukanya juga Python, dan tinggal di `src/` bersama sumber lain agar
// penyunting memperlakukannya sebagai kode, bukan sebagai aset.
tambah("app", join(AKAR, "src", "app.py"), false);

// ---------------------------------------------------------------------------
// Vektor konformansi
// ---------------------------------------------------------------------------

// Kesembilan berkas vektor ikut dikemas sebagai modul Python, supaya
// pemeriksaan konformansi yang sama persis dengan yang dijalankan CI bisa
// dijalankan ulang di dalam peramban pengunjung.
//
// Ini bukan hiasan. Klaim utama proyek ini — enam bahasa sepakat sampai ke
// bit terakhir — akan menjadi sekadar kalimat kalau yang bisa dilihat
// pengunjung hanyalah angka 3.796 yang diketik ke dalam HTML. Dan alasannya
// bukan teoretis: penerjemah di peramban ternyata memformat `'%.3e'` dengan
// salah, cacat yang membuat pemeriksa gradien melaporkan "0.000e+00" untuk
// setiap parameter. Runtime yang berbeda memang berperilaku berbeda; satu-
// satunya cara mengetahuinya adalah menjalankan ujinya di sana.
//
// Seluruhnya 24 KB setelah dimampatkan, dan hanya diurai kalau pengunjung
// menekan tombolnya.

// Ditulis lewat kode karakter, bukan sebagai escape di dalam untai. Berkas ini
// beberapa kali dihasilkan lewat perkakas yang menafsirkan escape-nya sendiri,
// dan `"\r\n"` yang berubah menjadi baris baru sungguhan di tengah untai adalah
// galat sintaks yang penyebabnya tidak terlihat sama sekali di layar.
const CR = String.fromCharCode(13);
const LF = String.fromCharCode(10);

const dirVektor = join(AKAR, "conformance", "vectors");
const vektor = {};
for (const berkas of readdirSync(dirVektor).filter((f) => f.endsWith(".tsv")).sort()) {
  const jalur = join(dirVektor, berkas);
  // Akhir baris dinormalkan. Berkas yang di-checkout di Windows membawa CRLF,
  // dan carriage return yang ikut terbawa akan menempel di kolom terakhir
  // tiap baris — membuat setiap pola bit di kolom itu gagal diurai, dan
  // hanya di sebagian mesin.
  vektor[berkas] = readFileSync(jalur, "utf8").split(CR).join("");
  capWaktu = Math.max(capWaktu, Math.trunc(statSync(jalur).mtimeMs));
}
if (Object.keys(vektor).length === 0) {
  console.error("Tidak ada satu pun berkas vektor di conformance/vectors.");
  process.exit(2);
}

// JSON.stringify menghasilkan untai yang juga sah sebagai literal Python untuk
// isi seperti ini: escape tab, baris baru, kutip ganda, dan garis miring
// terbalik ditulis sama persis di kedua bahasa. Yang tidak sama — pemisah
// baris U+2028 misalnya — tidak muncul di vektor, dan pemeriksaan konformansi
// itu sendiri yang akan berteriak kalau suatu saat muncul.
const kepalaVektor = [
  '"""Vektor uji lintas bahasa, dikemas untuk dijalankan di peramban.',
  "",
  "Dihasilkan scripts/salin-py.mjs dari conformance/vectors/.",
  "Jangan disunting tangan.",
  '"""',
  "",
  "",
].join(LF);

// Ditulis ke berkasnya sendiri, bukan ke dalam nusa_vfs.js.
//
// Vektornya 55 KB setelah dimampatkan — seperempat dari seluruh berat halaman,
// dan tidak satu pun dari itu dibutuhkan sampai pengunjung menekan tombol
// konformansi. Memuatnya di muka berarti setiap pengunjung membayar ongkos
// sebuah tombol yang mungkin tidak pernah ia tekan.
const vfsVektor = {
  $timestamp: capWaktu,
  ...vfsMalas,
  "nusa.vektor": [".py", kepalaVektor + "DATA = " + JSON.stringify(vektor) + LF, []],
};

const kepalaBerkasVektor = [
  "// Dihasilkan scripts/salin-py.mjs dari conformance/vectors/.",
  "// Dimuat saat diminta, bukan saat halaman dibuka. Lihat src/app.py.",
  "// .Deckyx",
  "",
].join(LF);

writeFileSync(
  join(VENDOR, "vektor_vfs.js"),
  kepalaBerkasVektor + "__BRYTHON__.update_VFS(" + JSON.stringify(vfsVektor) + ")" + LF,
);

const keluaran =
  "// Dihasilkan scripts/salin-py.mjs dari py/nusa/ dan src/app.py.\n" +
  "// Jangan disunting tangan: berkas ini ditimpa tiap kali build berjalan.\n" +
  "// .Deckyx\n" +
  `__BRYTHON__.update_VFS(${JSON.stringify({ $timestamp: capWaktu, ...vfs })})\n`;

writeFileSync(join(VENDOR, "nusa_vfs.js"), keluaran);

// ---------------------------------------------------------------------------
// Sisa susunan lama
// ---------------------------------------------------------------------------

// Bentuk sebelumnya menyalin .py mentah ke public/py/ dan menyerahkannya ke
// `pythonpath`. Berkas yang tertinggal di sana akan tetap ikut terbit tanpa
// satu pun halaman menunjuk ke sana — dan lebih buruk, akan tetap tampak
// benar saat dibuka satu per satu meski isinya sudah tertinggal jauh.
for (const usang of ["py", join("vendor", "brython_stdlib.js")]) {
  try {
    statSync(join(PUBLIK, usang));
    rmSync(join(PUBLIK, usang), { recursive: true, force: true });
    console.log(`Sisa susunan lama dihapus dari public/: ${usang}`);
  } catch {
    /* memang tidak ada; itu keadaan yang diharapkan */
  }
}

const kb = (n) => `${(n / 1024).toFixed(1)} KB`;
console.log(
  `Mesin Python dikemas: ${Object.keys(vfs).length} modul → ` +
    `vendor/nusa_vfs.js (${kb(keluaran.length)}); ` +
    `${Object.keys(vfsMalas).length} modul malas dan ` +
    `${Object.keys(vektor).length} berkas vektor → vendor/vektor_vfs.js.`,
);
