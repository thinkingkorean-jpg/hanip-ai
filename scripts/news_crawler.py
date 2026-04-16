"""
한입 AI 다중 카테고리 뉴스 크롤러.
구글 뉴스 RSS를 사용해 4개 주제의 최신 뉴스를 수집합니다.
"""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.parse
from datetime import datetime, timedelta

import feedparser
from bs4 import BeautifulSoup

# 4개의 카테고리와 검색 쿼리 정의
CATEGORIES = {
    "ai_tech": {
        "name": "AI & 테크",
        "queries": ['"인공지능" OR "챗GPT" OR "AI" OR "오픈AI" OR "생성형 AI"'],
    },
    "economy": {
        "name": "경제 & 국제정세",
        "queries": ['"경제" OR "금리" OR "환율" OR "국제정세" OR "거시경제"'],
    },
    "money": {
        "name": "머니 & 투자",
        "queries": ['"주식시장" OR "부동산" OR "비트코인" OR "투자" OR "재테크" OR "ETF"'],
    },
    "global": {
        "name": "글로벌 이슈",
        "queries": ['"미중갈등" OR "트럼프" OR "NATO" OR "중동" OR "지정학" OR "국제뉴스"'],
    },
    "mobility": {
        "name": "모빌리티 & 우주",
        "queries": ['"전기차" OR "자율주행" OR "스페이스X" OR "항공우주"'],
    },
    "startup": {
        "name": "스타트업 & 혁신",
        "queries": ['"스타트업" OR "실리콘밸리" OR "벤처투자" OR "유니콘기업"'],
    },
}

LOGGER = logging.getLogger(__name__)
MAX_FETCH_RETRIES = 2
MIN_ARTICLES_PER_CATEGORY = 3


def _configure_default_logging():
    if logging.getLogger().handlers:
        return
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def _normalize_title(title):
    return re.sub(r"[^\w\s]", "", title.lower()).strip()


def _extract_summary(entry):
    raw_summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
    if not raw_summary and getattr(entry, "content", None):
        raw_summary = " ".join(item.get("value", "") for item in entry.content if item.get("value"))

    if not raw_summary:
        return "구글 뉴스 원문 참조"

    text = BeautifulSoup(raw_summary, "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip() or "구글 뉴스 원문 참조"


def _parse_feed_with_retry(url):
    last_error = None

    for attempt in range(MAX_FETCH_RETRIES + 1):
        try:
            feed = feedparser.parse(url)
            if getattr(feed, "bozo", 0) and getattr(feed, "bozo_exception", None):
                raise feed.bozo_exception
            return feed
        except Exception as exc:
            last_error = exc
            if attempt < MAX_FETCH_RETRIES:
                LOGGER.warning("RSS 요청 실패, 재시도합니다. url=%s attempt=%s error=%s", url, attempt + 1, exc)

    raise RuntimeError(f"RSS 요청 실패: {last_error}") from last_error


def fetch_category_news(category_id, info, hours=48, seen_urls=None):
    """특정 카테고리의 기사를 구글 뉴스에서 수집합니다."""
    articles = []
    cutoff = datetime.now() - timedelta(hours=hours)
    seen_titles = set()
    tracked_urls = seen_urls if seen_urls is not None else set()

    for query in info["queries"]:
        encoded_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"

        try:
            feed = _parse_feed_with_retry(url)

            for entry in feed.entries[:20]:
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                else:
                    published = datetime.now()

                if published < cutoff:
                    continue

                title = entry.title
                if " - " in title:
                    title = " - ".join(title.split(" - ")[:-1])

                normalized = _normalize_title(title)
                article_url = getattr(entry, "link", "").strip()

                if normalized in seen_titles:
                    continue
                if article_url and article_url in tracked_urls:
                    LOGGER.info("교차 카테고리 중복 기사 제외: %s", article_url)
                    continue

                seen_titles.add(normalized)
                if article_url:
                    tracked_urls.add(article_url)

                articles.append(
                    {
                        "source": "Google News",
                        "title": title,
                        "link": article_url,
                        "summary": _extract_summary(entry),
                        "published": published.isoformat(),
                    }
                )
        except Exception as exc:
            LOGGER.error("%s 수집 실패: %s", info["name"], exc)

    articles.sort(key=lambda item: item["published"], reverse=True)
    return articles[:12]


def crawl_all_feeds(hours=48):
    """모든 카테고리의 뉴스를 수집합니다."""
    _configure_default_logging()
    LOGGER.info("다중 카테고리 뉴스 크롤링 시작")

    results = {}
    seen_urls = set()

    for cat_id, info in CATEGORIES.items():
        LOGGER.info("[%s] 수집 중...", info["name"])
        articles = fetch_category_news(cat_id, info, hours, seen_urls=seen_urls)
        results[cat_id] = articles
        LOGGER.info("[%s] %s건 수집 완료", info["name"], len(articles))

        if len(articles) < MIN_ARTICLES_PER_CATEGORY:
            LOGGER.warning("[%s] 최소 기사 수 미달: %s건", info["name"], len(articles))

    return results


def save_crawled_data(
    categorized_articles,
    output_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"),
):
    """수집한 카테고리별 기사를 JSON으로 저장합니다."""
    os.makedirs(output_dir, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    filepath = os.path.join(output_dir, f"news_{today}.json")
    total_articles = sum(len(articles) for articles in categorized_articles.values())

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(
            {
                "date": today,
                "crawled_at": datetime.now().isoformat(),
                "article_count": total_articles,
                "categories": categorized_articles,
            },
            file,
            ensure_ascii=False,
            indent=2,
        )

    LOGGER.info("카테고리 데이터 저장 완료: %s", filepath)
    return filepath


if __name__ == "__main__":
    data = crawl_all_feeds()
    save_crawled_data(data)
