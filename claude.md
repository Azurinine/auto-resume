# Project Constitution & System Manual — Claude
<!-- Last updated: 2026-06-24 | Fork of _constitution_base.md -->
<!-- Model-specific sections marked with ⚡ -->

## Project Architecture Overview

This project is a modular LaTeX resume system designed to separate raw data from visual presentation, enabling easy and scalable tailoring of resumes.

*   **/base/**: This directory is the immutable, read-only Source of Truth for raw content. It contains all potential building blocks of your resume data, including comprehensive CV sections (like leadership or conferences).
*   **/sections/**: This is the working directory for tailored resumes. Here, specific sections are assembled or customized for targeted job applications.
*   **`main.tex`**: The master controller for the 1-page resume. This file pulls together the tailored version of your resume from `/sections/`. It can be modified below the "RESUME STARTS HERE" line (line 113) to omit or include sections.
*   **`main-csv.tex`**: The controller for the comprehensive Master CV. This reads directly from `/base/` and includes all sections. **The agent must never modify or run this file; it is strictly for the user.**
*   **/templates/**: Acts as the structural blueprint and style guide. It represents what a high-quality 1-page resume looks like. The agent must use it as a reference for *how* to select and structure content from `/base/` into `/sections/`, intentionally omitting non-essential CV sections (like leadership or conferences) to maintain the 1-page limit.

## Operational Rules (The "Must-Follow" Constraints)

*   **Rule 1**: Never modify files inside `/base/` without explicit user permission to `chmod +w` them first. This directory is strictly read-only by default.
*   **Rule 2**: All content changes must be audited against the current `main.tex` structure to ensure consistency and prevent structural breakages.
*   **Rule 3**: Maintain absolute ATS (Applicant Tracking System) parsability. Under no circumstances should exotic fonts, graphical text boxes, or complex unparseable layouts be introduced.
*   **Rule 4**: If an error occurs during `make`, immediately analyze the `output/main.log` file before attempting or suggesting any code changes.
*   **Rule 5**: The generated resume must strictly fit on **one single page**. If the output PDF exceeds one page after compilation, the agent must delete the generated file, trim or optimize the content, and redo it to fix the overflow. Use best practice judgment to shorten (e.g., convert projects to 1-liners, shorten skills section headings).
*   **Rule 10**: **Compact Education Section**: The education section must always use the compact single-bullet format found in `/templates/education.tex`. The only permitted bullet is a single-line listing of honors, fellowships, and clubs (e.g., *"Competitive Programming Club, NSF REU Fellow, UC Scholars Research Fellow"*). A Coursework bullet is strictly forbidden — it wastes 2–3 vertical lines that are better spent on high-impact technical experience. Any coursework the agent would list in education must instead be woven into bullet points in the relevant Experience or Research entries.
*   **Rule 11**: **Graduation Date Re-Evaluation (Never Inherit)**: The graduation date must be re-evaluated fresh against every new JD's eligibility criteria. When bootstrapping from an archive, the graduation date in the copied template is considered stale and must be overridden. Always re-read the JD's eligibility window (e.g., "penultimate year", "graduating between Dec 2026 – Dec 2027") and set the graduation date specifically for the new role. Never blindly inherit a date fabricated for a prior application.
*   **Rule 6**: Section order in `main.tex` is strictly defined and must **never** be modified.
*   **Rule 7**: **Mandatory Sections**: Education, Work Experience, and Projects must always be present in `main.tex` and cannot be omitted.
*   **Rule 8**: **JD Keyword Syntax Fidelity**: When a keyword appears in the JD with specific formatting (hyphenation, capitalization, abbreviation, spacing), reproduce it with byte-for-byte accuracy throughout the resume. `front-end` ≠ `frontend` ≠ `Front End`. `React.js` ≠ `ReactJS`. `PostgreSQL` ≠ `Postgres`. ATS parsers are exact-string matchers.
*   **Rule 9**: **No Fabrication**: The agent must never invent, embellish, or extrapolate metrics, outcomes, or responsibilities that are not grounded in the content of `/base/`. If a bullet lacks a real number, restructure it — do not manufacture one.
    *   **Specific Exceptions & Flexibility**:
        *   **Graduation Date**: Fabricating or adjusting the graduation date is fully allowed and highly recommended if necessary to align with the eligibility criteria specified in the JD, as graduation timelines are flexible.
        *   **Implied Tech Skills**: Adding relevant, industry-standard tech skills (e.g., `LLMs`) to the Skills section is fully acceptable to satisfy JD requirements, even if not explicitly written in `/base/`, provided they relate to the candidate's projects or experience documented in `/base/`.
        *   **No Template Project Fallbacks**: `/templates/` is strictly a visual layout and structure guide. Copying, adapting, or hallucinating projects or experiences from `/templates/` (such as sample placeholder projects) is strictly forbidden if they do not exist in `/base/`. `/base/` is the absolute, single source of truth for the candidate's achievements.

## Workflow Protocol

*   **Section Selection**: When creating a tailored resume, the agent must reference `/templates/` to determine which sections to include. It must omit extensive CV-specific sections (e.g., `leadership.tex`, `conference.tex`) from `/base/` to ensure the final output fits strictly on one page.
*   **Build Pipeline** ⚡: To compile the tailored resume, the AI agent (Claude) must run the following exact command in the terminal: `export PATH=$PATH:/Library/TeX/texbin && make NAME=company_name-job_posting-date`. This ensures `latexmk` is found in the PATH and the output file is named correctly.
    * **Crucial Agent Instruction:** The agent must run this as a single combined command using the available bash/terminal tool. Execute it directly without seeking prior approval for the compile step.
    * If the build fails or exceeds one page, the agent must iteratively trim the content in `/sections/` and **rerun this exact `make` command** to overwrite and replace the file until it succeeds.
*   **Error Handling**: In the event of a build failure, the AI agent (Claude) must check the `output/main.log` file first to accurately diagnose the root cause before proposing any solutions.
*   **Extended Thinking** ⚡: When using a Claude model with extended thinking enabled, the agent should use its reasoning budget to silently pre-plan the best trimming strategy and section selection *before* writing any files — ensuring the first compile attempt is as close to correct as possible.

## Formatting Standards

*   **Experiences**: All professional experiences must be structured using the `\resumeSubheading` and `\resumeItemListStart` macros defined in the project's preamble.
*   **Projects**: Ensure all project entries include placeholders for hyperlinks, utilizing the existing project heading macros to maintain a clean and clickable layout.
*   **Skills Section**: Technology names in the Skills section must mirror the exact syntax used in the JD (e.g., if the JD says "React.js", the skills section must say "React.js", not "React" or "ReactJS").

## Bullet Point Content Guidelines

### The PAR Method (Problem-Action-Result)
Every bullet point must follow this structure. A bullet that lacks any one of these three components is invalid and must be rewritten.

*   **Problem**: What was the technical/business bottleneck?
*   **Action**: What specific tools, languages, or algorithms did you use? (e.g., Python, NumPy, Asyncio, Django, AWS).
*   **Result**: What was the measurable outcome? Must include a quantitative metric (percentages, speed-up factors, data scale) wherever one exists in `/base/`. If no metric exists for that bullet, restructure the sentence to make the scope/impact explicit (e.g., "across a team of 8", "serving 50k+ daily users"). **A bullet that ends without either a quantitative metric in `\textbf{...}` or an explicit scope statement is invalid and must be rewritten before compilation.** Vague phrase endings like "from first principles", "via GUI automation", or "across internal dashboards" with no measurable outcome are forbidden.

### Formatting Constraints
*   Always use `\textbf{...}` for quantitative metrics (numbers, percentages, scale) to make them pop for recruiters.
*   **Strictly** keep bullet points concise (maximum 2 lines; no exceptions).
*   Each entry (experience/project) must maintain at least 2 to 3 bullet points.
*   Every bullet must begin with a strong past-tense action verb. **Banned phrases**: "responsible for", "helped", "assisted", "worked on", "involved in", "contributed to". These are passive and weak — replace with a concrete verb.
*   **Keyword Integration**: Reproduce JD keywords verbatim (see Rule 8) throughout bullet points. Density matters for ATS scoring, but integration must read naturally.
*   **Verb Diversity**: Draw from a broad verb bank. Do not reuse a verb within the same job/project block. Suggested verbs: Engineered, Architected, Optimized, Automated, Accelerated, Reduced, Designed, Implemented, Developed, Deployed, Refactored, Integrated, Benchmarked, Profiled, Parallelized, Containerized, Orchestrated, Authored, Delivered, Scaled, Migrated, Spearheaded, Eliminated.

### Spacing and Visual Rhythm
*   Use `\vspace{-4pt}` immediately after `\resumeItemListStart` to maintain a tight vertical rhythm.
*   Never add double line breaks inside a `\resumeItem{}` block.
*   Ensure bullet points align vertically with the global spacing settings defined in the preamble.

### Consistency Check
*   Before finalizing a bullet point, ensure it does not repeat a verb used in the previous bullet point within the same sub-heading.
*   Maintain consistent tense (always past tense for completed work, present for ongoing research).

## Agent Automation & Frictionless Generation

To ensure the user only ever has to paste a Job Description (JD) and nothing else, the agent must perform the following inferences and actions autonomously:

1. **Autonomous Bootstrapping (MANDATORY First Step):** When given a JD, you must run the bootstrapping system **before** reading or editing any files. Execute the exact command `make bootstrap JD=<path_to_jd.txt>`. 
    * If the result is a **Tier 3 clean slate**, proceed with a standard full-tailoring run from the `/base/` directory.
    * If the result is a **Tier 2 moderate overlap**, the sections folder has been successfully populated with your closest matching archived resume. Do **NOT** discard this template or start from scratch! This template has already solved the page-budget layout and formatting. Proceed immediately to Step 2.
    * **Immediately after bootstrapping**, regardless of tier, re-read the new JD's eligibility criteria and override the graduation date in `sections/education.tex` to match the new role (see Rule 11). The bootstrapped date is always stale.
2. **Focused Wording Refinement (The 1-Turn Polish Pass):** On a Tier 2 bootstrapped draft, do not perform major restructuring. Instead, compare the bootstrapped draft against the JD to enforce **Rule 8 (exact-string keyword matching) and syntax fidelity**. 
    * If the JD uses specific phrasing, jargon, or nouns (e.g., "massively-parallel systems", "compiler overhead", "high performance computing", "multi-agent models"), you must rewrite existing bullet items to **inject these exact phrases byte-for-byte**. 
    * Never use high-level synonyms or summaries where a byte-for-byte match is possible. Your sole cognitive focus must be maximizing exact ATS string density in a single, fast compilation turn.
3. **Automatic Keyword Extraction:** The agent must parse the provided JD and extract **all** matchable keywords — every skill, tool, framework, methodology, and concept that has a corresponding entry in `/base/`. Capture the exact syntax of each keyword (including punctuation and casing) for use in Rule 8. The goal is maximum ATS keyword density, not a ranked shortlist.
4. **Automatic Prioritization & Trimming:** To guarantee a 1-page fit on the very first try without multiple compile loops, the agent must autonomously evaluate all experiences and projects in `/base/`. It must automatically prioritize those that match the extracted keywords and **proactively drop** the least relevant projects or older experiences. **The agent must not wait for the user to specify what to drop.** To fit within the 1-page budget, the agent should drop entire non-essential sections or roles to keep remaining entries robust, rather than stripping projects down to a single, metric-less sentence (maintain the 2-3 bullets per entry requirement).
5. **Zero-Friction Execution:** The user's only job is to paste the JD. The agent assumes full responsibility for making all editorial choices (trimming, rewording, selecting) to instantly produce a tailored, 1-page ATS-compliant PDF. Do not ask the user clarifying questions about what to include or exclude — make the best executive decision based on the JD.

## Execution Efficiency & Page-Budget Planning (Anti-Loop Protections)

To prevent taking wrong turns, wasting API costs, and falling into long, slow compilation loops, you must adhere to these optimization guidelines:

1. **Calculate the Element Budget First (Bias Conservative)**: Before writing any files, perform vertical height mental math. A standard 1-page resume with a compact education section has space for about **55–60 lines** of content. **Start with the most conservative layout that guarantees 1-page fit**, and only add sections if needed:
    * **Safe Default Budget**: `2 companies + 1 research lab + 2 projects (2 bullets each)` — this is your target first draft.
    * **Expanded Budget (only attempt if education is compact and first compile succeeds)**: `2 companies + 1 research lab + 3 projects (1 bullet each)`.
    * It is far cheaper to add a project after a successful first compile than to enter a 5-iteration trimming loop. **When in doubt, leave it out of the first draft.**
2. **High-Entropy Coarse Trimming**: If the first compile yields 2 pages, **do not attempt word-level or character-level micro-trimming first.** Word-level shaving takes 4–5 iterations to resolve. Instead, make an immediate, high-entropy structural cut: drop a non-essential secondary project, remove an entire secondary research role, or eliminate a full bullet point. Shave off major blocks first to drop the page count to 1 instantly, then fine-tune.
3. **Log-Driven Debugging**: If compilation fails or overflows, check `output/main.log` on the first iteration to find the exact line and vertical box overflow (`Overfull \vbox`) instead of guessing.
