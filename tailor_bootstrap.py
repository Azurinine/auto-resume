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
        print(f"Recommending instant reuse of existing PDF: 'output/{best_match}.pdf'")
        print(f"Bootstrapping sections from '{best_match}' for safety.")
        
        # Copy cached files
        archive_src = os.path.join(ARCHIVE_DIR, best_match)
        for f in os.listdir(archive_src):
            if f.endswith(".tex"):
                shutil.copy(os.path.join(archive_src, f), os.path.join(SECTIONS_DIR, f))
        print("Done. Workspace successfully bootstrapped.")
        
    elif best_score >= threshold_good:
        print(f"⚡ TIER 2 MATCH (>= {threshold_good:.0%}): MODERATE overlap!")
        print(f"Bootstrapping starting draft from archived folder: 'archive/{best_match}/'")
        print("This preserves visual layout decisions (exactly 1 page) and high-quality reframing.")
        print("The agent will only need a rapid 1-turn 'polish' run to align exact-string phrasing!")
        
        # Copy cached files
        archive_src = os.path.join(ARCHIVE_DIR, best_match)
        for f in os.listdir(archive_src):
            if f.endswith(".tex"):
                shutil.copy(os.path.join(archive_src, f), os.path.join(SECTIONS_DIR, f))
        print("Done. Workspace successfully bootstrapped.")
        
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
            
    # 2. Extract keywords for registry — only from the JD to avoid LaTeX noise
    keywords = []
    if jd_path and os.path.exists(jd_path):
        with open(jd_path, 'r') as f:
            jd_content = f.read()
        keywords = extract_keywords(jd_content)
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resume Semantic Cache & Bootstrap Manager")
    subparsers = parser.add_argument_group("actions")
    
    parser.add_argument("--bootstrap", help="Path to Job Description file to bootstrap sections/", type=str)
    parser.add_argument("--archive", help="Name to archive current sections/ to", type=str)
    parser.add_argument("--jd", help="Path to JD for keyword extraction (use with --archive)", type=str)
    
    args = parser.parse_args()
    
    if args.bootstrap:
        bootstrap(args.bootstrap)
    elif args.archive:
        archive_sections(args.archive, args.jd)
    else:
        parser.print_help()
