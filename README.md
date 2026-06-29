# Business Glossary Extractor

An enterprise-grade, Nuwa/Luban-distilled automated pipeline for extracting Business Glossary definitions from unstructured data sources (Wikis, PRDs, large text files, multiple documents) and synchronizing them into Google Cloud Dataplex.

## 🌟 Key Features

1. **Map-Reduce Ingestion**: Break through LLM context limits. Safely ingest massive documents with overlapping chunking strategies.
2. **Entity Resolution (Deduplication)**: Intelligently merge synonyms and conflicting definitions on the fly.
3. **AI-Optimized Structuring**: Flattens logical formulas, related tables, and physical columns into a structured Markdown `Description` field to completely eradicate AI hallucination in Text-to-SQL tasks.
4. **Dataplex Toolbelt**: Comes with robust, argument-driven Python automation scripts to safely handle Dataplex Long-Running Operations (LROs) and deep bindings.

## 🚀 Architecture (5-State Machine)

1. **Data Ingestion & Chunking (Map Phase)**: Overlapping reads for context preservation.
2. **Semantic Extraction & Alignment (Reduce Phase)**: Global memory for term deduplication and conflict resolution.
3. **AI-Optimized Structuring**: Enforces strict Markdown schemas to optimize for Retrieval-Augmented Generation (RAG).
4. **Validation & Quality Gate**: Dataplex length checks, whitespace stripping, and completeness auditing.
5. **Output & Handoff**: Review dashboard and automated execution handoff.

## 📦 Toolbelt (Scripts)

Install dependencies first:
```bash
pip install -r requirements.txt
```

### 1. Import Glossary (`import_glossary.py`)
Parses the extracted JSON and imports Categories and Terms into Dataplex, handling asynchronous LROs seamlessly.
```bash
python scripts/import_glossary.py --project_id=YOUR_PROJECT --project_num=YOUR_PROJECT_NUM --glossary_id=YOUR_GLOSSARY_ID --json_file=extracted.json
```

### 2. Deep Binding (`bind_aspects.py`)
Scans terms, parses their `Description` for related tables, and automatically attaches Dataplex Aspects (`has_calculation`, `has_physical_mapping`) and BigQuery Entry Links.
```bash
python scripts/bind_aspects.py --project_id=YOUR_PROJECT --project_num=YOUR_PROJECT_NUM --glossary_id=YOUR_GLOSSARY_ID --json_file=extracted.json --dataset=YOUR_BQ_DATASET
```

### 3. Cleanup (`delete_glossary.py`)
Safely performs a cascading deletion (Terms -> Categories -> Glossary) to avoid GCP `400 Failed Precondition` errors.
```bash
python scripts/delete_glossary.py --project_id=YOUR_PROJECT --project_num=YOUR_PROJECT_NUM --glossary_id=YOUR_GLOSSARY_ID
```

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
