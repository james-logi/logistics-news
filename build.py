"""
JSON 데이터를 HTML 대시보드로 변환하는 스크립트
- data/ 폴더의 모든 JSON 파일을 읽음
- index.html 한 개를 생성
- 표준 라이브러리만 사용
"""

import json
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
KEYWORDS_FILE = ROOT / "keywords.txt"
OUT_FILE = ROOT / "index.html"


def load_keywords_file(path: Path) -> dict:
    if not path.exists():
        return {}
    categories = {}
    current_cat = None
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                current_cat = line[1:-1].strip()
                categories[current_cat] = []
            elif current_cat:
                categories[current_cat].append(line)
    return categories


def smart_excerpt(text: str, max_chars: int = 200) -> str:
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    if len(clean) <= max_chars:
        return clean
    sentences = re.split(r"(?<=[.!?。!?])\s+", clean)
    result = ""
    for s in sentences[:2]:
        if len(result) + len(s) > max_chars:
            break
        result += s + " "
    if not result:
        result = clean[:max_chars] + "…"
    return result.strip()


def is_korean(text: str) -> bool:
    if not text:
        return False
    korean = sum(1 for ch in text if "\uac00" <= ch <= "\ud7a3")
    return korean / max(len(text), 1) > 0.2


def load_all_data() -> dict:
    by_date = {}
    if not DATA_DIR.exists():
        return by_date
    for jf in sorted(DATA_DIR.glob("*.json"), reverse=True):
        date = jf.stem
        try:
            with jf.open(encoding="utf-8") as f:
                articles = json.load(f)
            by_date[date] = articles
        except Exception as e:
            print(f"[skip] {jf.name}: {e}")
    return by_date


def build_html(by_date: dict, keywords: dict) -> str:
    if not by_date:
        return "<!DOCTYPE html><html><body><h1>데이터 없음</h1><p>먼저 collect.py를 실행하세요.</p></body></html>"

    payload = {}
    for date, articles in by_date.items():
        items = []
        for a in articles:
            excerpt = smart_excerpt(a.get("summary_raw", ""), 200)
            items.append({
                "title": a.get("title", ""),
                "link": a.get("link", ""),
                "source": a.get("source", ""),
                "region": a.get("region", "domestic"),
                "tags": a.get("tags", []),
                "published": a.get("published", ""),
                "excerpt": excerpt,
                "is_korean": is_korean(a.get("title", "") + a.get("summary_raw", "")),
            })
        payload[date] = items

    payload_json = json.dumps(payload, ensure_ascii=False)
    keywords_json = json.dumps(keywords, ensure_ascii=False)
    dates = list(by_date.keys())
    latest_date = dates[0]

    return HTML_TEMPLATE.replace(
        "__PAYLOAD__", payload_json
    ).replace(
        "__KEYWORDS__", keywords_json
    ).replace(
        "__LATEST_DATE__", latest_date
    ).replace(
        "__BUILD_TIME__", datetime.now().strftime("%Y-%m-%d %H:%M")
    )


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>물류 산업 데일리 브리핑</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<style>
:root {
  --bg: #ffffff;
  --bg-soft: #f8f7f3;
  --bg-card: #ffffff;
  --bg-hover: #f1efe8;
  --border: #e5e3dc;
  --border-strong: #c9c7be;
  --text: #1a1a1a;
  --text-muted: #5a5a55;
  --text-faint: #8b8a82;
  --accent: #c8102e;
  --accent-bg: #fef2f2;
  --hot: #c8102e;
  --hot-bg: #fef2f2;
  --serif: "Noto Serif KR", "Times New Roman", serif;
}
[data-theme="dark"] {
  --bg: #131311;
  --bg-soft: #1c1c1a;
  --bg-card: #1c1c1a;
  --bg-hover: #2a2a27;
  --border: #2e2e2b;
  --border-strong: #404040;
  --text: #f0eee5;
  --text-muted: #b4b2a9;
  --text-faint: #888780;
  --accent: #ff6b7a;
  --accent-bg: #2a1518;
  --hot: #ff6b7a;
  --hot-bg: #2a1518;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, "맑은 고딕", sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
  letter-spacing: -0.01em;
}
.container { max-width: 1280px; margin: 0 auto; padding: 24px 28px 48px; }

.masthead {
  border-top: 3px solid var(--text);
  border-bottom: 0.5px solid var(--border);
  padding: 18px 0 14px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 16px;
}
.masthead-left { flex: 1; min-width: 280px; }
.brand {
  font-family: var(--serif);
  font-size: 38px;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.05;
  margin: 0;
  color: var(--text);
}
.brand-en {
  font-size: 11px;
  letter-spacing: 0.18em;
  color: var(--text-faint);
  text-transform: uppercase;
  margin-top: 4px;
  font-weight: 500;
}
.masthead-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}
.date-line { font-size: 13px; color: var(--text-muted); font-weight: 500; }
.admin-line {
  font-size: 11px;
  color: var(--text-faint);
  font-weight: 500;
  letter-spacing: 0.04em;
  margin-bottom: 2px;
}
.controls { display: flex; gap: 6px; align-items: center; }

button, select {
  font-family: inherit; font-size: 13px;
  background: var(--bg-card); color: var(--text);
  border: 0.5px solid var(--border-strong);
  border-radius: 4px; padding: 7px 12px; cursor: pointer;
  transition: all 0.12s;
  letter-spacing: -0.005em;
}
button:hover, select:hover { background: var(--bg-hover); }
button.icon { width: 32px; padding: 0; font-size: 14px; }
select { font-weight: 500; }

.tabs-region {
  display: flex; gap: 0;
  border-bottom: 0.5px solid var(--border);
  margin-bottom: 14px;
}
.tabs-region button {
  border: none; background: transparent;
  padding: 14px 20px 12px;
  border-bottom: 2px solid transparent;
  border-radius: 0;
  color: var(--text-faint);
  font-size: 14px;
  font-weight: 600;
  letter-spacing: -0.01em;
}
.tabs-region button.active {
  color: var(--text);
  border-bottom-color: var(--accent);
}

.filter-bar {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.chip-row { display: flex; gap: 5px; flex-wrap: wrap; flex: 1; }
.chip {
  font-size: 12px;
  padding: 5px 11px;
  border-radius: 999px;
  background: var(--bg-card);
  color: var(--text-muted);
  border: 0.5px solid var(--border);
  cursor: pointer;
  font-weight: 500;
  transition: all 0.12s;
  letter-spacing: -0.005em;
}
.chip:hover { color: var(--text); border-color: var(--border-strong); }
.chip.active {
  background: var(--text);
  color: var(--bg);
  border-color: var(--text);
  font-weight: 600;
}
.section-toggle { display: flex; gap: 4px; }
.section-toggle button {
  padding: 5px 12px;
  font-size: 12px;
  border-radius: 999px;
  font-weight: 500;
  color: var(--text-muted);
  border-color: var(--border);
}
.section-toggle button.active {
  background: var(--bg-soft);
  color: var(--text);
  border-color: var(--border-strong);
}

.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220px;
  gap: 12px;
  height: calc(100vh - 240px);
  min-height: 600px;
}
.content-col {
  display: grid;
  grid-template-rows: minmax(220px, 38vh) minmax(280px, 1fr);
  gap: 12px;
  min-height: 0;
}
.source-panel {
  background: var(--bg-card);
  border: 0.5px solid var(--border);
  border-radius: 8px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.source-panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: var(--bg-soft);
  border-bottom: 0.5px solid var(--border);
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  position: sticky;
  top: 0;
}
.source-clear {
  font-size: 10px;
  color: var(--text-faint);
  cursor: pointer;
  background: none;
  border: none;
  padding: 2px 6px;
  border-radius: 3px;
  text-transform: none;
  letter-spacing: 0;
}
.source-clear:hover { color: var(--accent); background: var(--accent-bg); }
.source-clear:disabled { opacity: 0.3; cursor: default; }
.source-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  cursor: pointer;
  font-size: 12px;
  border-bottom: 0.5px solid var(--border);
  transition: background 0.1s;
}
.source-item:last-child { border-bottom: none; }
.source-item:hover { background: var(--bg-hover); }
.source-item.active {
  background: var(--accent-bg);
  border-left: 2px solid var(--accent);
  padding-left: 12px;
}
.source-item-name {
  color: var(--text);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 8px;
}
.source-item.active .source-item-name { color: var(--accent); font-weight: 600; }
.source-item-count {
  font-size: 11px;
  color: var(--text-faint);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}
.source-empty {
  padding: 30px 14px;
  text-align: center;
  color: var(--text-faint);
  font-size: 12px;
}

.list {
  background: var(--bg-card);
  border: 0.5px solid var(--border);
  border-radius: 8px;
  overflow-y: auto;
}
.list-head {
  display: grid;
  grid-template-columns: 36px 100px 1fr 110px 80px 32px;
  gap: 12px;
  padding: 10px 16px;
  background: var(--bg-soft);
  border-bottom: 0.5px solid var(--border);
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  position: sticky;
  top: 0;
  z-index: 1;
}
.list-head .sortable {
  transition: color 0.12s;
}
.list-head .sortable:hover {
  color: var(--text);
}
.row {
  display: grid;
  grid-template-columns: 36px 100px 1fr 110px 80px 32px;
  gap: 12px;
  padding: 11px 16px;
  border-bottom: 0.5px solid var(--border);
  cursor: pointer;
  transition: background 0.1s;
  align-items: center;
}
.row:hover { background: var(--bg-hover); }
.row.active {
  background: var(--accent-bg);
  border-left: 3px solid var(--accent);
  padding-left: 13px;
}
.row:last-child { border-bottom: none; }
.row-num {
  font-size: 11px;
  color: var(--text-faint);
  font-variant-numeric: tabular-nums;
  font-weight: 500;
}
.row-tags { display: flex; gap: 3px; flex-wrap: wrap; overflow: hidden; }
.row-title {
  font-size: 14px;
  font-weight: 500;
  line-height: 1.4;
  color: var(--text);
  letter-spacing: -0.015em;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.row-source {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.row-date {
  font-size: 11px;
  color: var(--text-faint);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.bookmark {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 0;
  color: var(--text-faint);
  width: 32px;
  height: 32px;
  border-radius: 4px;
}
.bookmark:hover { background: var(--bg-hover); }
.bookmark.on { color: #d4a017; }
.badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 600;
  letter-spacing: -0.005em;
  white-space: nowrap;
}

.preview {
  background: var(--bg-card);
  border: 0.5px solid var(--border);
  border-radius: 8px;
  padding: 28px 36px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.preview-empty {
  margin: auto;
  text-align: center;
  color: var(--text-faint);
  font-size: 13px;
}
.preview-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 14px;
  padding-bottom: 14px;
  border-bottom: 0.5px solid var(--border);
}
.preview-source {
  font-size: 11px;
  font-weight: 600;
  color: var(--accent);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.preview-date {
  font-size: 12px;
  color: var(--text-faint);
  font-variant-numeric: tabular-nums;
}
.preview-headline {
  font-family: var(--serif);
  font-size: 30px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.025em;
  color: var(--text);
  margin: 0 0 16px;
  max-width: 880px;
}
.preview-body {
  font-size: 16px;
  line-height: 1.85;
  color: var(--text);
  margin-bottom: 24px;
  max-width: 720px;
  letter-spacing: -0.005em;
}
.preview-body::first-letter {
  font-family: var(--serif);
  font-size: 56px;
  font-weight: 700;
  float: left;
  line-height: 0.9;
  margin: 6px 8px 0 0;
  color: var(--text);
}
.preview-body.no-dropcap::first-letter { all: unset; }
.preview-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: auto;
  padding-top: 16px;
  border-top: 0.5px solid var(--border);
}
.lang-en {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 16px;
  padding: 8px 12px;
  background: var(--bg-soft);
  border-left: 2px solid var(--border-strong);
  border-radius: 0 4px 4px 0;
}
.empty {
  padding: 60px 20px;
  text-align: center;
  color: var(--text-faint);
  font-size: 13px;
}

.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.55);
  z-index: 100;
  display: none;
}
.modal-backdrop.open {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.modal {
  background: var(--bg-card);
  border-radius: 8px;
  padding: 28px;
  width: 100%;
  max-width: 760px;
  max-height: 88vh;
  overflow-y: auto;
}
.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 0.5px solid var(--border);
}
.modal-head h2 {
  font-family: var(--serif);
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin: 0;
}
.modal-tip {
  font-size: 12px;
  color: var(--text-muted);
  background: var(--bg-soft);
  padding: 12px 14px;
  border-radius: 6px;
  margin-bottom: 18px;
  line-height: 1.6;
  border-left: 2px solid var(--accent);
}
.modal-tip code {
  font-family: ui-monospace, "SF Mono", Consolas, monospace;
  background: var(--bg);
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 11px;
}
.cat-block {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 0.5px solid var(--border);
}
.cat-block:last-child { border-bottom: none; }
.cat-name {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 10px;
  color: var(--text);
}
.kw-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 10px;
}
.kw-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--bg-soft);
  border: 0.5px solid var(--border);
  border-radius: 999px;
  padding: 4px 4px 4px 11px;
  font-size: 12px;
  color: var(--text);
  font-weight: 500;
}
.kw-del {
  background: none;
  border: none;
  cursor: pointer;
  padding: 1px 6px;
  font-size: 14px;
  color: var(--text-faint);
  border-radius: 50%;
  line-height: 1;
}
.kw-del:hover { color: var(--hot); background: var(--hot-bg); }
.kw-add { display: flex; gap: 6px; align-items: center; }
.kw-add input {
  flex: 1;
  font-family: inherit;
  font-size: 13px;
  padding: 7px 11px;
  border: 0.5px solid var(--border-strong);
  border-radius: 5px;
  background: var(--bg-card);
  color: var(--text);
}
.kw-add input:focus { outline: none; border-color: var(--accent); }
.kw-add button { font-size: 12px; padding: 7px 14px; font-weight: 500; }
.modal-footer {
  display: flex; gap: 8px;
  margin-top: 20px;
  padding-top: 18px;
  border-top: 0.5px solid var(--border);
  flex-wrap: wrap;
}
.btn-primary {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
  font-weight: 600;
}
.btn-primary:hover { background: var(--accent); opacity: 0.92; }

.footer {
  text-align: center;
  color: var(--text-faint);
  font-size: 11px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 0.5px solid var(--border);
  letter-spacing: 0.02em;
}

@media (max-width: 900px) {
  .container { padding: 16px 18px 32px; }
  .brand { font-size: 28px; }
  .layout {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(200px, 35vh) minmax(280px, 1fr) auto;
    height: auto;
    min-height: auto;
  }
  .content-col {
    display: contents;
  }
  .source-panel {
    max-height: 240px;
    order: 3;
  }
  .list-head, .row {
    grid-template-columns: 28px 1fr 60px 24px;
  }
  .list-head > :nth-child(2),
  .list-head > :nth-child(4),
  .row > :nth-child(2),
  .row > :nth-child(4) { display: none; }
  .preview { padding: 20px 18px; }
  .preview-headline { font-size: 22px; }
  .preview-body { font-size: 15px; }
  .preview-body::first-letter { font-size: 42px; }
}
</style>
</head>
<body>
<div class="container">

<header class="masthead">
  <div class="masthead-left">
    <h1 class="brand">물류 산업 데일리 브리핑</h1>
    <div class="brand-en">Logistics Industry Daily Briefing</div>
  </div>
  <div class="masthead-meta">
    <div class="admin-line">관리자 : James.J</div>
    <div class="date-line" id="dateLabel">로딩 중...</div>
    <div class="controls">
      <select id="dateSelect"></select>
      <button class="icon" id="kwEdit" title="키워드 편집">⚙</button>
      <button class="icon" id="darkToggle" title="다크모드">◐</button>
    </div>
  </div>
</header>

<div class="tabs-region">
  <button data-region="domestic" class="active">국내</button>
  <button data-region="global">국외</button>
</div>

<div class="filter-bar">
  <div class="chip-row" id="chipRow"></div>
  <select id="dateRangeSel" style="font-size: 12px; padding: 5px 10px;">
    <option value="1w" selected>1주일 이내</option>
    <option value="1m">1개월 이내</option>
    <option value="3m">3개월 이내</option>
    <option value="6m">6개월 이내</option>
    <option value="1y">1년 이내</option>
    <option value="all">전부</option>
  </select>
  <div class="section-toggle">
    <button data-section="all" class="active">전체</button>
    <button data-section="bookmarked">★ 북마크</button>
  </div>
</div>

<div class="layout">
  <div class="content-col">
    <div class="list" id="listCol"></div>
    <div class="preview" id="previewCol"></div>
  </div>
  <aside class="source-panel" id="sourcePanel"></aside>
</div>

<div class="footer">마지막 빌드: __BUILD_TIME__</div>

</div>

<div class="modal-backdrop" id="kwModal">
<div class="modal" onclick="event.stopPropagation()">
  <div class="modal-head">
    <h2>키워드 편집</h2>
    <button class="icon" onclick="closeKwModal()">×</button>
  </div>
  <div class="modal-tip">
    여기서 추가/삭제하면 임시 저장됩니다. <strong>"keywords.txt 형식으로 복사"</strong> 버튼을 누른 후<br>
    프로젝트 폴더의 <code>keywords.txt</code> 파일에 붙여넣기 → 저장 → <code>collect.py</code> 다시 실행하면 반영됩니다.
  </div>
  <div id="kwBody"></div>
  <div class="modal-footer">
    <button class="btn-primary" onclick="copyKeywordsFile()">📋 keywords.txt 형식으로 복사</button>
    <button onclick="resetKwToOriginal()">원래대로 되돌리기</button>
    <div style="flex: 1;"></div>
    <button onclick="closeKwModal()">닫기</button>
  </div>
</div>
</div>

<script>
const DATA = __PAYLOAD__;
const KEYWORDS_INITIAL = __KEYWORDS__;
const LATEST = "__LATEST_DATE__";

let kwData = JSON.parse(localStorage.getItem("kwDraft") || "null") || JSON.parse(JSON.stringify(KEYWORDS_INITIAL));

const state = {
  date: LATEST,
  region: "domestic",
  section: "all",
  selected: 0,
  activeTags: new Set(),
  activeSources: new Set(),  // 우측 패널에서 선택한 출처들
  dateRange: '1w',  // '1w' (기본) | '1m' | '3m' | '6m' | '1y' | 'all'
  bookmarks: new Set(JSON.parse(localStorage.getItem("bookmarks") || "[]")),
  sortBy: null,
  sortDir: 'desc',
};

function saveBookmarks() {
  localStorage.setItem("bookmarks", JSON.stringify([...state.bookmarks]));
}

function tagBg(tag) {
  const map = {
    "1. 물류설비 공급사": ["#e1f5ee", "#0f6e56"],
    "2. 물류 서비스 기업": ["#eeedfe", "#534ab7"],
    "3. 이커머스 / 풀필먼트": ["#faece7", "#993c1d"],
    "4. 글로벌 빅테크": ["#fbeaf0", "#993556"],
    "5. 트렌드 기술": ["#faeeda", "#854f0b"],
    "6. 영업 시그널": ["#fcebeb", "#a32d2d"],
    "국가정책": ["#faeeda", "#854f0b"],
    "시설투자": ["#fcebeb", "#a32d2d"],
    "택배": ["#e6f1fb", "#185fa5"],
    "쿠팡": ["#faece7", "#993c1d"],
    "아마존": ["#faece7", "#993c1d"],
    "이커머스": ["#eeedfe", "#534ab7"],
    "물류시스템": ["#e1f5ee", "#0f6e56"],
    "물류산업": ["#f1efe8", "#5f5e5a"],
  };
  return map[tag] || ["#f1efe8", "#5f5e5a"];
}

function shortTag(tag) {
  const m = tag.match(/^\d+\.\s*(.+)$/);
  return m ? m[1] : tag;
}

function cleanSourceName(s) {
  // "[1. 물류설비 공급사] LG CNS 물류" → "LG CNS 물류"
  return s.replace(/^\[.*?\]\s*/, '');
}

function getDateCutoff() {
  // dateRange에 따라 cutoff 날짜 문자열(YYYY-MM-DD) 반환. 'all'이면 null.
  if (state.dateRange === 'all') return null;
  const today = new Date(state.date);  // 선택된 날짜 기준
  const cutoff = new Date(today);
  if (state.dateRange === '1w') {
    cutoff.setDate(cutoff.getDate() - 7);
  } else {
    const months = { '1m': 1, '3m': 3, '6m': 6, '1y': 12 }[state.dateRange] || 1;
    cutoff.setMonth(cutoff.getMonth() - months);
  }
  return cutoff.toISOString().slice(0, 10);
}

function getCurrentItems() {
  const items = (DATA[state.date] || []).filter(x => x.region === state.region);
  let filtered = items;

  // 날짜 범위 필터
  const cutoff = getDateCutoff();
  if (cutoff) {
    filtered = filtered.filter(x => {
      if (!x.published) return true;  // 날짜 없는 기사는 일단 포함
      return x.published >= cutoff;
    });
  }

  // 키워드 칩 필터
  if (state.activeTags.size > 0) {
    filtered = filtered.filter(x => x.tags.some(t => state.activeTags.has(t)));
  }

  // 출처 필터 (우측 패널)
  if (state.activeSources.size > 0) {
    filtered = filtered.filter(x => state.activeSources.has(cleanSourceName(x.source)));
  }

  // 북마크 필터
  if (state.section === "bookmarked") {
    filtered = filtered.filter(x => state.bookmarks.has(x.link));
  }

  // 정렬
  const sorted = [...filtered];
  const dir = state.sortDir === 'asc' ? 1 : -1;
  if (state.sortBy === 'tags') {
    sorted.sort((a, b) => dir * ((a.tags[0] || '').localeCompare(b.tags[0] || '')));
  } else if (state.sortBy === 'title') {
    sorted.sort((a, b) => dir * a.title.localeCompare(b.title));
  } else if (state.sortBy === 'source') {
    sorted.sort((a, b) => dir * cleanSourceName(a.source).localeCompare(cleanSourceName(b.source)));
  } else {
    sorted.sort((a, b) => {
      const da = a.published || '';
      const db = b.published || '';
      if (da !== db) return dir * (da < db ? -1 : 1);
      return 0;
    });
  }
  return sorted;
}

// 출처 목록 만들기 (현재 region/dateRange/tags 기준으로 나타나는 출처들)
function getSourceCounts() {
  // 출처 패널은 "출처 필터를 빼고" 다른 필터만 적용한 결과에서 카운트
  const items = (DATA[state.date] || []).filter(x => x.region === state.region);
  const cutoff = getDateCutoff();
  let pool = cutoff ? items.filter(x => !x.published || x.published >= cutoff) : items;
  if (state.activeTags.size > 0) {
    pool = pool.filter(x => x.tags.some(t => state.activeTags.has(t)));
  }
  if (state.section === "bookmarked") {
    pool = pool.filter(x => state.bookmarks.has(x.link));
  }
  const counts = {};
  pool.forEach(x => {
    const src = cleanSourceName(x.source);
    counts[src] = (counts[src] || 0) + 1;
  });
  return Object.entries(counts).sort((a, b) => b[1] - a[1]);
}

function getAllTags() {
  const tags = new Set();
  (DATA[state.date] || []).forEach(x => x.tags.forEach(t => tags.add(t)));
  return [...tags].sort();
}

function renderDateSelect() {
  const sel = document.getElementById("dateSelect");
  sel.innerHTML = "";
  Object.keys(DATA).forEach(d => {
    const opt = document.createElement("option");
    opt.value = d; opt.textContent = d;
    sel.appendChild(opt);
  });
  sel.value = state.date;
}

function renderDateLabel() {
  const d = new Date(state.date);
  const days = ["일","월","화","수","목","금","토"];
  document.getElementById("dateLabel").textContent =
    `${d.getFullYear()}년 ${d.getMonth()+1}월 ${d.getDate()}일 ${days[d.getDay()]}요일`;
}

function renderChips() {
  const row = document.getElementById("chipRow");
  row.innerHTML = "";
  getAllTags().forEach(tag => {
    const b = document.createElement("button");
    b.className = "chip" + (state.activeTags.has(tag) ? " active" : "");
    b.textContent = shortTag(tag);
    b.onclick = () => {
      if (state.activeTags.has(tag)) state.activeTags.delete(tag);
      else state.activeTags.add(tag);
      state.selected = 0; renderAll();
    };
    row.appendChild(b);
  });
}

function renderList() {
  const list = document.getElementById("listCol");
  const items = getCurrentItems();
  list.innerHTML = "";

  // 정렬 가능한 헤더 만들기
  const sortIndicator = (col) => {
    if (state.sortBy !== col) return '<span style="color:var(--text-faint);opacity:0.4;">↕</span>';
    return state.sortDir === 'asc'
      ? '<span style="color:var(--accent);">↑</span>'
      : '<span style="color:var(--accent);">↓</span>';
  };
  // 기본 정렬일 때 날짜 컬럼에 표시
  const dateIndicator = state.sortBy === null
    ? '<span style="color:var(--accent);">↓</span>'
    : sortIndicator('date');

  const head = document.createElement("div");
  head.className = "list-head";
  head.innerHTML = `
    <div>#</div>
    <div class="sortable" data-col="tags" style="cursor:pointer;user-select:none;">분류 ${sortIndicator('tags')}</div>
    <div class="sortable" data-col="title" style="cursor:pointer;user-select:none;">제목 ${sortIndicator('title')}</div>
    <div class="sortable" data-col="source" style="cursor:pointer;user-select:none;">출처 ${sortIndicator('source')}</div>
    <div class="sortable" data-col="date" style="cursor:pointer;user-select:none;">날짜 ${dateIndicator}</div>
    <div></div>
  `;
  list.appendChild(head);

  // 헤더 클릭으로 정렬 토글
  head.querySelectorAll(".sortable").forEach(el => {
    el.onclick = () => {
      const col = el.dataset.col;
      if (col === 'date') {
        // 날짜 컬럼: 기본(null,desc) → asc → desc → 기본
        if (state.sortBy === null) {
          state.sortBy = 'date'; state.sortDir = 'asc';
        } else if (state.sortBy === 'date' && state.sortDir === 'asc') {
          state.sortBy = 'date'; state.sortDir = 'desc';
        } else {
          state.sortBy = null; state.sortDir = 'desc';
        }
      } else {
        // 다른 컬럼: 같은 컬럼 다시 클릭하면 방향 토글, 새 컬럼은 asc
        if (state.sortBy === col) {
          if (state.sortDir === 'asc') state.sortDir = 'desc';
          else { state.sortBy = null; state.sortDir = 'desc'; }
        } else {
          state.sortBy = col; state.sortDir = 'asc';
        }
      }
      state.selected = 0;
      renderList(); renderPreview();
    };
  });

  if (items.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.innerHTML = '조건에 맞는 기사가 없습니다.<br>다른 키워드를 선택해보세요.';
    list.appendChild(empty);
    return;
  }
  items.forEach((it, i) => {
    const row = document.createElement("div");
    row.className = "row" + (i === state.selected ? " active" : "");
    const isMarked = state.bookmarks.has(it.link);
    const tagsHtml = it.tags.slice(0, 2).map(t => {
      const [bg, fg] = tagBg(t);
      return `<span class="badge" style="background:${bg};color:${fg};">${shortTag(t)}</span>`;
    }).join("");
    row.innerHTML = `
      <div class="row-num">${String(i + 1).padStart(2, '0')}</div>
      <div class="row-tags">${tagsHtml}</div>
      <div class="row-title">${it.title}</div>
      <div class="row-source">${it.source.replace(/^\[.*?\]\s*/, '')}</div>
      <div class="row-date">${it.published || '—'}</div>
      <button class="bookmark ${isMarked ? "on" : ""}" data-link="${it.link.replace(/"/g, "&quot;")}">${isMarked ? "★" : "☆"}</button>
    `;
    row.onclick = (e) => {
      if (e.target.classList.contains("bookmark")) return;
      state.selected = i; renderList(); renderPreview();
    };
    list.appendChild(row);
  });
  list.querySelectorAll(".bookmark").forEach(btn => {
    btn.onclick = (e) => {
      e.stopPropagation();
      const link = btn.dataset.link;
      if (state.bookmarks.has(link)) state.bookmarks.delete(link);
      else state.bookmarks.add(link);
      saveBookmarks(); renderList();
    };
  });
}

function renderPreview() {
  const items = getCurrentItems();
  const it = items[state.selected];
  const pv = document.getElementById("previewCol");
  if (!it) {
    pv.innerHTML = '<div class="preview-empty">위 리스트에서 기사를 선택하세요.</div>';
    return;
  }
  const cleanSource = it.source.replace(/^\[(.*?)\]\s*/, '$1 · ');
  const langNote = !it.is_korean ? `<div class="lang-en">영문 기사입니다 — 원문 또는 구글 번역 링크에서 전체 내용을 확인하세요.</div>` : "";
  const dropCapClass = it.is_korean ? '' : 'no-dropcap';
  pv.innerHTML = `
    <div class="preview-meta">
      <span class="preview-source">${cleanSource}</span>
      <span class="preview-date">${it.published || ''}</span>
    </div>
    <h2 class="preview-headline">${it.title}</h2>
    ${langNote}
    <div class="preview-body ${dropCapClass}">${it.excerpt || "(원문 발췌가 없습니다. 원문 보기를 눌러주세요.)"}</div>
    <div class="preview-actions">
      <a href="${it.link}" target="_blank" rel="noopener"><button class="btn-primary">원문 보기 ↗</button></a>
      ${!it.is_korean ? `<a href="https://translate.google.com/translate?sl=en&tl=ko&u=${encodeURIComponent(it.link)}" target="_blank" rel="noopener"><button>구글 번역 ↗</button></a>` : ""}
    </div>
  `;
}

function renderSourcePanel() {
  const panel = document.getElementById("sourcePanel");
  panel.innerHTML = "";

  const head = document.createElement("div");
  head.className = "source-panel-head";
  head.innerHTML = `
    <span>출처 (${state.activeSources.size > 0 ? state.activeSources.size + ' 선택됨' : '전체'})</span>
    <button class="source-clear" id="srcClear" ${state.activeSources.size === 0 ? 'disabled' : ''}>전체 해제</button>
  `;
  panel.appendChild(head);

  const counts = getSourceCounts();
  if (counts.length === 0) {
    const empty = document.createElement("div");
    empty.className = "source-empty";
    empty.textContent = "표시할 출처 없음";
    panel.appendChild(empty);
  } else {
    counts.forEach(([src, cnt]) => {
      const item = document.createElement("div");
      const isActive = state.activeSources.has(src);
      item.className = "source-item" + (isActive ? " active" : "");
      item.innerHTML = `
        <span class="source-item-name" title="${src.replace(/"/g, '&quot;')}">${src}</span>
        <span class="source-item-count">${cnt}</span>
      `;
      item.onclick = () => {
        if (state.activeSources.has(src)) state.activeSources.delete(src);
        else state.activeSources.add(src);
        state.selected = 0;
        renderList(); renderPreview(); renderSourcePanel();
      };
      panel.appendChild(item);
    });
  }

  document.getElementById("srcClear").onclick = () => {
    state.activeSources.clear();
    state.selected = 0;
    renderList(); renderPreview(); renderSourcePanel();
  };
}

function renderAll() {
  renderChips();
  renderList();
  renderPreview();
  renderSourcePanel();
}

document.querySelectorAll(".tabs-region button").forEach(b => {
  b.onclick = () => {
    state.region = b.dataset.region; state.selected = 0;
    state.activeSources.clear();  // region 바뀌면 출처 선택도 리셋
    document.querySelectorAll(".tabs-region button").forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    renderAll();
  };
});
document.querySelectorAll(".section-toggle button").forEach(b => {
  b.onclick = () => {
    state.section = b.dataset.section; state.selected = 0;
    document.querySelectorAll(".section-toggle button").forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    renderList(); renderPreview(); renderSourcePanel();
  };
});
document.getElementById("dateSelect").onchange = (e) => {
  state.date = e.target.value; state.selected = 0;
  state.activeSources.clear();  // 날짜 바뀌면 출처도 리셋
  renderDateLabel(); renderAll();
};
document.getElementById("dateRangeSel").onchange = (e) => {
  state.dateRange = e.target.value; state.selected = 0;
  state.activeSources.clear();  // 기간 바뀌면 출처도 리셋
  renderList(); renderPreview(); renderSourcePanel();
};
document.getElementById("darkToggle").onclick = () => {
  const cur = document.documentElement.getAttribute("data-theme") || "light";
  const next = cur === "light" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
};
const savedTheme = localStorage.getItem("theme");
if (savedTheme) document.documentElement.setAttribute("data-theme", savedTheme);

function saveKwDraft() {
  localStorage.setItem("kwDraft", JSON.stringify(kwData));
}
function renderKwModal() {
  const body = document.getElementById("kwBody");
  body.innerHTML = "";
  Object.keys(kwData).forEach(cat => {
    const block = document.createElement("div");
    block.className = "cat-block";
    const pillsHtml = kwData[cat].map((kw, i) => `
      <span class="kw-pill">
        ${kw.replace(/</g,"&lt;")}
        <button class="kw-del" data-cat="${cat.replace(/"/g, "&quot;")}" data-i="${i}" title="삭제">×</button>
      </span>
    `).join("");
    block.innerHTML = `
      <div class="cat-name">${cat} <span style="color:var(--text-faint);font-weight:400;">(${kwData[cat].length})</span></div>
      <div class="kw-list">${pillsHtml || '<span style="font-size:12px;color:var(--text-faint);">키워드 없음</span>'}</div>
      <div class="kw-add">
        <input type="text" placeholder="새 키워드 입력 후 Enter" data-cat="${cat.replace(/"/g, "&quot;")}">
        <button data-cat-add="${cat.replace(/"/g, "&quot;")}">추가</button>
      </div>
    `;
    body.appendChild(block);
  });
  body.querySelectorAll(".kw-del").forEach(btn => {
    btn.onclick = () => {
      const cat = btn.dataset.cat;
      const i = parseInt(btn.dataset.i);
      kwData[cat].splice(i, 1);
      saveKwDraft(); renderKwModal();
    };
  });
  body.querySelectorAll("[data-cat-add]").forEach(btn => {
    btn.onclick = () => {
      const cat = btn.dataset.catAdd;
      const input = body.querySelector(`input[data-cat="${cat.replace(/"/g,"&quot;")}"]`);
      const v = input.value.trim();
      if (v && !kwData[cat].includes(v)) {
        kwData[cat].push(v);
        saveKwDraft(); renderKwModal();
        setTimeout(() => {
          const newInput = document.querySelector(`input[data-cat="${cat.replace(/"/g,"&quot;")}"]`);
          if (newInput) newInput.focus();
        }, 0);
      }
    };
  });
  body.querySelectorAll(".kw-add input").forEach(inp => {
    inp.onkeydown = (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const cat = inp.dataset.cat;
        const btn = body.querySelector(`[data-cat-add="${cat.replace(/"/g,"&quot;")}"]`);
        if (btn) btn.click();
      }
    };
  });
}
function openKwModal() {
  document.getElementById("kwModal").classList.add("open");
  renderKwModal();
}
function closeKwModal() {
  document.getElementById("kwModal").classList.remove("open");
}
function resetKwToOriginal() {
  if (!confirm("현재 편집한 내용을 모두 버리고 keywords.txt 원본으로 되돌립니다. 계속할까요?")) return;
  kwData = JSON.parse(JSON.stringify(KEYWORDS_INITIAL));
  localStorage.removeItem("kwDraft");
  renderKwModal();
}
function copyKeywordsFile() {
  let text = "# =============================================================\n";
  text += "# 물류 산업 뉴스 검색 키워드 파일\n";
  text += "# (웹 편집기에서 자동 생성됨)\n";
  text += "# =============================================================\n\n";
  Object.keys(kwData).forEach(cat => {
    text += `[${cat}]\n`;
    kwData[cat].forEach(kw => {
      text += kw + "\n";
    });
    text += "\n";
  });
  navigator.clipboard.writeText(text).then(() => {
    alert("✅ 클립보드에 복사됐습니다!\n\n다음 단계:\n1. 프로젝트 폴더의 keywords.txt 열기\n2. 전체 선택 (Ctrl+A) → 삭제\n3. 붙여넣기 (Ctrl+V) → 저장 (Ctrl+S)\n4. 터미널에서 python collect.py 실행");
  }).catch(() => {
    prompt("클립보드 자동 복사 실패. 아래 내용을 수동으로 복사해서 keywords.txt에 붙여넣으세요:", text);
  });
}

document.getElementById("kwEdit").onclick = openKwModal;
document.getElementById("kwModal").onclick = (e) => {
  if (e.target.id === "kwModal") closeKwModal();
};

renderDateSelect();
renderDateLabel();
renderAll();
</script>
</body>
</html>
"""


def main():
    by_date = load_all_data()
    if not by_date:
        print("[!] data/ 폴더가 비어있습니다. 먼저 collect.py를 실행하세요.")
        return
    keywords = load_keywords_file(KEYWORDS_FILE)
    html = build_html(by_date, keywords)
    OUT_FILE.write_text(html, encoding="utf-8")

    total = sum(len(v) for v in by_date.values())
    total_keywords = sum(len(v) for v in keywords.values())
    print("=" * 50)
    print(f"[ok] HTML 생성 완료!")
    print(f"   날짜: {len(by_date)}개")
    print(f"   기사: {total}개")
    print(f"   카테고리: {len(keywords)}개 ({total_keywords}개 키워드)")
    print(f"   파일: {OUT_FILE}")
    print(f"   브라우저에서 index.html 더블클릭으로 열어보세요")
    print("=" * 50)


if __name__ == "__main__":
    main()
