.PHONY: help install dev-install test lint format clean run demo demo-interactive audio-test

help:
	@echo "HiyaDrive Development Commands"
	@echo "=============================="
	@echo ""
	@echo "Setup:"
	@echo "  make install           Install dependencies (production)"
	@echo "  make dev-install       Install with dev dependencies"
	@echo "  make venv              Create virtual environment"
	@echo ""
	@echo "Running:"
	@echo "  make demo              Run demo with sample text input"
	@echo "  make demo-interactive  Run demo with microphone input"
	@echo "  make audio-test        Test audio input/output"
	@echo "  make tts-test          Test text-to-speech"
	@echo "  make stt-test          Test speech-to-text"
	@echo "  make status            Show system status"
	@echo ""
	@echo "Development:"
	@echo "  make test              Run all tests"
	@echo "  make lint              Run code quality checks"
	@echo "  make format            Format code with black"
	@echo "  make type-check        Run type checking with mypy"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean             Remove build artifacts"
	@echo "  make clean-logs        Remove log files"
	@echo ""

venv:
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip setuptools wheel

install:
	pip install -r requirements.txt

dev-install: install
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov pytest-mock black pylint mypy ipython

test:
	pytest tests/ -v --cov=hiya_drive --cov-report=html

lint:
	pylint hiya_drive/ tests/ --disable=C0111,C0103,R0903

format:
	black hiya_drive/ tests/ setup.py

type-check:
	mypy hiya_drive/ --ignore-missing-imports

demo:
	python -m hiya_drive.main demo --utterance "Book a table for 2 at Italian next Friday at 7 PM"

demo-interactive:
	python -m hiya_drive.main demo --interactive

audio-test:
	python -m hiya_drive.main test-audio

tts-test:
	python -m hiya_drive.main test-tts

stt-test:
	python -m hiya_drive.main test-stt

status:
	python -m hiya_drive.main status

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true

clean-logs:
	rm -f data/logs/*.log*
	rm -f data/recordings/*.wav

clean-db:
	rm -f hiya_drive.db

.DEFAULT_GOAL := help
