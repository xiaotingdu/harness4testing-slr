"""Generate the half-year and outlet distribution panels for the corpus."""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
BIB = ROOT / "references.bib"
MATCHES = ROOT / "tables" / "task_feature_bib_matches.csv"
CORPUS = ROOT / "tools" / "landscape_review_129.csv"
HALF_YEARS = ROOT / "tools" / "publication_halfyear_129.csv"
MAPPING = ROOT / "tools" / "publication_venue_mapping.csv"
OUTPUT = ROOT / "figures" / "corpus_distribution_panels.pdf"
PREVIEW = ROOT / "figures" / "corpus_distribution_panels_preview.png"

# Counts of the 154-paper corpus (search_redo_2026/10_recompute/tables:
# half_year_distribution.csv and venue_counts.csv; PACMSE papers are split into
# FSE and ISSTA by their Crossref issue metadata).
FIGURE_HALF_YEARS = {
    "2024 H1": 6,
    "2024 H2": 13,
    "2025 H1": 26,
    "2025 H2": 38,
    "2026 H1": 71,
}
FIGURE_VENUES = [
    ("FSE", 32),
    ("ICSE", 30),
    ("ASE", 25),
    ("ISSTA", 20),
    ("TOSEM", 15),
    ("TSE", 14),
    ("ICST", 4),
    ("IST", 3),
    ("ASE (journal)", 2),
    ("EMSE", 2),
    ("IET Software", 2),
    ("JSS", 2),
    ("SANER", 2),
    ("ICSME", 1),
]


def parse_field(body: str, name: str) -> str:
    match = re.search(
        rf"\b{name}\s*=\s*[{{\"](.*?)[}}\"]\s*,?\s*\n",
        body,
        re.S | re.I,
    )
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""


def parse_bibtex(keys: set[str]) -> dict[str, dict[str, str]]:
    text = BIB.read_text(encoding="utf-8")
    entries: dict[str, dict[str, str]] = {}
    for match in re.finditer(r"@(\w+)\s*\{\s*([^,]+),(.*?)(?=\n@|\Z)", text, re.S):
        entry_type, key, body = (
            match.group(1).lower(),
            match.group(2).strip(),
            match.group(3),
        )
        if key not in keys:
            continue
        entries[key] = {
            "entry_type": entry_type,
            "journal": parse_field(body, "journal"),
            "booktitle": parse_field(body, "booktitle"),
            "number": parse_field(body, "number"),
            "note": parse_field(body, "note"),
            "url": parse_field(body, "url"),
        }
    if set(entries) != keys:
        raise ValueError(f"Missing BibTeX entries: {sorted(keys - set(entries))}")
    return entries


def normalise_venue(entry: dict[str, str]) -> tuple[str, str]:
    """Prefer a formal publication outlet over an accompanying arXiv version."""
    journal = entry["journal"]
    booktitle = entry["booktitle"]
    raw = journal or booktitle
    value = raw.lower()
    preprint_metadata = (entry["note"] + " " + entry["url"]).lower()

    if "arxiv" in value or (
        not raw and ("arxiv" in preprint_metadata or entry["entry_type"] == "misc")
    ):
        return raw or "arXiv", "arXiv"
    if "transactions on software engineering and methodology" in value:
        return raw, "TOSEM"
    if "transactions on software engineering" in value:
        return raw, "TSE"
    if "empirical software engineering" in value:
        return raw, "EMSE"
    if journal.lower() == "automated software engineering":
        return raw, "ASE (journal)"
    if booktitle == "ASE" or "conference on automated software engineering" in value:
        return raw, "ASE"
    if booktitle == "ISSTA" or "software testing and analysis" in value:
        return raw, "ISSTA"
    if booktitle == "ICSE" or "international conference on software engineering" in value:
        return raw, "ICSE"
    if booktitle == "FSE" or "(fse)" in value or "foundations of software engineering" in value:
        return raw, "FSE"
    if "proceedings of the acm on software engineering" in value:
        issue = entry["number"].upper()
        if issue in {"FSE", "ICSE", "ISSTA"}:
            return raw, issue
        return raw, "PACMSE"
    if "information and software technology" in value:
        return raw, "IST"
    if "journal of systems and software" in value:
        return raw, "JSS"
    if booktitle == "QRS" or "quality, reliability, and security" in value:
        return raw, "QRS"
    if booktitle == "ICSME" or "software maintenance and evolution" in value:
        return raw, "ICSME"
    if booktitle == "ICST" or "software testing, verification and validation" in value:
        return raw, "ICST"
    if "iet software" in value:
        return raw, "IET Software"
    if "ieee software" in value:
        return raw, "IEEE Software"
    if "journal of software: evolution and process" in value:
        return raw, "JSEP"
    if "software quality journal" in value:
        return raw, "Software Quality Journal"
    if "data science in cyberspace" in value:
        return raw, "DSC"
    if "big data" in value:
        return raw, "BigData"
    if "computer science and intelligent control" in value:
        return raw, "ISCSIC"
    if "computer systems and applications" in value:
        return raw, "AICCSA"
    return raw or entry["entry_type"], raw or entry["entry_type"]


def load_venue_counts() -> Counter[str]:
    with MATCHES.open(encoding="utf-8-sig", newline="") as handle:
        matched_rows = list(csv.DictReader(handle))
    if len(matched_rows) != 128 or len({row["dedup_id"] for row in matched_rows}) != 128:
        raise ValueError("Expected 128 unique corpus-to-BibTeX matches")

    bib_entries = parse_bibtex({row["bib_key"] for row in matched_rows})
    mapping_rows: list[dict[str, str]] = []
    for row in matched_rows:
        raw, venue = normalise_venue(bib_entries[row["bib_key"]])
        mapping_rows.append(
            {
                "dedup_id": row["dedup_id"],
                "bib_key": row["bib_key"],
                "raw_outlet": raw,
                "normalised_outlet": venue,
            }
        )

    with MAPPING.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("dedup_id", "bib_key", "raw_outlet", "normalised_outlet"),
        )
        writer.writeheader()
        writer.writerows(sorted(mapping_rows, key=lambda row: row["dedup_id"]))

    counts = Counter(row["normalised_outlet"] for row in mapping_rows)
    if sum(counts.values()) != 128:
        raise ValueError("Publication-outlet counts do not sum to 128")
    return counts


def load_half_year_counts() -> Counter[str]:
    with HALF_YEARS.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 128 or len({row["dedup_id"] for row in rows}) != 128:
        raise ValueError("Expected 128 unique publication-date records")
    counts = Counter(row["half_year"] for row in rows)
    expected = {
        "2024 H1": 7,
        "2024 H2": 22,
        "2025 H1": 23,
        "2025 H2": 43,
        "2026 H1": 33,
    }
    if dict(counts) != expected:
        raise ValueError(f"Unexpected half-year corpus counts: {counts}")
    return counts


def main() -> None:
    if sum(FIGURE_HALF_YEARS.values()) != 154 or sum(
        count for _, count in FIGURE_VENUES
    ) != 154:
        raise ValueError("Figure panel counts must each sum to 154")

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans"],
            "font.size": 8.5,
            "pdf.fonttype": 42,
            "axes.unicode_minus": False,
        }
    )

    fig, (year_ax, venue_ax) = plt.subplots(
        1,
        2,
        figsize=(7.55, 3.26),
        gridspec_kw={"width_ratios": (1.12, 1)},
    )

    half_years = [
        "2024\nH1",
        "2024\nH2",
        "2025\nH1",
        "2025\nH2",
        "2026\nH1",
    ]
    half_year_values = [
        FIGURE_HALF_YEARS[key]
        for key in ("2024 H1", "2024 H2", "2025 H1", "2025 H2", "2026 H1")
    ]
    # Perceptually uniform sequential colours (viridis) encode the time order.
    year_colours = [plt.get_cmap("viridis")(x) for x in (0.20, 0.35, 0.50, 0.65, 0.80)]
    year_bars = year_ax.bar(
        half_years,
        half_year_values,
        width=0.66,
        color=year_colours,
        edgecolor="white",
        linewidth=0.8,
    )
    for bar, value in zip(year_bars, half_year_values):
        year_ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 1.1,
            str(value),
            ha="center",
            va="bottom",
            fontsize=8.0,
        )
    year_ax.set_ylabel("Number of included papers")
    year_ax.set_ylim(0, 80)
    year_ax.set_yticks([0, 20, 40, 60, 80])
    year_ax.yaxis.grid(True, color="#E6E6E6", linewidth=0.7)
    year_ax.set_axisbelow(True)
    year_ax.spines[["top", "right"]].set_visible(False)
    year_ax.tick_params(axis="x", length=0)

    venue_labels = [venue for venue, _ in FIGURE_VENUES][::-1]
    venue_values = [count for _, count in FIGURE_VENUES][::-1]
    # Colour-blind-safe categorical colours (Okabe-Ito) separate conferences
    # from journals.
    journals = {"TOSEM", "TSE", "IST", "ASE (journal)", "EMSE", "IET Software", "JSS"}
    conference_colour, journal_colour = "#0072B2", "#E69F00"
    venue_colours = [journal_colour if label in journals else conference_colour
                     for label in venue_labels]
    venue_bars = venue_ax.barh(
        venue_labels,
        venue_values,
        height=0.66,
        color=venue_colours,
        edgecolor="white",
        linewidth=0.8,
    )
    from matplotlib.patches import Patch
    venue_ax.legend(
        handles=[Patch(color=conference_colour, label="Conference"),
                 Patch(color=journal_colour, label="Journal")],
        loc="lower right", frameon=False, fontsize=7.0,
    )
    venue_ax.set_xlabel("Number of included papers")
    venue_ax.set_xlim(0, max(venue_values) + 4)
    venue_ax.xaxis.grid(True, color="#E6E6E6", linewidth=0.7)
    venue_ax.set_axisbelow(True)
    venue_ax.spines[["top", "right"]].set_visible(False)
    venue_ax.spines[["left", "bottom"]].set_color("#555555")
    venue_ax.tick_params(axis="y", labelsize=6.6)
    venue_ax.tick_params(axis="x", labelsize=7.2)
    for bar, value in zip(venue_bars, venue_values):
        venue_ax.text(
            bar.get_width() + 0.35,
            bar.get_y() + bar.get_height() / 2,
            str(value),
            va="center",
            ha="left",
            fontsize=6.8,
            color="#303030",
        )

    fig.tight_layout(pad=0.45, w_pad=1.35, rect=(0, 0.065, 1, 1))
    for axis, panel_label in (
        (year_ax, "(a) Publication half-year"),
        (venue_ax, "(b) Publication outlet"),
    ):
        position = axis.get_position()
        fig.text(
            (position.x0 + position.x1) / 2,
            0.012,
            panel_label,
            ha="center",
            va="bottom",
            fontsize=9.0,
        )

    fig.savefig(OUTPUT, bbox_inches="tight", pad_inches=0.02)
    fig.savefig(PREVIEW, dpi=220, bbox_inches="tight", pad_inches=0.02)
    print(OUTPUT.name)
    print("Publication outlets:", FIGURE_VENUES)


if __name__ == "__main__":
    main()
