.PHONY: collect

collect:
	. .venv/bin/activate && python -m src.collectors.run_all

.PHONY: normalize

normalize:
	. .venv/bin/activate && python -m src.normalizers.normalize_run

.PHONY: enrich

enrich:
	. .venv/bin/activate && python -m src.enrichers.run_enrichment

.PHONY: merge

merge:
	. .venv/bin/activate && python -m src.merge.run_merge

.PHONY: correlate

correlate:
	. .venv/bin/activate && python -m src.correlation.run_correlate	

.PHONY: score

score:
	. .venv/bin/activate && python -m src.scoring.run_scoring

.PHONY: gen-detect mock-detect

gen-detect:
	. .venv/bin/activate && python -m src.detection.gen_sigma data/scored/$(DATE).jsonl data/rules/$(DATE)

mock-detect:
	. .venv/bin/activate && python -m src.detection.mock_engine data/rules/$(DATE) data/simlogs/$(DATE).jsonl data/alerts/$(DATE).json

.PHONY: summary charts report

summary:
	. .venv/bin/activate && python -m src.reporting.summary data/scored/$(DATE).jsonl data/feedback/$(DATE).json > data/reports/$(DATE).summary.json

charts:
	. .venv/bin/activate && python -m src.reporting.charts band_bar data/scored/$(DATE).jsonl data/reports/$(DATE).bands.png
	. .venv/bin/activate && python -m src.reporting.charts feedback_pie data/feedback/$(DATE).json data/reports/$(DATE).feedback.png

report:
	. .venv/bin/activate && python -m src.reporting.pdf_report data/reports/$(DATE).summary.json data/reports/$(DATE).bands.png data/reports/$(DATE).daily.pdf

.PHONY: daily playbook orchestrate-all

daily:
	. .venv/bin/activate && python -m src.orchestration.daily_run $(DATE)

playbook:
	. .venv/bin/activate && python -m src.orchestration.playbook data/alerts/$(DATE).json data/tickets/$(DATE).json

orchestrate-all:
	. .venv/bin/activate && python -m src.orchestration.daily_run $(DATE) && python -m src.orchestration.playbook data/alerts/$(DATE).json data/tickets/$(DATE).json

.PHONY: simulate coverage validate

simulate:
	. .venv/bin/activate && python -m src.simulation.replay data/rules/$(DATE) data/simulations/phishing_event.jsonl data/alerts/$(DATE).sim.json

coverage:
	. .venv/bin/activate && python -m src.simulation.coverage data/alerts/$(DATE).sim.json data/simulations/phishing_event.jsonl

validate: simulate coverage
	@echo "Simulation and coverage complete for $(DATE)"

.PHONY: dashboard

dashboard:
	. .venv/bin/activate && streamlit run src/dashboard/streamlit_app.py

.PHONY: flask-dashboard

flask-dashboard:
	. .venv/bin/activate && python -m src.dashboard.flask_app
