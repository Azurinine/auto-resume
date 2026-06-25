# Default name if none provided
NAME ?= resume_$(shell date +%Y%m%d_%H%M%S)
# Optional job description path for keyword mapping
JD ?= 

all:
	latexmk -pdf -output-directory=output main.tex
	mv output/main.pdf output/$(NAME).pdf
	latexmk -c -output-directory=output
	@echo "Generated: output/$(NAME).pdf"
	@# Automatically archive and register successful tailored builds if a custom NAME is specified
	@if [ -n "$(JD)" ] && [ -f "$(JD)" ]; then \
		python3 tailor_bootstrap.py --archive $(NAME) --jd $(JD); \
	elif [ -n "$(JD)" ]; then \
		echo "Warning: JD file '$(JD)' not found. Skipping keyword registration."; \
	else \
		echo "Tip: pass JD=path/to/jd.txt to register keywords in the archive for future bootstrapping."; \
	fi

bootstrap:
	@if [ -z "$(JD)" ]; then \
		echo "Error: JD path is required. Usage: 'make bootstrap JD=path/to/jd.txt'"; \
		exit 1; \
	fi
	python3 tailor_bootstrap.py --bootstrap $(JD)

template:
	mkdir -p sections
	cp templates/*.tex sections/
	$(MAKE) all

base:
	mkdir -p sections
	cp base/*.tex sections/
	$(MAKE) all

.PHONY: all template base bootstrap
