#!/usr/bin/env python3
"""Optional, explicit FRED downloader; does NOT run on import.

Only whitelisted FRED data URLs are queried; no user financial data is uploaded.
Network may be unavailable; failures are reported rather than fabricated.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SERIES = {
    'DGS10': ('US_NOMINAL10Y', 'https://fred.stlouisfed.org/series/DGS10'),
    'DFII10': ('US_TIPS_REAL10Y', 'https://fred.stlouisfed.org/series/DFII10'),
    'T10YIE': ('US_BREAKEVEN10Y', 'https://fred.stlouisfed.org/series/T10YIE'),
}


def latest_csv_point(series: str, contents: str) -> tuple[str, float]:
    reader = csv.DictReader(io.StringIO(contents))
    if not reader.fieldnames or series not in reader.fieldnames:
        raise ValueError(f'{series} 数据响应缺少对应列')
    date_column = 'DATE' if 'DATE' in reader.fieldnames else 'observation_date'
    if date_column not in reader.fieldnames:
        raise ValueError('数据响应缺少日期列')
    latest: tuple[str, float] | None = None
    for row in reader:
        observed = row.get(date_column, '')
        value = row.get(series, '')
        if not observed or value in ('', '.', None):
            continue
        date.fromisoformat(observed)
        latest = observed, float(value)
    if latest is None:
        raise ValueError(f'{series} 在CSV中没有有效观测')
    return latest


def collect_fred() -> list[dict]:
    rows = []
    for series, (key, page) in SERIES.items():
        url = f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}'
        request = Request(url, headers={'User-Agent': 'FinancePlannerSkill/0.2 (research; official-data-only)'})
        with urlopen(request, timeout=18) as response:
            data = response.read(3_000_001)
        if len(data) > 3_000_000:
            raise ValueError(f'{series} CSV超出安全读取上限')
        observed, number = latest_csv_point(series, data.decode('utf-8-sig'))
        rows.append({
            'id': key, 'region': 'US', 'currency':'USD', 'unit':'pct_per_year',
            'value_pct': number, 'observed_on': observed,
            'publisher': 'Board of Governors of the Federal Reserve System via FRED',
            'source_url': page, 'quality':'sourced',
        })
    return rows


def main() -> int:
    p = argparse.ArgumentParser(description='按用户允许的联网权限读取FRED官方3个长期利率指标')
    p.add_argument('--out', required=True, help='保存到私人工作目录，不要上传公开仓库')
    args = p.parse_args()
    try:
        results = collect_fred()
        result = {'retrieved_on': date.today().isoformat(), 'source':'FRED official CSV', 'observations':results}
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print('已取得FRED宏观观测值（尚未形成中国长期规划情景）：' + str(out))
        return 0
    except (HTTPError, URLError, TimeoutError, UnicodeError, ValueError, OSError) as exc:
        p.exit(2, '无法读取FRED；禁止用旧值冒充最新值，请用宿主浏览器查验或使用带时间戳的本地快照：' + str(exc)+'\n')


if __name__ == '__main__':
    raise SystemExit(main())
