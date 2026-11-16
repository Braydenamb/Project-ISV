# Verifikasi ulang proyek

Tanggal: **16 November 2026**. Aturan acuan: `/home/miq/Documents/ISV/Project ISV/Project/RULES.md`, berdasarkan pembacaan ulang dokumen UAS asli.

## Kesimpulan

### Pembaruan sistem interaktif

Aplikasi dapat diluncurkan tanpa path gambar dan membuka demo. Tombol Open image, Previous, Next, Reset ROI, Save results serta status pada jendela sudah tersedia. **11/11 unit test lulus**; pengujian tambahan membuktikan pergantian gambar mereset ROI dan memperbarui sumber/hasil ekspor. Event loop Qt desktop dijalankan dengan timer untuk menaikkan threshold, menyimpan, dan menutup jendela; hasil simpan menunjukkan threshold 132. Ini bukan pengujian manual mouse atau dialog file. Laporan/video dikerjakan manual oleh kelompok; kalibrasi fisik dan kamera live belum diimplementasikan.

### Pembaruan format dashboard

Aplikasi interaktif kini memakai layout 2×2 yang sama dengan preview dan ekspor `dashboard.png`: input/ROI, mask bernomor, histogram, dan tabel luas. Tabel maksimal 12 baris; seluruh data tetap di CSV. Header menyatakan px² belum terkalibrasi. Pengujian terbaru **10/10 lulus**, termasuk pembaruan tabel saat ROI berubah, kasus kosong, batas tabel, serta ekspor dashboard. Pengujian desktop manual dan validasi fisik tetap belum dibuktikan. Angka 9/9 pada audit awal di bawah merupakan hasil sebelum pembaruan ini.

**Prototipe citra statis berjalan dan memenuhi alur fungsional dasar Topik 10 pada pengujian terbatas. Proyek belum lengkap untuk pengumpulan UAS.** Ini bukan estimasi nilai atau persentase kelulusan rubrik.

## Lingkungan yang diperiksa

- Linux; Python 3.14.10.
- OpenCV 5.0.0; NumPy 2.5.4; Matplotlib 3.11.2.
- Interpreter: `/home/miq/Documents/ISV/Project ISV/Project/.venv/bin/python`.
- Venv memakai system-site-packages. `requirements.txt` belum mengunci versi; reproduksi pada lingkungan bersih/komputer lain belum diuji.

## Pemeriksaan yang dijalankan ulang

| Pemeriksaan | Hasil aktual | Batas kesimpulan |
| --- | --- | --- |
| Unit test | **9/9 lulus** | Menguji logika dan callback, bukan metrologi fisik |
| Kompilasi tiga file Python | Berhasil | Memeriksa sintaks, bukan semua perilaku runtime |
| `pip check` | No broken requirements found | Tidak membuktikan kompatibilitas pada komputer lain |
| Reproduksi sampel dataset | 50 gambar, lima varietas; **50/50** menghasilkan satu objek | Sampel dipilih berurutan menurut nama, bukan representatif seluruh dataset |
| Montage sintetis | Ekspektasi 5, terdeteksi **5**, pengecualian batas 0 | Susunan sintetis tanpa resize, bukan foto multi-butir nyata atau bukti kesamaan skala fisik |
| CLI headless | Exit 0, CSV berisi 5 objek dan JSON menyatakan `calibrated=false` | Satuan hanya px² |
| Berkas hasil | Lima PNG dapat dibaca; CSV dan JSON konsisten | Pengalaman visual desktop belum dinilai manual |
| Input CLI tidak valid | Threshold negatif, ROI di luar gambar, gambar hilang: semuanya exit **2** | Tidak mencakup seluruh kemungkinan input API |
| ROI dan keyboard | Simulasi drag memilih ROI `[5,5,35,35]`, hitungan 1; `+` menghasilkan threshold 132; reset mengembalikan hitungan 2 dan threshold 127 setelah `-`; simpan dan keluar berhasil | Backend Agg noninteraktif, bukan pengujian perangkat mouse/keyboard pada jendela desktop |

Unit test meliputi jumlah/luas kontur, citra kosong dan threshold, koordinat global ROI, pengecualian batas, filter luas dan inversi, parameter tidak valid, isi ekspor termasuk hasil kosong, pemisahan mask biner/bernomor, dan interaksi GUI tersimulasi.

Perintah reproduksi unit test:

```bash
"/home/miq/Documents/ISV/Project ISV/Project/.venv/bin/python" \
  -m unittest discover -s "/home/miq/Documents/ISV/Project ISV/Project" -v
```

Perintah reproduksi sampel (menulis ulang sampel dan hasil montage):

```bash
"/home/miq/Documents/ISV/Project ISV/Project/.venv/bin/python" \
  "/home/miq/Documents/ISV/Project ISV/Project/prepare_samples.py"
```

Hasil CLI verifikasi tersimpan di `/home/miq/Documents/ISV/Project ISV/Project/outputs/reverification`: `overlay.png`, `mask.png`, `mask_numbered.png`, `binary.png`, `histogram.png`, `particles.csv`, dan `summary.json`.

## Kesesuaian dengan kebutuhan tugas

| Ketentuan | Status | Bukti / kekurangan |
| --- | --- | --- |
| Pendekatan klasik deterministik | Terpenuhi pada kode yang diperiksa | Grayscale, threshold, kontur eksternal; tidak ada model pre-trained pada kode proyek |
| Penghitungan dan pengelompokan luas | Terverifikasi terbatas | Luas kontur px² dan histogram; belum validasi luas fisik |
| Mask partikel bernomor | Diperbaiki dan diuji | Sebelumnya nomor hanya pada overlay; kini panel mask dan ekspor `mask_numbered.png` bernomor, mask biner tetap terpisah |
| Histogram distribusi | Terverifikasi terbatas | Ekspor PNG dan histogram UI; menggunakan objek yang diterima |
| ROI dengan mouse | Callback lulus | Interaksi desktop manual masih perlu diuji |
| Threshold dengan keyboard | Callback lulus | Interaksi desktop manual masih perlu diuji |
| Rekayasa optik 20% | Belum dibuktikan | Belum ada foto setup HP, spesifikasi sensor, jarak/pencahayaan atau evaluasi pengkondisian citra |
| Ekstraksi fitur 25% | Sebagian | Deteksi dasar teruji; robustness terhadap fluktuasi minor fisik belum diuji |
| Kalibrasi 25% | Belum | Belum ada konversi mm², acuan fisik, galat ukuran, atau standar deviasi eksperimen |
| UI 15% | Sebagian | Mask bernomor dan histogram ada; besaran fisik serta keterbacaan desktop manual belum dibuktikan |
| Laporan dan demo 15% | Belum | Belum ada PDF akhir, bookmark, pemeriksaan 8 halaman inti, diagram blok final, atau video demo |
| Sumber internet | Sebagian | Sumber dan permintaan sitasi tersedia di data/dokumentasi; belum dimasukkan dalam laporan akhir, kelayakan mengganti eksperimen fisik tidak diasumsikan |
| Administrasi | Belum diverifikasi | Nomor kelompok, nama 4–5 anggota, pembagian tugas aktual, dan jadwal UAS belum tersedia |

## Temuan dan perubahan terbatas

1. **Mask belum bernomor:** diperbaiki di kode dan ditambahkan regression test. Mask biner asli tetap dipertahankan.
2. **Uji GUI sebelumnya tidak tersimpan sebagai unit test:** simulasi ROI, threshold, simpan, reset, dan keluar kini dapat dijalankan ulang melalui unittest.
3. **Pemeriksaan ekspor sebelumnya hanya mengecek keberadaan file:** kini jumlah baris CSV dibandingkan dengan objek pada JSON dan status satuan/kalibrasi diperiksa.
4. **Persyaratan resmi dan pilihan internal perlu dibedakan:** `RULES.md` memisahkan keduanya; kamera real-time tidak dinyatakan sebagai kewajiban resmi Topik 10.

## Batasan yang tetap berlaku

- Luas menggunakan kontur eksternal; lubang internal tidak dikurangi. Piksel mask terisi tidak identik dengan luas geometri kontur.
- Partikel bersentuhan dapat menjadi satu kontur; butir terpotong ROI dikecualikan setelah filter luas.
- Threshold global belum diuji pada foto HP dengan bayangan atau latar tidak seragam.
- Tidak ada ground truth mask untuk membuktikan akurasi segmentasi; satu objek terdeteksi tidak membuktikan batas objek tepat.
- Nilai default bukan hasil optimasi atau jaminan performa pada sampel lain.
- Penyimpanan pada folder keluaran yang sama menimpa berkas sebelumnya.
- Arsip, data sampel, dan keluaran diabaikan Git. Arsip Kaggle masih diperlukan untuk menjalankan ulang persiapan sampel.
- Lisensi redistribusi belum diverifikasi dalam audit ini.

## Prioritas berikutnya

1. Periksa UI pada desktop secara manual menggunakan montage dan gambar asli.
2. Dokumentasikan setup kamera HP dan ambil foto beras terpisah bersama acuan ukuran sebidang.
3. Uji pipeline pada foto nyata, kemudian tambahkan kalibrasi yang tervalidasi.
4. Kumpulkan pengukuran berulang, galat, standar deviasi, dan uji perubahan kecil pencahayaan/posisi.
5. Susun PDF dan video demo sesuai `RULES.md`; jangan menyebut proyek selesai sebelum bukti tersebut tersedia.