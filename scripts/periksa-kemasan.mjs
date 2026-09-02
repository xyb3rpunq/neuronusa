/**
 * Memeriksa bahwa mesin Python yang terbit benar-benar sama dengan sumbernya.
 *
 * # Kenapa ini ada
 *
 * Karena yang dijalankan peramban bukan berkas di `py/nusa/`, melainkan
 * salinannya di dalam `dist/vendor/nusa_vfs.js` — dan tidak ada satu pun uji
 * di proyek ini yang menyentuh berkas itu. Uji Python membaca `py/nusa/`,
 * konformansi membaca `conformance/vectors/`, anggaran ukuran hanya menimbang
 * bita.
 *
 * Kemasan yang rusak karena itu bisa lolos seluruh gerbang: ia tetap sah
 * sebagai JavaScript, tetap berukuran wajar, dan tetap memuat nama modul yang
 * benar. Yang gagal hanyalah halamannya, di peramban pengunjung, setelah
 * terbit.
 *
 * Yang diperiksa di sini:
 *
 *   1. Kedua berkas kemasan bisa dijalankan dan memanggil `update_VFS`.
 *   2. Setiap modul yang diharapkan ada, dengan penanda paket yang benar.
 *   3. Sumber tiap modul **sama persis**, bita demi bita, dengan berkas di
 *      `py/nusa/` dan `src/app.py`.
 *   4. Kesembilan berkas vektor ada, dan isinya sama dengan yang di cakram
 *      setelah akhir barisnya dinormalkan.
 *   5. Modul vektornya bisa diurai sebagai Python — diuji dengan menjalankan
 *      CPython, bukan dengan menebak.
 *
 * .Deckyx
 */

import { execFileSync } from "node:child_process";
import { readFileSync, readdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const AKAR = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const DIST = join(AKAR, "dist");
const CR = String.fromCharCode(13);

const galat = [];
const catat = (pesan) => galat.push(pesan);

/** Menjalankan sebuah berkas kemasan dan mengembalikan VFS yang dititipkannya. */
function muatKemasan(berkas) {
  const vfs = {};
  const sumber = readFileSync(join(DIST, "vendor", berkas), "utf8");
  const __BRYTHON__ = {
    update_VFS(kumpulan) {
      Object.assign(vfs, kumpulan);
    },
  };
  // Dijalankan, bukan dicocokkan dengan pola. Berkas yang sintaksnya rusak
  // harus gagal di sini dengan pesan dari mesin JavaScript itu sendiri.
  new Function("__BRYTHON__", sumber)(__BRYTHON__);
  return vfs;
}

let vfs;
let vfsVektor;
try {
  vfs = muatKemasan("nusa_vfs.js");
  vfsVektor = muatKemasan("vektor_vfs.js");
} catch (e) {
  console.error(`Kemasan tidak bisa dijalankan: ${e}`);
  process.exit(1);
}

// --- 1. modul yang diharapkan ----------------------------------------------

const diharapkan = new Map([["app", join(AKAR, "src", "app.py")]]);
const dirNusa = join(AKAR, "py", "nusa");
for (const berkas of readdirSync(dirNusa).filter((f) => f.endsWith(".py"))) {
  const nama =
    berkas === "__init__.py" ? "nusa" : `nusa.${basename(berkas, ".py")}`;
  diharapkan.set(nama, join(dirNusa, berkas));
}

for (const [nama, jalur] of diharapkan) {
  const entri = vfs[nama];
  if (!entri) {
    catat(`Modul '${nama}' tidak ada di dalam kemasan.`);
    continue;
  }
  if (entri[0] !== ".py") catat(`Modul '${nama}' bukan bertipe .py.`);

  const adalahPaket = entri.length > 3 && entri[3] === 1;
  if (nama === "nusa" && !adalahPaket) {
    catat("Modul 'nusa' tidak ditandai sebagai paket; submodulnya tidak akan ketemu.");
  }
  if (nama !== "nusa" && adalahPaket) {
    catat(`Modul '${nama}' salah ditandai sebagai paket.`);
  }

  const asli = readFileSync(jalur, "utf8");
  if (entri[1] !== asli) {
    catat(
      `Sumber '${nama}' di dalam kemasan berbeda dari ${jalur}. ` +
        `Jalankan 'npm run build' lalu ulangi.`,
    );
  }
}

for (const nama of Object.keys(vfs)) {
  if (nama.startsWith("$")) continue;
  if (!diharapkan.has(nama)) catat(`Modul tak dikenal ikut terkemas: '${nama}'.`);
}

// --- 2. vektor --------------------------------------------------------------

const entriVektor = vfsVektor["nusa.vektor"];
if (!entriVektor) {
  catat("Modul 'nusa.vektor' tidak ada di dalam vektor_vfs.js.");
} else {
  const dirVektor = join(AKAR, "conformance", "vectors");
  const berkasVektor = readdirSync(dirVektor).filter((f) => f.endsWith(".tsv")).sort();
  if (berkasVektor.length !== 9) {
    catat(`Diharapkan 9 berkas vektor di cakram, ditemukan ${berkasVektor.length}.`);
  }
  for (const berkas of berkasVektor) {
    const asli = readFileSync(join(dirVektor, berkas), "utf8").split(CR).join("");
    // Isinya berada di dalam literal Python, jadi yang bisa diperiksa dari
    // JavaScript adalah bahwa bentuk JSON-nya muncul apa adanya. Keduanya
    // memakai escape yang sama untuk isi seperti ini — dan pemeriksaan
    // langkah 3 di bawah yang membuktikan hasilnya memang terurai.
    if (!entriVektor[1].includes(JSON.stringify(asli))) {
      catat(`Vektor '${berkas}' di dalam kemasan berbeda dari yang di cakram.`);
    }
  }
}

// --- 3. modul vektor harus sah sebagai Python -------------------------------

if (entriVektor) {
  const sementara = join(tmpdir(), `neuronusa-vektor-${process.pid}.py`);
  writeFileSync(sementara, entriVektor[1]);
  try {
    const keluaran = execFileSync(
      process.platform === "win32" ? "python" : "python3",
      [
        "-c",
        [
          "import ast, sys, io",
          "sumber = io.open(sys.argv[1], encoding='utf-8').read()",
          "pohon = ast.parse(sumber)",
          "ruang = {}",
          "exec(compile(pohon, 'vektor', 'exec'), ruang)",
          "data = ruang['DATA']",
          "print(len(data), sum(len(v) for v in data.values()))",
        ].join("\n"),
        sementara,
      ],
      { encoding: "utf8" },
    ).trim();
    const [jumlah, bita] = keluaran.split(/\s+/).map(Number);
    if (jumlah !== 9) catat(`Modul vektor memuat ${jumlah} berkas, bukan 9.`);
    if (!(bita > 100000)) catat(`Modul vektor hanya memuat ${bita} karakter; terlalu sedikit.`);
    console.log(`Modul vektor terurai: ${jumlah} berkas, ${bita} karakter.`);
  } catch (e) {
    catat(`Modul vektor tidak bisa diurai sebagai Python: ${e}`);
  }
}

// --- 4. rujukan di dalam HTML -----------------------------------------------

// Sidik isi pada URL vendor mencegah `index.html` yang baru berpasangan dengan
// mesin Python yang lama dari singgahan peramban. Kegagalannya senyap dan
// menyesatkan: antarmuka mencari elemen yang tidak ada di HTML pasangannya,
// dan halamannya berhenti di layar "memuat".
//
// Diperiksa di sini karena tidak ada uji lain yang menyentuh HTML terbitan.
{
  const berkasHtml = readFileSync(join(DIST, "index.html"), "utf8");

  const rujukanSkrip = [...berkasHtml.matchAll(/src="([^"]*vendor\/[^"]+)"/g)].map(
    (m) => m[1],
  );
  if (rujukanSkrip.length !== 3) {
    catat(`Diharapkan 3 skrip vendor di index.html, ditemukan ${rujukanSkrip.length}.`);
  }
  for (const url of rujukanSkrip) {
    if (!/\?v=[0-9a-f]{12}$/.test(url)) {
      catat(`Skrip vendor tanpa sidik isi: ${url}`);
    }
    if (!url.startsWith("/neuronusa/")) {
      catat(`Skrip vendor tidak memakai base situs: ${url}`);
    }
  }

  const meta = berkasHtml.match(/name="neuronusa-vektor"\s+content="([^"]+)"/);
  if (!meta) {
    catat("Meta 'neuronusa-vektor' tidak ada di index.html.");
  } else {
    const rujukan = meta[1];
    if (rujukan.startsWith("/")) {
      // Alamat yang diawali garis miring diselesaikan terhadap asal situs dan
      // bukan terhadap base-nya, sehingga di GitHub Pages ia menunjuk ke luar
      // /neuronusa/ dan menemui 404. Cacat ini sudah pernah terjadi.
      catat(`Alamat vektor harus relatif, bukan diawali garis miring: ${rujukan}`);
    }
    if (!/\?v=[0-9a-f]{12}$/.test(rujukan)) {
      catat(`Alamat vektor tanpa sidik isi: ${rujukan}`);
    }
  }
}

// --- hasil ------------------------------------------------------------------

if (galat.length) {
  console.error(`\n${galat.length} masalah pada kemasan:`);
  for (const g of galat) console.error(`  - ${g}`);
  process.exit(1);
}

console.log(
  `Kemasan sepadan dengan sumbernya: ${diharapkan.size} modul Python ` +
    `dan 9 berkas vektor.`,
);
