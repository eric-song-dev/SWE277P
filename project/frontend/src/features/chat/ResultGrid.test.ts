import { describe, expect, it } from "vitest";
import { columnsFor } from "./ResultGrid";

describe("columnsFor", () => {
  it("right-aligns columns whose non-null values are all numbers", () => {
    const cols = columnsFor({
      columns: ["school", "people"],
      rows: [["Eng", 7], [null, 3]],
      row_count: 2,
      truncated: false,
    });
    expect(cols[0].align).not.toBe("right");
    expect(cols[1].align).toBe("right");
    expect(cols[1].headerAlign).toBe("right");
    expect(cols[1].cellClassName).toBeTruthy();
  });

  it("does not treat an all-null column as numeric", () => {
    const [col] = columnsFor({ columns: ["x"], rows: [[null], [null]], row_count: 2, truncated: false });
    expect(col.align).not.toBe("right");
  });

  it("does not treat a column mixing '7' and 7 as numeric", () => {
    const [col] = columnsFor({ columns: ["x"], rows: [["7"], [7]], row_count: 2, truncated: false });
    expect(col.align).not.toBe("right");
  });
});
