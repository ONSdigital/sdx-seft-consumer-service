
.PHONY: clean  build test start dev

build:
	git clone -b 0.7.0 https://github.com/ONSdigital/sdx-common.git
	pip install ./sdx-common
	pip install -r requirements.txt
	rm -rf sdx-common

dev:
	cd .. && pip3 uninstall -y sdx-common && pip3 install -I ./sdx-common
	pip install -r requirements.txt

test:
	pip install -r test_requirements.txt
	flake8 --exclude lib .
	python -m unittest discover app/tests/

start:
	./startup.sh

clean:
	rm -rf ./sdx-common
