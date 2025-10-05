from __future__ import annotations
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from pathlib import Path
import json # FIXED: Changed from orjson
from collections import Counter

def band_bar(scored_path: str, out_path: str):
    counts = Counter()
    # FIXED: Changed from "rb" to "r" for text mode
    with open(scored_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            # json.loads handles strings from "r" mode correctly
            row = json.loads(line) 
            counts[row.get("band", "P4")] += 1
            
    bands = ["P1", "P2", "P3", "P4"]
    vals = [counts.get(b, 0) for b in bands]

    plt.figure(figsize=(6, 4))
    plt.bar(bands, vals, color=['red', 'orange', 'yellow', 'green'])
    plt.title("Indicators per Band")
    plt.xlabel("Band")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"[ok] saved chart -> {out_path}")

def feedback_pie(feedback_path: str, out_path: str):
    if not Path(feedback_path).exists():
        return
    
    # FIXED: Changed from read_bytes() to read_text()
    fb = json.loads(Path(feedback_path).read_text(encoding="utf-8"))
    counts = Counter(x.get("decision", "unknown") for x in fb)

    if counts:
        labels, sizes = zip(*counts.items())
        plt.figure(figsize=(5, 5))
        plt.pie(sizes, labels=labels, autopct="%1.1f%%")
        plt.title("Feedback Outcomes")
        plt.tight_layout()
        plt.savefig(out_path)
        plt.close()
        print(f"[ok] saved pie chart -> {out_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        raise SystemExit("usage: python -m src.reporting.charts <band_bar|feedback_pie> <input> <output>")

    if sys.argv[1] == "band_bar":
        band_bar(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "feedback_pie":
        feedback_pie(sys.argv[2], sys.argv[3])
