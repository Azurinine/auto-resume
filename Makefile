# Default name if none provided
NAME ?= resume_$(shell date +%Y%m%d_%H%M%S)
# Optional job description path for keyword mapping
JD ?=

all:
	latexmk -pdf -output-directory=output main.tex
	@# Rule 5 guard: read the TRUE page count from LaTeX's own log (authoritative and
	@# dependency-free) BEFORE cleaning aux files, and guard BEFORE archiving. Do NOT trust
	@# Spotlight/mdls -- its cache can be stale right after a rebuild and wrongly pass a 2-page PDF.
	@pages=$$(sed -n 's/.*Output written on .*(\([0-9][0-9]*\) pages\{0,1\}.*/\1/p' output/main.log 2>/dev/null | tail -1); \
	if [ -z "$$pages" ]; then pages=$$(pdfinfo output/main.pdf 2>/dev/null | awk '/^Pages:/{print $$2}'); fi; \
	echo "Page count: $${pages:-unknown}"; \
	if [ -n "$$pages" ] && [ "$$pages" -gt 1 ] 2>/dev/null; then \
		echo "ERROR: build is $$pages pages. Rule 5 requires exactly 1 page."; \
		echo "       Trim sections/ (compress-before-drop) and rebuild. NOT archiving a failed build."; \
		rm -f output/main.pdf; latexmk -c -output-directory=output >/dev/null 2>&1; \
		exit 1; \
	fi; \
	mv output/main.pdf output/$(NAME).pdf; \
	latexmk -c -output-directory=output >/dev/null 2>&1; \
	echo "Generated: output/$(NAME).pdf"; \
	if [ -n "$(JD)" ] && [ -f "$(JD)" ]; then \
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

# Regenerate archive/registry.json from the archive folders (self-heal drift).
sync-registry:
	python3 tailor_bootstrap.py --rebuild-registry

# Flag bullets that overflow into a stub second line (wasted vertical space).
lint:
	python3 tailor_bootstrap.py --lint-density

template:
	mkdir -p sections
	cp templates/*.tex sections/
	$(MAKE) all

base:
	mkdir -p sections
	cp base/*.tex sections/
	$(MAKE) all

.PHONY: all template base bootstrap sync-registry lint
