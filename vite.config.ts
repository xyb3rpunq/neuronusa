import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, type Plugin } from "vite";

const AKAR = dirname(fileURLToPath(import.meta.url));

/**
 * Mengemas ulang mesin Python saat berkas .py-nya disunting.
 *
 * Tanpa ini, menyunting `py/nusa/jaringan.py` tidak mengubah apa pun di
 * peramban: yang dimuat halaman adalah `public/vendor/nusa_vfs.js`, dan
 * berkas itu hanya dihasilkan saat `npm run dev` dimulai. Gejalanya adalah
 * jenis yang paling membuang waktu — perubahan yang "tidak berpengaruh",
 * padahal yang salah bukan perubahannya melainkan yang sedang dijalankan.
 */
function kemasPython(): Plugin {
  const kemas = (): void => {
    try {
      execFileSync(process.execPath, [resolve(AKAR, "scripts", "salin-py.mjs")], {
        stdio: "pipe",
      });
    } catch (galat) {
      // Dilaporkan, bukan dilempar: pengemasan yang gagal tidak boleh
      // mematikan server pengembangan di tengah sesi.
      console.error("[neuronusa] gagal mengemas Python:", String(galat));
    }
  };

  return {
    name: "neuronusa-kemas-python",
    apply: "serve",
    configureServer(server) {
      server.watcher.add([resolve(AKAR, "py"), resolve(AKAR, "src", "app.py")]);
      server.watcher.on("change", (jalur) => {
        if (!jalur.endsWith(".py")) return;
        kemas();
        server.ws.send({ type: "full-reload" });
      });
    },
  };
}

/**
 * Konfigurasi build.
 *
 * Tidak ada plugin sama sekali. Situs ini tidak punya modul JavaScript untuk
 * dibundel: seluruh logikanya Python yang dijalankan Brython saat halaman
 * dibuka, dan Vite di sini hanya menyalin berkas serta menyegel HTML-nya.
 *
 * .Deckyx
 */
/**
 * Menempelkan sidik isi pada URL berkas di public/vendor/.
 *
 * # Masalah yang diselesaikannya
 *
 * GitHub Pages menyajikan berkas statis dengan `Cache-Control: max-age=600`.
 * Berkas di `public/` tidak diberi sidik oleh Vite — namanya tetap sama dari
 * satu penerbitan ke penerbitan berikutnya — sehingga selama sepuluh menit
 * setelah terbit, seorang pengunjung lama bisa mendapat `index.html` yang baru
 * berpasangan dengan `nusa_vfs.js` yang lama.
 *
 * Pasangan itu tidak rusak dengan berisik. Ia rusak persis seperti yang sudah
 * terlihat selama pengembangan: `KeyError: 'langkah'` — antarmuka Python lama
 * mencari elemen yang baru ada di HTML baru, atau sebaliknya. Halamannya
 * berhenti di layar "memuat", dan tidak ada di CI yang bisa menangkapnya
 * karena keduanya benar; yang salah hanyalah pasangannya.
 *
 * Sidiknya ditempel sebagai kueri, bukan dengan mengganti nama berkas. Nama
 * yang tetap membuat `public/` bisa disalin apa adanya, dan kueri sudah cukup:
 * peramban memperlakukan URL yang berbeda sebagai sumber daya yang berbeda.
 *
 * Hanya berjalan saat build. Saat pengembangan, Vite sendiri yang mengurus
 * penyegarannya.
 */
function sidikVendor(): Plugin {
  const sidik = (namaBerkas: string): string =>
    createHash("sha256")
      .update(readFileSync(resolve(AKAR, "public", "vendor", namaBerkas)))
      .digest("hex")
      .slice(0, 12);

  return {
    name: "neuronusa-sidik-vendor",
    apply: "build",
    // Dijalankan setelah Vite memasang base-nya, sehingga yang dicocokkan
    // adalah URL final dan bukan bentuk yang belum diterjemahkan.
    enforce: "post",
    transformIndexHtml(html) {
      // Dicocokkan hanya di dalam atribut, dan hanya pada nama berkas yang
      // benar-benar ada di public/vendor/. Pola yang lebih longgar akan ikut
      // menyentuh kata "vendor/" di dalam komentar HTML — dan sidik isi yang
      // menempel di komentar tidak merusak apa pun hari ini, tetapi tidak ada
      // alasan untuk menaruhnya di sana.
      return html.replace(
        /((?:src|content)=")([^"]*?)(vendor\/)([A-Za-z0-9_.-]+\.js)(")/g,
        (cocok, atribut, awalan, dir, berkas, tutup) => {
          try {
            return `${atribut}${awalan}${dir}${berkas}?v=${sidik(berkas)}${tutup}`;
          } catch {
            // Berkas yang tidak ada di public/vendor/ dibiarkan apa adanya;
            // build tidak boleh gagal karena sebuah pengoptimalan singgahan.
            return cocok;
          }
        },
      );
    },
  };
}

export default defineConfig({
  base: "/neuronusa/",
  plugins: [kemasPython(), sidikVendor()],

  // Wajib "mpa". Dengan setelan bawaan "spa", server pengembangan menjawab
  // *setiap* jalur yang tidak dikenal dengan index.html dan kode status 200.
  // Brython mencari paket dengan menjajal `nusa.py` lebih dulu, baru
  // `nusa/__init__.py`; jajakan pertama itu akan dijawab halaman HTML
  // berstatus 200, dan Brython menguraikannya sebagai Python.
  //
  // Gejalanya: `SyntaxError: invalid syntax` pada baris `<!doctype html>` —
  // dan hanya di pengembangan, karena GitHub Pages menjawab 404 dengan benar.
  // Perbedaan diam-diam antara pengembangan dan produksi persis jenis cacat
  // yang paling mahal ditemukan.
  appType: "mpa",

  server: { port: 5176, strictPort: true },
  build: { target: "es2022" },
});
