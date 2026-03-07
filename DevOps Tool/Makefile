.PHONY: install test scan audit pentest ui ui-build

install:
	pip install -r requirements.txt
	pip install -e .

test:
	python -m pytest tests/ -v

scan:
	python -m cspm.cli scan aws --save-snapshot --output json

audit:
	bash scripts/run_audit.sh

pentest:
	bash scripts/run_pentest.sh

ui:
	python -m cspm.cli ui --host 127.0.0.1 --port 8000

ui-build:
	cd frontend && npm install && npm run build
