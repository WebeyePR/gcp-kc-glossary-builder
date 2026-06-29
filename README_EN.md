# GCP KC Glossary Builder

> **The Hook**: Cures "business term hallucination" in LLM Text-to-SQL tasks. Automatically distills scattered, unstructured business documents into a structured data dictionary in Google Dataplex, and establishes bidirectional lineage binding from terms directly to BigQuery physical columns.

[![Agent Skill](https://img.shields.io/badge/Agent-Skill-blue.svg)](https://github.com/WebeyePR/gcp-kc-glossary-builder) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*Read this in other languages: [English](README_EN.md), [简体中文](README.md).*


## 🎯 When do you need this?

1. **RAG / Text-to-SQL implementations getting stuck**: The LLM misunderstands your internal business jargon (e.g., confusing "5-water store" with "a store selling 5 waters"), causing generated SQL to fail completely. You need to feed the true business logic into the AI's retrieval foundation.
2. **Manual data dictionary maintenance is painful**: The business team writes tons of PRDs and Wikis, and data engineers have to manually copy-paste categories, names, and formulas into Google Knowledge Catalog every day, which is error-prone and tedious.
3. **Metrics and physical tables are disconnected**: The dictionary is just a dictionary, and the data warehouse is just a warehouse. You don't know where to query when looking at the dictionary, and you don't know the business meaning of a column when querying.

## 📦 What does it deliver?

1. **A high-density JSON Knowledge Graph**: Extracts standardized JSON from messy documents, including: `Category, Name, Definition, Calculation Logic, Related Tables, Related Columns, Synonyms, Stewards, Data Sensitivity, Lifecycle Status`.
2. **Automated Dataplex Injection**: Automatically generates category directories and term trees, supporting asynchronous LRO imports.
3. **Bidirectional BigQuery Column-Level Aspects**: Mounts business definitions and SQL formulas directly onto the physical columns at the bottom layer of the data warehouse. Looking at the table means looking at the documentation.

## 🚀 Quick Start

**1-Click Install (as an Agent Skill):**
This suite is perfectly compatible with the open agent skills ecosystem. You can install it directly in any terminal supporting `npx skills`:
```bash
npx skills add WebeyePR/gcp-kc-glossary-builder -g -y
```

**Connect as an MCP Server (Cursor / Claude Desktop / Windsurf):**
This tool natively supports the Model Context Protocol (MCP). Just add the following configuration to your MCP client:
```json
"mcpServers": {
  "gcp-glossary-builder": {
    "command": "uv",
    "args": [
      "run",
      "--with", "mcp>=1.0.0",
      "--with", "google-cloud-dataplex",
      "--with", "google-auth",
      "--with", "requests",
      "https://raw.githubusercontent.com/WebeyePR/gcp-kc-glossary-builder/main/mcp_server.py"
    ]
  }
}
```
*Tip: Running the remote script directly via `uv run` is the most lightweight way to integrate with MCP, granting your Cursor instant capability to orchestrate Dataplex.*


**As a standalone local automation toolbelt:**
```bash
git clone git@github.com:WebeyePR/gcp-kc-glossary-builder.git
cd gcp-kc-glossary-builder
pip install -r requirements.txt
```

## 💬 How to Trigger

Send these prompts to an AI Agent with this skill installed:
- *"Help me extract this PRD into a business glossary JSON."*
- *"Run the glossary builder and deep-bind the extracted terms to the `retail_dwh` dataset."*
- *"Clear everything in `retail-glossary` under project `my-gcp-project` to reset the dictionary."*
- *"Supplement the business metrics in this document into your glossary memory."*

## 💡 Examples

For more interaction examples, please refer to [examples/test-prompts.md](examples/test-prompts.md).

## 🆚 How is it different from existing tools?

| Dimension | Regular Regex/Scrapers | Generic LLM Chat | GCP KC Glossary Builder (This Tool) |
|---|---|---|---|
| **Context Limits** | Cannot understand natural language | Long documents get truncated or forgotten | **Map-Reduce extraction**, global memory deduplication |
| **Anti-Hallucination** | None | Generates divergent text | **Strict structured schemas**, flattens logic into Description |
| **GCP Deep Integration** | Requires reading API docs manually | Often fails on asynchronous LROs | Built-in **robust retries and reverse BigQuery Column-Level Aspect binding** |
| **Cleanup Mechanism** | Manual UI clicking only | Often hits `400 Failed Precondition` | Provides native **safe cascading deletion** script |

## 🛡️ Security Boundaries

- **Won't overwrite manual definitions blindly**: Uses soft-merging during entity resolution; won't brutally overwrite existing high-quality SQL formulas.
- **Won't secretly read unauthorized GCP projects**: All underlying scripts require explicit `--project_id` and `--glossary_id` arguments. If omitted, they will attempt to intelligently infer them from your local ADC (Application Default Credentials) and environment variables without blind guessing.
- **Interceptable before execution**: The Agent will print the refined JSON and explicitly ask *"Do you want to proceed with the import?"* before touching the production database.

## ⚙️ Parameters and Dependencies

When executing the underlying scripts, the following parameters support smart fallbacks and automatic resolution, saving you from typing complex commands:

| Parameter | CLI Flag | Environment Variable | Default Inference Logic |
|---|---|---|---|
| Project ID | `--project_id` | `GLOSSARY_PROJECT_ID` | The current gcloud default project returned by `google.auth.default()` |
| Project Number | `--project_num`| `GLOSSARY_PROJECT_NUM` | **Auto-resolved**: Query dynamically via Cloud Resource Manager API |
| Location | `--location` | `GLOSSARY_LOCATION` | Defaults to `us` |
| Glossary ID | `--glossary_id` | `GLOSSARY_ID` | Defaults to `business-glossary` |

*If the current environment lacks `gcloud` authentication, the script will fail gracefully and prompt you to run `gcloud auth application-default login` or configure `GOOGLE_APPLICATION_CREDENTIALS`, rather than throwing a messy Python stack trace.*

## 📁 File Structure

- `SKILL.md`: The execution pipeline (Map-Reduce, Schema constraints, instructions) for the AI Agent.
- `scripts/`: The physical toolbelt for AI and you to execute GCP operations:
  - `import_glossary.py`: Handles asynchronous KC term writes.
  - `bind_aspects.py`: Establishes entity links and bidirectional Column-Level Aspects.
  - `delete_glossary.py`: One-click cleanup, solving cascading dependency errors.
- `examples/`: Ready-to-copy trigger prompts (`test-prompts.md`).

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
