# Definisi ukuran

- **Sama persis dengan kunci jawaban**: nilai hasil parsing = nilai pada data rapi asli, untuk kunci (tanggal, shift, slot, stasiun, ukuran, metrik) yang sama. Dihitung atas 54.000 sel.
- **Sel tepercaya**: berstatus `ok` atau `fixed`. Tujuan: semua sel tepercaya sama persis dengan kunci jawaban.
- **Sel ditandai**: `flagged` atau `missing`, tercatat di log anomali.
- **Match rate rekonsiliasi**: subtotal yang cocok dibagi seluruh subtotal; dilaporkan sebelum dan sesudah pemulihan.
- **Kejadian yang ditanam terdeteksi**: sel yang benar-benar berubah di file (dicek dengan membaca sel) dan tercatat di log anomali pada file, sheet, dan sel yang sama.
- **Hasil metode (result_match)**: sel kunci jawaban pada file yang diproses yang nilainya sama persis dengan keluaran metode.
- **Jam dihemat per tahun** = laporan per bulan x menit copy-paste per laporan x 12 / 60 (estimated, simulated).
