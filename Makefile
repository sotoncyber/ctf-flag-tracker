.DEFAULT_GOAL := run
.PHONY: clean, clean-db, init-db, venv, run

clean: # Clean build files
	rm -rf **/*.pyc
	rm -rf **/__pycache__/

clean-db: # Delete database
	rm -rf *.db

init-db: # Create database
	flask/bin/python3 -c 'from tracker.db import init_db; init_db()'

venv: # Setup virtual environment
	python3 -m venv flask
	flask/bin/pip3 install flask flask_login flask_wtf

run: # Run app
	flask/bin/python3 run.py
