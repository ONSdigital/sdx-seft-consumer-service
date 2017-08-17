
.PHONY: clean  build test start dev

build:
	pip install -r requirements.txt
	rm -rf sdx-common

dev:
	cd ..  && pip3 install -I ./sdc-cryptography
	pip install -r requirements.txt

test:
	pip install -r test_requirements.txt
	flake8 --exclude lib .
	python -m unittest discover app/tests/

start:
	./startup.sh

clean:
	rm -rf ./sdx-common && pip3 uninstall -y sdc-cryptography
