"""The analysis built on this computer when results are not shared with the LLM (spec 7.1)."""

from app.chat.executor import QueryResult


def local_summary(result: QueryResult) -> str:
    if result.row_count == 0:
        return "No matching records."
    if result.row_count == 1 and len(result.columns) == 1:
        value = result.rows[0][0]
        return f"{result.columns[0]}: {'NULL' if value is None else value}"
    if result.truncated:  # row_count is the display cap; the true total is not known
        return f"More than {result.row_count} rows (showing the first {result.row_count})"
    return f"{result.row_count} row{'' if result.row_count == 1 else 's'}"
