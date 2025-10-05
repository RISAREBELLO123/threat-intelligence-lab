Threat Intelligence Aggregation Lab
A complete end-to-end SOC pipeline to collect, normalize, enrich, correlate, score, detect, and report on multi-source threat intelligence using safe, reproducible methods.

Table of Contents
Introduction

Objectives & Scope

Installation & Setup

Repository Structure

Pipeline Modules

Running the Pipeline

Data Flow & Artifacts

Troubleshooting

References

Introduction
This repository implements the Threat Intelligence Aggregation Lab for TE V OSINT, mirroring a practical SOC workflow. It covers all stages — aggregation, normalization, enrichment, correlation, detection, and reporting — for a realistic experience in threat intelligence engineering.

Objectives & Scope
Collect threat indicators from 12+ reputable public sources/APIs.

Normalize source data to a compact schema for reasoning and audit.

Enrich feeds with context: reputation, ASN, geo, malware families, ATTCK, CVE, CWE.

Merge and deduplicate overlapping items, preserving provenance.

Build a graph structure to correlate indicators, vulnerabilities, techniques.

Score and prioritize items into P1–P4 with clear breakdowns.

Generate detection rules, replay synthetic logs, and capture feedback.

Produce summary reports, charts, and PDF documentation.

Orchestrate and automate daily pipeline runs and validation.

All code, configs, and results are safe, reproducible, and version-controlled.

Installation & Setup
Clone the repository:

text
git clone https://github.com/RISAREBELLO123/threat-intelligence-lab.git
cd threat-intelligence-lab
Create a Python virtual environment:

text
python3 -m venv .venv
source .venv/bin/activate
Install required dependencies:

text
pip install -r requirements.txt
Configure environment variables:

Copy the template:

text
cp .env.example .env
Edit .env with API keys/tokens for your sources.

Edit configuration files:

Update config/config.yaml with sources, endpoints, and settings.

Provide mapping files under config/mappings as needed.

Repository Structure
Path	Purpose
config/	Source and field mappings, YAML config
data/	Raw, processed, enriched, merged, scored, ticket data
docs/samples/	Example JSONL datasets
src/	Code modules for each pipeline stage
Makefile	Common commands and workflow automation
README.md	Usage instructions and lab outline
.env.example	Template for environment secrets
requirements.txt	Python package dependencies
See the full folder tree for details.

Pipeline Modules
The pipeline includes:

Collection: Fetch indicators from 12+ open sources (e.g., AlienVault OTX, MITRE ATTCK, NVD, CISA KEV, VirusTotal, AbuseIPDB, Shodan, URLhaus, PhishTank, Hybrid Analysis, and more).

Normalization: Convert raw data to a unified schema using mappings.

Enrichment: Add context, reputation, ASN, malware family, and links.

Merging: De-duplicate and combine related indicator data.

Graph Building: Correlate indicators, CVEs, tactics, infrastructure.

Scoring: Prioritize all items into bands P1–P4 with transparent rules.

Detection: Generate Sigma-style rules for high-priority items, simulate logs, and record alerts.

Reporting: Output JSON summaries, charts, and multi-page PDF reports.

Orchestration: Daily runs and playbook automation with tickets for alerts.

Simulation/Validation: Replay safe synthetic logs and validate coverage.

Running the Pipeline
Activate your environment:

text
source .venv/bin/activate
Perform a daily run ("YYYY-MM-DD" is the run date):

text
make daily DATE=YYYY-MM-DD
# Or run scripts individually:
python -m src.collectors.runall YYYY-MM-DD
python -m src.normalizers.normalizeall YYYY-MM-DD
python -m src.enrichment.runall YYYY-MM-DD
python -m src.merge.runmerge YYYY-MM-DD
python -m src.correlation.graphbuild YYYY-MM-DD
python -m src.scoring.runscoring YYYY-MM-DD
python -m src.detection.gensigma data/scored/YYYY-MM-DD.jsonl data/rules/YYYY-MM-DD
python -m src.reporting.summary data/scored/YYYY-MM-DD.jsonl > data/reports/YYYY-MM-DD.summary.json
python -m src.reporting.charts bandbar data/scored/YYYY-MM-DD.jsonl data/reports/YYYY-MM-DD.bands.png
python -m src.reporting.pdfreport data/reports/YYYY-MM-DD.summary.json data/reports/YYYY-MM-DD.bands.png data/reports/YYYY-MM-DD.daily.pdf
For simulation/validation:

text
python -m src.simulation.replay data/rules/YYYY-MM-DD data/simulations/phishingevent.jsonl data/alerts/YYYY-MM-DD.sim.json
python -m src.simulation.coverage data/alerts/YYYY-MM-DD.sim.json data/simulations/phishingevent.jsonl
Automated playbook (escalate P1 alerts to tickets):

text
python -m src.orchestration.playbook data/alerts/YYYY-MM-DD.json data/tickets/YYYY-MM-DD.json
Data Flow & Artifacts
Stage	Path / Example Files
Raw data	data/raw/sourceYYYY-MM-DD.jsonl
Processed	data/processed/sourceYYYY-MM-DD.jsonl
Enriched	data/processed_enriched/sourceYYYY-MM-DD.jsonl
Merged	data/merged/YYYY-MM-DD.jsonl
Scored	data/scored/YYYY-MM-DD.jsonl
Detection rules	data/rules/YYYY-MM-DD.yaml
Alerts/logs	data/alerts/YYYY-MM-DD.json
Feedback	data/feedback/YYYY-MM-DD.json
Reports	data/reports/YYYY-MM-DD.summary.json, .daily.pdf, .bands.png
Simulations	data/simulations/
Tickets	data/tickets/YYYY-MM-DD.json
Troubleshooting
Always activate the virtual environment before running scripts.

If you experience dependency issues, run:

text
make env-ok
Check for missing files or paths in your config settings.

Logs and error messages are written for each module for debugging.

Only .env.example is committed; never share real secrets in .env.

References
Lab assignment PDF, all requirements, and workflow guidelines.

Sigma detection rule format: https://github.com/SigmaHQ/sigma

Atomic Red Team: https://github.com/redcanaryco/atomic-red-team

All modules, scripts, configs, and sample data are structured for clear reproducibility, grading, and audit. Extend/enhance as needed per course guidelines or feedback.

Author: [Your Name]
Course: TE V OSINT Threat Intelligence Lab
Institution: Fr. Conceicao Rodrigues College of Engineering
