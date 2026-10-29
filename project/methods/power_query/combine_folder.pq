// Menggabungkan semua file layout 1 dalam satu folder dengan fungsi L1_v1 (jadikan L1_v1.pq sebagai fungsi fnLayout1(Param_FilePath, Param_Year, Param_FirstValueCol)).
// Belum dijalankan. Setiap layout lain membutuhkan fungsi sendiri; Power Query tidak memilih template secara otomatis.
let
    Folder = Folder.Files(Param_FolderPath),
    OnlyL1 = Table.SelectRows(Folder, each Text.StartsWith([Name], "laporan_G1_")),
    WithData = Table.AddColumn(OnlyL1, "data", each fnLayout1([Folder Path] & [Name], Param_Year, if [Name] >= "laporan_G1_2026-06" then 7 else 5)),
    Combined = Table.Combine(WithData[data])
in
    Combined
