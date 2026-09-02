import { execFileSync } from "node:child_process";
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
export default defineConfig({
  base: "/neuronusa/",
  plugins: [kemasPython()],

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
