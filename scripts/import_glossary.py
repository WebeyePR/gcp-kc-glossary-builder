import json
import argparse
import os
import sys
import requests
import uuid

# Import shared utilities
sys.path.append(os.path.dirname(__file__))
from gcp_utils import get_gcp_params

def create_or_get_glossary(token, project_id, project_num, location, glossary_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id
    }
    
    url = f"https://dataplex.googleapis.com/v1/projects/{project_num}/locations/{location}/glossaries/{glossary_id}"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return url.replace("https://dataplex.googleapis.com/v1/", "")
        
    print(f"Glossary {glossary_id} not found, creating...")
    create_url = f"https://dataplex.googleapis.com/v1/projects/{project_num}/locations/{location}/glossaries?glossaryId={glossary_id}"
    payload = {
        "displayName": "业务术语表 (Business Glossary)",
        "description": "自动化提取的业务术语表"
    }
    res_create = requests.post(create_url, headers=headers, json=payload)
    if res_create.status_code == 200:
        op_name = res_create.json()["name"]
        print(f"Glossary creation operation: {op_name}, waiting...")
        import time
        while True:
            op_res = requests.get(f"https://dataplex.googleapis.com/v1/{op_name}", headers=headers)
            if op_res.status_code == 200:
                op_data = op_res.json()
                if op_data.get("done"):
                    break
            time.sleep(2)
        return url.replace("https://dataplex.googleapis.com/v1/", "")
    elif res_create.status_code == 403:
        raise Exception("\n[❌ IAM 权限不足 (403 Forbidden)]\n请确认当前账号对项目具有 Dataplex Catalog Admin 权限，或您的凭据是否已过期。")
    else:
        raise Exception(f"Failed to create Glossary: {res_create.text}")

def create_or_get_category(token, project_id, project_num, location, glossary_id, cat_name, cat_desc):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id
    }
    # First, list categories
    list_url = f"https://dataplex.googleapis.com/v1/projects/{project_num}/locations/{location}/glossaries/{glossary_id}/categories"
    res = requests.get(list_url, headers=headers)
    
    categories = res.json().get("categories", [])
    for cat in categories:
        if cat.get("displayName") == cat_name:
            return cat["name"]
            
    # Need to create it
    # Generate a category_id
    import hashlib
    # safe id formatting
    cat_id = "cat-" + hashlib.md5(cat_name.encode('utf-8')).hexdigest()[:8]
    
    create_url = f"{list_url}?categoryId={cat_id}"
    payload = {
        "parent": f"projects/{project_num}/locations/{location}/glossaries/{glossary_id}",
        "displayName": cat_name,
        "description": cat_desc
    }
    
    res = requests.post(create_url, headers=headers, json=payload)
    if res.status_code == 200:
        op_name = res.json()["name"]
        print(f"Category creation operation: {op_name}, waiting...")
        import time
        while True:
            op_res = requests.get(f"https://dataplex.googleapis.com/v1/{op_name}", headers=headers)
            if op_res.status_code == 200:
                op_data = op_res.json()
                if op_data.get("done"):
                    break
            time.sleep(2)
        return f"projects/{project_num}/locations/{location}/glossaries/{glossary_id}/categories/{cat_id}"
    elif res.status_code == 403:
        raise Exception("\n[❌ IAM 权限不足 (403 Forbidden)]\n创建类别失败，请确认是否具有 Dataplex 相应写入权限。")
    else:
        raise Exception(f"Failed to trigger category creation: {res.text}")

def create_term(token, project_id, parent_resource, term_id, payload, base_glossary_name):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id
    }
    create_url = f"https://dataplex.googleapis.com/v1/{base_glossary_name}/terms?termId={term_id}"
    
    res = requests.post(create_url, headers=headers, json=payload)
    if res.status_code == 200:
        return "CREATED"
    elif res.status_code == 409:
        return "ALREADY_EXISTS"
    elif res.status_code == 403:
        raise Exception("\n[❌ IAM 权限不足 (403 Forbidden)]\n创建术语失败，请确认是否具有 Dataplex 相应写入权限。")
    else:
        raise Exception(f"Term creation request failed: {res.text}")

def import_glossary():
    parser = argparse.ArgumentParser(description="Dataplex 业务术语表导入脚本 (带目录分类)")
    parser.add_argument("--project_id", type=str, required=False, help="GCP 项目 ID (默认: gcloud config 或 GLOSSARY_PROJECT_ID)")
    parser.add_argument("--project_num", type=str, required=False, help="GCP Project Number (默认: 自动解析或 GLOSSARY_PROJECT_NUM)")
    parser.add_argument("--location", type=str, default=None, help="Dataplex 资源位置 (Location) (默认: us 或 GLOSSARY_LOCATION)")
    parser.add_argument("--glossary_id", type=str, required=False, help="术语表 ID (默认: business-glossary 或 GLOSSARY_ID)")
    parser.add_argument("--json_file", type=str, required=True, help="提取的 JSON 文件路径")
    args = parser.parse_args()

    token, project_id, project_num, location, glossary_id = get_gcp_params(args)
    
    print(f"检查并确保术语表 {glossary_id} 存在 (Project: {project_id})...")
    create_or_get_glossary(token, project_id, project_num, location, glossary_id)

    with open(args.json_file, 'r', encoding='utf-8') as f:
        terms_data = json.load(f)

    # Gather categories
    cat_map = {}
    for item in terms_data:
        if "category" in item:
            cat_map[item["category"]] = item.get("category_desc", "")
            
    print(f"找到 {len(cat_map)} 个分类。正在创建或获取分类资源...")
    cat_resource_map = {}
    for cat_name, cat_desc in cat_map.items():
        res_name = create_or_get_category(
            token, project_id, project_num, location, glossary_id, cat_name, cat_desc
        )
        cat_resource_map[cat_name] = res_name
        print(f"  [Category] {cat_name} -> {res_name}")
        
    print(f"\n准备导入 {len(terms_data)} 个业务术语...")
    success = 0
    failed = 0
    skipped = 0

    base_glossary_name = f"projects/{project_num}/locations/{location}/glossaries/{glossary_id}"

    for i, item in enumerate(terms_data):
        term_id = f"term-v3-{i+1:03d}"
        display_name = item.get("term", f"未知术语-{i}").strip()
        if len(display_name) == 1:
            display_name = display_name + "数" if display_name == "入" else display_name + "_"
            
        desc_parts = [f"**定义**: {item.get('definition', '')}"]
        if item.get('synonyms'):
            desc_parts.append(f"**同义词**: {', '.join(item.get('synonyms'))}")
        if item.get('related_tables') and item.get('related_tables') != ["*"]:
            desc_parts.append(f"**关联表**: {', '.join(item.get('related_tables'))}")
        if item.get('related_columns'):
            desc_parts.append(f"**关联字段**: {', '.join(item.get('related_columns'))}")
        if item.get('calculation_logic'):
            desc_parts.append(f"**计算逻辑**: {item.get('calculation_logic')}")

        term_labels = {}
        if item.get("calculation_logic"):
            term_labels["has_calculation"] = "true"
        if item.get("related_tables") and item.get("related_tables") != ["*"]:
            term_labels["has_physical_mapping"] = "true"

        parent_resource = base_glossary_name
        if "category" in item and item["category"] in cat_resource_map:
            parent_resource = cat_resource_map[item["category"]]

        payload = {
            "parent": parent_resource,
            "displayName": display_name,
            "description": "\n\n".join(desc_parts),
            "labels": term_labels
        }

            
        try:
            status = create_term(token, project_id, parent_resource, term_id, payload, base_glossary_name)
            if status == "CREATED":
                print(f"  [+] 导入成功: {display_name} (ID: {term_id}) in {item.get('category', 'root')}")
                success += 1
            else:
                print(f"  [~] 已存在，跳过: {display_name} (ID: {term_id})")
                skipped += 1
        except Exception as e:
            print(f"  [-] 导入失败: {display_name} -> {e}")
            failed += 1

    print(f"\n✅ V3导入流程执行完毕！成功: {success} 个，跳过: {skipped} 个，失败: {failed} 个")

if __name__ == "__main__":
    import_glossary()
