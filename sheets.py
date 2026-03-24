import os
import json
from datetime import datetime, timezone, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
SERVICE_ACCOUNT_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

def get_service():
    creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)

def ensure_header(sheets):
    result = sheets.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="오늘마감!A1:F1"
    ).execute()
    if not result.get("values"):
        sheets.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range="오늘마감!A1",
            valueInputOption="RAW",
            body={"values": [["수집일", "프로젝트명", "URL", "카테고리", "펀딩금액", "달성률"]]}
        ).execute()

def upload_to_sheets(data: list):
    service = get_service()
    sheets = service.spreadsheets()
    ensure_header(sheets)

    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst).strftime("%Y-%m-%d")

    rows = [[
        today,
        item.get("title", ""),
        item.get("url", ""),
        item.get("category", ""),
        item.get("funding_amount", ""),
        item.get("achievement_rate", ""),
    ] for item in data]

    sheets.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="오늘마감!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows}
    ).execute()

    print(f"{today} | {len(data)}건 업로드 완료")