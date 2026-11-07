from datetime import date, datetime, timedelta, timezone
import os
import requests

API_KEY = os.environ.get("TMDB_API_KEY")
if not API_KEY:
    raise SystemExit("找不到環境變數 TMDB_API_KEY")

movies = []
page = 1
while len(movies) < 100:
    res = requests.get(
        "https://api.themoviedb.org/3/movie/now_playing",
        params={"api_key": API_KEY, "language": "zh-TW", "region": "TW", "page": page},
        timeout=15,
    )
    res.raise_for_status()
    data = res.json()
    movies.extend(data.get("results", []))
    if page >= data.get("total_pages", 1):
        break
    page += 1
movies = movies[:100]

def clean(text):
    return (text or "").replace("|", "｜").replace("\n", " ").strip()

today = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d")

lines = [
    "---",
    f"title: 最近上映電影（{today}）",
    f"date: {today} 16:00:00",
    "categories: 電影",
    "tags: 電影",
    "---",
    "",
    "資料來源：TMDB。此產品使用 TMDB API，但未經 TMDB 認可或認證。",
    "",
    "| 海報 | 片名 | 上映日 | 評分 | 簡介 |",
    "|:--:|:--|:--|--:|:--|",
]

for m in movies:
    poster = (
        f"![{clean(m.get('title'))}](https://image.tmdb.org/t/p/w154{m['poster_path']})"
        if m.get("poster_path") else ""
    )
    overview = clean(m.get("overview"))
    if len(overview) > 60:
        overview = overview[:60] + "…"
    lines.append(
        f"| {poster} | {clean(m.get('title'))} | {m.get('release_date', '')} "
        f"| {m.get('vote_average', 0):.1f} | {overview} |"
    )

os.makedirs("source/_posts", exist_ok=True)
path = f"source/_posts/movies-{today}.md"
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"已產生 {path}，共 {len(movies)} 部")