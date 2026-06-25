# Default name if none provided
NAME ?= resume_$(shell date +%Y%m%d_%H%M%S)

all:
	latexmk -pdf -output-directory=output main.tex
	mv output/main.pdf output/$(NAME).pdf
	latexmk -c -output-directory=output
	@echo "Generated: output/$(NAME).pdf"

template:
	mkdir -p sections
	cp templates/*.tex sections/
	$(MAKE) all

base:
	mkdir -p sections
	cp base/*.tex sections/
	$(MAKE) all

.PHONY: all template base
