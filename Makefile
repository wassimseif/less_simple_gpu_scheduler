VERSION=0.1.4
WHEEL=dist/less_simple_gpu_scheduler-$(VERSION)-py3-none-any.whl
SOURCE_DIST=dist/less_simple_gpu_scheduler-$(VERSION).tar.gz

.PHONY: build upload

upload: $(WHEEL) $(SOURCE_DIST)
	python3 -m twine upload $^

build: $(WHEEL) $(SOURCE_DIST)

$(WHEEL): setup.py less_simple_gpu_scheduler/*
	python3 setup.py bdist_wheel

$(SOURCE_DIST): setup.py less_simple_gpu_scheduler/*
	python3 setup.py sdist

