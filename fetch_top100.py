from datetime import datetime
import os
import sys

import pandas as pd
import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
headers = {"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"}

res = requests.get(URL, headers=headers, timeout=15)
res.raise_for_status()
df = pd.DataFrame(res.json())

required = ["Date", "Code", "Name", "TradeVolume", "TradeValue", "ClosingPrice", "Change"]
missing = [c for c in required if c not in df.columns]
if df.empty or missing:
    raise SystemExit(f"TWSE API 沒有回傳可用資料，或缺少欄位：{missing}")

raw_dates = df["Date"].dropna().astype(str).str.strip()
valid_dates = raw_dates[raw_dates.str.fullmatch(r"\d{7}")]
if valid_dates.empty:
    raise SystemExit(f"日期格式不正確：{raw_dates.head(3).tolist()!r}")

raw = max(valid_dates)
try:
    market_date = datetime(int(raw[:3]) + 1911, int(raw[3:5]), int(raw[5:7])).date()
except ValueError as exc:
    raise SystemExit(f"無效日期：{raw!r}") from exc

date = market_date.isoformat()
path = f"source/_posts/top100-{date}.md"

# 這一天已經有文章：休市日，或已經處理過
if os.path.exists(path):
    print(f"::notice::{date} 的文章已存在，沒有新交易日資料，略過。")
    raise SystemExit(0)

for col in ["TradeVolume", "TradeValue", "ClosingPrice", "Change"]:
    df[col] = pd.to_numeric(
        df[col].astype(str).str.replace(",", "").str.strip(),
        errors="coerce",
    )

top100 = df.sort_values("TradeVolume", ascending=False).head(100)

up = int((df["Change"] > 0).sum())
down = int((df["Change"] < 0).sum())
flat = int((df["Change"] == 0).sum())
total_volume = int(df["TradeVolume"].sum())
total_value = int(df["TradeValue"].sum())

summary = [
    f"[{date} 台股概況]",
    f"上漲 {up} 檔、下跌 {down} 檔、平盤 {flat} 檔",
    f"總成交量 {total_volume:,} 股、總成交值 {total_value:,} 元",
    "成交量前 5 名：",
]
for i, (_, r) in enumerate(top100.head(5).iterrows(), 1):
    change = "" if pd.isna(r["Change"]) else f"{r['Change']:+g}"
    summary.append(
        f"  {i}. {r['Code']} {r['Name']}  收 {r['ClosingPrice']:g} ({change})  "
        f"量 {int(r['TradeVolume']):,}"
    )
print("\n".join(summary))

step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
if step_summary:
    with open(step_summary, "a", encoding="utf-8") as f:
        f.write("\n".join(summary) + "\n")

lines = [
    "---",
    f"title: 台股成交量前 100 名（{date}）",
    f"date: {date} 15:30:00",
    "categories: 台股",
    "tags: 台股",
    "---",
    "",
    f"**{date} 市場概況**：上漲 {up} 檔、下跌 {down} 檔、平盤 {flat} 檔；"
    f"總成交量 {total_volume:,} 股。",
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
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print("已產生", path)
