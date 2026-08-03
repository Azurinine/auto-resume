# Default name if none provided
NAME ?= resume_$(shell date +%Y%m%d_%H%M%S)
# Optional job description path for keyword mapping
JD ?=

all:
	latexmk -pdf -output-directory=output main.tex
	mv output/main.pdf output/$(NAME).pdf
	latexmk -c -output-directory=output
	@echo "Generated: output/$(NAME).pdf"
	@# Rule 5 guard: refuse to archive a resume that overflows one page.
	@pages=$$(mdls -name kMDItemNumberOfPages -raw "output/$(NAME).pdf" 2>/dev/null); \
	case "$$pages" in ''|*[!0-9]*) pages=$$(python3 -c "from pypdf import PdfReader; print(len(PdfReader('output/$(NAME).pdf').pages))" 2>/dev/null || pdfinfo "output/$(NAME).pdf" 2>/dev/null | awk '/^Pages:/{print $$2}');; esac; \
	echo "Page count: $${pages:-unknown}"; \
	if [ -n "$$pages" ] && [ "$$pages" -gt 1 ] 2>/dev/null; then \
		echo "ERROR: output/$(NAME).pdf is $$pages pages. Rule 5 requires exactly 1 page."; \
		echo "       Trim sections/ (compress-before-drop) and rebuild. NOT archiving a failed build."; \
		exit 1; \
	fi; \
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
