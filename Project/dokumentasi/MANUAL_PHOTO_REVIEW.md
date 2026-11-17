# Pemeriksaan foto manual

## Data yang ditemukan

Tujuh JPEG tersedia di `/home/miq/Documents/ISV/Project ISV/foto`. File asli tidak diedit atau dipindahkan. Lima foto memperlihatkan banyak beras dengan beberapa butir bersentuhan; dua foto memperlihatkan satu butir. Tiga file beresolusi 1528×1528 dan empat file 3056×3056. Tidak terlihat acuan ukuran fisik yang dapat digunakan untuk kalibrasi. Nama file WhatsApp tidak membuktikan apakah gambar masih merupakan file kamera asli tanpa kompresi.

## Hasil deteksi awal — bukan jumlah beras tervalidasi

| Akhiran nama foto | Threshold | Blur | Luas minimum px² | Kontur diterima |
| --- | ---: | ---: | ---: | ---: |
| 19.10.09.jpeg | 150 | 5 | 93 | 112 |
| 19.22.17.jpeg | 85 | 5 | 93 | 125 |
| 19.22.18.jpeg | 85 | 5 | 93 | 127 |
| 19.23.23 (1).jpeg | 110 | 5 | 374 | 166 |
| 19.23.23.jpeg | 110 | 5 | 374 | 169 |
| 19.27.38 (1).jpeg | 150 | 5 | 374 | 1 |
| 19.27.38.jpeg | 150 | 5 | 374 | 1 |

Parameter merupakan titik awal pengembangan yang dipilih setelah pemeriksaan citra, bukan hasil optimasi menggunakan ground truth. Gaussian blur 5×5 digunakan untuk mengurangi tekstur/noise. Luas minimum mengikuti 0,00004 dari jumlah piksel citra, bukan ukuran fisik beras.

Percobaan Otsu pada seluruh gambar menghasilkan 87 dan 78 objek pada dua foto satu butir karena tekstur latar terang ikut terdeteksi. Karena itu auto-threshold tetap opsional, bukan metode yang dianggap selalu benar. Hasil percobaan awal Otsu tidak dijadikan hasil akhir.

Pada lima foto padat, kontur masih dapat menggabungkan beberapa butir. Beberapa area tekstur terang juga lolos filter. **Angka pada tabel bukan hitungan beras final dan tidak boleh disebut akurat.** Dua foto satu butir menghasilkan satu objek yang sesuai pemeriksaan visual, tetapi belum menjadi validasi statistik.

## Cara menggunakan foto nyata

```bash
"/home/miq/Documents/ISV/Project ISV/Project/.venv/bin/python" \
  "/home/miq/Documents/ISV/Project ISV/Project/run_manual_photos.py"
```

- Next/Previous memindahkan foto. Threshold awal per foto dibaca dari `/home/miq/Documents/ISV/Project ISV/Project/dokumentasi/photo_settings.json`; ROI direset.
- Drag ROI mengelilingi area beras untuk menghindari kilau/tekstur di luar area sampel.
- `+/-`: threshold; `[`/`]`: turunkan/naikkan luas minimum; `B`: siklus smoothing 0,3,5,7; `A`: titik awal Otsu opsional.
- Periksa mask dan kontur, bukan hanya angka jumlah. Area terhubung dapat berisi lebih dari satu butir.
- Save menulis subfolder khusus foto berdasarkan nama dan hash path. Menyimpan ulang foto yang sama mengganti ekspor foto tersebut; foto lain tetap dipertahankan.
- Parameter yang diubah manual belum dipersistenkan ke pengaturan awal GUI; hasil Save menyimpan parameter aktual dalam summary JSON.

Hasil batch dan indeks berada di `/home/miq/Documents/ISV/Project ISV/Project/outputs/manual_photos`. `photo_results.csv` merangkum ekspor terkini; `photo_review.json` merekam percobaan batch dan sensitivitas threshold ±10. Pengeditan GUI dan Save tidak memperbarui catatan sensitivitas batch tersebut.

Preview semua foto: `/home/miq/Documents/ISV/Project ISV/Project/dokumentasi/manual_photo_review.png`.

Reproduksi batch:

```bash
"/home/miq/Documents/ISV/Project ISV/Project/.venv/bin/python" \
  "/home/miq/Documents/ISV/Project ISV/Project/process_photos.py" \
  "/home/miq/Documents/ISV/Project ISV/foto" \
  --settings "/home/miq/Documents/ISV/Project ISV/Project/dokumentasi/photo_settings.json"
```

## Pekerjaan validasi berikutnya

1. Tentukan hitungan manual per foto atau ROI beras terpisah; jangan menjumlahkan foto yang mungkin mengambil sampel sama sebagai butir unik.
2. Evaluasi kebutuhan pemisahan butir bersentuhan secara terpisah; versi saat ini belum menerapkannya.
3. Uji pengulangan dan sensitivitas parameter dengan acuan tersebut.
4. Tambahkan acuan panjang sebidang pada pengambilan foto berikutnya untuk kalibrasi; saat ini hanya px².