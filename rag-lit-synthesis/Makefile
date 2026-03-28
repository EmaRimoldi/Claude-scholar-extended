.PHONY: install validate refresh check-gates tables build-pdf clean

install:
	uv sync

validate:
	python -m pytest tests/ -x -q
	python -m src.evaluation.validate_setup

refresh:
	python -m src.evaluation.collect_results --output-dir analysis-output

check-gates:
	python -m src.evaluation.check_gates --plan ../experiment-plan.md

tables:
	python -m src.evaluation.generate_tables --input analysis-output --output figures

build-pdf:
	cd manuscript && latexmk -pdf main.tex

clean:
	rm -rf outputs/*.json analysis-output/*.csv figures/*.pdf __pycache__ .pytest_cache
