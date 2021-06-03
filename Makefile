.PHONY: all build

PROJECT    		  ?= "aws-teams-logger"
PACKAGE 		  ?= "aws_teams_logger"

init:
	pip install -e .[standalone]
	pip install -r requirements-dev.txt

test:
    # This runs all of the tests
	pytest -v tests

test-readme:
    # Build dist but show less output
	python3 setup.py --quiet sdist bdist_wheel
	@echo --
	@twine check dist/* && ([ $$? -eq 0 ] && echo "README.md and HISTORY.md ok") || echo "Invalid markup in README.md or HISTORY.md!"
	@make clean

flake8:
	flake8 --ignore=E501,F401,E128,E402,E731,F821 ${PACKAGE}

bump-patch:
    # Ref: https://stackoverflow.com/a/39950969/10237506
	@current_version=$$(python3 -c "from ${PACKAGE}.__version__ import __version__ as v; print(v)"); \
	bumpversion --allow-dirty --current-version $${current_version} patch ${PACKAGE}/__version__.py

bump-minor:
	@current_version=$$(python3 -c "from ${PACKAGE}.__version__ import __version__ as v; print(v)"); \
	bumpversion --allow-dirty --current-version $${current_version} minor ${PACKAGE}/__version__.py

bump-major:
	@current_version=$$(python3 -c "from ${PACKAGE}.__version__ import __version__ as v; print(v)"); \
	bumpversion --allow-dirty --current-version $${current_version} major ${PACKAGE}/__version__.py

coverage:
	pytest --cov-config .coveragerc --verbose --cov-report term --cov-report html --cov=${PACKAGE} tests

build : clean
	python3 setup.py sdist bdist_wheel

publish : build
	twine upload dist/*
	make clean

publish-test : build
	twine upload --repository testpypi dist/*
	make clean

clean:
	@rm -fr build dist .egg $(subst -,_,${PROJECT}).egg-info

docs:
	cd docs && make html
	@echo "\033[95m\n\nBuild successful! View the docs homepage at docs/_build/html/index.html.\n\033[0m"