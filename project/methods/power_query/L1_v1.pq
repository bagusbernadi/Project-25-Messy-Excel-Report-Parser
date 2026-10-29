// Metode Power Query untuk layout 1 (tanggal sebagai kolom, blok PRODUKSI dan REJECT).
// CATATAN: kode ini ditulis mengikuti dokumentasi M tetapi TIDAK dijalankan di Excel pada project ini (tidak ada Excel di lingkungan pengerjaan).
// Parameter: Param_FilePath (teks), Param_Year (angka), Param_FirstValueCol (angka; 5 untuk layout lama, 7 setelah revisi form bulan ke-4).
let
    Source = Excel.Workbook(File.Contents(Param_FilePath), null, false),
    Raw = Source{[Item = "Sheet1", Kind = "Sheet"]}[Data],
    Idx = Table.AddIndexColumn(Raw, "Row", 1, 1, Int64.Type),
    BlockOf = (markerText as text, metricName as text) as table =>
        let
            MarkerRow = Table.SelectRows(Idx, each [Column1] = markerText){0}[Row],
            TotalRow = Table.SelectRows(Idx, each [Row] > MarkerRow and [Column1] <> null and Text.StartsWith(Text.From([Column1]), "TOTAL")){0}[Row],
            HdrRow = Table.SelectRows(Idx, each [Row] = MarkerRow + 1){0},
            Body = Table.SelectRows(Idx, each [Row] > MarkerRow + 1 and [Row] < TotalRow),
            ColNames = Table.ColumnNames(Raw),
            ValueCols = List.Skip(ColNames, Param_FirstValueCol - 1),
            DateCols = List.Select(ValueCols, each Record.Field(HdrRow, _) <> null),
            Keep = Table.SelectColumns(Body, {"Column1", "Column2", "Column3", "Column4", "Row"} & DateCols),
            Renamed = Table.RenameColumns(Keep, {{"Column1", "station"}, {"Column2", "size"}, {"Column3", "shift"}, {"Column4", "slot"}}),
            Unpivot = Table.UnpivotOtherColumns(Renamed, {"station", "size", "shift", "slot", "Row"}, "src_col", "raw"),
            WithDate = Table.AddColumn(Unpivot, "date_text", each Record.Field(HdrRow, [src_col])),
            Typed = Table.AddColumn(WithDate, "date", each #date(Param_Year, Number.FromText(Text.End([date_text], 2)), Number.FromText(Text.Start([date_text], 2))), type date),
            Clean = Table.AddColumn(Typed, "value", each try Number.FromText(Text.Replace(Text.Replace(Text.From([raw]), " btl", ""), ".", "")) otherwise null, Int64.Type),
            Metric = Table.AddColumn(Clean, "metric", each metricName, type text)
        in
            Table.SelectColumns(Metric, {"date", "shift", "slot", "station", "size", "metric", "value", "Row", "src_col"}),
    Result = Table.Combine({BlockOf("PRODUKSI", "produced"), BlockOf("REJECT", "reject")})
in
    Result
