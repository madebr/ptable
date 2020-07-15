BUILD_DIR=_build
SPHINXOPTS=-n -W -d $(BUILD_DIR)/doctrees .

.PHONY: all
all: html

.PHONY: html
html:
	sphinx-build -b html $(SPHINXOPTS) $(BUILD_DIR)/html

.PHONY: coverage
coverage:
	sphinx-build -b coverage ${SPHINXOPTS} $(BUILD_DIR)/coverage
	cat build/coverage/python.txt

.PHONY: clean
clean:
	rm -rf ${BUILD_DIR}
