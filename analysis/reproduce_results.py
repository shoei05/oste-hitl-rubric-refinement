#!/usr/bin/env python3
"""Validate the public score data and reproduce manuscript tables/figures."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import statistics


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
FIGURES = ROOT / "generated" / "figures"

VERSIONS = {
    "v2": "Second revised rubric",
    "v3": "Strict third rubric",
}

EXPECTED = {
    "v2": {"distribution": {1: 58, 2: 20, 3: 314, 4: 2047, 5: 3961}, "imputed": 68},
    "v3": {"distribution": {1: 190, 2: 82, 3: 261, 4: 3343, 5: 2524}, "imputed": 37},
}

CONSTRUCTS = {
    "U13": "Learner-centered feedback",
    "U17": "Consultation climate",
    "U9": "Tailoring principles",
    "U3": "Eliciting learner reasoning",
    "U14": "Specific detailed feedback",
    "U16": "Safe learning climate",
    "U18": "Respect",
    "U20": "Overall feedback ability",
    "U7": "Prioritizing urgent diagnoses",
    "U19": "Teaching enthusiasm",
    "U2": "Deepening questions",
    "U10": "Key points with rationale",
}


def format_half_up(value: float, places: int) -> str:
    quantum = Decimal("1").scaleb(-places)
    return str(Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP))


def read_scores(version: str) -> list[dict[str, object]]:
    path = DATA / f"ai_item_scores_{version}.csv"
    rows: list[dict[str, object]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for raw in csv.DictReader(handle):
            rows.append(
                {
                    "video_id": raw["video_id"],
                    "ai_run": raw["ai_run"],
                    "item_id": raw["item_id"],
                    "score": int(raw["score"]),
                    "imputed": raw["imputed"] == "1",
                    "imputation_reason": raw["imputation_reason"],
                }
            )
    return rows


def validate(rows_by_version: dict[str, list[dict[str, object]]]) -> None:
    for version, rows in rows_by_version.items():
        assert len(rows) == 6400, f"{version}: expected 6400 rows"
        assert len({r["video_id"] for r in rows}) == 64, f"{version}: expected 64 video IDs"
        assert {r["ai_run"] for r in rows} == {f"R{i}" for i in range(1, 6)}
        assert {r["item_id"] for r in rows} == {f"U{i}" for i in range(1, 21)}
        triples = {(r["video_id"], r["ai_run"], r["item_id"]) for r in rows}
        assert len(triples) == 6400, f"{version}: duplicate video/run/item combination"
        distribution = Counter(int(r["score"]) for r in rows)
        assert dict(sorted(distribution.items())) == EXPECTED[version]["distribution"]
        imputed = sum(bool(r["imputed"]) for r in rows)
        assert imputed == EXPECTED[version]["imputed"]
        assert all(1 <= int(r["score"]) <= 5 for r in rows)
        assert all(str(r["video_id"]).startswith("V") for r in rows)


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows_by_version: dict[str, list[dict[str, object]]]):
    table2 = []
    figure2 = []
    item_stats: dict[str, dict[str, dict[str, float]]] = defaultdict(dict)

    for version, label in VERSIONS.items():
        rows = rows_by_version[version]
        values = [int(r["score"]) for r in rows]
        counts = Counter(values)
        table2.append(
            {
                "rubric_version": label,
                "model_access": "Gemini 2.5 Flash via OpenRouter",
                "video_runs": 320,
                "item_scores": 6400,
                "mean": format_half_up(statistics.mean(values), 2),
                "sd": format_half_up(statistics.stdev(values), 2),
                "score_1_n": counts[1],
                "score_1_pct": f"{counts[1] / 64:.1f}",
                "score_2_n": counts[2],
                "score_2_pct": f"{counts[2] / 64:.1f}",
                "score_3_n": counts[3],
                "score_3_pct": f"{counts[3] / 64:.1f}",
                "score_4_n": counts[4],
                "score_4_pct": f"{counts[4] / 64:.1f}",
                "score_5_n": counts[5],
                "score_5_pct": f"{counts[5] / 64:.1f}",
                "score_4_or_5_pct": f"{(counts[4] + counts[5]) / 64:.1f}",
            }
        )
        for score in range(1, 6):
            figure2.append(
                {
                    "rubric_version": version,
                    "score": score,
                    "count": counts[score],
                    "percent": f"{counts[score] / 64:.1f}",
                }
            )
        grouped: dict[str, list[int]] = defaultdict(list)
        for row in rows:
            grouped[str(row["item_id"])].append(int(row["score"]))
        for item, values_for_item in grouped.items():
            item_stats[item][version] = {
                "mean": statistics.mean(values_for_item),
                "score_5_pct": 100 * values_for_item.count(5) / len(values_for_item),
            }

    all_items = []
    for item in sorted(item_stats, key=lambda x: int(x[1:])):
        v2 = item_stats[item]["v2"]
        v3 = item_stats[item]["v3"]
        all_items.append(
            {
                "item_id": item,
                "v2_mean": f"{v2['mean']:.3f}",
                "v3_mean": f"{v3['mean']:.3f}",
                "mean_change_v3_minus_v2": f"{v3['mean'] - v2['mean']:.3f}",
                "v2_score_5_pct": f"{v2['score_5_pct']:.1f}",
                "v3_score_5_pct": f"{v3['score_5_pct']:.1f}",
                "score_5_change_pp": f"{v3['score_5_pct'] - v2['score_5_pct']:.1f}",
            }
        )

    ranked = sorted(all_items, key=lambda r: float(r["mean_change_v3_minus_v2"]))
    table3 = []
    for row in ranked[:12]:
        table3.append({"construct": CONSTRUCTS[str(row["item_id"])], **row})
    return table2, table3, all_items, figure2


def make_figures(figure2_rows, item_rows):
    import matplotlib.pyplot as plt

    FIGURES.mkdir(parents=True, exist_ok=True)
    by_version = defaultdict(dict)
    for row in figure2_rows:
        by_version[row["rubric_version"]][int(row["score"])] = float(row["percent"])
    scores = list(range(1, 6))
    width = 0.36
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    ax.bar([x - width / 2 for x in scores], [by_version["v2"][x] for x in scores], width, label="Second revised")
    ax.bar([x + width / 2 for x in scores], [by_version["v3"][x] for x in scores], width, label="Strict third")
    ax.set(xlabel="Score", ylabel="Item scores (%)", xticks=scores)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES / "figure2_score_distribution_reproduced.png", dpi=300)
    plt.close(fig)

    ranked = sorted(item_rows, key=lambda r: float(r["mean_change_v3_minus_v2"]))
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    ax.barh([r["item_id"] for r in ranked], [float(r["mean_change_v3_minus_v2"]) for r in ranked])
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set(xlabel="Mean change (strict third minus second revised)", ylabel="Rubric item")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(FIGURES / "figure3_item_mean_decreases_reproduced.png", dpi=300)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    rows_by_version = {version: read_scores(version) for version in VERSIONS}
    validate(rows_by_version)
    if args.validate_only:
        print("Validation passed: 2 x 6400 item scores; anonymized IDs; expected distributions and imputations.")
        return

    table2, table3, all_items, figure2 = summarize(rows_by_version)
    write_csv(RESULTS / "table2_score_distribution.csv", table2, list(table2[0]))
    write_csv(RESULTS / "table3_item_decreases.csv", table3, list(table3[0]))
    write_csv(RESULTS / "figure2_score_distribution_source.csv", figure2, list(figure2[0]))
    write_csv(RESULTS / "figure3_item_mean_decreases_source.csv", all_items, list(all_items[0]))
    make_figures(figure2, all_items)
    print("Validation and reproduction completed.")


if __name__ == "__main__":
    main()
