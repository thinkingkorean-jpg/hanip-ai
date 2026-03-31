"""
한입 AI — 뉴스 크롤러
RSS 피드에서 AI/테크 뉴스를 수집하고 중요도 기반으로 선별합니다.
"""

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
import os

# RSS 피드 소스 목록
RSS_FEEDS = {
    # 해외 주요 소스
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",
    "Ars Technica AI": "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "MIT Tech Review": "https://www.technologyreview.com/feed/",
    "Wired AI": "https://www.wired.com/feed/tag/ai/latest/rss",
    
    # AI 기업 블로그
    "OpenAI Blog": "https://openai.com/blog/rss.xml",
    "Google AI Blog": "https://blog.google/technology/ai/rss/",
    "Anthropic": "https://www.anthropic.com/feed.xml",
    
    # 한국 소스
    "AI타임스": "https://www.aitimes.com/rss/allArticle.xml",
    "ZDNet Korea": "https://zdnet.co.kr/rss/all_news.xml",
}

# AI 관련 키워드 (관련도 필터링용)
AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "gpt", "gemini", "claude", "llm", "chatbot", "neural network",
    "openai", "google ai", "anthropic", "meta ai", "microsoft ai",
    "인공지능", "머신러닝", "딥러닝", "생성형", "챗봇", "대규모 언어 모델",
    "자율주행", "로봇", "반도체", "ai 칩", "nvidia", "transformer",
    "stable diffusion", "midjourney", "dall-e", "sora", "copilot",
    "agent", "에이전트", "rag", "fine-tuning", "파인튜닝",
]


def fetch_rss_feed(name, url, hours=48):
    """단일 RSS 피드에서 기사를 수집합니다."""
    articles = []
    try:
        feed = feedparser.parse(url)
        cutoff = datetime.now() - timedelta(hours=hours)
        
        for entry in feed.entries[:15]:  # 피드당 최대 15개
            # 날짜 파싱
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6])
            else:
                published = datetime.now()
            
            # 최근 기사만
            if published < cutoff:
                continue
            
            # 요약 텍스트 추출
            summary = ""
            if hasattr(entry, 'summary'):
                summary = BeautifulSoup(entry.summary, 'html.parser').get_text()[:500]
            elif hasattr(entry, 'description'):
                summary = BeautifulSoup(entry.description, 'html.parser').get_text()[:500]
            
            articles.append({
                "source": name,
                "title": entry.title,
                "link": entry.link,
                "summary": summary,
                "published": published.isoformat(),
            })
    except Exception as e:
        print(f"  ⚠️ {name} 피드 수집 실패: {e}")
    
    return articles


def calculate_relevance(article):
    """기사의 AI 관련도 점수를 계산합니다."""
    text = f"{article['title']} {article['summary']}".lower()
    score = 0
    
    for keyword in AI_KEYWORDS:
        if keyword.lower() in text:
            score += 1
    
    # 제목에 키워드가 있으면 가중치
    title_lower = article['title'].lower()
    for keyword in AI_KEYWORDS:
        if keyword.lower() in title_lower:
            score += 2
    
    return score


def crawl_all_feeds(hours=48):
    """모든 RSS 피드에서 기사를 수집하고 관련도순으로 정렬합니다."""
    print("🔍 뉴스 크롤링 시작...")
    all_articles = []
    
    for name, url in RSS_FEEDS.items():
        print(f"  📡 {name} 수집 중...")
        articles = fetch_rss_feed(name, url, hours)
        all_articles.extend(articles)
        print(f"    → {len(articles)}건 수집")
    
    print(f"\n📊 총 {len(all_articles)}건 수집 완료")
    
    # 중복 제거 (제목 유사도 기반)
    unique = []
    seen_titles = set()
    for article in all_articles:
        # 제목 정규화
        normalized = re.sub(r'[^\w\s]', '', article['title'].lower())
        if normalized not in seen_titles:
            seen_titles.add(normalized)
            unique.append(article)
    
    print(f"🔄 중복 제거 후: {len(unique)}건")
    
    # 관련도 점수 계산 및 정렬
    for article in unique:
        article['relevance'] = calculate_relevance(article)
    
    unique.sort(key=lambda x: x['relevance'], reverse=True)
    
    # 상위 기사 선별
    top_articles = [a for a in unique if a['relevance'] > 0][:10]
    print(f"🎯 AI 관련 주요 기사: {len(top_articles)}건\n")
    
    for i, article in enumerate(top_articles, 1):
        print(f"  {i}. [{article['source']}] {article['title']} (점수: {article['relevance']})")
    
    return top_articles


def save_crawled_data(articles, output_dir="data"):
    """크롤링된 기사를 JSON으로 저장합니다."""
    os.makedirs(output_dir, exist_ok=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = os.path.join(output_dir, f"news_{today}.json")
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({
            "date": today,
            "crawled_at": datetime.now().isoformat(),
            "article_count": len(articles),
            "articles": articles,
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 저장 완료: {filepath}")
    return filepath


if __name__ == "__main__":
    articles = crawl_all_feeds()
    if articles:
        save_crawled_data(articles)
    else:
        print("❌ 수집된 기사가 없습니다.")
