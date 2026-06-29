import argparse
import json
import time
import os
import sys

# Import shared utilities
sys.path.append(os.path.dirname(__file__))
from gcp_utils import get_gcp_params
import time
from google.cloud import dataplex_v1
from google.api_core.exceptions import AlreadyExists, PermissionDenied

def robust_call(func, *args, **kwargs):
    for attempt in range(3):
        try:
            return func(*args, **kwargs)
        except AlreadyExists:
            raise
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(1)

def main():
    parser = argparse.ArgumentParser(description="Deep bind Aspects and Definition Links for Glossary Terms.")
    parser.add_argument("--project_id", required=False, help="GCP Project ID (默认: 自动获取)")
    parser.add_argument("--project_num", required=False, help="GCP Project Number (默认: 自动解析)")
    parser.add_argument("--location", default=None, help="Dataplex Location")
    parser.add_argument("--glossary_id", required=False, help="Glossary ID")
    parser.add_argument("--json_file", required=True, help="Path to Extracted JSON")
    parser.add_argument("--dataset", required=True, help="BigQuery Dataset containing related tables")
    args = parser.parse_args()

    token, project_id, project_num, location, glossary_id = get_gcp_params(args)
    
    # We must construct a client but we should pass credentials explicitly if we can,
    # or just let Dataplex client use the default ADC. Since get_gcp_params verifies ADC, it will work.
    client = dataplex_v1.CatalogServiceClient(transport="rest")
    
    with open(args.json_file, 'r', encoding='utf-8') as f:
        terms_data = json.load(f)
        
    term_mapping = {}
    for i, item in enumerate(terms_data):
        display_name = item.get("term", "").strip()
        term_id = f"term-v3-{i+1:03d}"
        entry_name = f"projects/{project_num}/locations/{location}/entryGroups/@dataplex/entries/projects/{project_num}/locations/{location}/glossaries/{glossary_id}/terms/{term_id}"
        term_mapping[display_name] = entry_name

    for i, item in enumerate(terms_data):
        display_name = item.get("term", "").strip()
        term_id = f"term-v3-{i+1:03d}"
        entry_name = term_mapping[display_name]
        
        print(f"\nProcessing [{display_name}]...")
        
        # 1. Attach Aspects
        aspects_to_update = {}
        
        desc_parts = [f"**定义**: {item.get('definition', '')}"]
        if item.get('calculation_logic'):
            desc_parts.append(f"**计算逻辑**:\n```sql\n{item.get('calculation_logic')}\n```")
            
        overview_aspect = dataplex_v1.Aspect()
        overview_aspect.aspect_type = "dataplex-types:overview"
        overview_aspect.data = {"content": "\n\n".join(desc_parts)}
        aspects_to_update["dataplex-types.global.overview"] = overview_aspect
        
        custom_aspect_key = f"{project_num}.{location}.retail-business-logic"
        data = {}
        if item.get("calculation_logic"): data["calculation_logic"] = item.get("calculation_logic")
        if item.get("related_tables") and item.get("related_tables") != ["*"]: data["related_tables"] = item.get("related_tables")
        if item.get("related_columns"): data["related_columns"] = item.get("related_columns")
        if item.get("stewards"): data["stewards"] = item.get("stewards")
        if item.get("sensitivity"): data["sensitivity"] = item.get("sensitivity")
        if item.get("lifecycle_status"): data["lifecycle_status"] = item.get("lifecycle_status")
        
        if data:
            custom_aspect = dataplex_v1.Aspect()
            custom_aspect.aspect_type = f"projects/{project_num}/locations/{location}/aspectTypes/retail-business-logic"
            custom_aspect.data = data
            aspects_to_update[custom_aspect_key] = custom_aspect

        try:
            entry = dataplex_v1.Entry()
            entry.name = entry_name
            entry.aspects = aspects_to_update
            req = dataplex_v1.UpdateEntryRequest(entry=entry, update_mask={"paths": ["aspects"]})
            robust_call(client.update_entry, request=req)
            print("  [+] Aspects updated")
        except PermissionDenied:
            print(f"  [-] ❌ IAM 权限不足 (403): 无法更新 Aspect，请确认您具有 Dataplex Catalog Admin 权限。")
        except Exception as e:
            print(f"  [-] Failed to update aspects: {e}")

        # 2. Definition Links
        related_tables = item.get("related_tables", [])
        related_columns = item.get("related_columns", [])
        if related_tables and related_tables != ["*"]:
            for table in related_tables:
                table = table.strip()
                if not table: continue
                
                table_entry = f"projects/{project_num}/locations/{location}/entryGroups/@bigquery/entries/bigquery.googleapis.com/projects/{project_id}/datasets/{args.dataset}/tables/{table}"
                link_id = f"def-v3-{term_id}-bq-{table.encode('utf-8').hex()[:8]}"
                
                link = dataplex_v1.EntryLink(
                    entry_link_type="projects/dataplex-types/locations/global/entryLinkTypes/definition",
                    entry_references=[
                        dataplex_v1.EntryLink.EntryReference(
                            name=table_entry,
                            type_=dataplex_v1.EntryLink.EntryReference.Type.SOURCE
                        ),
                        dataplex_v1.EntryLink.EntryReference(
                            name=entry_name,
                            type_=dataplex_v1.EntryLink.EntryReference.Type.TARGET
                        )
                    ]
                )
                
                try:
                    robust_call(client.create_entry_link, request=dataplex_v1.CreateEntryLinkRequest(
                        parent=f"projects/{project_num}/locations/{location}/entryGroups/@bigquery",
                        entry_link_id=link_id,
                        entry_link=link
                    ))
                    print(f"  [+] Definition Link created -> {table}")
                except AlreadyExists:
                    print(f"  [ℹ️] Definition Link already exists -> {table}")
                except PermissionDenied:
                    print(f"  [-] ❌ IAM 权限不足 (403): 无法创建关联表 Entry Link，请确认相关 BigQuery 表的权限。")
                except Exception as e:
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print(f"  [ℹ️] Definition Link already exists -> {table}")
                    elif "not found" in str(e).lower() and "bigquery" in str(e).lower():
                         print(f"  [-] BigQuery table entry not found -> {table}")
                    else:
                         print(f"  [-] Failed to link table {table}: {e}")
                
                # --- NEW LOGIC: Bidirectional Column Aspect Binding ---
                if related_columns and related_columns != ["*"]:
                    try:
                        print(f"  [+] Injecting Business Context into BigQuery Columns for {table}...")
                        bq_entry = client.get_entry(name=table_entry)
                        
                        col_aspects_to_update = {}
                        if bq_entry.aspects:
                            col_aspects_to_update = dict(bq_entry.aspects)
                            
                        col_updated = False
                        for col in related_columns:
                            col = col.strip()
                            if not col: continue
                            
                            aspect_key = f"dataplex-types.global.overview@{col}"
                            col_aspect = dataplex_v1.Aspect()
                            col_aspect.aspect_type = "dataplex-types:overview"
                            col_aspect.data = {
                                "content": f"**关联业务术语 (Business Term)**: {display_name}\n\n**计算逻辑 (Calculation Logic)**:\n```sql\n{item.get('calculation_logic', 'N/A')}\n```"
                            }
                            col_aspects_to_update[aspect_key] = col_aspect
                            col_updated = True
                            
                        if col_updated:
                            update_bq_req = dataplex_v1.UpdateEntryRequest(
                                entry=dataplex_v1.Entry(name=table_entry, aspects=col_aspects_to_update),
                                update_mask={"paths": ["aspects"]}
                            )
                            robust_call(client.update_entry, request=update_bq_req)
                            print(f"      -> Injected business context into {len(related_columns)} columns of {table}.")
                    except PermissionDenied:
                        print(f"      [-] ❌ IAM 权限不足 (403): 无法将业务信息注入 BigQuery 字段切面，请确认表权限。")
                    except Exception as e:
                        print(f"      [-] Failed to inject column aspects into BigQuery table {table}: {e}")

if __name__ == "__main__":
    main()
