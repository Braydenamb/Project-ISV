# Aturan Tugas UAS ISV — Topik 10

Sumber utama: `/home/miq/Documents/ISV/Project ISV/Tugas UAS ISV 2026-Edited.docx`.
Dokumen sumber dibaca ulang pada 16 November 2026. Dokumen ini merupakan rangkuman operasional, bukan pengganti atau perubahan ketentuan dosen. Jika terdapat perbedaan, ikuti dokumen sumber dan klarifikasi dosen.

## A. Ketentuan resmi dari dokumen UAS

### A1. Kelompok dan pengumpulan

- Tugas dikerjakan oleh kelompok beranggotakan **4–5 orang**.
- Tugas dikumpulkan **saat UAS ISV dilakukan, bukan sebelum atau setelah**.
- Tujuan surel: `yakubfahimluckyarno@ugm.ac.id`.
- Subjek surel: `ISV_UAS_<Nomor Kelompok>_<Judul topik>`.
- Dokumen tidak menetapkan tanggal dan jam UAS; jangan mengarang tenggat.
- Tugas merupakan **rancang bangun**: rancangan dan eksekusi sama-sama dinilai.

### A2. Pendekatan pengolahan

- Gunakan **computer vision klasik dan spatial signal processing berbasis prinsip deterministik dan fisik**.
- Contoh dalam sumber: konvolusi kernel 2D, transformasi ruang warna, operator gradien, analisis kontur, thresholding adaptif, dan transformasi frekuensi/FFT.
- Sumber membatasi penggunaan algoritma/model AI siap pakai seperti YOLO, SAM, R-CNN, VGG, ResNet, dan model pre-trained lainnya. Implementasi proyek ini tidak menggunakan model tersebut.
- Jika machine learning diperlukan, sumber memperbolehkan regresi sederhana, k-NN, SVM, atau arsitektur buatan sendiri **tanpa transfer learning**. Machine learning bukan kewajiban proyek ini.
- Arsitektur pengolahan citra bebas dirancang mahasiswa.
- **Tidak wajib menerapkan semua jenis filter**. Setiap tahap yang dipilih perlu memiliki alasan teknis.

### A3. Penggunaan sumber internet

- Jika fenomena fisik atau eksperimen sulit direplikasi, sumber memperbolehkan video atau sumber serupa dari internet.
- Jika memakai sumber tersebut, tautan sumber **wajib disediakan** dan hasil percobaan **tetap wajib dilaporkan**.
- Ketentuan ini bukan izin tanpa syarat untuk mengganti semua eksperimen dengan dataset. Untuk penggunaan dataset beras sebagai keseluruhan eksperimen akhir, konfirmasikan kesesuaiannya kepada dosen bila syarat kesulitan replikasi tidak terpenuhi.
- Saat ini dataset digunakan untuk pengembangan prototipe; pemakaian dataset saja tidak membuktikan pencapaian rubrik rekayasa optik atau kalibrasi fisik.

### A4. Kebutuhan khusus Topik 10

Judul resmi: **Particle Counter & Size Distribution Analyzer**.

| Aspek | Ketentuan pada tabel topik |
| --- | --- |
| Algoritma dan konsep | Thresholding + Blob Detection (FindContours), untuk menghitung jumlah partikel dan mengelompokkan luas areanya |
| Keluaran visual | Citra masking partikel bernomor dan grafik histogram distribusi ukuran partikel |
| Mouse | Memilih ROI area perhitungan partikel |
| Keyboard | Mengatur nilai threshold biner |

Tabel Topik 10 tidak secara eksplisit mewajibkan streaming, kamera real-time, pengenalan varietas, atau klasifikasi mutu. Jangan menyebut fitur tersebut sebagai kewajiban resmi.

### A5. Deliverables dan struktur laporan

1. **Laporan akhir PDF** berisi pendahuluan, teori, perancangan, dan hasil.
2. **Video demo**, dari setup sampai hasil pemrosesan sinyal; dikumpulkan sebagai **tautan dalam laporan akhir**.

Struktur laporan yang diminta:

- Judul.
- Daftar anggota dan pembagian tugas.
- **Bab 1:** deskripsi sistem dan setup fisik, termasuk blok diagram, skema penataan kamera, dan spesifikasi sensor.
- **Bab 2:** metodologi pengolahan sinyal dan ekstraksi fitur.
- **Bab 3:** hasil, prosedur serta hasil kalibrasi dan metrologi sistem.
- **Bab 4:** analisis kinerja dan limitasi sistem.
- Bab dan subbab rapi serta dapat dilihat dan diakses melalui **bookmark PDF**.
- Maksimal **8 halaman inti untuk Bab 1–4**, dan diagram blok sistem harus jelas.

### A6. Rubrik penilaian

| Kriteria | Bobot | Indikator sumber |
| --- | --- | --- |
| Rekayasa optik | 20% | Kualitas penyetelan fisik sensor, posisi kamera/pencahayaan; kejelasan dan ketepatan alasan teknis tahapan pengkondisian sinyal |
| Ekstraksi fitur | 25% | Ekstraksi deterministik berhasil; tahan terhadap fluktuasi minor posisi atau pencahayaan |
| Kalibrasi | 25% | Konversi piksel ke besaran fisik nyata valid; data pengujian seperti galat dan standar deviasi disajikan |
| Antarmuka/UI | 15% | Antarmuka visual jelas, misalnya label besaran fisik, bounding box metrik, grafik tren, dan lainnya |
| Laporan dan demo | 15% | Laporan rapi dan ringkas, maksimal 8 halaman inti Bab 1–4, diagram blok jelas |

Contoh tampilan dalam rubrik UI bukan kewajiban menerapkan setiap jenis grafik pada semua topik; keluaran spesifik Topik 10 tetap menjadi acuan.

Sumber mencantumkan mikroskop digital dan headset VR sebagai fasilitas. Ini bukan kewajiban pemakaian atau jaminan akses aktual; pengguna menyatakan kamera HP tersedia, webcam mungkin tersedia, dan mikroskop belum tersedia bagi kelompok.

## B. Keputusan internal proyek — bukan ketentuan dosen

- Sampel yang disepakati: **beras**.
- Folder kerja: `/home/miq/Documents/ISV/Project ISV/Project`.
- Pedoman kerja: `/home/miq/Documents/ISV/Project ISV/karpathy/skills/karpathy-guidelines/SKILL.md`.
- Implementasi awal: Python, OpenCV, NumPy, dan Matplotlib; citra statis sebelum integrasi kamera.
- Dataset pengembangan: `https://www.kaggle.com/datasets/mbsoroush/rice-images-dataset`.
- Simpan sumber dan baca permintaan sitasi yang disertakan dataset; lisensi harus diperiksa sebelum redistribusi. Dokumen UAS tidak menetapkan lisensi dataset ini.
- Gunakan segmentasi grayscale, threshold biner, dan kontur eksternal tanpa model AI pre-trained.
- Luas versi awal adalah **luas kontur eksternal dalam px²**; lubang internal tidak dikurangi. Mask biner dan mask bernomor dipisahkan agar anotasi tidak mencemari data biner.
- Objek dengan luas di bawah batas minimum disaring. Objek yang lolos filter luas tetapi menyentuh batas ROI dikecualikan dan dilaporkan terpisah.
- Asumsi awal: beras diam, satu lapisan, terpisah, dan kontras terhadap latar. Butir bersentuhan mungkin dihitung sebagai satu objek.
- Tidak mengklaim volume, massa, varietas, atau mutu beras dari pengukuran ini.
- Citra gabungan dari gambar dataset harus disebut **sintetis**, bukan eksperimen fisik. Tidak mengubah ukuran piksel gambar saat membuat montage tidak membuktikan kesamaan skala fisik antar gambar.
- Jangan melaporkan mm² sebelum ada kalibrasi valid. Untuk skala seragam, `s = L_mm / L_px` dan `A_mm2 = A_px2 × s²`; asumsi bidang, posisi kamera, resolusi, dan pembesaran harus diuji.
- Jumlah gambar, threshold 127, luas minimum 30 px², aturan batas ROI, penyimpanan CSV/JSON, dan jenis unit test adalah pilihan proyek, bukan angka wajib dari dosen.
- Jangan membuat klaim akurasi keseluruhan dataset berdasarkan 50 gambar pilihan berurutan atau menyebut kelulusan unit test sebagai validasi metrologi.

## C. Gerbang penyelesaian proyek

Proyek belum boleh disebut selesai hanya karena aplikasi berjalan. Periksa:

- [ ] Kelompok dan pembagian tugas tercatat.
- [ ] Setup optik, spesifikasi kamera, dan diagram blok terdokumentasi.
- [ ] Threshold + kontur, jumlah, mask bernomor, dan histogram bekerja.
- [ ] ROI mouse dan threshold keyboard diuji pada antarmuka sebenarnya.
- [ ] Kalibrasi fisik dan validasi terhadap acuan tersedia.
- [ ] Data galat, pengulangan, dan statistik pengukuran tersedia.
- [ ] Ketahanan terhadap perubahan kecil posisi/pencahayaan diuji.
- [ ] Limitasi dan aturan pengecualian objek dijelaskan.
- [ ] Semua sumber internet dan hasil percobaan dicantumkan.
- [ ] PDF akhir memenuhi struktur, batas halaman, dan bookmark.
- [ ] Video demo dari setup hingga hasil tersedia dan ditautkan dalam PDF.
- [ ] Pengiriman memenuhi alamat, subjek, dan waktu UAS.

Status aktual dan bukti pemeriksaan disimpan di `/home/miq/Documents/ISV/Project ISV/Project/VERIFICATION.md`, bukan dicampur dengan ketentuan resmi.