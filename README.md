# Threat Intelligence Aggregation Lab

An automated end-to-end threat intelligence pipeline that collects, normalizes, enriches, correlates, scores, and generates detections from 12+ open-source intelligence feeds.

## Overview

This project implements a complete Security Operations Center (SOC) pipeline covering the full lifecycle from raw threat data ingestion to actionable detection rules and executive reporting.

## Installation

### Prerequisites
- Python 3.10+
- Git
- API keys for selected threat intelligence sources

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
