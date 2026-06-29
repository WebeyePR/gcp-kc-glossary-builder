import argparse
import requests
import time
import os
import sys

# Import shared utilities
sys.path.append(os.path.dirname(__file__))
from gcp_utils import get_gcp_params

def main():
    parser = argparse.ArgumentParser(description="Delete a Dataplex Glossary and all its terms.")
    parser.add_argument("--project_id", required=False, help="GCP Project ID (默认: 自动获取)")
    parser.add_argument("--project_num", required=False, help="GCP Project Number (默认: 自动解析)")
    parser.add_argument("--location", default=None, help="Dataplex Location")
    parser.add_argument("--glossary_id", required=False, help="Glossary ID")
    args = parser.parse_args()

    token, project_id, project_num, location, glossary_id = get_gcp_params(args)

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Goog-User-Project": project_id
    }

    url_base = f"https://dataplex.googleapis.com/v1/projects/{project_num}/locations/{location}/glossaries/{glossary_id}"
    
    print(f"Targeting glossary: {url_base}")
    # We must loop because terms are paginated
    page_token = ""
    deleted_count = 0
    while True:
        url_terms = f"{url_base}/terms?pageSize=1000"
        if page_token:
            url_terms += f"&pageToken={page_token}"
            
        res_terms = requests.get(url_terms, headers=headers)
        if res_terms.status_code != 200:
            if res_terms.status_code == 404:
                print("Glossary not found. Nothing to delete.")
                return
            elif res_terms.status_code == 403:
                print("\n[❌ IAM 权限不足 (403)] 无法列出术语，请确认是否具有 Dataplex Catalog Admin 权限。")
                return
            print(f"Error listing terms: {res_terms.text}")
            break

        data = res_terms.json()
        terms = data.get("terms", [])
        
        for t in terms:
            tname = t["name"]
            requests.delete(f"https://dataplex.googleapis.com/v1/{tname}", headers=headers)
            deleted_count += 1
            print(f"Deleted term: {tname.split('/')[-1]} (Total: {deleted_count})")
            
        page_token = data.get("nextPageToken")
        if not page_token:
            break

    print("Deleting Categories...")
    cat_page_token = ""
    cat_deleted_count = 0
    while True:
        url_cats = f"{url_base}/categories?pageSize=100"
        if cat_page_token:
            url_cats += f"&pageToken={cat_page_token}"
            
        res_cats = requests.get(url_cats, headers=headers)
        if res_cats.status_code == 200:
            c_data = res_cats.json()
            cats = c_data.get("categories", [])
            for c in cats:
                cname = c["name"]
                requests.delete(f"https://dataplex.googleapis.com/v1/{cname}", headers=headers)
                cat_deleted_count += 1
                print(f"Deleted category: {cname.split('/')[-1]} (Total: {cat_deleted_count})")
            
            cat_page_token = c_data.get("nextPageToken")
            if not cat_page_token:
                break
        else:
            break

    print("Deleting Glossary itself...")
    time.sleep(5)
    
    res = requests.delete(url_base, headers=headers)
    if res.status_code == 403:
        print("\n[❌ IAM 权限不足 (403)] 删除 Glossary 本体失败。")
    else:
        print(f"Glossary delete status: {res.status_code}")

    time.sleep(5)
    res_check = requests.get(url_base, headers=headers)
    if res_check.status_code == 200:
        print("Warning: Glossary is still present.")
    else:
        print("Glossary deleted successfully.")

if __name__ == "__main__":
    main()
