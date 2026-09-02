/**
 * Menyalakan penerjemah Python.
 *
 * Ini satu-satunya berkas TypeScript yang ikut terbit, dan sengaja dijaga
 * sependek mungkin. Seluruh isi situs — perhitungan maupun antarmukanya —
 * ditulis dalam Python di `src/app.py` dan `py/nusa/`.
 *
 * Seluruh modul Python sudah berada di dalam mesin virtual Brython sebelum
 * berkas ini jalan (lihat scripts/salin-py.mjs), jadi yang tersisa di sini
 * hanya menunggu runtime siap, meminta Brython mengimpor `app`, lalu
 * memastikan impornya benar-benar berhasil.
 *
 * .Deckyx
 */

interface BrythonGlobal {
  brython?: (opsi: { debug: number }) => void;
}

/** Berapa lama menunggu antarmuka muncul sebelum menyerah dan melapor. */
const BATAS_MS = 20000;

function beritahuGagal(pesan: string, rincian?: unknown): void {
  const wadah = document.getElementById("memuat");
  if (!wadah) return;
  wadah.replaceChildren();
  const p = document.createElement("p");
  p.className = "galat";
  p.textContent = pesan;
  wadah.append(p);
  if (rincian !== undefined) {
    const pre = document.createElement("pre");
    pre.className = "galat__rincian";
    pre.textContent = String(rincian);
    wadah.append(pre);
  }
  console.error("[neuronusa]", pesan, rincian);
}

/** Menunggu sebuah syarat terpenuhi, memeriksanya berkala. */
function tunggu(syarat: () => boolean, batasMs: number, gagalKarena: string): Promise<void> {
  if (syarat()) return Promise.resolve();
  return new Promise((selesai, tolak) => {
    const mulai = Date.now();
    const periksa = (): void => {
      if (syarat()) selesai();
      else if (Date.now() - mulai > batasMs) tolak(new Error(gagalKarena));
      else setTimeout(periksa, 25);
    };
    periksa();
  });
}

async function nyalakan(): Promise<void> {
  const global = window as unknown as BrythonGlobal;

  // Ketiga skrip runtime dimuat dengan `defer` dan berada sebelum modul ini
  // di dokumen, jadi urutannya sudah dijamin spesifikasi. Penantian ini untuk
  // keadaan yang tidak dijamin siapa pun: berkasnya gagal diambil, atau
  // dijalankan lewat perkakas yang menyusun ulang skrip.
  try {
    await tunggu(
      () => typeof global.brython === "function",
      BATAS_MS,
      "brython.min.js tidak pernah selesai dimuat",
    );
  } catch (galat) {
    beritahuGagal(
      "Runtime Python gagal dimuat, jadi tidak ada yang bisa dihitung. " +
        "Coba muat ulang halamannya.",
      galat,
    );
    return;
  }

  // Skrip Python dipasang dari sini, bukan ditulis di dalam HTML. Perkakas
  // build memeriksa setiap <script> di dalam HTML; yang berisi Python akan
  // membuatnya bingung, dan yang menunjuk berkas .py akan ditolaknya sebagai
  // modul JavaScript yang tidak sah.
  //
  // Isinya satu baris karena memang hanya perlu satu baris: modul `app` ada
  // di mesin virtual, dan mengimpornya menjalankan seluruh antarmuka.
  const skrip = document.createElement("script");
  skrip.type = "text/python";
  skrip.id = "neuronusa";
  skrip.textContent = "import app";
  document.body.append(skrip);

  // Wajib menyerahkan giliran di sini.
  //
  // Brython mengumpulkan skrip Python sekali saat runtime-nya dimuat, lalu
  // menemukan tambahan berikutnya lewat MutationObserver. Callback pengamat
  // itu berjalan setelah tugas sekarang selesai — jadi memanggil `brython()`
  // pada baris tepat setelah `append` akan menjalankan daftar yang masih
  // kosong. Tidak ada galat, tidak ada peringatan; halamannya hanya diam.
  await new Promise((lanjut) => setTimeout(lanjut, 0));

  try {
    global.brython?.({ debug: 1 });
  } catch (galat) {
    beritahuGagal("Kode Python gagal dijalankan.", galat);
    return;
  }

  // Brython melaporkan galat Python ke konsol lalu berjalan terus, jadi
  // panggilan di atas selesai dengan tenang meski `app` berhenti di tengah
  // jalan. Tanpa pemeriksaan ini, kegagalan itu terlihat sebagai halaman yang
  // memuat selamanya — gejala yang tidak memberi petunjuk apa pun.
  try {
    await tunggu(
      () => !document.getElementById("aplikasi")?.hasAttribute("hidden"),
      BATAS_MS,
      "#aplikasi tidak pernah ditampilkan",
    );
  } catch {
    beritahuGagal(
      "Python berjalan tetapi antarmukanya tidak selesai dibangun. " +
        "Jejak galatnya ada di konsol peramban.",
    );
  }
}

void nyalakan();
