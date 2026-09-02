"""Dwibahasa Indonesia dan Inggris.

# Kenapa ini modul mesin, bukan bagian dari antarmuka

Karena kamusnya bisa diuji, dan memang perlu diuji. Terjemahan yang hilang
tidak pernah menabrak: ia muncul sebagai teks kosong di tempat yang seharusnya
berisi satu paragraf — dan yang hilang hampir selalu bahasa yang tidak dipakai
penulisnya sehari-hari, sehingga penulisnya sendiri tidak akan pernah
melihatnya.

Uji di ``py/uji/test_nusa.py`` memeriksa tiga hal yang tidak bisa dilihat
dengan membaca: setiap kunci punya kedua bahasa, keduanya benar-benar berbeda
(bukan salinan), dan jumlah penanda format seperti ``%s`` sama di keduanya.
Yang terakhir itu penting — sebuah terjemahan yang kehilangan satu ``%d``
melempar ``TypeError`` di tengah penggambaran, dan hanya pada bahasa yang
tidak diuji siapa pun.

# Kenapa pasangan, bukan dua berkas terpisah

Karena kedua bahasa ditulis di baris yang sama, sehingga tidak mungkin
menyunting salah satunya tanpa melihat yang lain. Dua berkas terpisah selalu
berakhir sama: yang satu diperbaiki, yang lain tidak.

.Deckyx
"""

#: Kode bahasa yang didukung, berikut namanya sendiri.
#:
#: Nama bahasa ditulis dalam bahasa itu sendiri — "English", bukan "Inggris".
#: Pemilih bahasa dibaca justru oleh orang yang belum tentu paham bahasa yang
#: sedang aktif, dan menuliskannya dalam bahasa aktif membuat pemilihnya tidak
#: bisa dipakai oleh satu-satunya orang yang membutuhkannya.
BAHASA = [("id", "Indonesia"), ("en", "English")]

_BAWAAN = "id"
_sekarang = _BAWAAN


def kode_sah(kode):
    """Apakah sebuah kode bahasa dikenali."""
    return kode in [k for k, _nama in BAHASA]


def atur(kode):
    """Mengganti bahasa aktif. Kode yang tidak dikenal diabaikan."""
    global _sekarang
    if kode_sah(kode):
        _sekarang = kode


def sekarang():
    """Kode bahasa yang sedang aktif."""
    return _sekarang


def t(kunci):
    """Teks untuk sebuah kunci, dalam bahasa yang sedang aktif.

    Melempar ``KeyError`` untuk kunci yang tidak ada, dan itu disengaja: kunci
    yang salah ketik harus berhenti dengan berisik saat pertama kali dilalui,
    bukan menghasilkan teks kosong yang lolos ke halaman terbit.
    """
    pasangan = TEKS[kunci]
    return pasangan[0] if _sekarang == "id" else pasangan[1]


#: Seluruh teks antarmuka, sebagai pasangan ``(Indonesia, English)``.
TEKS = {
    # -- kerangka -----------------------------------------------------------
    "bahasa": ("Bahasa", "Language"),
    # Judul tab peramban. Ia tidak terlihat di halaman, jadi ia satu-satunya
    # teks yang bisa tertinggal berbulan-bulan tanpa ada yang menyadarinya —
    # padahal ia yang menjadi nama penanda buku dan judul jendela, dan yang
    # dibacakan pembaca layar saat tabnya berpindah.
    "judul_tab": (
        "neuronusa — jaringan syaraf dengan gradien yang bisa dibuktikan",
        "neuronusa — a neural network with provable gradients",
    ),
    "tema": ("Tema", "Theme"),
    "tema_sistem": ("Ikut sistem", "Match system"),
    "tema_terang": ("Terang", "Light"),
    "tema_gelap": ("Gelap", "Dark"),

    # -- kartu masalah ------------------------------------------------------
    "kartu_masalah": ("Masalah", "The problem"),
    "kumpulan_data": ("Kumpulan data", "Dataset"),
    "data_sendiri": ("Data sendiri", "Your own data"),
    "catatan_masalah": (
        "XOR dan cincin tidak terpisahkan garis lurus mana pun. Setel neuron "
        "tersembunyi ke nol pada keduanya, dan perhatikan jaringannya berhenti "
        "di sekitar setengah — itulah temuan Minsky dan Papert yang "
        "menghentikan penelitian bidang ini hampir dua dekade.",
        "Neither XOR nor the ring can be separated by any straight line. Set "
        "the hidden neurons to zero on either one and watch the network stall "
        "around one half — that is the Minsky and Papert result which halted "
        "research in this field for nearly two decades.",
    ),

    # -- bentuk jaringan ----------------------------------------------------
    "kartu_bentuk": ("Bentuk jaringan", "Network shape"),
    "neuron_tersembunyi": ("Neuron tersembunyi", "Hidden neurons"),
    "bantuan_tersembunyi": (
        "Nol berarti perceptron satu lapis, tanpa lapis tersembunyi sama sekali.",
        "Zero means a single-layer perceptron, with no hidden layer at all.",
    ),
    "aktivasi_tersembunyi": ("Aktivasi lapis tersembunyi", "Hidden-layer activation"),
    "benih_awal": ("Benih bobot awal", "Initial-weight seed"),
    "bantuan_benih": (
        "Benih yang sama menghasilkan bobot awal yang sama persis, sehingga "
        "hasil pelatihannya bisa diulang dan dibandingkan.",
        "The same seed yields bit-identical initial weights, so a training run "
        "can be repeated and compared.",
    ),

    # -- sabotase -----------------------------------------------------------
    "kartu_sabotase": ("Sabotase", "Sabotage"),
    "ajakan_sabotase": (
        "Halaman ini menyatakan bahwa jaringan yang gradiennya salah tetap "
        "sering terlihat belajar. Jangan percayai itu — nyalakan salah satu "
        "cacat di bawah, latih, lalu perhatikan kurva galatnya.",
        "This page claims that a network with wrong gradients still often "
        "appears to learn. Do not take that on trust — switch on one of the "
        "defects below, train, and watch the error curve.",
    ),
    "cacat_perambatan": ("Cacat perambatan balik", "Backpropagation defect"),

    # -- label laporan yang diunduh -----------------------------------------
    #
    # Dipakai ``py/nusa/ekspor.py``, bukan ``app.py``. Sebelumnya seluruh
    # laporan CSV ditulis dalam bahasa Indonesia saja, sehingga pengunjung
    # yang membaca situs ini dalam bahasa Inggris mengunduh berkas yang tidak
    # bisa ia baca — dan tidak akan melaporkannya, karena ia hanya akan
    # menyimpulkan berkasnya memang begitu.
    "eks_judul": (
        "neuronusa \u2014 laporan pelatihan",
        "neuronusa \u2014 training report",
    ),
    "eks_dihasilkan": ("dihasilkan", "generated by"),
    "eks_sumber": ("halaman neuronusa (.Deckyx)", "the neuronusa page (.Deckyx)"),
    "eks_bahasa_berkas": ("bahasa laporan", "report language"),
    "eks_setelan": ("SETELAN", "SETTINGS"),
    "eks_kumpulan_data": ("kumpulan data", "dataset"),
    "eks_tersembunyi": ("neuron tersembunyi", "hidden neurons"),
    "eks_aktivasi": ("aktivasi", "activation"),
    "eks_benih": ("benih bobot awal", "initial weight seed"),
    "eks_laju": ("laju belajar", "learning rate"),
    "eks_momentum_baris": ("momentum", "momentum"),
    "eks_laju_efektif": ("laju efektif", "effective rate"),
    "eks_cacat": ("cacat perambatan balik", "backpropagation defect"),
    "eks_epoch": ("epoch dijalankan", "epochs run"),
    "eks_parameter": ("jumlah parameter", "parameter count"),
    "eks_hasil": ("HASIL", "RESULTS"),
    "eks_galat_rata": ("galat kuadrat rata-rata", "mean squared error"),
    "eks_titik_benar": ("titik benar", "points correct"),
    "eks_titik_semua": ("titik seluruhnya", "points in total"),
    "eks_galat_pembanding": (
        "galat pembanding tanpa cacat",
        "reference error without the defect",
    ),
    "eks_ramalan": ("RAMALAN TIAP TITIK", "PREDICTION FOR EACH POINT"),
    "eks_kol_sasaran": ("sasaran", "target"),
    "eks_kol_keluaran": ("keluaran", "output"),
    "eks_kol_selisih": ("selisih", "difference"),
    "eks_kol_benar": ("benar", "correct"),
    "eks_bobot": ("BOBOT DAN BIAS", "WEIGHTS AND BIASES"),
    "eks_kol_parameter": ("parameter", "parameter"),
    "eks_kol_lapis": ("lapis", "layer"),
    "eks_kol_ke": ("ke", "to"),
    "eks_kol_dari": ("dari", "from"),
    "eks_kol_nilai": ("nilai", "value"),
    "eks_bobot_nama": ("bobot", "weight"),
    "eks_bias_nama": ("bias", "bias"),
    "eks_kurva": ("KURVA GALAT", "ERROR CURVE"),
    "eks_kol_riwayat": ("titik riwayat", "history point"),
    "eks_kol_galat": ("galat", "error"),
    "eks_gradien": ("PEMERIKSAAN GRADIEN", "GRADIENT CHECK"),
    "eks_hasil_periksa": ("hasil", "outcome"),
    "eks_lolos": ("LOLOS", "PASS"),
    "eks_gagal": ("GAGAL", "FAIL"),
    "eks_terburuk": ("galat relatif terburuk", "worst relative error"),
    "eks_ambang": ("ambang", "threshold"),
    "eks_kol_analitik": ("perambatan balik", "backpropagation"),
    "eks_kol_numerik": ("selisih hingga", "finite difference"),
    "eks_kol_relatif": ("galat relatif", "relative error"),
    "eks_catatan": ("CATATAN", "NOTES"),
    "eks_catatan_desimal": (
        "Angka memakai titik sebagai pemisah desimal. Excel berwilayah "
        "Indonesia mungkin membacanya sebagai teks; ubah kolomnya menjadi "
        "angka lewat Data > Text to Columns bila perlu.",
        "Numbers use a full stop as the decimal separator. Excel in some "
        "locales may read them as text; convert the column to numbers via "
        "Data > Text to Columns if needed.",
    ),
    "eks_catatan_skala": (
        "Nilai x1 dan x2 sudah dalam skala 0 sampai 1. Untuk data tempelan, "
        "rentang aslinya tercantum di halaman.",
        "The x1 and x2 values are already scaled to the range 0 to 1. For "
        "pasted data, the original ranges are shown on the page.",
    ),
    "eks_catatan_mesin": (
        "Seluruh perhitungan dijalankan Python di dalam peramban Anda lewat "
        "Brython; tidak ada satu bita pun yang dikirim ke mana pun.",
        "Every calculation runs as Python inside your own browser via "
        "Brython; not one byte is sent anywhere.",
    ),

    # -- nama kumpulan data -------------------------------------------------
    #
    # Ada di sini dan bukan di ``jaringan.py`` karena nama yang dilihat
    # pengguna adalah terjemahan, dan modul mesin tidak punya urusan memegang
    # terjemahan. Sebelumnya nama-nama ini tinggal di tabel ``DATASET`` dan
    # ``CACAT``, sehingga pemilih kumpulan data dan seluruh kartu sabotase
    # tetap berbahasa Indonesia meski situsnya disetel ke Inggris — satu-satunya
    # bagian halaman yang tidak ikut berganti, dan justru bagian dengan prosa
    # terpanjang.
    "data_nama_xor": ("XOR", "XOR"),
    "data_nama_and": ("AND", "AND"),
    "data_nama_lingkaran": ("Cincin", "Ring"),

    # -- nama cacat ---------------------------------------------------------
    "cacat_nama_tidak_ada": ("Tidak ada", "None"),
    "cacat_nama_tanda_terbalik": ("Satu tanda terbalik", "One flipped sign"),
    "cacat_nama_turunan_hilang": (
        "Turunan aktivasi tidak dikalikan",
        "Activation derivative not multiplied",
    ),
    "cacat_nama_faktor_dua": ("Faktor dua tertinggal", "A factor of two left behind"),
    "cacat_nama_bias_beku": ("Bias tidak pernah diperbarui", "Bias never updated"),

    # -- penjelasan tiap cacat ----------------------------------------------
    "cacat_jelas_tidak_ada": (
        "Perambatan balik yang benar — dasar pembanding untuk keempat cacat "
        "di bawah. Perhatikan galat akhirnya, lalu bandingkan dengan galat "
        "akhir tiap cacat.",
        "Correct backpropagation — the baseline for the four defects below. "
        "Note its final error, then compare it against the final error of "
        "each defect.",
    ),
    "cacat_jelas_tanda_terbalik": (
        "Satu bobot gradiennya dibalik tandanya — salah ketik indeks, atau "
        "kurang tanda minus di satu tempat. Bobot itu didorong ke arah yang "
        "justru memperburuk, sementara enam belas lainnya benar. Pelatihan "
        "tetap berjalan; ia hanya berhenti di tempat yang keliru.",
        "One weight has its gradient sign flipped — a mistyped index, or a "
        "missing minus sign in one place. That weight is pushed in the "
        "direction that makes things worse while the other sixteen are "
        "correct. Training still runs; it simply settles somewhere wrong.",
    ),
    "cacat_jelas_turunan_hilang": (
        "Delta lapis tersembunyi diteruskan tanpa dikalikan turunan "
        "aktivasinya. Ini cacat perambatan balik yang paling sering ditulis "
        "orang: aturan rantai kehilangan satu mata rantai. Gradiennya jadi "
        "salah arah maupun salah besaran, tetapi tetap menunjuk ke arah yang "
        "kira-kira benar cukup sering untuk membuat galatnya menurun.",
        "The hidden-layer delta is passed on without being multiplied by the "
        "activation derivative. This is the backpropagation defect people "
        "write most often: the chain rule loses one link. The gradient ends "
        "up wrong in both direction and magnitude, yet still points roughly "
        "the right way often enough to keep the error falling.",
    ),
    "cacat_jelas_faktor_dua": (
        "Galat kuadrat di sini dibagi dua supaya turunannya menjadi (y − t) "
        "tanpa faktor dua yang menempel di mana-mana. Cacat ini melupakan "
        "pembagian itu, sehingga seluruh gradien menjadi dua kali lipat. "
        "Pelatihan tetap benar arahnya dan hanya melangkah dua kali lebih "
        "jauh — nyaris mustahil dilihat dari kurva galat, dan langsung "
        "terlihat oleh pemeriksa gradien sebagai galat relatif 1,0.",
        "The squared error here is halved so that its derivative is (y − t) "
        "with no factor of two clinging to everything. This defect forgets "
        "that halving, so every gradient is doubled. Training still heads the "
        "right way and merely steps twice as far — all but invisible in the "
        "error curve, and immediately visible to the gradient check as a "
        "relative error of 1.0.",
    ),
    "cacat_jelas_bias_beku": (
        "Gradiennya dihitung benar, tetapi biasnya tidak pernah digeser. "
        "Perhatikan baik-baik: pemeriksa gradien **tidak** menangkap yang ini, "
        "dan memang tidak bisa. Ia memeriksa apakah turunannya benar, bukan "
        "apakah turunannya dipakai. Setiap alat punya batas, dan alat yang "
        "batasnya tidak diketahui lebih berbahaya daripada tidak punya alat.",
        "The gradients are computed correctly, but the biases are never "
        "moved. Watch closely: the gradient check does **not** catch this "
        "one, and cannot. It checks whether the derivatives are right, not "
        "whether they are used. Every tool has a limit, and a tool whose "
        "limit is unknown is more dangerous than no tool at all.",
    ),
    "pemeriksa_menangkap": ("Pemeriksa gradien %s cacat ini.", "The gradient check %s this defect."),
    "menangkap": ("MENANGKAP", "CATCHES"),
    "tidak_menangkap": ("TIDAK BISA menangkap", "CANNOT catch"),
    "catatan_pembanding": (
        "Sebuah jaringan pembanding dengan bobot awal yang sama persis dan "
        "perambatan balik yang benar ikut dilatih berdampingan. Ia muncul "
        "sebagai garis putus-putus di kurva galat.",
        "A reference network with bit-identical initial weights and correct "
        "backpropagation trains alongside it. It appears as the dashed line on "
        "the error curve.",
    ),

    # -- pelatihan ----------------------------------------------------------
    "kartu_pelatihan": ("Pelatihan", "Training"),
    "laju_belajar": ("Laju belajar", "Learning rate"),
    "momentum": ("Momentum", "Momentum"),
    "bantuan_momentum": (
        "Momentum menjumlahkan langkah sebelumnya, sehingga langkah tunaknya "
        "laju ÷ (1 − momentum).",
        "Momentum accumulates the previous step, so the steady-state step is "
        "rate ÷ (1 − momentum).",
    ),
    "laju_efektif": (
        "Laju efektif %s = %s ÷ (1 − %s).",
        "Effective rate %s = %s ÷ (1 − %s).",
    ),
    "peringatan_laju": (
        " Sebesar ini pelatihan biasanya tidak meledak melainkan macet: "
        "keluarannya jenuh di 0 atau 1, turunan sigmoidnya nyaris nol, dan "
        "galatnya berhenti di satu angka sambil jaringan menjawab sama untuk "
        "setiap masukan. Jalankan dan perhatikan — kurvanya mendatar, bukan "
        "meroket.",
        " At this magnitude training usually does not explode but stalls: the "
        "outputs saturate at 0 or 1, the sigmoid derivative goes nearly to "
        "zero, and the error settles on one number while the network answers "
        "the same for every input. Run it and watch — the curve flattens, it "
        "does not shoot up.",
    ),
    "latih": ("Latih", "Train"),
    "berhenti": ("Berhenti", "Stop"),
    "satu_epoch": ("Satu epoch", "One epoch"),
    "ulang_awal": ("Ulang dari awal", "Reset"),
    "pelatihan_takhingga": (
        "Pelatihan menghasilkan nilai yang tidak berhingga pada epoch %d dan "
        "dihentikan. Ini tidak diharapkan terjadi pada arsitektur ini — "
        "kalau Anda melihatnya, setelan yang Anda pakai menemukan sesuatu "
        "yang belum pernah terukur. Ulang dari awal untuk melanjutkan.",
        "Training produced a non-finite value at epoch %d and was stopped. "
        "This is not expected on this architecture — if you are seeing it, "
        "your settings have found something never previously measured. Reset "
        "to continue.",
    ),

    # -- data sendiri -------------------------------------------------------
    "petunjuk_data": (
        "Tempelkan tiga kolom: dua angka masukan dan satu kelas (0 atau 1). "
        "Pemisahnya boleh koma, titik koma, tab, atau spasi — dan koma "
        "desimal gaya Indonesia diterima. Angkanya akan diskalakan ke rentang "
        "0 sampai 1, dan rentang aslinya diberitahukan.",
        "Paste three columns: two input numbers and one class (0 or 1). The "
        "separator may be a comma, semicolon, tab, or space — and Indonesian "
        "decimal commas are accepted. The numbers are scaled to the range 0 to "
        "1, and the original range is reported back to you.",
    ),
    "label_tempel": ("Tempelkan data Anda di sini", "Paste your data here"),
    "pakai_data": ("Pakai data ini", "Use this data"),
    "isi_contoh": ("Isi contoh", "Fill in an example"),
    "contoh_terisi": (
        "Contoh diisi — tekan “Pakai data ini”.",
        "Example filled in — press “Use this data”.",
    ),
    "baris_dipakai": ("%d baris dipakai.", "%d rows in use."),

    # -- berbagi dan ekspor -------------------------------------------------
    "kartu_berbagi": ("Bagikan dan tampilan", "Share and appearance"),
    "catatan_tautan": (
        "Alamat di bilah alamat selalu mencerminkan setelan sekarang. Siapa "
        "pun yang membukanya akan mendapat jaringan yang sama persis — benih "
        "yang sama berarti bobot awal yang sama, dan pelatihan yang sama bisa "
        "diulang. Itu bukan kenyamanan tambahan melainkan syarat: hasil yang "
        "tidak bisa diulang tidak bisa diperiksa siapa pun.",
        "The address bar always reflects the current settings. Anyone who "
        "opens it gets a bit-identical network — the same seed means the same "
        "initial weights, and the same training run can be repeated. That is "
        "not a convenience but a requirement: a result nobody can reproduce is "
        "a result nobody can check.",
    ),
    "salin_tautan": ("Salin tautan setelan ini", "Copy a link to these settings"),
    "tautan_disalin": ("Tautan disalin.", "Link copied."),
    "papan_klip_ditolak": (
        "Peramban menolak akses papan klip — salin saja alamat di bilah "
        "alamat, isinya sudah tepat.",
        "The browser refused clipboard access — just copy the address bar, its "
        "contents are already correct.",
    ),
    "catatan_ekspor": (
        "Unduh seluruh hasilnya — setelan, ramalan tiap titik, bobot, kurva "
        "galat, dan pemeriksaan gradien kalau sudah dijalankan — sebagai satu "
        "berkas yang bisa dibuka Excel, atau cetak halamannya menjadi PDF.",
        "Download the whole result — settings, per-point predictions, weights, "
        "error curve, and the gradient check if you have run it — as one file "
        "Excel can open, or print the page to PDF.",
    ),
    "unduh_csv": ("Unduh CSV (Excel)", "Download CSV (Excel)"),
    "cetak_pdf": ("Cetak / simpan PDF", "Print / save as PDF"),
    "diunduh": ("Diunduh: %s", "Downloaded: %s"),
    "unduhan_ditolak": ("Peramban menolak unduhan: %s", "The browser refused the download: %s"),

    # -- ringkasan hasil ----------------------------------------------------
    "galat_kuadrat": ("Galat kuadrat rata-rata", "Mean squared error"),
    "ringkas_hasil": (
        "%d dari %d titik diramalkan benar setelah %d epoch — %d parameter dilatih.",
        "%d of %d points predicted correctly after %d epochs — %d parameters trained.",
    ),

    # -- kurva galat --------------------------------------------------------
    "kartu_kurva": ("Kurva galat", "Error curve"),
    "judul_kurva": ("Galat tiap epoch", "Error per epoch"),
    "belum_dilatih": ("Belum ada langkah pelatihan.", "No training steps yet."),
    "menurun": ("menurun", "fell"),
    "tidak_menurun": ("TIDAK menurun", "did NOT fall"),
    "terang_kurva": (
        "Galat %s dari %s menjadi %s setelah %d epoch. Sumbu tegaknya berskala "
        "dari nilai terkecil sampai terbesar yang pernah dicapai, jadi kurva "
        "yang terlihat curam belum tentu turun banyak — perhatikan angka di "
        "sumbunya, bukan kemiringannya.",
        "The error %s from %s to %s after %d epochs. The vertical axis is "
        "scaled between the smallest and largest values ever reached, so a "
        "steep-looking curve has not necessarily fallen far — read the numbers "
        "on the axis, not the slope.",
    ),
    "terang_pembanding": (
        " Garis putus-putus adalah jaringan pembanding dengan bobot awal yang "
        "sama persis dan perambatan balik yang benar. Perhatikan berapa banyak "
        "— atau berapa sedikit — keduanya berbeda: %s berbanding %s.",
        " The dashed line is a reference network with bit-identical initial "
        "weights and correct backpropagation. Note how much — or how little — "
        "the two differ: %s against %s.",
    ),
    "kunci_disabotase": ("jaringan yang disabotase", "the sabotaged network"),
    "kunci_pembanding": ("pembanding yang benar (putus-putus)", "correct reference (dashed)"),

    # -- batas keputusan ----------------------------------------------------
    "kartu_batas": ("Batas keputusan", "Decision boundary"),
    "judul_batas": ("Tebakan jaringan di seluruh bidang", "The network's guess across the plane"),
    "kelas_0": ("kelas 0", "class 0"),
    "kelas_1": ("kelas 1", "class 1"),
    "terang_batas": (
        "Warna latar adalah tebakan jaringan di setiap titik bidang; makin "
        "pekat makin yakin. Lingkaran adalah data latihnya. Saat ini %d dari "
        "%d titik diramalkan benar. Perhatikan bentuk batasnya: perceptron "
        "tanpa lapis tersembunyi hanya bisa menarik garis lurus, dan itulah "
        "sebabnya XOR mustahil baginya.",
        "The background colour is the network's guess at every point of the "
        "plane; the denser it is, the more confident. The circles are the "
        "training data. Right now %d of %d points are predicted correctly. "
        "Note the shape of the boundary: a perceptron with no hidden layer can "
        "only draw a straight line, which is why XOR is impossible for it.",
    ),

    # -- peta bobot ---------------------------------------------------------
    "kartu_bobot": ("Bobot yang dipelajari", "Learned weights"),
    "judul_bobot": ("Peta bobot jaringan", "Network weight map"),
    "bobot_positif": ("bobot positif", "positive weight"),
    "bobot_negatif": ("bobot negatif", "negative weight"),
    "terang_bobot": (
        "Tebal garis menyatakan besar bobotnya, warnanya menyatakan tandanya. "
        "Bobot negatif dan positif berperan berlawanan, jadi menyamakan "
        "warnanya akan menyembunyikan struktur yang justru sedang dipelajari "
        "jaringan. Nilai tepatnya ada di tabel di bawah — bukan sebagai "
        "gelembung yang muncul saat disentuh tetikus, karena gelembung itu "
        "tidak pernah muncul di layar sentuh dan tidak pernah terbaca pembaca "
        "layar.",
        "Line thickness shows the weight's magnitude, its colour shows the "
        "sign. Negative and positive weights play opposite roles, so giving "
        "them one colour would hide the very structure the network is "
        "learning. Exact values are in the table below — not in a tooltip, "
        "because tooltips never appear on touchscreens and are never read out "
        "by screen readers.",
    ),
    "kolom_parameter": ("parameter", "parameter"),
    "kolom_nilai": ("nilai", "value"),

    # -- tabel ramalan ------------------------------------------------------
    "kartu_ramalan": ("Ramalan tiap titik data", "Prediction for each data point"),
    "kolom_sasaran": ("sasaran", "target"),
    "kolom_keluaran": ("keluaran", "output"),
    "kolom_galat": ("galat", "error"),
    "kolom_benar": ("benar", "correct"),
    "ya": ("ya", "yes"),

    # -- diagnosis ----------------------------------------------------------
    "macet_tanpa_tersembunyi": (
        "Pelatihan berhenti bergerak. Ini bukan setelan yang salah melainkan "
        "batas yang sesungguhnya: tanpa lapis tersembunyi jaringan ini cuma "
        "bisa menarik satu garis lurus, dan tidak ada garis lurus yang "
        "memisahkan masalah ini. Tambahkan neuron tersembunyi.",
        "Training has stopped moving. This is not a wrong setting but a real "
        "limit: without a hidden layer this network can draw only one straight "
        "line, and no straight line separates this problem. Add hidden "
        "neurons.",
    ),
    "macet_jenuh": (
        "Pelatihan berhenti bergerak, dan jaringan menjawab sama untuk setiap "
        "masukan — neuronnya jenuh atau mati, sehingga turunannya nyaris nol "
        "dan tidak ada lagi yang mendorongnya. Kecilkan laju efektifnya, atau "
        "ganti aktivasinya; relu paling sering mati begini.",
        "Training has stopped moving, and the network answers the same for "
        "every input — its neurons are saturated or dead, so the derivatives "
        "are nearly zero and nothing pushes it any further. Reduce the "
        "effective rate, or change the activation; relu dies this way most "
        "often.",
    ),
    "macet_umum": (
        "Pelatihan berhenti bergerak sebelum seluruh titik benar. Coba tambah "
        "neuron tersembunyi, atau ganti benih bobot awal — sebagian titik awal "
        "memang berakhir di lembah yang bukan yang terdalam.",
        "Training has stopped moving before every point is correct. Try adding "
        "hidden neurons, or changing the initial-weight seed — some starting "
        "points do end in a valley that is not the deepest one.",
    ),

    # -- spanduk cacat ------------------------------------------------------
    "banding_cacat": (
        "Cacat menyala: %s. Yang disabotase ada di %s dengan %d dari %d titik "
        "benar; pembanding yang benar di %s dengan %d. ",
        "Defect active: %s. The sabotaged network is at %s with %d of %d "
        "points correct; the correct reference is at %s with %d. ",
    ),
    "banding_belum": (
        "Keduanya belum dilatih — tekan Latih.",
        "Neither has been trained yet — press Train.",
    ),
    "banding_lebih_rendah": (
        "Yang disabotase justru berakhir LEBIH RENDAH. Itu bukan kebetulan "
        "yang lucu melainkan seluruh maksud halaman ini.",
        "The sabotaged one actually ends LOWER. That is not an amusing "
        "coincidence but the entire point of this page.",
    ),
    "banding_setara": (
        "Keduanya sama-sama menurun, dan keduanya menjawab sama banyak.",
        "Both fell, and both answer the same number correctly.",
    ),
    "banding_tertinggal": (
        "Yang disabotase tertinggal — tetapi tetap menurun.",
        "The sabotaged one lags behind — but it still fell.",
    ),
    "banding_tertangkap": (
        "  Pemeriksa gradien menangkap cacat ini.",
        "  The gradient check catches this defect.",
    ),
    "banding_lolos": (
        "  Pemeriksa gradien tidak bisa menangkap yang ini.",
        "  The gradient check cannot catch this one.",
    ),

    # -- pemeriksaan gradien ------------------------------------------------
    "menghitung_ulang": (
        "Menghitung ulang setiap turunan dengan selisih hingga…",
        "Recomputing every derivative with finite differences…",
    ),
    "lolos": ("LOLOS", "PASS"),
    "gagal": ("GAGAL", "FAIL"),
    "ringkas_gradien": (
        "  Galat relatif terburuk %s pada %d parameter. Ambangnya 1e-5.",
        "  Worst relative error %s across %d parameters. The threshold is 1e-5.",
    ),
    "catatan_gradien": (
        "Perambatan balik menghitung turunan dengan aturan rantai; selisih "
        "hingga menghitungnya dengan menggeser bobotnya sedikit lalu melihat "
        "galatnya berubah berapa. Keduanya harus sepakat. Kalau tidak, "
        "perambatan baliknya salah — dan jaringan yang gradiennya salah tetap "
        "sering terlihat belajar, hanya berhenti di tempat yang keliru.",
        "Backpropagation computes derivatives with the chain rule; finite "
        "differences compute them by nudging the weight and seeing how much "
        "the error moves. The two must agree. If they do not, the "
        "backpropagation is wrong — and a network with wrong gradients still "
        "often appears to learn, it just stops in the wrong place.",
    ),
    "kolom_perambatan": ("perambatan balik", "backpropagation"),
    "kolom_selisih": ("selisih hingga", "finite differences"),
    "kolom_relatif": ("galat relatif", "relative error"),
    "menampilkan_sebagian": (
        "Menampilkan 14 dari %d parameter, diurutkan dari galat terbesar.",
        "Showing 14 of %d parameters, ordered by largest error.",
    ),
    "tafsir_tanpa_cacat_lolos": (
        "Tidak ada cacat yang menyala, dan pemeriksanya lolos — seperti "
        "seharusnya. Untuk membuktikan pemeriksa ini benar-benar memeriksa "
        "sesuatu, nyalakan salah satu cacat di panel Sabotase lalu tekan "
        "tombol ini lagi.",
        "No defect is active, and the check passes — as it should. To prove "
        "this check really checks something, switch on one of the defects in "
        "the Sabotage panel and press this button again.",
    ),
    "tafsir_tanpa_cacat_gagal": (
        "Tidak ada cacat yang menyala, tetapi pemeriksanya gagal. Ini tidak "
        "diharapkan terjadi; kalau Anda melihatnya, ada yang salah di mesin "
        "ini dan bukan di setelan Anda.",
        "No defect is active, yet the check fails. This is not expected; if "
        "you are seeing it, something is wrong in this engine and not in your "
        "settings.",
    ),
    "tafsir_tertangkap": (
        "Cacat “%s” menyala, dan pemeriksanya menangkapnya. Perhatikan kurva "
        "galat di sebelah: ia tetap menurun. Tidak ada satu pun angka di kurva "
        "itu yang bisa memberi tahu Anda hal yang baru saja diberitahukan "
        "tabel ini.",
        "The defect “%s” is active, and the check caught it. Look at the error "
        "curve beside it: it is still falling. Not one number on that curve "
        "could have told you what this table just did.",
    ),
    "tafsir_batas_alat": (
        "Cacat “%s” menyala, dan pemeriksanya LOLOS. Itu bukan kegagalan "
        "pemeriksanya melainkan batasnya: ia memeriksa apakah turunannya "
        "benar, bukan apakah turunannya dipakai. Cacat ini bekerja pada "
        "langkah pembaruan, jauh setelah gradiennya selesai dihitung. Alat "
        "yang batasnya tidak diketahui lebih berbahaya daripada tidak punya "
        "alat.",
        "The defect “%s” is active, and the check PASSES. That is not a "
        "failure of the check but its limit: it verifies whether the "
        "derivative is right, not whether it is used. This defect acts on the "
        "update step, long after the gradient has been computed. A tool whose "
        "limits are unknown is more dangerous than no tool.",
    ),
    "tafsir_tak_terduga": (
        "Cacat “%s” menyala dan hasilnya tidak seperti yang diperkirakan "
        "katalog cacatnya. Ini tidak diharapkan terjadi.",
        "The defect “%s” is active and the outcome differs from what the "
        "defect catalogue predicts. This is not expected.",
    ),

    # -- langkah demi langkah ------------------------------------------------
    "judul_jejak": (
        "Satu contoh melewati jaringan, maju lalu balik",
        "One example through the network, forward then back",
    ),
    "terang_jejak": (
        "Angka di dalam lingkaran adalah keluaran neuron itu pada perambatan "
        "maju. Bulatan di bawahnya adalah delta — bagian galat yang sampai ke "
        "neuron itu pada perambatan balik; makin besar bulatannya makin besar "
        "pengaruhnya, dan warnanya menyatakan arahnya. Garis di antara neuron "
        "adalah bobot yang sama untuk kedua arah, dan justru itulah seluruh "
        "gagasan perambatan balik.",
        "The number inside each circle is that neuron's output on the forward "
        "pass. The dot beneath it is the delta — the share of the error "
        "reaching that neuron on the backward pass; the larger the dot, the "
        "larger its influence, and its colour shows the direction. The lines "
        "between neurons are the same weights in both directions, and that is "
        "the whole idea of backpropagation.",
    ),
    "delta_positif": ("delta positif", "positive delta"),
    "bobot_negatif_delta": (
        "bobot negatif / delta negatif",
        "negative weight / negative delta",
    ),
    "ringkas_jejak": (
        "Masukan (%s, %s), sasaran %s, ramalan %s — galat contoh ini %s.",
        "Input (%s, %s), target %s, prediction %s — this example's error is %s.",
    ),
    "kolom_neuron": ("neuron", "neuron"),
    "kolom_z": ("jumlah berbobot z", "weighted sum z"),
    "kolom_a": ("keluaran a = f(z)", "output a = f(z)"),
    "kolom_delta": ("delta", "delta"),
    "kolom_gradien_bias": ("gradien bias", "bias gradient"),
    "catatan_jejak": (
        "Angka-angka ini bukan tiruan yang dihitung khusus untuk ditampilkan. "
        "Uji test_telusuri_sama_dengan_gradien membandingkannya dengan gradien "
        "yang benar-benar dipakai melatih — pola bit demi pola bit, pada empat "
        "aktivasi dan empat bentuk jaringan. Termasuk membedakan nol positif "
        "dari nol negatif, yang pernah membuat keduanya berbeda.",
        "These numbers are not a replica computed just for display. The test "
        "test_telusuri_sama_dengan_gradien compares them against the gradients "
        "actually used for training — bit pattern by bit pattern, across four "
        "activations and four network shapes. Including telling positive zero "
        "from negative zero, which once made the two differ.",
    ),
    # Nama lapis pada diagram. Dibedakan dari nama kolom tabel yang
    # kebetulan berbunyi sama: kunci yang bentrok membuat pengganti
    # otomatis tidak bisa menentukan yang mana yang dimaksud.
    "lapis_masukan": ("masukan", "input"),
    "lapis_tersembunyi": ("tersembunyi", "hidden"),
    "lapis_keluaran": ("keluaran", "output"),

    # -- konformansi --------------------------------------------------------
    "mengambil_vektor": ("Mengambil berkas vektor…", "Fetching the test vectors…"),
    "vektor_gagal": (
        "Berkas vektor gagal diambil, jadi tidak ada yang bisa diperiksa. "
        "Periksa sambungan jaringan lalu coba lagi.",
        "The vector file could not be fetched, so there is nothing to check. "
        "Check your network connection and try again.",
    ),
    "memeriksa": ("Memeriksa…", "Checking…"),
    "memeriksa_maju": (
        "Memeriksa… %d baris vektor, %d pernyataan.",
        "Checking… %d vector rows, %d assertions.",
    ),
    "cocok": ("COCOK", "MATCH"),
    "tidak_cocok": ("TIDAK COCOK", "NO MATCH"),
    "ringkas_konformansi": (
        "  %d pernyataan diperiksa di peramban ini dalam %s detik, %d tidak cocok.",
        "  %d assertions checked in this browser in %s seconds, %d did not match.",
    ),
    "vektor_tak_terbaca": ("Vektor tidak terbaca — ", "Vector unreadable — "),
    "kolom_berkas": ("berkas vektor", "vector file"),
    "kolom_pernyataan": ("pernyataan", "assertions"),
    "kolom_keterbandingan": ("keterbandingan", "comparability"),
    "kolom_ulp": ("ULP maks", "max ULP"),
    "kolom_hasil": ("hasil", "result"),
    "n_gagal": ("%d GAGAL", "%d FAILED"),
    "pola_berbeda": (
        "Pola bit yang berbeda — harapan diambil dari vektor Rust:",
        "Differing bit patterns — the expected values come from the Rust vectors:",
    ),
    "kolom_baris": ("baris", "row"),
    "kolom_diuji": ("yang diuji", "what was tested"),
    "kolom_harap": ("harap", "expected"),
    "kolom_dapat": ("dapat", "got"),
    "ulp_bitexact": (
        "Perhatikan kolom ULP maks. Seluruh berkas BitExact nol — di situ "
        "memang tidak boleh ada selisih sedikit pun, dan tidak ada. Yang bukan "
        "nol semuanya jatuh di berkas yang tingkat keterbandingannya sudah "
        "menyatakan kelonggaran di muka.",
        "Look at the max-ULP column. Every BitExact file is zero — no "
        "difference at all is permitted there, and there is none. Everything "
        "non-zero falls in files whose comparability tier already declared "
        "slack up front.",
    ),
    "ulp_nearly": (
        "Berkas NearlyEqual(4) meleset sampai %d ULP. IEEE-754 mewajibkan "
        "penjumlahan, pengurangan, perkalian, pembagian, dan akar kuadrat "
        "dibulatkan dengan benar — tetapi tidak exp, log, maupun pow. Python "
        "di peramban menghitung ketiganya lewat pustaka matematika JavaScript, "
        "yang menempuh jalan berbeda dari pustaka C yang dipakai CPython di "
        "CI. Di CI angka ini nol; di sini tidak. Keduanya benar.",
        "The NearlyEqual(4) files are off by up to %d ULP. IEEE-754 requires "
        "addition, subtraction, multiplication, division, and square root to "
        "be correctly rounded — but not exp, log, or pow. Python in the "
        "browser computes all three through the JavaScript maths library, "
        "which takes a different route from the C library CPython uses in CI. "
        "In CI this number is zero; here it is not. Both are correct.",
    ),
    "ulp_cancelling": (
        "Dan perhatikan ml_gain.tsv: %d ULP, jauh di luar empat — tetapi tetap "
        "cocok. Bukan kelonggaran yang dilebarkan diam-diam. "
        "CancellingDifference mengukur toleransinya pada skala masukan, bukan "
        "pada hasil. Perolehan informasi adalah selisih dua entropi yang "
        "hampir sama besar; pengurangan seperti itu membuang digit berarti di "
        "depan dan memperbesar galat relatifnya berlipat-lipat, sampai puluhan "
        "kali. Menuntut ketepatan pada hasilnya adalah menuntut sesuatu yang "
        "tidak dimiliki angka mana pun di sana. Angka %d inilah pembalikan "
        "yang paling jelas: di CPython ia nol, dan tingkat keterbandingan ini "
        "yang membuat perbedaannya terlihat sebagai keterangan alih-alih "
        "sebagai kegagalan.",
        "And look at ml_gain.tsv: %d ULP, far outside four — and still a "
        "match. This is not slack quietly widened. CancellingDifference "
        "measures its tolerance at the input scale, not on the result. "
        "Information gain is the difference of two nearly equal entropies; "
        "such a subtraction discards leading significant digits and multiplies "
        "the relative error many times over, up to tens of times. Demanding "
        "precision on the result would demand something no number there "
        "possesses. That %d is the clearest reversal of all: in CPython it is "
        "zero, and this comparability tier is what makes the difference read "
        "as an explanation rather than as a failure.",
    ),
    "catatan_tingkat": (
        "Angkanya berpindah antar bahasa sebagai pola bit heksadesimal 16 "
        "digit, bukan sebagai desimal. “BitExact” menuntut kecocokan sampai "
        "bit terakhir. “NearlyEqual(4)” memberi kelonggaran empat ULP, dan "
        "hanya untuk perhitungan yang menyentuh exp atau log — IEEE-754 memang "
        "tidak mewajibkan keduanya dibulatkan dengan benar. "
        "“CancellingDifference(4)” mengukur kelonggarannya pada skala masukan, "
        "bukan pada hasil: perolehan informasi adalah selisih dua entropi yang "
        "hampir sama besar, dan pengurangan seperti itu memperbesar galat "
        "relatifnya berlipat-lipat.",
        "Numbers cross language boundaries as 16-digit hexadecimal bit "
        "patterns, not as decimal. “BitExact” demands agreement to the last "
        "bit. “NearlyEqual(4)” allows four ULP of slack, and only for "
        "computations touching exp or log — IEEE-754 does not require either "
        "to be correctly rounded. “CancellingDifference(4)” measures its slack "
        "at the input scale rather than on the result: information gain is the "
        "difference of two nearly equal entropies, and such a subtraction "
        "multiplies the relative error many times over.",
    ),
}
