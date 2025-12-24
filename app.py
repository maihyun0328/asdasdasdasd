import json
import os
from datetime import datetime, timedelta, timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ===== 설정 =====
TARGET_WORD = "원고"   # 이 단어가 제목에 있으면 삭제
CHECK_MINUTES = 180    # 최근 3시간 영상만 검사 (원하면 조절)

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

def build_youtube():
    raw = os.environ.get("YT_TOKEN_JSON")
    if not raw:
        raise RuntimeError("YT_TOKEN_JSON secret not found")

    info = json.loads(raw)
    creds = Credentials.from_authorized_user_info(info, SCOPES)
    return build("youtube", "v3", credentials=creds)

def is_recent(published_at: str) -> bool:
    published = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return published >= now - timedelta(minutes=CHECK_MINUTES)

def main():
    youtube = build_youtube()

    res = youtube.search().list(
        part="snippet",
        forMine=True,
        type="video",
        order="date",
        maxResults=25
    ).execute()

    deleted = 0

    for item in res.get("items", []):
        video_id = item["id"]["videoId"]
        snippet = item["snippet"]

        title = snippet.get("title", "")
        published_at = snippet.get("publishedAt", "")

        if not published_at or not is_recent(published_at):
            continue

        if TARGET_WORD in title:
            youtube.videos().delete(id=video_id).execute()
            print(f"[DELETED] {title} ({video_id})")
            deleted += 1

    print(f"Finished. deleted={deleted}")

if __name__ == "__main__":
    main()
