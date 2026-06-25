from __future__ import annotations

from io import BytesIO
import pandas as pd


def make_excel_workbook(sheets: dict[str, pd.DataFrame]) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, df in sheets.items():
            safe_name = name[:31].replace("/", "-").replace("\\", "-")
            df.to_excel(writer, index=False, sheet_name=safe_name)
            ws = writer.book[safe_name]
            for col in ws.columns:
                max_len = 0
                letter = col[0].column_letter
                for cell in col:
                    try:
                        max_len = max(max_len, len(str(cell.value)))
                    except Exception:
                        pass
                ws.column_dimensions[letter].width = min(max_len + 2, 42)
    return buffer.getvalue()
