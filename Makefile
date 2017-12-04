
.PHONY: build test start dev

build:
	pip install --require-hashes -r requirements.txt

test:
	pip3 install -r test_requirements.txt
	flake8 --exclude ./lib/*
	pytest -v --cov app

start:
	./startup.sh
