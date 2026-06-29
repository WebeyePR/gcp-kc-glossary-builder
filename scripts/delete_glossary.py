import argparse
import requests
import google.auth
from google.auth.transport.requests import Request
import time

def main():
    parser = argparse.ArgumentParser(description="Delete a Dataplex Glossary and all its terms.")
    parser.add_argument("--project_id", required=True, help="GCP Project ID")
    parser.add_argument("--project_num", required=True, help="GCP Project Number")
    parser.add_argument("--location", default="us", help="Dataplex Location")
    parser.add_argument("--glossary_id", required=True, help="Glossary ID")
    args = parser.parse_args()

    credentials, project_id_auth = google.auth.default()
    credentials.refresh(Request())
    token = credentials.token

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Goog-User-Project": args.project_id
    }

    url_base = f"https://dataplex.googleapis.com/v1/projects/{args.project_num}/locations/{args.location}/glossaries/{args.glossary_id}"
    
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
    print(f"Glossary delete status: {res.status_code}")

    time.sleep(5)
    res_check = requests.get(url_base, headers=headers)
    if res_check.status_code == 200:
        print("Warning: Glossary is still present.")
    else:
        print("Glossary deleted successfully.")

if __name__ == "__main__":
    main()
