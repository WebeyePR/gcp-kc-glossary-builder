---
name: business-glossary-extractor
description: Advanced Nuwa/Luban-distilled skill for extracting, chunking, deduplicating, formatting unstructured business documents into a Dataplex-ready Business Glossary JSON, and providing LRO-safe automation scripts for importing, deep binding, and deleting.
---

# Business Glossary Extractor (Nuwa/Luban Distilled)

This skill provides an enterprise-grade automated pipeline for extracting Business Glossary definitions from unstructured data sources (Wikis, PRDs, large text files, multiple documents) and robust scripts to synchronize them into Google Cloud Dataplex.

It is designed with robust state management, Map-Reduce handling for large files, strict validation gates for Google Cloud Dataplex, and AI-optimized serialization to prevent hallucination during Text-to-SQL tasks.

## [Trigger & Sensing]
**Activate this skill when:** 
The user asks to "extract terms", "summarize a dictionary", "process these docs into a glossary", "generate a business glossary json", "import the glossary to dataplex", "delete all terms", or "deep bind aspects".

## [State Machine Workflow]

Follow these states sequentially. Do not skip validation steps.

### State 1: Data Ingestion & Chunking (Map Phase)
1. **Analyze Inputs**: If the user provides a directory or multiple files, use `list_dir`. If the files are large (e.g., > 1000 lines of text), you MUST process them in overlapping chunks.
2. **Chunking Strategy**: 
   - Read the file sequentially using `view_file` with `StartLine` and `EndLine` (e.g., lines 1-300, 250-550 to maintain context).
   - If there are multiple documents, process one document at a time.
   - For each chunk, identify business terms, metrics, KPIs, dimensions, and their contextual definitions or calculation formulas.

### State 2: Semantic Extraction & Alignment (Reduce Phase)
1. Maintain a global working memory (scratchpad JSON) of extracted terms.
2. **Deduplication (Entity Resolution)**: As you process new chunks, check if a term already exists.
   - *Synonyms*: If a new chunk uses a synonym (e.g., "5L Water" vs "Large Pack Water"), merge them into the `synonyms` array.
   - *Conflict Resolution*: If definitions differ, merge the nuances gracefully. Do NOT overwrite existing logical formulas unless the new chunk provides a clearly more detailed SQL/formula.

### State 3: AI-Optimized Structuring (Anti-Hallucination)
For every term in your global memory, you must format it specifically to optimize it for AI/LLM retrieval (RAG). **DO NOT use native Synonym terms or Related terms relationships which are prone to Retrieval truncation.**

Instead, flatten all critical logic into the `description` field using a structured Markdown format.

Your intermediate JSON should look like this:
```json
{
  "category": "The business category name (e.g., 商品类)",
  "category_desc": "Description of this category",
  "term": "The display name (e.g., 5水活跃)",
  "definition": "The pure business definition.",
  "calculation_logic": "SQL or pseudo-code...",
  "related_tables": ["v_trd_dist_ord_dtl"],
  "related_columns": ["capacity", "ctg_name"],
  "synonyms": ["5水", "5水SKU", "5水SKU门店"]
}
```

**CRITICAL STEP**: Before finalizing the JSON, you MUST concatenate these fields into a rich `description` string using this exact Markdown template:
`**定义**: {definition}\n\n**同义词**: {synonyms}\n\n**关联表**: {related_tables}\n\n**关联字段**: {related_columns}\n\n**计算逻辑**: {calculation_logic}`

If information is missing, omit that line — **DO NOT HALLUCINATE**.

### State 4: Validation & Quality Gate (Dataplex Constraints)
Before outputting, you MUST run these checks over your generated JSON:
1. **Length Check**: Are there any 1-character terms? (Dataplex requires >= 2 chars). If yes, append a relevant suffix (e.g., "入" -> "入数", "单" -> "单号").
2. **Whitespace Check**: Strip all leading and trailing whitespace from the `term` field.
3. **Completeness Audit**: Count how many terms lack `calculation_logic` or `related_tables`.

### State 5: Output & Handoff
1. Write the final validated JSON to the artifacts directory as `Business_Glossary_Extracted_V3.json` (or similar).
2. Present a **Review Dashboard** to the user in your response:
   - Total terms extracted.
   - Number of terms merged/deduplicated.
   - Number of terms missing technical bindings (Requires Human Review).
3. Ask the user: *"Would you like to manually review the JSON, or should I proceed to execute the `import_glossary.py` script to upload this to your Data Catalog?"*

## [Automation Scripts (Toolbelt)]
You have access to specialized Python scripts in the `scripts/` directory of this skill.
Always review the script parameters by reading the script file before executing it.

*   `scripts/import_glossary.py`: Use this to parse the Extracted JSON and import Categories and Terms into Dataplex. This script safely handles Long-Running Operations (LROs) and sets the `description` correctly.
*   `scripts/delete_glossary.py`: Use this to interactively list or forcefully delete all terms and categories inside a glossary. Useful for clean-slate recreations.
*   `scripts/bind_aspects.py`: Use this for "Deep Binding". It scans the terms in the glossary, looks at their `description` to find `related_tables`, and attaches Dataplex Aspects (`has_calculation`, `has_physical_mapping`) and BigQuery Entry links automatically.

## [Prompting Techniques for Extraction]
When reading chunks, silently apply this internal prompt logic:
*Does this paragraph define a metric? Does it mention a table? Is this a completely new term, or an elaboration on a term I found in Chunk 1?*
