dev: check-env
	if pip list | grep sdx-common; \
	then \
		cd .. && pip3 uninstall -y sdx-common && pip3 install -I ./sdx-common; \
	else \
		cd .. && pip3 install -I ./sdx-common; \
	fi;

	pip3 install -r requirements.txt

build:
	pip3 install -r requirements.txt

test:
	pip3 install -r test_requirements.txt
	flake8 --exclude lib .
	python3 -m unittest */tests/*.py

start:
	./startup.sh

check-env:
ifeq ($(SDX_HOME),)
	$(error SDX_HOME is not set)
endif
