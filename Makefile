
.PHONY: build test start dev

build:
	pip install --require-hashes -r requirements.txt

dev:
	pip install --require-hashes -r requirements.txt

test:
	pip install -r test_requirements.txt
	flake8 --exclude lib .
	python -m unittest discover app/tests/

start:
	./startup.sh
