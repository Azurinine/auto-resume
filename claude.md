# Project Constitution — LaTeX Resume Tailoring System
<!-- Single source of truth. gemini.md points here; there is no separate _constitution_base. -->

## 0. The one job
The user pastes a Job Description (JD) and nothing else. The agent autonomously produces a tailored, **one-page, ATS-clean** PDF. Make every editorial decision (what to include, trim, reword) yourself — do not ask the user clarifying questions.

## 1. Invariants (never violate)

1. **No fabrication — the highest rule.** Every metric, technology, outcome, and responsibility must be grounded in `/base/` (the single source of truth for the candidate's achievements). Never invent, embellish, or extrapolate. If a bullet has no real number, restructure it with real scope — never manufacture one.
   - **The archive is a *layout* reference, never a source of facts.** Re-derive every bullet's wording and metrics from `/base/` on each tailoring. `sections/.layout_hint.md` (written by the bootstrapper) describes a prior resume's *structure* only. **Never copy bullet text from `archive/` — older archived resumes may contain ungrounded claims.**
   - Allowed exceptions: (a) the **graduation date** may be adjusted to fit a JD's eligibility window; (b) industry-standard skills implied by real `/base/` work (e.g. `LLMs`) may be added to the Skills section; (c) never pull projects or content from `/templates/` — it is layout only.
2. **Exactly one page.** A build that overflows to 2 pages is a *failed build* — `make` refuses to archive it. Trim (see Appendix A) and rebuild until it fits.
3. **ATS parsability.** No exotic fonts, graphical text boxes, or complex unparseable layouts. ATS parsers are exact-string matchers.
4. **Section order is fixed** in `main.tex` and must never be reordered. **Mandatory sections:** Education, Work Experience, Projects. The one-page resume **omits** leadership & conferences.
5. **`/base/` is read-only** — never modify it without explicit user permission to `chmod +w` first. Never modify or run `main-csv.tex` (the user's Master CV).
6. **JD keyword syntax fidelity.** Reproduce a JD keyword byte-for-byte wherever it appears: `front-end` ≠ `frontend`, `React.js` ≠ `ReactJS`, `PostgreSQL` ≠ `Postgres`.

## 2. Workflow

1. **Bootstrap first (mandatory), before reading or editing any file:** `make bootstrap JD=<path_to_jd.txt>`.
   - **Tier 3 (low overlap):** `sections/` is seeded from `/base/`. Do a full tailoring pass.
   - **Tier 1 / Tier 2 (match found):** `sections/` is *still* seeded from `/base/`, plus a `sections/.layout_hint.md` describing the matched archive's structure (which entries, how many bullets each). **Mirror that layout** to reuse a page-budget that already fit one page — but write every bullet fresh from `/base/`. This is the anti-fabrication guarantee: no archived bullet text ever enters `sections/`.
2. **Re-evaluate the graduation date every time** against the new JD's eligibility window (e.g. "penultimate year"). Never inherit a bootstrapped date — edit `sections/education.tex` for the current role.
3. **Tailor from `/base/`:** autonomously select the most JD-relevant experiences/projects and drop the rest. `/base/` bullets are a verbose *pool of raw facts* — rewrite each into a compressed one-line bullet, stripping phrasing left over from earlier applications, keeping only the JD-relevant fact + metric, and injecting exact JD keywords (Invariant 6).
4. **Lint density, then build:** run `make lint` and resolve every waste-zone bullet (§3) so no bullet spills a stub second line. Then **build:** `export PATH=$PATH:/Library/TeX/texbin && make NAME=company-role-date JD=<path_to_jd.txt>` — run as one command, no approval needed. Passing `JD=` auto-archives the build **only if it is one page**. On failure/overflow, read `output/main.log` first, apply compress-before-drop (Appendix A), and rerun the same command.
5. **Keep the cache honest:** `make sync-registry` rebuilds `archive/registry.json` from the archive folders if it ever drifts. New archives store their JD at `archive/<name>/jd.txt` so the registry can always be rebuilt.
6. Audit any content change against the current `main.tex` structure so nothing breaks.

## 3. Bullet standards — the PAR method
Every bullet = **P**roblem + **A**ction + **R**esult, begins with a strong past-tense verb, and ends in either a `\textbf{}` metric **or** an explicit scope statement (e.g. "across a team of 8"). A bullet missing any of these is invalid.
- **Banned openers:** responsible for, helped, assisted, worked on, involved in, contributed to. **Banned endings:** metric-less filler like "from first principles", "via GUI automation", "across internal dashboards".
- **Verb diversity:** never repeat a verb within the same entry. Bank: Engineered, Architected, Optimized, Automated, Accelerated, Reduced, Designed, Implemented, Developed, Deployed, Refactored, Integrated, Benchmarked, Profiled, Parallelized, Containerized, Orchestrated, Authored, Delivered, Scaled, Migrated, Spearheaded, Eliminated.
- **Length & line density:** count characters, not words. Every bullet must be **either** a dense single line (**≤95 chars**) **or** a genuinely full two-liner (**~150–190 chars**). The **waste zone is ~96–149 chars**: the bullet spills one word onto a nearly-empty second line, burning vertical space that could hold another bullet — or, summed across the resume, a whole extra entry. Fix a waste-zone bullet by **trimming it to ≤95** or by **splitting it into two shorter bullets and filling them with more grounded facts from `/base/`**. 2 lines (≤190) is the hard ceiling. Also aim single lines at the **fuller end (~75–95 chars)**: a very short single-liner leaves a ragged right edge / trailing whitespace, so grow it toward 95 with a grounded detail when you can. Run **`make lint`** (`python3 tailor_bootstrap.py --lint-density`) before the final build — it fails on waste-zone/too-long bullets and light entries, and prints a non-blocking advisory for underfilled (<65-char) single lines.
- **Entry minimum — never ship a light entry:** every **experience and research** entry must carry **≥3 bullets (≥3 rendered lines)** — the top entry typically 3 with one two-liner. An entry that can't sustain 3 grounded bullets from `/base/`, or isn't worth 3 lines, must be **dropped entirely** — never left as a 1–2 bullet stub. Over-trimming an entry into anemia is as bad as overflow. **Projects are the exception and the trim buffer:** a project may have 2, 1, or **0** bullets (header + tech-stack line only). `make lint` flags any light non-project entry. Quality over quantity: 3–4 full entries beat 6 thin ones.
- Keep tense consistent (past for completed work, present for ongoing research).

## 4. Formatting reference
- **Experience:** `\resumeSubheading` + `\resumeItemListStart`; `\vspace{-4pt}` right after `\resumeItemListStart`. **Projects:** `\resumeProjectHeading` with a clickable `\href` link. Never put a double line break inside a `\resumeItem{}`.
- **Metrics:** always wrap quantitative values in `\textbf{...}` so they pop.
- **Skills:** exactly 3 rows, each fitting on **one** rendered line. Mirror JD syntax exactly; when adding a JD keyword to a row, remove an irrelevant item so the row never wraps.
- **Education (compact):** subheading only (university, degree, GPA, dates) plus at most a single honors line. A Coursework bullet is forbidden — weave any coursework into Experience/Research bullets instead.

---

## Appendix A — Page-budget math & anti-loop protections (reference)

**Line budget.** A one-page resume with compact education holds ~55–60 rendered lines. Approximate line costs:
```
  Section header:                              1 line
  Entry subheading (company + title + dates):  1.5 lines
  Research sub-subheading (project row):       0.5 lines
  1-line bullet (≤95 chars):                   1 line
  2-line bullet (>95 chars):                   2 lines
  Skills (3 rows):                             3 lines
  Education (compact, 1 honors bullet):        2 lines
```
**Target fill: 48–52 lines (~85–90%).** Under 45 lines looks sparse. Every experience/research entry is **≥3 bullets** (never thinned below that — drop the whole entry instead); projects absorb the remaining space. Reference density: 2 experience entries (3 bullets each) + 1–2 research entries (3 each) + 2 projects (e.g. 2 and 1 bullets) ≈ 50–52 lines. Default first draft: 2–3 experience + 1–2 research (each ≥3 bullets), then projects to fill.

**Overflow recovery — compress before dropping, in order:**
1. Compress a project from 2 bullets to 1 (keeps its header/keyword signal).
2. Drop the education honors line (near-zero ATS value).
3. Only then drop a whole low-priority entry. **Non-project entries are all-or-nothing:** never thin an experience/research entry below 3 bullets to recover space — drop the entire entry instead.

**High-entropy trimming:** if the first compile is 2 pages, make one structural cut (drop a secondary project/research role or a full bullet) to hit 1 page instantly — do **not** micro-shave words across 4–5 iterations.

**Log-driven debugging:** on any failure/overflow, read `output/main.log` first and find the `Overfull \vbox` before changing anything.

**Extended thinking:** use reasoning budget to pre-plan section selection and trimming *before* writing files, so the first compile is as close to correct as possible.
