from __future__ import annotations
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import json # FIXED: Changed from orjson
from pathlib import Path
from datetime import datetime

def make_pdf(summary_json: str, chart_paths: dict, out_path: str):
    styles = getSampleStyleSheet()
    story = []
    doc = SimpleDocTemplate(out_path, pagesize=A4)
    
    # FIXED: Changed from read_bytes() to read_text()
    summary = json.loads(Path(summary_json).read_text(encoding="utf-8"))

    # Title
    story.append(Paragraph("Threat Intel Daily Report", styles["Title"]))
    story.append(Spacer(1, 12))

    # Date
    story.append(Paragraph(f"Report Date: {datetime.now().strftime('%Y-%m-%d')}", styles["Normal"]))
    story.append(Spacer(1, 12))

    # Stats
    story.append(Paragraph(f"Total indicators processed: {summary['total']}", styles["Normal"]))
    story.append(Paragraph(f"Band distribution: P1={summary['bands'].get('P1', 0)}, P2={summary['bands'].get('P2', 0)}, P3={summary['bands'].get('P3', 0)}, P4={summary['bands'].get('P4', 0)}", styles["Normal"]))

    # Average scores
    avg_text = ", ".join([f"{k}={round(v, 3)}" for k, v in summary.get('avg_score', {}).items()])
    story.append(Paragraph(f"Average scores: {avg_text}", styles["Normal"]))

    story.append(Paragraph(f"Enrichment coverage: {summary['enrichment_coverage']*100:.1f}%", styles["Normal"]))

    if "feedback" in summary:
        fb_text = ", ".join([f"{k}={v}" for k, v in summary['feedback'].items()])
        story.append(Paragraph(f"Feedback outcomes: {fb_text}", styles["Normal"]))

    story.append(Spacer(1, 24))

    # Add charts
    for label, path in chart_paths.items():
        if path and Path(path).exists():
            story.append(Paragraph(label, styles["Heading2"]))
            img = Image(path, width=4*inch, height=3*inch)
            story.append(img)
            story.append(Spacer(1, 24))

    doc.build(story)
    print(f"[ok] pdf report -> {out_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        raise SystemExit("usage: python -m src.reporting.pdf_report <summary.json> <chart1.png> <out.pdf>")
    make_pdf(sys.argv[1], {"Band Distribution": sys.argv[2]}, sys.argv[3])
