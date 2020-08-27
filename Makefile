PYTHON = .venv/bin/python
TWINE = .venv/bin/twine

.PHONY: dist
dist:
	-rm dist/*
	$(PYTHON) setup.py sdist bdist_wheel

.PHONY: upload
upload: dist
	$(TWINE) upload dist/*

.PHONY: upload
clean:
	rm -r build dist *.egg-info
