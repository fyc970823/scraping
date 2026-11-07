import os
import requests
import pandas as pd

URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
headers = {"User-Agent": "Mozilla/5.0"}

res = requests.get(URL, headers=headers, timeout=15)
res.raise_for_status()
df = pd.DataFrame(res.json())
print("欄位：", list(df.columns))

for col in ["TradeVolume", "ClosingPrice", "Change"]:
    df[col] = pd.to_numeric(
        df[col].astype(str).str.replace(",", "").str.strip(),
        errors="coerce",
    )

top100 = df.sort_values("TradeVolume", ascending=False).head(100)

# 民國日期轉西元，例如 1151107 -> 2026-11-07
raw = str(top100.iloc[0]["Date"])
date = f"{int(raw[:-4]) + 1911}-{raw[-4:-2]}-{raw[-2:]}"

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