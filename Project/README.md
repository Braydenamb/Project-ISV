# Topik 10 — Particle Counter & Size Distribution Analyzer

Aturan resmi dan keputusan internal: `/home/miq/Documents/ISV/Project ISV/Project/RULES.md`.
Hasil audit terbaru (16 November 2026): `/home/miq/Documents/ISV/Project ISV/Project/VERIFICATION.md`.

## Prototipe yang sudah dibuat

### Format dashboard saat ini

Aplikasi interaktif dan ekspor kini memakai renderer yang sama dengan layout **2×2**:
input + ROI (kiri atas), mask bernomor (kanan atas), histogram (kiri bawah), dan tabel luas per partikel (kanan bawah).
Header menampilkan jumlah, objek batas yang dikecualikan, threshold, dan status **px² — UNCALIBRATED**.
Tabel menampilkan maksimal 12 objek agar tetap terbaca; CSV selalu menyimpan seluruh objek.
ROI dan threshold memperbarui keempat panel dari hasil analisis yang sama.
Tombol `s` atau mode `--headless` juga menyimpan `dashboard.png` bersama berkas individual.
Preview dokumentasi di `/home/miq/Documents/ISV/Project ISV/Project/dokumentasi/current_output.png` menggunakan layout yang sama; buat ulang dengan `/home/miq/Documents/ISV/Project ISV/Project/create_preview.py`.
Verifikasi terbaru: **10/10 unit test lulus**, termasuk layout, tabel, kasus kosong, batas tampilan tabel, ekspor, dan interaksi tersimulasi.

Sampel proyek sudah diputuskan: beras. Implementasi awal memakai citra statis dari dataset Kaggle, bukan model klasifikasi. Pengukuran masih **px²**, belum terkalibrasi secara fisik.

File aplikasi: `/home/miq/Documents/ISV/Project ISV/Project/particle_counter.py`.

Jalankan antarmuka (perintah dapat digunakan dari folder mana pun):

```bash
"/home/miq/Documents/ISV/Project ISV/Project/.venv/bin/python" \
  "/home/miq/Documents/ISV/Project ISV/Project/particle_counter.py" \
  "/home/miq/Documents/ISV/Project ISV/Project/data/samples/synthetic_montage.png"
```

- Drag mouse kiri pada panel citra pertama untuk memilih ROI. Matikan mode pan/zoom toolbar saat memilih ROI.
- `+` / `=` / panah atas: naikkan threshold sebesar 5.
- `-` / panah bawah: turunkan threshold sebesar 5.
- `i`: balik polaritas untuk objek gelap pada latar terang.
- `r`: reset ROI ke seluruh gambar.
- `s`: simpan hasil; `q` / Escape: keluar. Fokuskan jendela gambar sebelum menekan tombol.
- File keluaran default ditulis ulang di `/home/miq/Documents/ISV/Project ISV/Project/outputs/latest`; gunakan `--output` untuk menyimpan eksperimen berbeda.
- Opsi lain: `--threshold 127`, `--min-area 30`, `--roi X Y W H`, `--invert`, dan `--headless`.

Contoh tanpa jendela:

```bash
"/home/miq/Documents/ISV/Project ISV/Project/.venv/bin/python" \
  "/home/miq/Documents/ISV/Project ISV/Project/particle_counter.py" \
  "/home/miq/Documents/ISV/Project ISV/Project/data/samples/synthetic_montage.png" \
  --headless --output "/home/miq/Documents/ISV/Project ISV/Project/outputs/demo"
```

Keluaran: overlay bernomor, mask biner objek diterima, mask bernomor terpisah (`mask_numbered.png`), citra threshold ROI, histogram, tabel CSV, dan JSON parameter/hasil. CSV menyimpan pusat objek pada koordinat gambar penuh. Mask diterima mengisi kontur eksternal; lubang internal tidak dikurangi dari luas kontur. Objek menyentuh batas ROI dikecualikan setelah filter luas. Partikel bersentuhan dapat terhitung sebagai satu objek.

### Data dan reproduksi

- Arsip dataset berhasil diunduh ke `/home/miq/Documents/ISV/Project ISV/Project/data/raw/rice-images-dataset.zip`.
- Sumber: `https://www.kaggle.com/datasets/mbsoroush/rice-images-dataset`.
- Sebanyak 10 gambar per varietas (50 total) diekstrak tanpa perubahan ke `/home/miq/Documents/ISV/Project ISV/Project/data/samples`.
- Pemilihan berurutan berdasarkan nama file, bukan sampling acak representatif. Hasil ini bukan evaluasi keseluruhan dataset.
- Skrip `/home/miq/Documents/ISV/Project ISV/Project/prepare_samples.py` mereproduksi pemilihan, manifest, serta montage sintetis lima gambar tanpa resize. Montage bukan foto eksperimen fisik.
- Baca berkas permintaan sitasi `.txt` yang ikut diekstrak sebelum menyusun laporan; periksa lisensi dataset sebelum redistribusi.
- Arsip, gambar turunan, virtual environment, dan keluaran diabaikan oleh Git; jangan menganggap semuanya ikut tersimpan dalam commit.

Lingkungan lokal: virtual environment memakai `--system-site-packages` untuk NumPy/Matplotlib yang sudah ada dan OpenCV dipasang di virtual environment. Untuk komputer lain, buat venv biasa dan pasang `/home/miq/Documents/ISV/Project ISV/Project/requirements.txt`; kompatibilitas lintas platform belum diuji.

### Verifikasi awal

- 10 unit test lulus: jumlah/luas kontur, citra kosong/threshold, ROI/koordinat global, batas ROI, filter noise/inversi, parameter invalid, isi ekspor termasuk hasil kosong, mask bernomor terpisah, callback interaksi GUI, serta dashboard kosong dan batas tampilan tabel.
- 50/50 gambar sampel menghasilkan satu kontur diterima pada threshold 127 dan luas minimum 30 px². Ini pemeriksaan jumlah, bukan validasi akurasi segmentasi atau ukuran fisik.
- Montage sintetis: 5 objek diharapkan, 5 terdeteksi.
- CLI headless berhasil menyimpan hasil.
- Callback mouse ROI, keyboard threshold, reset, simpan, dan keluar diuji otomatis menggunakan backend noninteraktif. Pengalaman interaksi jendela desktop secara manual masih perlu diperiksa.
- Uji awal menemukan konflik tombol `s` dengan dialog Save Matplotlib; shortcut bawaan yang bertabrakan sudah dinonaktifkan.

Jalankan unit test:

```bash
"/home/miq/Documents/ISV/Project ISV/Project/.venv/bin/python" \
  -m unittest discover -s "/home/miq/Documents/ISV/Project ISV/Project" -v
```

Belum dikerjakan: kalibrasi mm², validasi foto HP, integrasi kamera, pengujian metrologi, laporan akhir, dan video demo. Bagian berikut merupakan arah eksperimen lanjutan, bukan fitur yang semuanya telah selesai.

## Lokasi dan pedoman kerja

- Seluruh hasil tugas disimpan di `/home/miq/Documents/ISV/Project ISV/Project`.
- Pedoman pengerjaan: `/home/miq/Documents/ISV/Project ISV/karpathy/skills/karpathy-guidelines/SKILL.md`.
- Sumber ketentuan: `/home/miq/Documents/ISV/Project ISV/Tugas UAS ISV 2026-Edited.docx`.
- Terapkan prinsip: nyatakan asumsi, mulai dari solusi sederhana, ubah hanya yang diperlukan, dan verifikasi setiap tahap.
- Status prototipe dan batas verifikasi tercatat pada bagian awal dokumen; data eksperimen fisik belum tersedia.

## 1. Tujuan dan ruang lingkup

Membangun sistem penghitungan partikel dan analisis distribusi luas proyeksi 2D menggunakan thresholding dan deteksi kontur, tanpa model AI pre-trained.

Fitur inti sesuai topik:

1. Memilih ROI area penghitungan dengan mouse.
2. Mengatur threshold biner dengan keyboard.
3. Menghitung partikel yang lolos aturan deteksi.
4. Menampilkan mask dan nomor partikel.
5. Menampilkan histogram distribusi luas partikel.

Kebutuhan pendukung rubrik:

- Setup kamera dan pencahayaan yang terdokumentasi.
- Kalibrasi ukuran piksel ke satuan fisik.
- Pengujian jumlah, galat ukuran, repeatability, dan limitasi.
- Penyimpanan bukti hasil untuk laporan dan demo.

Batasan versi awal: partikel diam, satu lapisan, kontras terhadap latar, dan tidak saling bersentuhan. Mulai dari citra statis sebelum mengintegrasikan kamera. Sistem tidak mengukur volume atau ukuran 3D.

## 2. Keputusan sebelum implementasi

Catat keputusan berikut berdasarkan perangkat dan sampel nyata; jangan menganggapnya sudah ditentukan:

| Keputusan | Hal yang perlu dipastikan |
| --- | --- |
| Sampel | Beras sudah dipilih; sampel fisik dan kisaran ukuran belum ditentukan |
| Kamera | Kamera HP tersedia; resolusi dan setup fisik belum diuji, webcam opsional |
| Setup | Jarak kamera, bidang sampel, penyangga, latar, dan pencahayaan |
| Referensi | Acuan ukuran berdimensi diketahui, sumber nilai acuannya, dan penempatan sebidang dengan sampel |
| Lingkungan kode | Python dan library yang tersedia; tetapkan dependensi setelah pemeriksaan |
| Target kinerja | Toleransi galat jumlah dan ukuran sebelum pengujian akhir |

Jangan membeli perangkat atau mengunci stack UI sebelum kebutuhan ini jelas. Tidak perlu web dashboard, database, deep learning, atau tracking lintas frame untuk memenuhi fitur inti.

## 3. Tahapan pengerjaan dan verifikasi

### Tahap A — Setup fisik dan data awal

- Tetapkan sampel dan kamera yang tersedia.
- Dokumentasikan posisi kamera, jarak kerja, pencahayaan, latar, resolusi, dan pengaturan fokus.
- Ambil citra kosong, sampel terpisah, referensi ukuran, dan contoh kondisi sulit.
- Buat hitungan manual untuk setiap citra uji; pisahkan citra pengembangan dari citra evaluasi akhir.

Selesai jika: citra dapat dibaca, partikel terlihat jelas, referensi tersedia, dan hitungan manual tercatat.

### Tahap B — Penghitungan pada citra statis

Alur awal: citra → ROI → grayscale → threshold → kontur eksternal → filter luas → jumlah dan label.

- Tentukan polaritas threshold berdasarkan sampel dan latar.
- Tambahkan pengurangan noise atau morfologi hanya jika dibutuhkan oleh data. Catat pengaruhnya pada luas.
- Tetapkan luas minimum untuk menolak noise menggunakan data pengembangan.
- Untuk analisis ukuran, usulkan mengecualikan objek yang menyentuh batas ROI; tampilkan jumlah pengecualian secara terpisah.
- Tetapkan definisi luas: luas kontur atau jumlah piksel mask. Gunakan definisi yang sama pada pengujian dan laporan.

Selesai jika: citra kosong menghasilkan nol, sampel terpisah sesuai hitungan manual, label sesuai objek yang diterima, dan ROI membatasi area analisis.

### Tahap C — Kalibrasi dan distribusi ukuran

- Ukur panjang referensi dalam piksel dan masukkan panjang fisiknya.
- Untuk asumsi skala seragam: `s = panjang_referensi_mm / panjang_referensi_px`.
- Konversi luas: `luas_mm2 = luas_px2 × s²`.
- Histogram utama menggunakan luas dengan satuan jelas. Diameter ekuivalen boleh ditambahkan, bukan menggantikan keluaran luas yang diminta.
- Jika ditampilkan, diameter ekuivalen: `d_eq = sqrt(4 × luas / pi)`; ini bukan diameter maksimum objek.
- Validasi skala pada beberapa posisi bidang pandang. Jika pembesaran, resolusi, jarak kamera, atau bidang objek berubah, evaluasi ulang kalibrasi.
- Jangan menampilkan satuan fisik seolah valid sebelum kalibrasi dilakukan.

Selesai jika: konversi diuji dengan nilai yang diketahui, pengukuran pembanding dicatat, dan histogram memuat objek yang sama dengan daftar partikel diterima.

### Tahap D — Antarmuka dan integrasi kamera

- Pilih bentuk UI paling sederhana yang mendukung ROI mouse, keyboard, mask bernomor, dan histogram setelah memeriksa lingkungan.
- Tampilkan sumber citra, ROI, threshold, jumlah, satuan, dan status kalibrasi.
- Tentukan tombol menaikkan/menurunkan threshold, reset ROI, menyimpan hasil, dan keluar; dokumentasikan tombol aktual setelah implementasi.
- Integrasikan kamera setelah pipeline citra statis teruji.
- Hitungan pada kamera adalah hitungan per frame, bukan jumlah kumulatif partikel unik.
- Simpan citra keluaran dan tabel hasil minimal: identitas citra, ID partikel, luas, satuan, threshold, ROI, dan informasi skala.

Selesai jika: perubahan threshold memperbarui hasil, pemilihan ROI bekerja, keluaran dapat disimpan, dan demo dapat dijalankan ulang dengan prosedur yang sama.

### Tahap E — Pengujian kinerja

Pisahkan pengujian logika menggunakan citra sintetis dari validasi metrologi menggunakan objek fisik. Citra sintetis tidak membuktikan ketepatan pengukuran fisik.

| Pengujian | Bukti yang dicatat |
| --- | --- |
| Jumlah partikel | Hitungan manual, hitungan sistem, selisih absolut; galat relatif hanya jika acuan bukan nol |
| Ketepatan ukuran | Nilai acuan, nilai ukur, galat, metode dan keterbatasan acuan |
| Repeatability | Pengukuran berulang, rata-rata, simpangan baku, serta apakah sampel ditata ulang |
| Pencahayaan | Kondisi nominal dan variasi kecil dengan parameter pengolahan tercatat |
| Posisi bidang pandang | Pengukuran referensi di beberapa lokasi |
| Kasus batas | Citra kosong, noise, partikel menyentuh ROI, dan partikel bersentuhan |

Untuk partikel bersentuhan, catat jika satu kontur mencakup beberapa partikel. Jangan menjanjikan pemisahan otomatis pada versi awal. Jika diperlukan, evaluasi metode tambahan sebagai perubahan ruang lingkup yang diuji terpisah.

Selesai jika: hasil memenuhi target yang telah ditetapkan atau penyimpangannya dijelaskan dengan bukti; tidak ada angka hasil yang direkayasa.

### Tahap F — Laporan dan video demo

Laporan PDF maksimal 8 halaman inti untuk Bab 1–4, dengan bookmark bab dan subbab:

1. Bab 1: deskripsi sistem, diagram blok, setup fisik, dan spesifikasi sensor.
2. Bab 2: metodologi pengolahan dan ekstraksi fitur beserta alasan pemilihannya.
3. Bab 3: prosedur kalibrasi, hasil pengukuran, galat, dan repeatability.
4. Bab 4: kinerja, limitasi, dan kesimpulan berbasis hasil.

Sertakan judul, anggota dan pembagian tugas, serta tautan video demo. Video memperlihatkan setup, kalibrasi, pemilihan ROI, perubahan threshold, dan hasil analisis. Jika memakai citra/video internet, catat tautan sumber dalam laporan.

Pengumpulan mengikuti waktu UAS dan ketentuan pada dokumen; jangan menetapkan tanggal sendiri. Subjek surel: `ISV_UAS_<Nomor Kelompok>_<Judul topik>`.

## 4. Prioritas berdasarkan rubrik

| Aspek | Bobot | Fokus pekerjaan |
| --- | --- | --- |
| Rekayasa optik | 20% | Setup stabil dan alasan teknis pengkondisian citra |
| Ekstraksi fitur | 25% | Deteksi deterministik dan ketahanan terhadap perubahan kecil |
| Kalibrasi | 25% | Konversi fisik valid, galat, dan statistik pengukuran |
| UI | 15% | Mask, label, histogram, dan interaksi yang jelas |
| Laporan dan demo | 15% | Bukti hasil, diagram, laporan ringkas, dan demo runtut |

Prioritas: setup dan data → deteksi dasar → kalibrasi → UI → pengujian akhir → laporan/demo. Catat eksperimen sejak tahap pertama, bukan menunggu aplikasi selesai.

## 5. Pembagian kerja yang diusulkan

- Anggota 1: setup optik dan pengambilan data.
- Anggota 2: segmentasi, kontur, dan penghitungan.
- Anggota 3: kalibrasi, metrologi, dan pengujian.
- Anggota 4: UI, integrasi, dan penyimpanan hasil.
- Jika ada anggota 5: koordinasi dokumentasi, data, dan demo; jika hanya 4 anggota, pekerjaan ini dibagi bersama.

Semua anggota tetap harus memahami alur sistem dan memverifikasi bagian masing-masing. Jadwal rinci ditetapkan setelah tanggal UAS dan ketersediaan alat diketahui.

## 6. Langkah terdekat

1. Jalankan prototipe dengan gambar dataset dan periksa UI secara manual.
2. Ambil satu foto HP berisi beras terpisah serta referensi ukuran sebidang.
3. Uji pipeline pada foto HP sebelum menambah pemrosesan lain.
4. Implementasikan kalibrasi dan validasi ukuran menggunakan acuan fisik.

Dokumen ini adalah arahan kerja, bukan bukti bahwa aplikasi atau eksperimen sudah selesai.