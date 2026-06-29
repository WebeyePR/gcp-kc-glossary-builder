import os
import requests
import google.auth
from google.auth.transport.requests import Request

def get_auth_token():
    try:
        credentials, default_project_id = google.auth.default()
        credentials.refresh(Request())
        return credentials.token, default_project_id
    except google.auth.exceptions.DefaultCredentialsError:
        print("\n[❌ 鉴权失败] 未找到有效的 Google Cloud 凭据。")
        print("请通过以下方式之一配置凭据：")
        print("1. (推荐) 安装 Google Cloud SDK (gcloud) 并执行：")
        print("   gcloud auth application-default login")
        print("   安装指南: https://cloud.google.com/sdk/docs/install")
        print("2. 或者设置环境变量 GOOGLE_APPLICATION_CREDENTIALS 指向您的 Service Account Key JSON 文件。")
        raise SystemExit(1)

def resolve_project_number(token, project_id):
    """Fetches the project number for a given project_id using the Cloud Resource Manager API."""
    url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}"
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json().get("projectNumber")
    elif res.status_code == 403:
        print(f"\n[❌ IAM 权限不足] 无法获取项目 {project_id} 的 Project Number，请提供 --project_num 参数或确保具有 resourcemanager.projects.get 权限。")
        raise SystemExit(1)
    else:
        print(f"\n[❌ 获取 Project Number 失败] {res.text}。请尝试显式提供 --project_num 参数。")
        raise SystemExit(1)

def get_gcp_params(args):
    """
    Resolves project_id, project_num, location, and glossary_id based on args, env vars, and gcloud config.
    """
    token, default_project_id = get_auth_token()
    
    # 1. Resolve Project ID
    project_id = getattr(args, "project_id", None) or os.environ.get("GLOSSARY_PROJECT_ID") or default_project_id
    if not project_id:
        print("\n[❌ 缺少参数] 未能自动获取 project_id。请通过 --project_id 参数或 GLOSSARY_PROJECT_ID 环境变量提供。")
        raise SystemExit(1)
        
    # 2. Resolve Project Number
    project_num = getattr(args, "project_num", None) or os.environ.get("GLOSSARY_PROJECT_NUM")
    if not project_num:
        print(f"[*] 正在自动解析项目 {project_id} 的 Project Number...")
        project_num = resolve_project_number(token, project_id)
        
    # 3. Resolve Location
    location = getattr(args, "location", None) or os.environ.get("GLOSSARY_LOCATION") or "us"
    
    # 4. Resolve Glossary ID
    glossary_id = getattr(args, "glossary_id", None) or os.environ.get("GLOSSARY_ID") or "business-glossary"
    
    return token, project_id, project_num, location, glossary_id
