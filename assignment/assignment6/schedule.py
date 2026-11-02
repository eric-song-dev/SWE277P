"""Draw the Gantt and burndown charts from WBS.xlsx and print the schedule totals.

Run from this folder:  uv run --with matplotlib --with openpyxl python schedule.py

Edit WBS.xlsx (Actual Time, Status, dates), set TODAY, and re-run at each sprint planning.
"""
import datetime as dt
import re
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from openpyxl import load_workbook
from openpyxl.chart import LineChart, Reference

WBS_FILE = "WBS.xlsx"
TODAY = dt.date(2026, 11, 2)          # last day of Sprint 1; the re-plan date
START, END = dt.date(2026, 9, 24), dt.date(2026, 12, 7)
BASELINE_TOTAL = 272                  # WBS version 1 (Assignment 5) total estimate
SPRINTS = [
    ("Sprint 0", dt.date(2026, 9, 24), dt.date(2026, 10, 19)),
    ("Sprint 1", dt.date(2026, 10, 20), dt.date(2026, 11, 2)),
    ("Sprint 2", dt.date(2026, 11, 3), dt.date(2026, 11, 16)),
    ("Sprint 3", dt.date(2026, 11, 17), dt.date(2026, 12, 7)),
]
HOLIDAYS = [("Veterans Day", dt.date(2026, 11, 11), dt.date(2026, 11, 11)),
            ("Thanksgiving", dt.date(2026, 11, 26), dt.date(2026, 11, 27))]
PEOPLE = ["Brandon Lau", "Jennifer Sun", "Molly Tran", "Zhenyu Song"]

# Reference palette (validated): owners in fixed categorical order; status as one blue ramp.
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
SURFACE, GRID, AXIS, BAND = "#fcfcfb", "#e1e0d9", "#c3c2b7", "#f3f2ee"
OWNER_COLOR = {"Brandon Lau": "#2a78d6", "Jennifer Sun": "#eb6834", "Molly Tran": "#1baf7a",
               "Zhenyu Song": "#eda100", "All team": "#e87ba4"}
STATUS_COLOR = {"Done": "#184f95", "In progress": "#3987e5", "Planned": "#86b6ef"}

plt.rcParams.update({
    "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 9, "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": INK2, "axes.edgecolor": AXIS,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
})


# ---------- read the WBS ----------

def as_date(v):
    return v.date() if isinstance(v, dt.datetime) else v


def read_wbs():
    ws = load_workbook(WBS_FILE)["WBS"]
    rows, sprint = [], None
    for r in ws.iter_rows(min_row=3, values_only=True):
        key = str(r[0]) if r[0] is not None else ""
        if key.startswith("Sprint "):
            sprint = int(key.split()[1].rstrip(":"))
            continue
        if not re.fullmatch(r"1(\.\d+)+", key):
            continue
        rows.append(dict(id=key, desc=r[1], est=r[3], act=r[4], owner=r[5],
                         start=as_date(r[6]), finish=as_date(r[7]), status=r[8],
                         label=r[9], sprint=sprint))
    ids = {x["id"] for x in rows}
    for x in rows:
        x["leaf"] = not any(i.startswith(x["id"] + ".") for i in ids)
        x["top"] = x["id"].count(".") == 1
        x["est"] = x["est"] if isinstance(x["est"], (int, float)) else None
        x["act"] = x["act"] if isinstance(x["act"], (int, float)) else None
    return rows


def days(a, b):
    d, out = a, []
    while d <= b:
        out.append(d)
        d += dt.timedelta(days=1)
    return out


# ---------- numbers ----------

def summarize(rows):
    leaves = [x for x in rows if x["leaf"]]
    done = [x for x in leaves if x["status"] == "Done"]
    open_ = [x for x in leaves if x["status"] != "Done" and x["est"]]
    print("Sprint | estimate | actual | unplanned actual | carried over (est)")
    for s in range(4):
        ls = [x for x in leaves if x["sprint"] == s]
        est = sum(x["est"] or 0 for x in ls)
        act = sum(x["act"] or 0 for x in ls)
        unpl = sum(x["act"] or 0 for x in ls if x["est"] is None)
        car = sum(x["est"] for x in ls if x["status"] == "Carried over")
        print(f"  {s} | {est:g} | {act:g} | {unpl:g} | {car:g}")

    burned = sum(x["est"] or 0 for x in done)
    actual = sum(x["act"] or 0 for x in leaves)
    remaining = sum(x["est"] for x in open_)
    elapsed = (TODAY - START).days + 1
    rate = burned / elapsed
    finish = TODAY + dt.timedelta(days=round(remaining / rate))
    need = remaining / ((END - TODAY).days)
    print(f"done estimate {burned:g} h, actual to date {actual:g} h "
          f"(x{actual / burned:.2f}), remaining {remaining:g} h")
    print(f"total now {burned + remaining:g} h vs baseline {BASELINE_TOTAL} "
          f"(+{burned + remaining - BASELINE_TOTAL:g})")
    print(f"pace {rate * 7:.1f} h/week over {elapsed} days -> finish {finish}; "
          f"needed {need * 7:.1f} h/week")

    per = defaultdict(lambda: [0.0] * 4)
    for x in leaves:
        hours = x["act"] if x["status"] == "Done" else x["est"]
        if not hours:
            continue
        s = 2 if x["status"] == "Carried over" else x["sprint"]
        owners = PEOPLE if x["owner"] == "All team" else [x["owner"]]
        for p in owners:
            per[p][s] += hours / len(owners)
    print("Person | S0 actual | S1 actual | S2 plan | S3 plan | total")
    for p in PEOPLE:
        v = per[p]
        print(f"  {p} | " + " | ".join(f"{h:g}" for h in v) + f" | {sum(v):g}")
    return dict(burned=burned, remaining=remaining, rate=rate, finish=finish)


def left(x, d):
    """Share of a planned task still to do at the end of day d."""
    if d < x["start"]:
        return 1.0
    return max(0.0, (x["finish"] - d).days / ((x["finish"] - x["start"]).days + 1))


def burndown(rows, s):
    leaves = [x for x in rows if x["leaf"] and x["est"]]
    total = (END - START).days
    out = []
    for d in days(START, max(END, s["finish"])):
        ideal = BASELINE_TOTAL * (1 - (d - START).days / total) if d <= END else None
        actual = plan = forecast = None
        if d <= TODAY:
            actual = BASELINE_TOTAL - sum(x["est"] for x in leaves
                                          if x["status"] == "Done" and x["finish"] <= d)
        if d == TODAY:
            plan = s["remaining"]
        elif d > TODAY:   # planned work burns evenly over each task's dates
            plan = sum(x["est"] * left(x, d) for x in leaves if x["status"] != "Done")
            if d > END:
                plan = None
        if d >= TODAY:
            forecast = max(0.0, s["remaining"] - s["rate"] * (d - TODAY).days)
        out.append((d, ideal, actual, plan, forecast))
    return out


# ---------- charts ----------

def style_axis(ax):
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)


def sprint_bands(ax, lo, hi, label_y):
    for i, (name, a, b) in enumerate(SPRINTS):
        a, b = max(a, lo), min(b, hi)
        if a > b:
            continue
        if i % 2 == 0:
            ax.axvspan(a, b + dt.timedelta(days=1), color=BAND, zorder=0, lw=0)
        ax.text(a + (b - a + dt.timedelta(days=1)) / 2, label_y, name, ha="center",
                va="bottom", color=INK2, fontsize=8.5, fontweight="bold")


def holidays(ax, y, lo, hi, rotation=0):
    for name, a, b in HOLIDAYS:
        if lo <= a <= hi:
            ax.axvspan(a, b + dt.timedelta(days=1), color="#e1e0d9", alpha=0.6, zorder=0, lw=0)
            ax.text(a + (b - a + dt.timedelta(days=1)) / 2, y, name, rotation=rotation,
                    ha="center", va="top", fontsize=7, color=MUTED)


def today_line(ax, y, text="Today (Nov 2)"):
    x = TODAY + dt.timedelta(days=1)
    ax.axvline(x, color=INK2, lw=1, zorder=3)
    ax.text(x, y, " " + text, ha="left", va="top", fontsize=7.5, color=INK2)


def gantt(rows, path, lo, hi, color_of, legend, title, day_ticks):
    n = len(rows)
    fig, ax = plt.subplots(figsize=(10, 0.27 * n + 1.6))
    for i, x in enumerate(rows):
        if x["est"] == 0 and x["start"] == x["finish"] and x["desc"].startswith("Milestone"):
            ax.plot(x["finish"] + dt.timedelta(days=1), i, marker="D", ms=7, color=INK,
                    mec=SURFACE, mew=2, zorder=4, clip_on=False)
            right = x["finish"] < hi - dt.timedelta(days=2)
            ax.annotate(x["finish"].strftime("%b %-d"), xy=(x["finish"] + dt.timedelta(days=1), i),
                        xytext=(9 if right else -9, 0), textcoords="offset points",
                        ha="left" if right else "right", va="center", fontsize=7.5, color=INK2)
            continue
        a, b = x["start"], x["finish"] + dt.timedelta(days=1)
        ax.barh(i, b - a, left=a, height=0.62, color=color_of(x), lw=0, zorder=2)
    ax.set_yticks(range(n))
    ax.set_yticklabels([f"{x['id']}  {x['label']}" for x in rows], fontsize=8)
    ax.set_ylim(n + 0.6, -2.2)
    ax.set_xlim(lo, hi + dt.timedelta(days=1))
    sprint_bands(ax, lo, hi, -1.35)
    holidays(ax, n - 0.3, lo, hi)
    today_line(ax, -0.95)
    if day_ticks:
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%a\n%b %-d"))
    else:
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %-d"))
    ax.grid(axis="x", color=GRID, lw=0.8, zorder=1)
    ax.tick_params(axis="x", labelsize=7.5)
    style_axis(ax)
    ax.spines["bottom"].set_visible(False)
    ax.xaxis.tick_top()
    ax.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=len(legend),
              frameon=False, fontsize=8)
    fig.suptitle(title, x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def draw_burndown(series, s, path):
    fig, ax = plt.subplots(figsize=(10, 4.8))
    d = [r[0] + dt.timedelta(days=1) for r in series]   # value at the end of each day

    def pick(k):
        pts = [(x, r[k]) for x, r in zip(d, series) if r[k] is not None]
        return [p[0] for p in pts], [p[1] for p in pts]

    sprint_bands(ax, START, max(END, s["finish"]), BASELINE_TOTAL * 1.07)
    holidays(ax, BASELINE_TOTAL * 0.98, START, END, rotation=90)
    ax.plot(*pick(1), color=MUTED, lw=2, label="Ideal (baseline 272 h to zero by Dec 7)")
    xs, ys = pick(2)
    xs.append(xs[-1])
    ys.append(s["remaining"])                     # the re-plan jump on Nov 2
    ax.plot(xs, ys, color="#2a78d6", lw=2, solid_capstyle="round", label="Actual remaining")
    ax.plot(*pick(3), color="#2a78d6", lw=2, ls=(0, (4, 2)), label="Plan (task dates in the Gantt)")
    ax.plot(*pick(4), color="#eb6834", lw=2, ls=(0, (1, 2)), label="Forecast at average pace so far")
    ax.plot(xs[-1], ys[-1], "o", ms=8, color="#2a78d6", mec=SURFACE, mew=2, zorder=5)
    ax.plot(xs[-2], ys[-2], "o", ms=8, color="#2a78d6", mec=SURFACE, mew=2, zorder=5)
    today_line(ax, BASELINE_TOTAL * 0.98, "Today (Nov 2)")

    note = dict(fontsize=8, color=INK2)
    mvp = dt.date(2026, 10, 22)
    ax.annotate("MVP built and verified\nOct 20–22 (−53 h)", xy=(mvp, 162), xytext=(dt.date(2026, 10, 3), 120),
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8), **note)
    ax.annotate(f"Re-plan: +{s['burned'] + s['remaining'] - BASELINE_TOTAL:g} h\n"
                f"{ys[-2]:g} → {ys[-1]:g} h", xy=(xs[-1], (ys[-1] + ys[-2]) / 2),
                xytext=(dt.date(2026, 11, 8), 190), arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8), **note)
    ax.annotate(f"{s['finish']:%b %-d}", xy=(s["finish"] + dt.timedelta(days=1), 0),
                xytext=(0, 8), textcoords="offset points", ha="center", **note)

    ax.set_ylim(0, BASELINE_TOTAL * 1.13)
    ax.set_xlim(START, max(END, s["finish"]) + dt.timedelta(days=2))
    ax.set_ylabel("Remaining work (estimated person-hours)")
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %-d"))
    ax.grid(axis="y", color=GRID, lw=0.8)
    style_axis(ax)
    ax.spines["bottom"].set_color(AXIS)
    ax.legend(loc="lower left", frameon=False, fontsize=8)
    fig.suptitle("Project burndown: remaining estimated work, Sep 24 – Dec 7, 2026",
                 x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def write_burndown_sheet(series):
    wb = load_workbook(WBS_FILE)
    if "Burndown" in wb.sheetnames:
        del wb["Burndown"]
    ws = wb.create_sheet("Burndown")
    ws.append(["Date (end of day)", "Ideal", "Actual", "Plan", "Forecast"])
    for d, *vals in series:
        ws.append([d] + [round(v, 1) if v is not None else None for v in vals])
    for c in ws["A"][1:]:
        c.number_format = "mmm d"
    chart = LineChart()
    chart.title, chart.y_axis.title, chart.width, chart.height = "Burndown", "Remaining hours", 24, 12
    chart.add_data(Reference(ws, min_col=2, max_col=5, min_row=1, max_row=ws.max_row), titles_from_data=True)
    chart.set_categories(Reference(ws, min_col=1, min_row=2, max_row=ws.max_row))
    ws.add_chart(chart, "G2")
    wb.save(WBS_FILE)


def main():
    rows = read_wbs()
    s = summarize(rows)

    top = [x for x in rows if x["top"]]
    gantt(top, "images/gantt-project.png", START, END,
          lambda x: STATUS_COLOR[x["status"] if x["status"] in STATUS_COLOR else "In progress"],
          [Patch(color=c, label=k) for k, c in STATUS_COLOR.items()]
          + [Line2D([], [], marker="D", color=INK, ls="", label="Milestone")],
          "Project Gantt chart by deliverable, Sep 24 – Dec 7, 2026", day_ticks=False)

    lo, hi = dt.date(2026, 11, 1), SPRINTS[2][2]
    detail = [x for x in rows if x["leaf"] and (x["sprint"] == 2 or x["status"] == "Carried over")]
    gantt(detail, "images/gantt-sprint2.png", lo, hi,
          lambda x: OWNER_COLOR[x["owner"]],
          [Patch(color=c, label=k) for k, c in OWNER_COLOR.items()]
          + [Line2D([], [], marker="D", color=INK, ls="", label="Milestone")],
          "Sprint 2 Gantt chart by task and owner, Nov 1 – Nov 16, 2026", day_ticks=True)

    series = burndown(rows, s)
    draw_burndown(series, s, "images/burndown.png")
    write_burndown_sheet(series)


if __name__ == "__main__":
    main()
