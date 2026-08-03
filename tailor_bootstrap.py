#!/usr/bin/env python3
import os
import sys
import json
import re
import shutil
import argparse

# Absolute path configurations
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(WORKSPACE_DIR, "base")
SECTIONS_DIR = os.path.join(WORKSPACE_DIR, "sections")
ARCHIVE_DIR = os.path.join(WORKSPACE_DIR, "archive")
REGISTRY_PATH = os.path.join(ARCHIVE_DIR, "registry.json")

# Global technical keyword vocabulary
# This vocabulary represents our base capabilities and is updated dynamically from base/skills.tex
TECH_VOCAB = {
    # System & Industry standard concepts
    "compiler", "inference", "runtime", "parallelized", "massively-parallel", "hpc", "high performance computing", 
    "optimization", "backpropagation", "embedding", "manifolds", "llama", "deepseek", "neural network", "networks",
    "quantization", "transformers", "rest api", "endpoints"
}

def load_skills_vocabulary():
    """Dynamically load and merge technical skills from base/skills.tex into TECH_VOCAB."""
    skills_path = os.path.join(BASE_DIR, "skills.tex")
    if not os.path.exists(skills_path):
        return
        
    try:
        with open(skills_path, 'r') as f:
            content = f.read()
            
        # Extract skills inside the braces e.g., \textbf{Languages}{: Skill1, Skill2}
        # Find matches of words and phrases separated by commas
        matches = re.findall(r'\{([^}]+)\}', content)
        for match in matches:
            # Skip the category headers (e.g. "Languages", "Development")
            if match.endswith(":") or "margin" in match or "label" in match:
                continue
                
            # Clean up the leading ": " if present
            if match.startswith(": "):
                match = match[2:]
                
            # Split by commas, slashes, or parentheses to isolate actual skills
            for item in re.split(r'[,/()]', match):
                clean_item = item.strip().lower()
                # Remove LaTeX tags like \textbf, \small, or special characters
                clean_item = re.sub(r'\\[a-z]+', '', clean_item)
                clean_item = re.sub(r'[{}]', '', clean_item)
                clean_item = clean_item.replace("&", "").strip()
                
                # If valid skill, add to vocabulary
                if clean_item and len(clean_item) > 1 and "item" not in clean_item and "cloud" not in clean_item and "development" not in clean_item:
                    TECH_VOCAB.add(clean_item)
                    
                    # Split compound slash/hyphen terms to index them separately as well
                    for part in re.split(r'[-\s]', clean_item):
                        part = part.strip()
                        if len(part) > 1 and part not in ["use", "api", "actions"]:
                            TECH_VOCAB.add(part)
    except Exception as e:
        print(f"Warning: Could not dynamically parse base/skills.tex: {e}")

# Load dynamic base skills on initialization
load_skills_vocabulary()

# Unsupervised Keyphrase Extraction Stop Words (filters noise out of JDs)
STOP_WORDS = {
    'and', 'the', 'for', 'with', 'from', 'using', 'your', 'our', 'this', 'that', 'these', 'those', 'their', 'will', 
    'would', 'should', 'could', 'have', 'has', 'had', 'been', 'being', 'well', 'plus', 'huge', 'work', 'role', 'team', 
    'part', 'experience', 'skills', 'familiarity', 'concepts', 'understand', 'design', 'development', 'engineer', 
    'engineering', 'highly', 'expert', 'strong', 'solid', 'excellent', 'position', 'start', 'approximate', 'continue', 
    'return', 'apply', 'please', 'consult', 'ability', 'limit', 'academic', 'recent', 'seeking', 'employment', 
    'internship', 'program', 'actively', 'enrolled', 'we', 'you', 'they', 'she', 'he', 'it', 'to', 'in', 'on', 'at', 
    'by', 'of', 'an', 'is', 'are', 'was', 'were', 'or', 'but', 'as', 'if', 'be', 'can', 'us', 'who', 'about', 'most',
    'more', 'less', 'than', 'some', 'any', 'all', 'such', 'into', 'out', 'up', 'down', 'over', 'under', 'again', 'further'
}

def clean_text(text):
    """Normalize text for keyword extraction."""
    text = text.lower()
    # Replace common hyphens, slashes, and punctuation with spaces, but preserve standard c++ / node.js
    text = re.sub(r'[^a-z0-9+#\.\s-]', ' ', text)
    return text

def extract_keywords(text):
    """
    Extract technical keywords/keyphrases from text autonomously using an unsupervised
    compound noun-phrase extraction heuristic. This isolates exact jargon, multi-word terms,
    and skills with zero dependencies, 100% speed, and zero overfitting.
    """
    found_keywords = set()
    
    # 1. Direct regex match against our dynamic certified skills from base/skills.tex
    cleaned_full = clean_text(text)
    for vocab in TECH_VOCAB:
        escaped_vocab = re.escape(vocab)
        if vocab.endswith("++"):
            pattern = r'(?:^|\s)' + escaped_vocab + r'(?:$|\s|[,;:.])'
        else:
            pattern = r'\b' + escaped_vocab + r'\b'
            
        if re.search(pattern, cleaned_full):
            found_keywords.add(vocab)

    # 2. Extract multi-word jargon (n-grams) from the JD to capture exact phrasing requirements
    text_clean = text.lower()
    text_clean = re.sub(r'[^a-z0-9+#\s-]', ' ', text_clean)
    words = text_clean.split()
    
    i = 0
    while i < len(words):
        if words[i] in STOP_WORDS or len(words[i]) <= 1:
            i += 1
            continue
            
        # Found starting content word. Build contiguous n-grams up to 3 words
        seq = [words[i]]
        j = i + 1
        while j < len(words) and j < i + 3:
            if words[j] not in STOP_WORDS and len(words[j]) > 1:
                seq.append(words[j])
                j += 1
            else:
                break
                
        # If we got a multi-word sequence, register the exact compound phrase
        if len(seq) >= 2:
            exact_phrase = ' '.join(seq)
            found_keywords.add(exact_phrase)
            
            # Also register smaller sub-grams (e.g. "multi-agent models" -> "multi-agent")
            if len(seq) == 3:
                found_keywords.add(' '.join(seq[:2]))
                found_keywords.add(' '.join(seq[1:]))
                
            # Add individual words
            found_keywords.update(seq)
            
        i += 1
        
    return sorted(list(found_keywords))

def load_registry():
    """Load the JSON registry."""
    if not os.path.exists(REGISTRY_PATH):
        return {}
    try:
        with open(REGISTRY_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not read registry.json: {e}. Starting fresh.")
        return {}

def save_registry(registry):
    """Save the JSON registry."""
    try:
        with open(REGISTRY_PATH, 'w') as f:
            json.dump(registry, f, indent=2)
    except Exception as e:
        print(f"Error: Could not write registry.json: {e}", file=sys.stderr)

def strip_latex(text):
    """Remove LaTeX commands/braces so JD-style keyword extraction can run on .tex content."""
    text = re.sub(r'\\[a-zA-Z]+\*?', ' ', text)   # drop \commands
    text = re.sub(r'[{}$|]', ' ', text)            # drop braces, math, pipes
    return text

def summarize_layout(archive_name):
    """
    Produce a human-readable LAYOUT summary of an archived resume: which section files
    exist and, per entry (company/project), how many bullets it used. This is the ONLY
    thing the archive is allowed to contribute — the wording/metrics of bullets must be
    re-derived from /base/ (see Rule 9, anti-fabrication). No bullet text is emitted here.
    """
    archive_src = os.path.join(ARCHIVE_DIR, archive_name)
    # Only the sections main.tex actually renders (the 1-page resume omits leadership/conferences).
    order = ["header", "education", "experience", "research", "projects", "skills"]
    tex_files = set(f for f in os.listdir(archive_src) if f.endswith(".tex"))

    lines = []
    for section in order:
        fname = f"{section}.tex"
        if fname not in tex_files:
            continue
        try:
            with open(os.path.join(archive_src, fname)) as fh:
                content = fh.read()
        except Exception:
            continue
        # \resumeSubheading / \resumeProjectHeading mark entries; the *ListStart wrappers
        # (\resumeSubHeadingListStart, capital H) are deliberately NOT matched.
        markers = list(re.finditer(r'\\resume(?:Subheading|ProjectHeading)', content))
        entries = []
        for idx, m in enumerate(markers):
            end = markers[idx + 1].start() if idx + 1 < len(markers) else len(content)
            chunk = content[m.start():end]
            # The entry's name is the FIRST innermost {...} group after the macro
            # (company for \resumeSubheading, the \textbf{Name} arg for projects).
            label_m = re.search(r'\{([^{}]+)\}', chunk)
            label = re.sub(r'\\[a-zA-Z]+\*?', '', label_m.group(1)).strip() if label_m else "(entry)"
            n = len(re.findall(r'\\resumeItem\{', chunk))
            entries.append((label, n))
        if entries:
            desc = "; ".join(f"{lbl} ({n} bullet{'' if n == 1 else 's'})" for lbl, n in entries)
            lines.append(f"- **{section}**: {desc}")
        else:
            lines.append(f"- **{section}**: (present, no bulleted entries)")
    return "\n".join(lines)

def write_layout_hint(archive_name, score):
    """Write sections/.layout_hint.md: the matched archive's STRUCTURE only, as a reference
    for mirroring the already-solved 1-page layout. Facts/metrics still come from /base/."""
    summary = summarize_layout(archive_name)
    hint = (
        "# Layout reference — NOT a source of facts\n\n"
        f"Closest prior resume: `archive/{archive_name}/` (similarity {score:.0%}).\n\n"
        "Use this ONLY to mirror the page-budget layout that already fit on one page: which\n"
        "sections/entries were included and how many bullets each carried. **Re-derive every\n"
        "bullet's wording and metrics from `/base/` (the ground truth). NEVER copy bullet text\n"
        "from the archive — it may contain claims not grounded in `/base/` (Rule 9).**\n\n"
        f"## Structure that fit one page for a similar JD\n{summary}\n"
    )
    with open(os.path.join(SECTIONS_DIR, ".layout_hint.md"), "w") as f:
        f.write(hint)
    print(f"Wrote sections/.layout_hint.md (structure of '{archive_name}'; bullet text NOT copied).")

def _copy_base_into_sections():
    """Copy the immutable /base/ ground-truth .tex into sections/."""
    for f in os.listdir(BASE_DIR):
        if f.endswith(".tex"):
            shutil.copy(os.path.join(BASE_DIR, f), os.path.join(SECTIONS_DIR, f))

def bootstrap(jd_path, threshold_perfect=0.85, threshold_good=0.40):
    """Bootstrap workspace from the closest matching archive or the clean base."""
    if not os.path.exists(jd_path):
        print(f"Error: Job description file not found at {jd_path}", file=sys.stderr)
        sys.exit(1)
        
    with open(jd_path, 'r') as f:
        jd_content = f.read()
        
    jd_keywords = set(extract_keywords(jd_content))
    print(f"Parsed {len(jd_keywords)} technical keywords from Job Description:")
    print(f"  {', '.join(sorted(jd_keywords))}\n")
    
    registry = load_registry()
    
    best_match = None
    best_score = 0.0
    best_keywords = []
    
    for name, meta in registry.items():
        archived_keywords = set(meta.get("keywords", []))
        if not archived_keywords:
            continue
            
        # Calculate Jaccard Similarity (Intersection over Union)
        intersection = jd_keywords.intersection(archived_keywords)
        union = jd_keywords.union(archived_keywords)
        score = len(intersection) / len(union) if union else 0.0
        
        if score > best_score:
            best_score = score
            best_match = name
            best_keywords = sorted(list(intersection))
            
    print(f"Closest match found: '{best_match}' with score: {best_score:.2%}")
    if best_match:
        print(f"  Shared keywords: {', '.join(best_keywords)}\n")
        
    # Determine Action Based on Similarity Tiers
    os.makedirs(SECTIONS_DIR, exist_ok=True)
    
    if best_score >= threshold_perfect:
        print(f"🎯 TIER 1 MATCH (>= {threshold_perfect:.0%}): PERFECT overlap!")
        print(f"A near-identical resume already exists: 'output/{best_match}.pdf' — reuse it if the JD truly matches.")
        print("Re-grounding sections/ from /base/ (facts) with a layout reference, in case edits are needed.")
        _copy_base_into_sections()
        write_layout_hint(best_match, best_score)
        print("Done. Workspace bootstrapped from base with a layout reference.")

    elif best_score >= threshold_good:
        print(f"⚡ TIER 2 MATCH (>= {threshold_good:.0%}): MODERATE overlap!")
        print(f"Using 'archive/{best_match}/' as a LAYOUT REFERENCE ONLY (see sections/.layout_hint.md).")
        print("Copying /base/ (ground-truth facts) into sections/; rewrite bullets from base, mirroring the referenced layout.")
        print("Do NOT copy bullet text from the archive — it may carry ungrounded claims (Rule 9).")
        _copy_base_into_sections()
        write_layout_hint(best_match, best_score)
        print("Done. Workspace bootstrapped from base with a layout reference.")

    else:
        print(f"🧹 TIER 3 MATCH (< {threshold_good:.0%}): LOW overlap.")
        print("Starting with a fresh slate from immutable base files ('base/').")
        
        for f in os.listdir(BASE_DIR):
            if f.endswith(".tex"):
                shutil.copy(os.path.join(BASE_DIR, f), os.path.join(SECTIONS_DIR, f))
        print("Done. Fresh base resume copied to workspace sections.")

def archive_sections(name, jd_path=None):
    """Archive current sections/ state and register it in registry.json."""
    archive_dest = os.path.join(ARCHIVE_DIR, name)
    os.makedirs(archive_dest, exist_ok=True)
    
    if not os.path.exists(SECTIONS_DIR) or not os.listdir(SECTIONS_DIR):
        print("Error: sections/ folder is empty. Nothing to archive.", file=sys.stderr)
        sys.exit(1)
        
    # 1. Copy files to archive folder
    for f in os.listdir(SECTIONS_DIR):
        if f.endswith(".tex"):
            shutil.copy(os.path.join(SECTIONS_DIR, f), os.path.join(archive_dest, f))

    # 2. Extract keywords for registry — only from the JD to avoid LaTeX noise.
    #    Also persist the JD inside the archive folder so registry.json can always be
    #    rebuilt from folders alone (see rebuild_registry / `make sync-registry`).
    keywords = []
    if jd_path and os.path.exists(jd_path):
        with open(jd_path, 'r') as f:
            jd_content = f.read()
        keywords = extract_keywords(jd_content)
        with open(os.path.join(archive_dest, "jd.txt"), 'w') as f:
            f.write(jd_content)
    # No fallback: parsing .tex files produces LaTeX syntax noise (textbf, itemize, etc.)
    # If no JD provided, keywords remain empty and the entry will be skipped during similarity matching
            
    # 3. Save to registry
    registry = load_registry()
    registry[name] = {
        "keywords": keywords,
        "sections_source": f"archive/{name}/"
    }
    save_registry(registry)
    print(f"Successfully archived current state to 'archive/{name}/' with {len(keywords)} registered keywords.")

def rebuild_registry():
    """Rebuild registry.json from the archive folders so it can never silently drift.

    For each archive/<name>/ folder, keywords are sourced in priority order:
      1. archive/<name>/jd.txt          (authoritative — how new archives are stored)
      2. an existing registry entry     (preserve keywords for legacy folders)
      3. archived .tex fallback (noisy)  (last resort so no folder is left unregistered)
    """
    existing = load_registry()
    rebuilt = {}
    if not os.path.isdir(ARCHIVE_DIR):
        print("No archive directory found; nothing to rebuild.")
        return

    for name in sorted(os.listdir(ARCHIVE_DIR)):
        folder = os.path.join(ARCHIVE_DIR, name)
        if not os.path.isdir(folder):
            continue

        jd_file = os.path.join(folder, "jd.txt")
        if os.path.exists(jd_file):
            with open(jd_file) as f:
                keywords = extract_keywords(f.read())
            source = "jd.txt"
        elif name in existing and existing[name].get("keywords"):
            keywords = existing[name]["keywords"]
            source = "existing entry (no jd.txt)"
        else:
            blob = ""
            for f in os.listdir(folder):
                if f.endswith(".tex"):
                    with open(os.path.join(folder, f)) as fh:
                        blob += " " + strip_latex(fh.read())
            keywords = extract_keywords(blob)
            source = ".tex fallback (noisy — add a jd.txt to fix)"

        rebuilt[name] = {"keywords": keywords, "sections_source": f"archive/{name}/"}
        print(f"  {name}: {len(keywords)} keywords [{source}]")

    save_registry(rebuilt)
    print(f"Rebuilt registry.json with {len(rebuilt)} entries.")

# --- Line-density lint -------------------------------------------------------
# Character thresholds calibrated to the resume's text width (see CLAUDE.md §3).
LINT_SINGLE_MAX = 95    # a dense single line
LINT_DENSE_MIN2 = 150   # a two-liner must be at least this full to earn its 2nd line
LINT_DOUBLE_MAX = 190   # beyond this wraps to a 3rd line

def _visible_len(item_body):
    r"""Approximate the rendered width of a \resumeItem body: strip LaTeX commands and
    braces but KEEP the text they wrap (e.g. \textbf{60.6M+} -> 60.6M+)."""
    s = re.sub(r'\\href\{[^}]*\}', '', item_body)   # drop the URL argument of \href
    s = re.sub(r'\\[a-zA-Z]+\*?', '', s)            # drop \commands (textbf, emph, small, ...)
    s = re.sub(r'\\([&%$#_])', r'\1', s)            # unescape \& \% \$ \# \_ to one char
    s = s.replace('{', '').replace('}', '').replace('$', '').replace('~', ' ')
    return len(re.sub(r'\s+', ' ', s).strip())

MIN_ENTRY_BULLETS = 3   # non-project entries must carry at least this many bullets

def _entry_bullet_counts(content):
    r"""Return [(label, bullet_count)] per top-level entry (\resumeSubheading boundary).
    Bullets under \resumeSubSubheading stay grouped with their parent entry."""
    markers = list(re.finditer(r'\\resumeSubheading', content))
    out = []
    for idx, m in enumerate(markers):
        end = markers[idx + 1].start() if idx + 1 < len(markers) else len(content)
        chunk = content[m.start():end]
        lm = re.search(r'\{([^{}]+)\}', chunk)
        label = re.sub(r'\\[a-zA-Z]+\*?', '', lm.group(1)).strip() if lm else "(entry)"
        out.append((label, len(re.findall(r'\\resumeItem\{', chunk))))
    return out

def _iter_resume_items(content):
    r"""Yield the brace-balanced body of each \resumeItem{...} (handles nested \textbf{})."""
    token = r'\resumeItem{'
    idx = 0
    while True:
        pos = content.find(token, idx)
        if pos == -1:
            return
        i = start = pos + len(token)
        depth = 1
        while i < len(content) and depth:
            depth += (content[i] == '{') - (content[i] == '}')
            i += 1
        yield content[start:i - 1]
        idx = i

def lint_density():
    r"""Flag bullets that waste vertical space. A bullet just over one line wraps to a
    nearly-empty second line — that whitespace could hold another bullet or entry. Each
    bullet should be a dense single line (<= LINT_SINGLE_MAX) or a full two-liner
    (LINT_DENSE_MIN2..LINT_DOUBLE_MAX). See CLAUDE.md section 3. Returns nonzero if issues."""
    # Only the bulleted sections main.tex actually renders on the 1-page resume.
    # (leadership/conferences are omitted, so their bullets don't affect layout.)
    rendered = ["experience", "research", "projects"]
    files = [f"{n}.tex" for n in rendered if os.path.exists(os.path.join(SECTIONS_DIR, f"{n}.tex"))]

    waste = toolong = total = 0
    for fname in files:
        with open(os.path.join(SECTIONS_DIR, fname)) as fh:
            content = fh.read()
        header_printed = False
        for body in _iter_resume_items(content):
            total += 1
            n = _visible_len(body)
            if n <= LINT_SINGLE_MAX or LINT_DENSE_MIN2 <= n <= LINT_DOUBLE_MAX:
                continue  # dense single line, or full two-liner — both fine
            if n < LINT_DENSE_MIN2:
                msg = f"STUB 2nd line ({n} chars) -> trim to <={LINT_SINGLE_MAX} OR expand to >={LINT_DENSE_MIN2}"
                waste += 1
            else:
                msg = f"TOO LONG ({n} chars) -> wraps to 3 lines, trim below {LINT_DOUBLE_MAX}"
                toolong += 1
            if not header_printed:
                print(f"\n[{fname[:-4]}]")
                header_printed = True
            preview = re.sub(r'\s+', ' ', body)[:64]
            print(f"  WARN {msg}\n       \"{preview}...\"")

    # Entry minimum: non-project entries (experience, research) must not be left "light".
    # Projects are exempt — they are the trim buffer (2/1/0 bullets, header-only is fine).
    light = 0
    for fname in ("experience.tex", "research.tex"):
        path = os.path.join(SECTIONS_DIR, fname)
        if not os.path.exists(path):
            continue
        header_printed = False
        for label, cnt in _entry_bullet_counts(open(path).read()):
            if cnt < MIN_ENTRY_BULLETS:
                if not header_printed:
                    print(f"\n[{fname[:-4]} — entry density]")
                    header_printed = True
                print(f"  WARN '{label}' has {cnt} bullet(s) (<{MIN_ENTRY_BULLETS}) -> add grounded "
                      f"bullets from /base/, or drop the entry (don't ship a light entry).")
                light += 1

    print(f"\nLine-density: {total} bullets | {waste} waste-zone | {toolong} too-long | {light} light entries.")
    if waste or toolong or light:
        print("Fix: right-size each flagged bullet (shorten, or split & fill from /base/), and give")
        print(f"every experience/research entry >={MIN_ENTRY_BULLETS} bullets or drop it. No fabrication.")
        return 1
    print("OK: bullets are dense, and every non-project entry carries its weight.")
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resume Semantic Cache & Bootstrap Manager")
    subparsers = parser.add_argument_group("actions")
    
    parser.add_argument("--bootstrap", help="Path to Job Description file to bootstrap sections/", type=str)
    parser.add_argument("--archive", help="Name to archive current sections/ to", type=str)
    parser.add_argument("--jd", help="Path to JD for keyword extraction (use with --archive)", type=str)
    parser.add_argument("--rebuild-registry", action="store_true",
                        help="Regenerate registry.json from the archive folders (self-heal drift)")
    parser.add_argument("--lint-density", action="store_true",
                        help="Flag bullets in the stub-line waste zone (see CLAUDE.md section 3)")

    args = parser.parse_args()

    if args.lint_density:
        sys.exit(lint_density())
    elif args.rebuild_registry:
        rebuild_registry()
    elif args.bootstrap:
        bootstrap(args.bootstrap)
    elif args.archive:
        archive_sections(args.archive, args.jd)
    else:
        parser.print_help()
