"""
한입 AI — HTML 페이지 빌더 & 퍼블리셔
생성된 뉴스레터 콘텐츠를 HTML 페이지로 변환하고 사이트에 배포합니다.
"""

import json
import os
import shutil
from datetime import datetime
from jinja2 import Template

# 프로젝트 루트 (scripts 상위)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html lang="ko" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="한입 AI — {{ headline_title }}. 매일 한입 크기의 AI 뉴스.">
  <meta name="keywords" content="AI 뉴스, 인공지능, {{ headline_title }}, 한입AI, 한입이">
  <meta property="og:title" content="{{ headline_title }} — 한입 AI">
  <meta property="og:description" content="매일 아침, AI 세상에서 가장 중요한 이슈를 쉽고 위트있게 정리해드립니다.">
  <meta property="og:type" content="article">
  <meta property="og:image" content="../assets/hannip.png">
  <title>{{ headline_title }} — 한입 AI</title>
  <link rel="icon" type="image/png" href="../assets/hannip.png">
  <link rel="stylesheet" href="../style.css">
</head>
<body>
  <div class="bg-gradient"></div>

  <header class="header">
    <div class="header-inner">
      <a href="../index.html" class="logo">
        <img src="../assets/hannip.png" alt="한입이" class="logo-icon">
        <div>
          <div class="logo-text">한입 AI</div>
          <div class="logo-sub">매일 한입, AI 세상을 떠먹여드립니다</div>
        </div>
      </a>
      <div class="header-actions">
        <a href="../archive.html" style="color: var(--text-secondary); font-size: 0.9rem; font-weight: 500;">아카이브</a>
        <button class="theme-toggle" id="themeToggle" aria-label="테마 전환">🌙</button>
      </div>
    </div>
  </header>

  <main class="main">
    <section class="hero animate-in">
      <div class="hero-date">
        <span>📅</span>
        <span>{{ date_display }}</span>
      </div>
      <h1 class="hero-title">오늘의 AI 한입 🍪</h1>
      <p class="hero-subtitle">한입이이가 오늘의 AI 뉴스를 맛있게 정리했어요</p>
    </section>

    <div class="ad-space">광고 영역 — AdSense 승인 후 활성화</div>

    <section class="section animate-in animate-delay-1">
      <div class="section-header">
        <span class="section-icon">🔥</span>
        <h2 class="section-title">오늘의 헤드라인</h2>
      </div>
      <article class="headline-card">
        <div class="headline-tag">🔴 {{ headline_tag }}</div>
        <h3 class="headline-title">{{ headline_title }}</h3>
        <div class="headline-body">{{ headline_body }}</div>
      </article>
    </section>

    <section class="section animate-in animate-delay-2">
      <div class="section-header">
        <span class="section-icon">⚡</span>
        <h2 class="section-title">빠른 뉴스</h2>
      </div>
      <div class="news-list">
        {% for news in quick_news %}
        <div class="news-item">
          <div class="news-bullet">{{ loop.index }}</div>
          <div class="news-content">
            <h3>{{ news.title }}</h3>
            <p>{{ news.summary }}</p>
          </div>
        </div>
        {% endfor %}
      </div>
    </section>

    <div class="ad-space">광고 영역 — AdSense 승인 후 활성화</div>

    <section class="section animate-in animate-delay-3">
      <div class="section-header">
        <span class="section-icon">🛠️</span>
        <h2 class="section-title">오늘의 추천 도구</h2>
      </div>
      <div class="tool-card">
        <div class="tool-icon">✨</div>
        <div class="tool-info">
          <div class="tool-category">{{ tool_category }}</div>
          <h3>{{ tool_name }}</h3>
          <p>{{ tool_description }}</p>
          {% if tool_url %}
          <a href="{{ tool_url }}" target="_blank" class="tool-link">사이트 방문하기 →</a>
          {% endif %}
        </div>
      </div>
    </section>

    <section class="section animate-in animate-delay-4">
      <div class="section-header">
        <span class="section-icon">💬</span>
        <h2 class="section-title">한입이의 한마디</h2>
      </div>
      <div class="hannip-comment">
        <img src="../assets/hannip.png" alt="한입이" class="hannip-avatar">
        <div class="hannip-bubble">
          <div class="hannip-name">한입이 🐻</div>
          <p class="hannip-text">"{{ hannip_comment }}"</p>
        </div>
      </div>
    </section>

    <div class="share-bar">
      <span class="share-label">공유하기</span>
      <button class="share-btn" id="shareTwitter" aria-label="트위터 공유">𝕏</button>
      <button class="share-btn" id="shareKakao" aria-label="카카오톡 공유">💬</button>
      <button class="share-btn" id="shareCopy" aria-label="링크 복사">🔗</button>
    </div>

    <div class="ad-space">광고 영역 — AdSense 승인 후 활성화</div>

    <section class="section animate-in animate-delay-5">
      <div class="subscribe">
        <h2>📬 매일 아침, 메일로 받아보세요</h2>
        <p>한입이이가 정리한 AI 뉴스를 매일 오전 7시에 보내드려요. 무료!</p>
        <form class="subscribe-form" id="subscribeForm">
          <input type="email" class="subscribe-input" placeholder="이메일 주소를 입력하세요" required id="emailInput">
          <button type="submit" class="subscribe-btn">구독하기</button>
        </form>
      </div>
    </section>
  </main>

  <footer class="footer">
    <div class="footer-logo">한입 AI</div>
    <p class="footer-desc">매일 한입, AI 세상을 떠먹여드립니다 🐻</p>
    <div style="margin: 10px 0;">
      <!-- 방문자수 카운터 배지 -->
      <a href="https://hits.seeyoufarm.com"><img src="https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fthinkingkorean-jpg.github.io%2Fhanip-ai&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=VISITORS&edge_flat=false"/></a>
    </div>
    <nav class="footer-links">
      <a href="../index.html">오늘의 뉴스</a>
      <a href="../archive.html">아카이브</a>
      <a href="../index.html#subscribe">이메일 구독</a>
    </nav>
    <p class="footer-copy">© 2026 한입 AI (Hannip). All rights reserved.</p>
  </footer>

  <script src="../app.js"></script>
</body>
</html>"""


def load_newsletter(data_dir="data"):
    """가장 최근 뉴스레터 데이터를 로드합니다."""
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = os.path.join(data_dir, f"newsletter_{today}.json")
    
    if not os.path.exists(filepath):
        files = sorted([f for f in os.listdir(data_dir) if f.startswith("newsletter_")], reverse=True)
        if not files:
            raise FileNotFoundError("뉴스레터 데이터가 없습니다. content_generator.py를 먼저 실행하세요.")
        filepath = os.path.join(data_dir, files[0])
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def build_article_page(newsletter):
    """뉴스레터 데이터로 HTML 페이지를 빌드합니다."""
    today = datetime.now()
    days_ko = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
    date_display = f"{today.year}년 {today.month}월 {today.day}일 {days_ko[today.weekday()]}"
    date_slug = today.strftime("%Y-%m-%d")
    
    template = Template(ARTICLE_TEMPLATE)
    
    # headline body: 텍스트를 <p> 태그로 감싸기 (이미 감싸져 있지 않다면)
    headline_body = newsletter['headline']['body']
    if not headline_body.strip().startswith('<p>'):
        paragraphs = headline_body.split('\n\n')
        headline_body = ''.join(f'<p>{p.strip()}</p>' for p in paragraphs if p.strip())
    
    html = template.render(
        date_display=date_display,
        headline_tag=newsletter['headline'].get('tag', 'HOT ISSUE'),
        headline_title=newsletter['headline']['title'],
        headline_body=headline_body,
        quick_news=newsletter['quick_news'],
        tool_category=newsletter['tool'].get('category', '생산성'),
        tool_name=newsletter['tool']['name'],
        tool_description=newsletter['tool']['description'],
        tool_url=newsletter['tool'].get('url', ''),
        hannip_comment=newsletter['hannip_comment'],
    )
    
    # 개별 기사 파일 저장
    articles_dir = os.path.join(PROJECT_ROOT, "articles")
    os.makedirs(articles_dir, exist_ok=True)
    
    filepath = os.path.join(articles_dir, f"{date_slug}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"📄 기사 페이지 생성: {filepath}")
    return filepath, date_slug


def update_index_page(newsletter):
    """메인 페이지(index.html)를 최신 뉴스레터로 업데이트합니다."""
    today = datetime.now()
    days_ko = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
    date_display = f"{today.year}년 {today.month}월 {today.day}일 {days_ko[today.weekday()]}"
    
    # headline body 처리
    headline_body = newsletter['headline']['body']
    if not headline_body.strip().startswith('<p>'):
        paragraphs = headline_body.split('\n\n')
        headline_body = ''.join(f'<p>{p.strip()}</p>' for p in paragraphs if p.strip())
    
    # 빠른 뉴스 HTML 생성
    news_html = ""
    for i, news in enumerate(newsletter['quick_news'], 1):
        news_html += f"""
        <div class="news-item">
          <div class="news-bullet">{i}</div>
          <div class="news-content">
            <h3>{news['title']}</h3>
            <p>{news['summary']}</p>
          </div>
        </div>"""
    
    # index.html 읽기
    index_path = os.path.join(PROJECT_ROOT, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    # 동적 콘텐츠 교체 (정규식 기반)
    import re
    
    # 헤드라인 제목
    html = re.sub(
        r'(<h3 class="headline-title">)(.*?)(</h3>)',
        f'\\1{newsletter["headline"]["title"]}\\3',
        html, flags=re.DOTALL
    )
    
    # 헤드라인 본문
    html = re.sub(
        r'(<div class="headline-body">)(.*?)(</div>\s*</article>)',
        f'\\g<1>\n          {headline_body}\n        \\3',
        html, flags=re.DOTALL
    )
    
    # 헤드라인 태그
    html = re.sub(
        r'(<div class="headline-tag">🔴 )(.*?)(</div>)',
        f'\\g<1>{newsletter["headline"].get("tag", "HOT ISSUE")}\\3',
        html
    )
    
    # 빠른 뉴스
    html = re.sub(
        r'(<div class="news-list"[^>]*>)(.*?)(</div>\s*</section>)',
        f'\\g<1>{news_html}\n      \\3',
        html, flags=re.DOTALL, count=1
    )
    
    # 추천 도구
    html = re.sub(
        r'(<div class="tool-category">)(.*?)(</div>)',
        f'\\g<1>{newsletter["tool"].get("category", "생산성")}\\3',
        html
    )
    html = re.sub(
        r'(<div class="tool-card"[\s\S]*?<h3>)(.*?)(</h3>)',
        f'\\g<1>{newsletter["tool"]["name"]}\\3',
        html
    )
    
    # 한입이 코멘트
    html = re.sub(
        r'(<p class="hannip-text">)(.*?)(</p>)',
        f'\\g<1>\n            "{newsletter["hannip_comment"]}"\n          \\3',
        html, flags=re.DOTALL
    )
    
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"🏠 메인 페이지 업데이트 완료")


def update_archive_page(newsletter, date_slug):
    """아카이브 페이지에 새 항목을 추가합니다."""
    archive_path = os.path.join(PROJECT_ROOT, "archive.html")
    
    today = datetime.now()
    month_names = ['1월', '2월', '3월', '4월', '5월', '6월', 
                   '7월', '8월', '9월', '10월', '11월', '12월']
    
    new_entry = f"""
      <a href="articles/{date_slug}.html" class="archive-item">
        <div class="archive-date">
          <div class="day">{today.day}</div>
          <div class="month">{month_names[today.month - 1]}</div>
        </div>
        <div class="archive-info">
          <h3>{newsletter['headline']['title']}</h3>
          <p>{' · '.join(n['title'] for n in newsletter['quick_news'][:3])}</p>
        </div>
      </a>"""
    
    with open(archive_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    # 아카이브 그리드에 새 항목 추가 (맨 위에)
    import re
    html = re.sub(
        r'(<div class="archive-grid"[^>]*>)',
        f'\\1{new_entry}',
        html
    )
    
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"📚 아카이브 페이지 업데이트 완료")


def publish(newsletter=None):
    """뉴스레터를 빌드하고 퍼블리시합니다."""
    data_dir = os.path.join(PROJECT_ROOT, "scripts", "data")
    
    if newsletter is None:
        newsletter = load_newsletter(data_dir)
    
    print("🚀 퍼블리싱 시작...\n")
    
    # 1. 개별 기사 페이지 생성
    filepath, date_slug = build_article_page(newsletter)
    
    # 2. 메인 페이지 업데이트
    update_index_page(newsletter)
    
    # 3. 아카이브 업데이트
    update_archive_page(newsletter, date_slug)
    
    print(f"\n✅ 퍼블리싱 완료! 🎉")
    print(f"  📄 기사: articles/{date_slug}.html")
    print(f"  🏠 메인: index.html (업데이트)")
    print(f"  📚 아카이브: archive.html (업데이트)")


if __name__ == "__main__":
    publish()
