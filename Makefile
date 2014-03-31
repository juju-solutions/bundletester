PROJECT=bundlerunner

all: lint test

clean:
	python setup.py clean
	rm -rf build/ MANIFEST dist/* bundletester.egg-inf .cover
	find . -name '*.pyc' -delete

clean_all: clean
	rm -rf .venv

test: .venv
	@echo Starting tests...
	@./bin/nosetests --nologcapture

coverage: .venv
	@echo Starting tests...
	@./bin/nosetests --nologcapture --with-coverage
	@xdg-open .cover/index.html


ftest:
	@echo Starting fast tests...
	@./bin/nosetests --attr '!slow' --nologcapture 

lint:
	@flake8 $(PROJECT) $(TESTS) && echo OK

.venv:
	./bin/test_setup

