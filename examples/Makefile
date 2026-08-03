# Runs every .py in this folder. The C++ examples' Makefile compiles them;
# these need no build, so this just runs them and cleans up what they wrote.
#
# Usage:
#   make            # run all examples
#   make example1   # run a single example
#   make clean      # remove the generated svg/pdf/ipe files

PYTHON ?= python3

SOURCES := $(wildcard example*.py)
TARGETS := $(SOURCES:.py=)

.PHONY: all clean $(TARGETS)

all: $(TARGETS)

$(TARGETS): %: %.py
	$(PYTHON) $<

clean:
	$(RM) *.svg *.pdf *.ipe
