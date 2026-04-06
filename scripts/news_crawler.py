"""
한입 AI — 다중 카테고리 뉴스 크롤러
구글 뉴스 RSS를 활용해 4가지 주제의 최신 뉴스를 수집합니다.
"""

import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
import os
import urllib.parse

# 4개의 카테고리와 검색 쿼리 정의
CATEGORIES = {
    "ai_tech": {
        "name": "AI & 테크",
        "queries": ['"인공지능" OR "챗GPT" OR "AI" OR "오픈AI" OR "생성형 AI"']
    },
    "economy": {
        "name": "경제 & 국제정세",
        "queries": ['"경제" OR "금리" OR "환율" OR "국제정세" OR "거시경제"']
    },
    "mobility": {
        "name": "모빌리티 & 우주",
        "queries": ['"전기차" OR "자율주행" OR "스페이스X" OR "항공우주"']
    },
    "startup": {
        "name": "스타트업 & 혁신",
        "queries": ['"스타트업" OR "실리콘밸리" OR "벤처투자" OR "유니콘기업"']
    }
}

def fetch_category_news(category_id, info, hours=48):
    """특정 카테고리의 기사를 구글 뉴스에서 수집합니다."""
    articles = []
    cutoff = datetime.now() - timedelta(hours=hours)
    seen_titles = set()
    
    for query in info["queries"]:
        encoded_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
        
        try:
            feed = feedparser.parse(url)
            
            for entry in feed.entries[:20]:  # 쿼리당 최대 20개
                # 날짜 파싱
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                else:
                    published = datetime.now()
                
                # 최근 기사만
                if published < cutoff:
                    continue
                
                title = entry.title
                # 구글 뉴스 제목 뒤에 붙는 '- 출처' 제거
                if " - " in title:
                    title = " - ".join(title.split(" - ")[:-1])
                    
                # 중복 확인
                normalized = re.sub(r'[^\w\s]', '', title.lower())
                if normalized in seen_titles:
                    continue
                seen_titles.add(normalized)
                
                articles.append({
                    "source": "Google News",
                    "title": title,
                    "link": entry.link,
                    "summary": "구글 뉴스 원문 참조",
                    "published": published.isoformat(),
                })
        except Exception as e:
            print(f"  ⚠️ {info['name']} 수집 실패: {e}")
            
    # 최근 시간순 정렬 후 상위 10-12개만 리턴
    articles.sort(key=lambda x: x['published'], reverse=True)
    return articles[:12]

def crawl_all_feeds(hours=48):
    """모든 카테고리의 뉴스를 수집합니다."""
    print("🔍 다중 카테고리 뉴스 크롤링 시작...")
    
    results = {}
    
    for cat_id, info in CATEGORIES.items():
        print(f"  📡 [{info['name']}] 수집 중...")
        articles = fetch_category_news(cat_id, info, hours)
        results[cat_id] = articles
        print(f"    → {len(articles)}건 수집 완료")
    
    return results

def save_crawled_data(categorized_articles, output_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")):
    """수집된 카테고리별 기사를 JSON으로 저장합니다."""
    os.makedirs(output_dir, exist_ok=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = os.path.join(output_dir, f"news_{today}.json")
    
    # 총 기사 수 계산
    total_articles = sum(len(arts) for arts in categorized_articles.values())
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({
            "date": today,
            "crawled_at": datetime.now().isoformat(),
            "article_count": total_articles,
            "categories": categorized_articles,
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 카테고리 데이터 저장 완료: {filepath}")
    return filepath

if __name__ == "__main__":
    data = crawl_all_feeds()
    save_crawled_data(data)
