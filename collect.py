"""
물류 산업 뉴스 RSS 수집기
- 매일 실행하면 오늘 새로 올라온 글들을 모아 data/YYYY-MM-DD.json 파일로 저장합니다.
- 국내/국외, 그리고 키워드(택배·이커머스·국가정책 등)를 자동으로 태깅합니다.
"""

import json
import os
import time
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path
import urllib.request
import urllib.error

import feedparser

# ===========================================================
# 설정
# ===========================================================

# 회사·키워드는 외부 파일(keywords.txt)에서 읽어옵니다
# 그 파일을 메모장이나 VS Code로 편집하면 collect.py 코드는 안 건드려도 됩니다
KEYWORDS_FILE = Path(__file__).parent / "keywords.txt"


def google_news_url(query: str) -> str:
    """검색어를 넣으면 모든 매체 기사를 모아오는 구글 뉴스 RSS URL을 반환"""
    return (
        "https://news.google.com/rss/search?"
        f"q={urllib.parse.quote(query)}"
        "&hl=ko&gl=KR&ceid=KR:ko"
    )


def load_keywords_file(path: Path) -> dict:
    """keywords.txt를 읽어서 {카테고리명: [키워드 리스트]} 딕셔너리로 반환합니다.
    파일 형식:
      [카테고리명]
      키워드1
      키워드2
      # 주석은 무시됨
    """
    if not path.exists():
        print(f"[!] {path.name} 파일이 없습니다. 빈 키워드로 시작합니다.")
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


# === 일반 RSS 소스 ===
# 큰 흐름·정책 동향 파악용 (keywords.txt와 별도로 코드에서 관리)
GENERAL_RSS = [
    ("정책브리핑-국토교통부", "https://www.korea.kr/rss/dept_molit.xml", "domestic"),
    ("정책브리핑-보도자료", "https://www.korea.kr/rss/pressrelease.xml", "domestic"),
    ("연합뉴스-경제", "https://www.yna.co.kr/rss/economy.xml", "domestic"),
    ("연합뉴스-산업", "https://www.yna.co.kr/rss/industry.xml", "domestic"),
    ("매일경제-기업경영", "https://www.mk.co.kr/rss/50300009/", "domestic"),
    ("Supply Chain Dive", "https://www.supplychaindive.com/feeds/news/", "global"),
    ("Maritime Executive", "https://maritime-executive.com/articles.rss", "global"),
]


# keywords.txt를 읽어서 SOURCES 만들기
KEYWORD_CATEGORIES = load_keywords_file(KEYWORDS_FILE)

# 글로벌 카테고리 식별 (영문 검색은 region=global, 그 외는 domestic)
GLOBAL_CATEGORIES = {"4. 글로벌 빅테크"}

SOURCES = []
for cat_name, queries in KEYWORD_CATEGORIES.items():
    region = "global" if cat_name in GLOBAL_CATEGORIES else "domestic"
    for q in queries:
        SOURCES.append((f"[{cat_name}] {q}", google_news_url(q), region))
SOURCES.extend(GENERAL_RSS)

# 키워드 매칭 규칙. 제목/요약에 이 단어들이 있으면 해당 태그를 붙여요.
# 물류산업 영업 관점에서 잠재 고객 시그널을 빠르게 잡도록 구성됨.
KEYWORDS = {
    "물류산업": [
        "물류", "logistics", "supply chain", "공급망",
        # 정부 정책은 곧 산업 전체 영향이라 정책 키워드도 여기에 같이
        "국토부", "관세청", "해수부",
    ],
    "물류시스템": [
        # 시스템·솔루션
        "WMS", "TMS", "풀필먼트", "fulfillment",
        # 시설·설비·창고 (확장)
        "물류센터", "물류설비", "물류장비", "물류시설", "물류단지",
        "warehouse", "창고", "허브", "터미널",
        # 자동화·기술
        "automation", "자동화", "로봇", "AGV", "AMR", "분류기",
    ],
    "시설투자": [
        # 신축·확장·가동 (영업 시그널의 핵심)
        "신축", "증설", "확장", "착공", "준공", "가동",
        "오픈", "개소", "구축", "도입", "투자", "확보",
        "건립", "조성", "기공", "완공",
        "investment", "expansion", "open", "launch", "deploy",
    ],
    "국가정책": [
        "국토부", "관세청", "해수부",
        "법", "규제", "정책", "고시", "시행령", "지침",
        "policy", "regulation", "FMCSA", "DOT",
    ],
    "택배": [
        "택배", "배송", "delivery", "courier", "last mile", "라스트마일",
    ],
    "쿠팡": ["쿠팡", "Coupang"],
    "아마존": ["아마존", "Amazon", "AWS"],
    "이커머스": [
        "이커머스", "ecommerce", "e-commerce", "온라인 쇼핑",
        "Shopify", "Walmart", "네이버쇼핑",
    ],
}

# 한 키워드가 매겨지면 자동으로 같이 붙는 태그 (의존 관계)
# 예: "국가정책"이 매겨졌으면 → 물류 분야 정책이라는 뜻이므로 "물류산업"도 같이
TAG_IMPLICATIONS = {
    "국가정책": ["물류산업"],
    "시설투자": ["물류산업"],  # 시설 투자 = 산업 동향
}

# 일반 브라우저처럼 보이게 헤더 설정 (정부/뉴스 사이트 봇 차단 우회용)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# 이 폴더 기준으로 data/ 폴더에 저장
ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"

# ===========================================================
# 함수들
# ===========================================================

def fetch_feed(url: str, timeout: int = 10):
    """User-Agent 헤더를 붙여서 RSS를 가져옵니다."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    return feedparser.parse(data)


def tag_keywords(text: str) -> list[str]:
    """제목+요약에서 어떤 키워드에 해당하는지 찾아 태그 리스트를 반환합니다.
    추가로 TAG_IMPLICATIONS에 따라 의존 태그도 자동 부여합니다.
    예: '국가정책'이 매겨지면 '물류산업'도 자동으로 함께 붙음.
    """
    text_lower = text.lower()
    tags = []
    for tag, terms in KEYWORDS.items():
        for term in terms:
            if term.lower() in text_lower:
                tags.append(tag)
                break

    # 의존 태그 자동 부여
    extra = []
    for tag in tags:
        for implied in TAG_IMPLICATIONS.get(tag, []):
            if implied not in tags and implied not in extra:
                extra.append(implied)
    tags.extend(extra)

    return tags


def parse_published(entry) -> str:
    """기사 작성일을 YYYY-MM-DD 형태로 추출합니다."""
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return time.strftime("%Y-%m-%d", t)
    return ""


def normalize_link(url: str) -> str:
    """구글 뉴스 RSS는 같은 기사가 다른 URL로 잡힐 수 있어서,
    중복 검출을 위해 URL의 핵심 부분만 남깁니다."""
    if not url:
        return ""
    # 구글 뉴스 redirect URL은 그대로 비교
    # 일반 기사는 query string과 fragment 제거
    if "news.google.com" in url:
        return url
    parsed = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def collect():
    """모든 소스에서 수집해서 키워드 매칭된 기사만 모은다."""
    DATA_DIR.mkdir(exist_ok=True)
    today = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")  # KST 기준
    out_file = DATA_DIR / f"{today}.json"

    # 이미 저장된 게 있으면 그걸 읽어서 중복 방지에 사용
    existing_links = set()
    seen_titles = set()  # 제목으로도 중복 검사 (다른 URL이지만 같은 기사인 경우)
    articles = []
    if out_file.exists():
        with out_file.open(encoding="utf-8") as f:
            articles = json.load(f)
        existing_links = {normalize_link(a["link"]) for a in articles}
        seen_titles = {a["title"] for a in articles}

    success = 0
    fail = 0
    new_count = 0

    for name, url, region in SOURCES:
        # 구글 뉴스 검색은 결과가 너무 많으므로 상위 10개만
        is_google = "news.google.com" in url
        max_items = 10 if is_google else 50

        try:
            feed = fetch_feed(url)
            if not feed.entries:
                print(f"[skip] {name}: 항목 0개")
                fail += 1
                continue

            added_here = 0
            for entry in feed.entries[:max_items]:
                link = entry.get("link", "")
                norm_link = normalize_link(link)
                if not link or norm_link in existing_links:
                    continue

                title = entry.get("title", "").strip()
                if title in seen_titles:
                    continue  # 같은 제목 = 같은 기사 (다른 매체에서 같은 보도자료)

                summary = entry.get("summary", "").strip()
                published = parse_published(entry)

                # 제목+요약을 합쳐서 키워드 태깅
                tags = tag_keywords(title + " " + summary)
                if not tags:
                    continue  # 물류 관련 없는 글은 스킵

                articles.append({
                    "title": title,
                    "link": link,
                    "source": name,
                    "region": region,
                    "tags": tags,
                    "published": published,
                    "summary_raw": summary[:500],
                    "summary_ai": "",
                    "collected_at": datetime.now().isoformat(timespec="seconds"),
                })
                existing_links.add(norm_link)
                seen_titles.add(title)
                new_count += 1
                added_here += 1

            print(f"[ok]   {name}: {added_here}개 신규")
            success += 1

        except urllib.error.HTTPError as e:
            print(f"[fail] {name}: HTTP {e.code}")
            fail += 1
        except Exception as e:
            print(f"[fail] {name}: {type(e).__name__} - {str(e)[:60]}")
            fail += 1

    # 저장
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 50)
    print(f"수집 완료: 성공 {success}개 / 실패 {fail}개 소스")
    print(f"오늘({today}) 누적 기사: {len(articles)}개 (이번에 신규 {new_count}개)")
    print(f"저장 위치: {out_file}")
    print("=" * 50)


if __name__ == "__main__":
    collect()
