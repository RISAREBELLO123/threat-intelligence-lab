# Threat Intelligence Aggregation Lab

An automated end-to-end threat intelligence pipeline that collects, normalizes, enriches, correlates, scores, and generates detections from open-source intelligence feeds.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Pipeline Workflow](#pipeline-workflow)
- [Usage](#usage)
  - [Data Collection](#data-collection)
  - [Normalization](#normalization)
  - [Enrichment](#enrichment)
  - [Merging](#merging)
  - [Correlation](#correlation)
  - [Scoring](#scoring)
  - [Detection Rule Generation](#detection-rule-generation)
  - [Reporting](#reporting)
  - [Simulation & Coverage](#simulation--coverage)
  - [Playbook Automation](#playbook-automation)
  - [Dashboards](#dashboards)
- [Directory Structure](#directory-structure)
- [Extending the Pipeline](#extending-the-pipeline)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

This project implements a complete Security Operations Center (SOC) pipeline covering the full lifecycle from raw threat data ingestion to actionable detection rules and executive reporting.

It supports modular integration of multiple threat intelligence sources, normalization to a unified schema, enrichment, graph-based correlation, scoring, detection rule generation, and reporting.

---

## Features

- **Multi-source Collection:** REST API collectors for public and commercial threat feeds.
- **Normalization:** Converts raw data to a canonical schema for downstream processing.
- **Enrichment:** Adds context (reputation, categories, ASN, geo, malware families) via external APIs or mock enrichers.
- **Merging:** Deduplicates and merges indicators using fuzzy matching and source precedence.
- **Correlation:** Builds a knowledge graph linking indicators, sources, references, malware, vulnerabilities, and techniques.
- **Scoring:** Assigns risk scores using recency, confidence, trust, enrichment, and graph signals.
- **Detection Generation:** Auto-generates Sigma rules for prioritized indicators.
- **Reporting:** Summarizes results, generates charts, and produces PDF reports.
- **Simulation:** Validates detection coverage using synthetic event logs.
- **Dashboards:** Interactive dashboards via Streamlit and Flask.

---

## Architecture

```
Raw Data → Normalization → Enrichment → Merge → Correlation → Scoring → Detection → Reporting
```

- **src/collectors/**: Data collection modules
- **src/normalizers/**: Data normalization
- **src/enrichers/**: Data enrichment
- **src/merge/**: Deduplication and merging
- **src/correlation/**: Graph-based correlation
- **src/scoring/**: Risk scoring
- **src/detection/**: Detection rule generation
- **src/reporting/**: Reporting and visualization
- **src/simulation/**: Simulation and coverage
- **src/dashboard/**: Dashboards (Streamlit/Flask)

---

## Installation

### Prerequisites

- Python 3.10+
- Git
- API keys for selected threat intelligence sources (see `.env.example`)

### Setup

```bash
# Clone the repository
git clone https://github.com/risarebelo123/threat-intelligence-lab.git
cd threat-intelligence-lab

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Configuration

- Copy `.env.example` to `.env` and fill in your API keys.
- Edit `config/config.yaml` to enable/disable sources and adjust pipeline settings.
- Mapping files for each source are in `config/mappings/`.

---

## Pipeline Workflow

The pipeline is modular and can be run step-by-step or orchestrated as a daily batch.

**Typical daily workflow:**

1. **Collect:** Fetch raw data from all enabled sources.
2. **Normalize:** Convert raw data to canonical schema.
3. **Enrich:** Add context from external APIs.
4. **Merge:** Deduplicate and merge indicators.
5. **Correlate:** Build a knowledge graph.
6. **Score:** Assign risk scores and bands.
7. **Detect:** Generate detection rules.
8. **Report:** Summarize and visualize results.
9. **Simulate:** Validate detection coverage.
10. **Playbook:** Automate ticket creation for high-priority alerts.

---

## Usage

All major steps are available as Makefile targets and Python modules.

### Data Collection

Collect data from all enabled sources:

```bash
make collect
# or
. .venv/bin/activate && python -m src.collectors.run_all
```

### Normalization

Normalize raw data to canonical schema:

```bash
make normalize
```

### Enrichment

Enrich normalized data with external context:

```bash
make enrich
```

### Merging

Deduplicate and merge indicators:

```bash
make merge
```

### Correlation

Build the knowledge graph:

```bash
make correlate
```

### Scoring

Score indicators and assign priority bands:

```bash
make score
```

### Detection Rule Generation

Generate Sigma rules for prioritized indicators:

```bash
make gen-detect DATE=2025-10-01
```

### Reporting

Generate summary and charts:

```bash
make summary DATE=2025-10-01
make charts DATE=2025-10-01
make report DATE=2025-10-01
```

### Simulation & Coverage

Replay simulated events and measure coverage:

```bash
make simulate DATE=2025-10-01
make coverage DATE=2025-10-01
```

### Playbook Automation

Create tickets for high-priority alerts:

```bash
make playbook DATE=2025-10-01
```

### Dashboards

#### Streamlit Dashboard

```bash
make dashboard
# or
. .venv/bin/activate && streamlit run src/dashboard/streamlit_app.py
```

#### Flask Dashboard

```bash
make flask-dashboard
# or
. .venv/bin/activate && python -m src.dashboard.flask_app
```

---

## Directory Structure

```
.env.example
.gitignore
Makefile
README.md
requirements.txt
config/
  config.yaml
  detections/
    template_sigma.yaml
  mappings/
    abuseipdb.yaml
    test_public.yaml
data/
  raw/
  processed/
  processed_enriched/
  merged/
  graph/
  scored/
  rules/
  alerts/
  reports/
  feedback/
  simlogs/
  simulations/
src/
  collectors/
  normalizers/
  enrichers/
  merge/
  correlation/
  scoring/
  detection/
  reporting/
  simulation/
  dashboard/
  utils/
docs/
  samples/
```

---

## Extending the Pipeline

- **Add a new source:** Create a mapping file in `config/mappings/`, update `config.yaml`, and implement a collector if needed.
- **Custom enrichment:** Add new enrichers in `src/enrichers/`.
- **Detection templates:** Add new Jinja templates in `config/detections/`.
- **Reporting:** Extend `src/reporting/` for new report types.

---

## Troubleshooting

- **No data collected:** Check API keys in `.env` and source configuration in `config.yaml`.
- **Pipeline errors:** Run each step manually to isolate issues.
- **Missing dependencies:** Ensure all packages in `requirements.txt` are installed.
- **Dashboard not loading:** Check that scored data exists in `data/scored/`.

---

## License

This project is released under the MIT License.

---

## Credits

Developed by [risarebelo123](https://github.com/risarebelo123) and contributors.

---

## References

- [Sigma Detection Rules](https://github.com/SigmaHQ/sigma)
- [MITRE ATT&CK](https://attack.mitre.org/)
- [AbuseIPDB](https://www.abuseipdb.com/)
- [AlienVault OTX](https://otx.alienvault.com/)
