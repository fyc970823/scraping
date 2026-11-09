from datetime import datetime, timedelta, timezone
import os
import sys

import pandas as pd
import requests

URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
headers = {"User-Agent": "Mozilla/5.0"}

res = requests.get(URL, headers=headers, timeout=15)
res.raise_for_status()
df = pd.DataFrame(res.json())
print("欄位：", list(df.columns))

if df.empty or "Date" not in df.columns:
    raise SystemExit("TWSE API 沒有回傳可用的交易資料或 Date 欄位。")

# 取 API 回傳資料中最新的民國日期（格式例如 1151109）。
raw_dates = df["Date"].dropna().astype(str).str.strip()
valid_dates = raw_dates[raw_dates.str.fullmatch(r"\d{7}")]
if valid_dates.empty:
    raise SystemExit(f"TWSE API 回傳的日期格式不正確：{raw_dates.head(3).tolist()!r}")

raw = max(valid_dates)
roc_year, month, day = int(raw[:3]), int(raw[3:5]), int(raw[5:7])
try:
    market_date = datetime(roc_year + 1911, month, day).date()
except ValueError as exc:
    raise SystemExit(f"TWSE API 回傳了無效日期：{raw!r}") from exc

taipei_tz = timezone(timedelta(hours=8))
today = datetime.now(taipei_tz).date()
if market_date > today:
    raise SystemExit(f"TWSE API 日期 {market_date} 晚於台灣今天 {today}，請檢查 API 資料。")
if market_date < today:
    print(
        f"::notice::略過台股文章：TWSE 最新資料日期為 {market_date}，"
        f"台灣今天是 {today}。可能是週末、休市日或資料尚未發布。"
    )
    sys.exit(0)

date = market_date.isoformat()

for col in ["TradeVolume", "ClosingPrice", "Change"]:
    df[col] = pd.to_numeric(
        df[col].astype(str).str.replace(",", "").str.strip(),
        errors="coerce",
    )

top100 = df.sort_values("TradeVolume", ascending=False).head(100)

lines = [
    "---",
    f"title: 台股成交量前 100 名（{date}）",
    f"date: {date} 15:30:00",
    "categories: 台股",
    "tags: 台股",
    "---",
    "",
    "資料來源：臺灣證券交易所 OpenAPI",
    "",
    "| # | 代號 | 名稱 | 收盤價 | 漲跌 | 成交量（股） |",
    "|--:|:--|:--|--:|--:|--:|",
]
for i, (_, r) in enumerate(top100.iterrows(), 1):
    change = "" if pd.isna(r["Change"]) else f"{r['Change']:+g}"
    lines.append(
        f"| {i} | {r['Code']} | {r['Name']} | {r['ClosingPrice']:g} "
        f"| {change} | {int(r['TradeVolume']):,} |"
    )

os.makedirs("source/_posts", exist_ok=True)
path = f"source/_posts/top100-{date}.md"
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print("已產生", path)
