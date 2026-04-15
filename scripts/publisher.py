"""
한입 AI HTML 페이지 빌더 & 퍼블리셔.
생성된 뉴스레터 콘텐츠를 HTML 페이지로 변환하고 사이트에 배포합니다.
"""

from __future__ import annotations

import html
import json
import os
import re
from datetime import datetime

from jinja2 import Template
from dotenv import load_dotenv
import requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
ARCHIVE_INDEX_PATH = os.path.join(ARTICLES_DIR, "index.json")
SITE_URL = "https://thinkingkorean-jpg.github.io/hanip-ai"

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

CATEGORY_CONFIG = {
    "ai_tech": {"name": "AI & 테크", "icon": "🤖", "tab_id": "tab-ai"},
    "economy": {"name": "경제", "icon": "📰", "tab_id": "tab-economy"},
    "mobility": {"name": "우주 & 모빌리티", "icon": "🚀", "tab_id": "tab-mobility"},
    "startup": {"name": "스타트업 & 혁신", "icon": "💡", "tab_id": "tab-startup"},
}


def load_latest_newsletter():
    """가장 최근 생성된 뉴스레터 데이터를 불러옵니다."""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    files = sorted([file for file in os.listdir(data_dir) if file.startswith("newsletter_")], reverse=True)
    if not files:
        raise FileNotFoundError("뉴스레터 데이터가 없습니다. content_generator.py를 먼저 실행하세요.")

    filepath = os.path.join(data_dir, files[0])
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)


def _resolve_date(newsletter):
    metadata = newsletter.get("metadata", {})
    return metadata.get("date") or newsletter.get("date") or datetime.now().strftime("%Y-%m-%d")


def _format_date_display(date_text):
    date_value = datetime.strptime(date_text, "%Y-%m-%d")
    days_ko = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    return f"{date_value.year}년 {date_value.month}월 {date_value.day}일 {days_ko[date_value.weekday()]}"


def _sanitize_paragraph_html(raw_body):
    text = re.sub(r"</p>\s*<p>", "\n\n", raw_body, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    paragraphs = [segment.strip() for segment in re.split(r"\n{2,}", text) if segment.strip()]
    if not paragraphs:
        paragraphs = [raw_body.strip()]
    return "".join(f"<p>{html.escape(paragraph)}</p>" for paragraph in paragraphs)


def _safe_text(value):
    return html.escape(str(value or ""))


def _strip_html(value):
    return re.sub(r"<[^>]+>", "", str(value or "")).strip()


def render_deep_dives(deep_dives):
    rendered = []
    for dive in deep_dives:
        body = _sanitize_paragraph_html(dive.get("body", ""))
        source_url = html.escape(dive.get("source_url", ""), quote=True)
        source_html = ""
        if source_url:
            source_html = f'<p class="news-source"><a href="{source_url}" target="_blank" rel="noopener noreferrer">원문 보기 →</a></p>'
        rendered.append(
            f"""
        <article class="headline-card" style="margin-bottom: 2rem;">
          <div class="headline-tag">🔥 {_safe_text(dive.get("tag", "DEEP DIVE"))}</div>
          <h3 class="headline-title">{_safe_text(dive.get("title", ""))}</h3>
          <div class="headline-body">{body}{source_html}</div>
        </article>"""
        )
    return "".join(rendered)


def render_quick_news(quick_news):
    rendered = []
    for index, news in enumerate(quick_news, 1):
        source_url = html.escape(news.get("source_url", ""), quote=True)
        source_html = ""
        if source_url:
            source_html = f'<a href="{source_url}" target="_blank" rel="noopener noreferrer" class="tool-link">원문 보기 →</a>'
        rendered.append(
            f"""
        <div class="news-item">
          <div class="news-bullet">{index}</div>
          <div class="news-content">
            <h3>{_safe_text(news.get("title", ""))}</h3>
            <p>{_safe_text(news.get("content", ""))}</p>
            {source_html}
          </div>
        </div>"""
        )
    return "".join(rendered)


def render_tools(recommended_tools):
    rendered = []
    for tool in recommended_tools:
        url = html.escape(tool.get("url", ""), quote=True)
        rendered.append(
            f"""
        <div class="tool-card" style="margin-bottom: 1.5rem;">
          <div class="tool-icon">✨</div>
          <div class="tool-info">
            <div class="tool-category">{_safe_text(tool.get("category", ""))}</div>
            <h3>{_safe_text(tool.get("name", ""))}</h3>
            <p>{_safe_text(tool.get("description", ""))}</p>
            <a href="{url}" target="_blank" rel="noopener noreferrer" class="tool-link">사이트 방문하기 →</a>
          </div>
        </div>"""
        )
    return "".join(rendered)


def get_publishable_categories(newsletter):
    categories = []
    for category_id, config in CATEGORY_CONFIG.items():
        category_data = newsletter.get(category_id, {})
        deep_dives = category_data.get("deep_dives", [])
        quick_news = category_data.get("quick_news", [])
        if not deep_dives and not quick_news:
            continue
        categories.append(
            {
                "id": category_id,
                "name": config["name"],
                "icon": config["icon"],
                "tab_id": config["tab_id"],
                "deep_dives_html": render_deep_dives(deep_dives),
                "quick_news_html": render_quick_news(quick_news),
            }
        )
    return categories


def render_tabs_nav(categories):
    buttons = []
    for index, category in enumerate(categories):
        active_class = " active" if index == 0 else ""
        buttons.append(
            f'<button class="tab-btn{active_class}" data-target="{category["tab_id"]}">{category["icon"]} {category["name"]}</button>'
        )
    return "\n".join(buttons)


def render_tab_panes(categories):
    panes = []
    for index, category in enumerate(categories):
        active_class = " active" if index == 0 else ""
        panes.append(
            f"""
    <div id="{category['tab_id']}" class="tab-pane{active_class}">
      <section class="section">
        <div class="section-header">
          <span class="section-icon">🔥</span><h2 class="section-title">오늘의 심층 분석</h2>
        </div>
        <div class="deep-dives-list">{category['deep_dives_html']}</div>
      </section>
      <section class="section">
        <div class="section-header">
          <span class="section-icon">⚡</span><h2 class="section-title">빠른 뉴스</h2>
        </div>
        <div class="news-list">{category['quick_news_html']}</div>
      </section>
    </div>"""
        )
    return "\n".join(panes)


def build_article_summary(newsletter):
    categories = get_publishable_categories(newsletter)
    for category in categories:
        category_data = newsletter.get(category["id"], {})
        deep_dives = category_data.get("deep_dives", [])
        if deep_dives:
            return deep_dives[0].get("title", "")
        quick_news = category_data.get("quick_news", [])
        if quick_news:
            return quick_news[0].get("title", "")
    return "오늘의 한입 AI 브리핑"


def build_next_issue_preview(newsletter):
    metadata = newsletter.get("metadata", {})
    counts = metadata.get("category_article_counts", {})
    parts = []
    for category_id, count in counts.items():
        if count <= 0 or category_id not in CATEGORY_CONFIG:
            continue
        parts.append(f"{CATEGORY_CONFIG[category_id]['name']} {count}건")
    joined = ", ".join(parts) if parts else "새 기사 수집 중"
    return f"내일 아침 7시에는 {joined}을 바탕으로 가장 중요한 흐름만 다시 한입 크기로 정리해드릴게요."


def _load_archive_index():
    if not os.path.exists(ARCHIVE_INDEX_PATH):
        return []
    with open(ARCHIVE_INDEX_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def _save_archive_index(entries):
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    with open(ARCHIVE_INDEX_PATH, "w", encoding="utf-8") as file:
        json.dump(entries, file, ensure_ascii=False, indent=2)


def update_archive_index(newsletter, article_path):
    date_value = _resolve_date(newsletter)
    summary = build_article_summary(newsletter)
    description = newsletter.get("hannip_comment", "")[:180]

    entries = [entry for entry in _load_archive_index() if entry.get("date") != date_value]
    entries.append(
        {
            "date": date_value,
            "title": summary,
            "description": description,
            "href": os.path.relpath(article_path, PROJECT_ROOT).replace("\\", "/"),
        }
    )
    entries.sort(key=lambda item: item["date"], reverse=True)
    _save_archive_index(entries)
    return entries


def update_archive_page(entries):
    archive_path = os.path.join(PROJECT_ROOT, "archive.html")
    if not os.path.exists(archive_path):
        return

    with open(archive_path, "r", encoding="utf-8") as file:
        archive_html = file.read()

    latest_date = entries[0]["date"] if entries else ""
    archive_html = re.sub(
        r'(<main class="main"[^>]*data-latest-article=")[^"]*(")',
        rf"\g<1>{latest_date}\2",
        archive_html,
        count=1,
    )

    with open(archive_path, "w", encoding="utf-8") as file:
        file.write(archive_html)


def _build_stibee_letter_payload(newsletter, article_path):
    date_value = _resolve_date(newsletter)
    article_title = build_article_summary(newsletter) or "오늘의 한입 AI"
    relative_path = os.path.relpath(article_path, PROJECT_ROOT).replace("\\", "/")
    article_url = f"{SITE_URL}/{relative_path}"

    sections = [
        f"<h1>{html.escape(article_title)}</h1>",
        f"<p>한입 AI {html.escape(date_value)} 발행본입니다.</p>",
    ]

    for category_id, config in CATEGORY_CONFIG.items():
        category_data = newsletter.get(category_id, {})
        deep_dives = category_data.get("deep_dives", [])
        quick_news = category_data.get("quick_news", [])
        if not deep_dives and not quick_news:
            continue

        sections.append(f"<h2>{html.escape(config['name'])}</h2>")

        for dive in deep_dives[:2]:
            sections.append(f"<h3>{html.escape(dive.get('title', ''))}</h3>")
            sections.append(f"<p>{html.escape(_strip_html(dive.get('body', ''))[:300])}</p>")

        if quick_news:
            items = "".join(
                f"<li>{html.escape(news.get('title', ''))}</li>"
                for news in quick_news[:5]
            )
            sections.append(f"<ul>{items}</ul>")

    sections.append(f'<p><a href="{html.escape(article_url, quote=True)}">웹에서 전체 보기</a></p>')

    return {
        "subject": f"[한입 AI] {article_title}",
        "name": f"한입 AI {date_value}",
        "addressBookId": os.getenv("STIBEE_ADDRESS_BOOK_ID", "").strip(),
        "content": {
            "type": "html",
            "value": "".join(sections),
        },
    }


def send_stibee_letter(newsletter, article_path):
    api_key = os.getenv("STIBEE_API_KEY", "").strip()
    address_book_id = os.getenv("STIBEE_ADDRESS_BOOK_ID", "").strip()
    if not api_key or not address_book_id:
        print("Stibee letter send skipped: missing STIBEE_API_KEY or STIBEE_ADDRESS_BOOK_ID.")
        return False

    payload = _build_stibee_letter_payload(newsletter, article_path)

    try:
        response = requests.post(
            "https://api.stibee.com/v1/letters",
            headers={
                "AccessToken": api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        print("Stibee letter send completed.")
        return True
    except requests.RequestException as exc:
        print(f"Stibee letter send failed: {exc}")
        return False


def _build_article_page(newsletter, categories, date_display, article_title):
    tools_html = render_tools(newsletter.get("recommended_tools", []))
    tabs_nav_html = render_tabs_nav(categories)
    tab_panes_html = render_tab_panes(categories)
    comment = _safe_text(newsletter.get("hannip_comment", "오늘도 수고 많으셨어요!"))
    next_issue_preview = _safe_text(build_next_issue_preview(newsletter))

    return f"""<!DOCTYPE html>
<html lang="ko" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="한입 AI — {html.escape(article_title)}. 매일 한입 크기의 핵심 뉴스레터.">
  <meta property="og:title" content="{html.escape(article_title)} — 한입 AI">
  <meta property="og:type" content="article">
  <meta property="og:image" content="../assets/hannip.png">
  <meta name="stibee-list-id" content="{html.escape(os.getenv('STIBEE_LIST_ID', ''), quote=True)}">
  <title>{html.escape(article_title)} — 한입 AI</title>
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
          <div class="logo-sub">매일 한입, 세상을 떠먹여드립니다</div>
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
        <span>{date_display}</span>
      </div>
      <h1 class="hero-title">{html.escape(article_title)}</h1>
      <p class="hero-subtitle">하루치 핵심 뉴스를 카테고리별로 다시 읽어보세요.</p>
    </section>

    <nav class="tabs-nav animate-in animate-delay-1">
      {tabs_nav_html}
    </nav>

    {tab_panes_html}

    <section class="section animate-in">
      <div class="section-header">
        <span class="section-icon">🛠️</span>
        <h2 class="section-title">오늘의 추천 도구</h2>
      </div>
      <div class="tools-list">{tools_html}</div>
    </section>

    <section class="section animate-in">
      <div class="section-header">
        <span class="section-icon">⏭️</span>
        <h2 class="section-title">다음 발행 예고</h2>
      </div>
      <article class="headline-card">
        <h3 class="headline-title">내일 아침 발행 준비 중</h3>
        <div class="headline-body"><p>{next_issue_preview}</p></div>
      </article>
    </section>

    <section class="section animate-in">
      <div class="section-header">
        <span class="section-icon">💬</span>
        <h2 class="section-title">한입이의 한마디</h2>
      </div>
      <div class="hannip-comment">
        <img src="../assets/hannip.png" alt="한입이" class="hannip-avatar">
        <div class="hannip-bubble">
          <div class="hannip-name">한입이 🐻</div>
          <p class="hannip-text">"{comment}"</p>
        </div>
      </div>
    </section>

    <div class="share-bar">
      <span class="share-label">공유하기</span>
      <button class="share-btn" id="shareTwitter" aria-label="트위터 공유">𝕏</button>
      <button class="share-btn" id="shareKakao" aria-label="카카오톡 공유">💬</button>
      <button class="share-btn" id="shareCopy" aria-label="링크 복사">🔗</button>
    </div>

    <section class="section animate-in">
      <div class="subscribe" id="subscribe">
        <h2>📬 매일 아침, 메일로 받아보세요</h2>
        <p>한입이가 매일 중요한 흐름만 골라 보내드려요. 무료!</p>
        <form class="subscribe-form" id="subscribeForm">
          <input type="email" class="subscribe-input" placeholder="이메일 주소를 입력하세요" required id="emailInput">
          <button type="submit" class="subscribe-btn">구독하기</button>
        </form>
        <p id="subscribeStatus"></p>
      </div>
    </section>
  </main>

  <footer class="footer">
    <div class="footer-logo">한입 AI</div>
    <p class="footer-desc">매일 한입, 세상을 떠먹여드립니다 🐻</p>
    <nav class="footer-links">
      <a href="../index.html">오늘의 뉴스</a>
      <a href="../archive.html">아카이브</a>
      <a href="../index.html#subscribe">이메일 구독</a>
    </nav>
    <p class="footer-copy">© 2026 한입 AI (Hannip). All rights reserved.</p>
  </footer>

  <script src="../app.js"></script>
  <script>
    document.querySelectorAll('.tab-btn').forEach((button) => {{
      button.addEventListener('click', () => {{
        document.querySelectorAll('.tab-btn').forEach((btn) => btn.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach((pane) => pane.classList.remove('active'));
        button.classList.add('active');
        document.getElementById(button.dataset.target).classList.add('active');
      }});
    }});
  </script>
</body>
</html>
"""


def create_article_page(newsletter):
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    categories = get_publishable_categories(newsletter)
    date_value = _resolve_date(newsletter)
    date_display = _format_date_display(date_value)
    article_title = build_article_summary(newsletter)
    article_path = os.path.join(ARTICLES_DIR, f"{date_value}.html")

    with open(article_path, "w", encoding="utf-8") as file:
        file.write(_build_article_page(newsletter, categories, date_display, article_title))

    return article_path


def update_index_page(newsletter):
    """메인 페이지(index.html)를 최신 뉴스레터 데이터로 렌더링합니다."""
    categories = get_publishable_categories(newsletter)
    if not categories:
        raise ValueError("발행 가능한 카테고리 콘텐츠가 없습니다.")

    date_value = _resolve_date(newsletter)
    template_path = os.path.join(PROJECT_ROOT, "template_index.html")
    with open(template_path, "r", encoding="utf-8") as file:
        template_str = file.read()

    template = Template(template_str)
    final_html = template.render(
        date_display=_format_date_display(date_value),
        tabs_nav=render_tabs_nav(categories),
        tab_panes=render_tab_panes(categories),
        recommended_tools=render_tools(newsletter.get("recommended_tools", [])),
        hannip_comment=_safe_text(newsletter.get("hannip_comment", "오늘도 수고 많으셨어요!")),
        next_issue_preview=_safe_text(build_next_issue_preview(newsletter)),
        stibee_list_id=os.getenv("STIBEE_LIST_ID", "").strip(),
    )

    index_path = os.path.join(PROJECT_ROOT, "index.html")
    with open(index_path, "w", encoding="utf-8") as file:
        file.write(final_html)

    article_path = create_article_page(newsletter)
    archive_entries = update_archive_index(newsletter, article_path)
    update_archive_page(archive_entries)
    send_stibee_letter(newsletter, article_path)

    print(f"메인 페이지 업데이트 완료: {index_path}")
    print(f"개별 아티클 페이지 생성 완료: {article_path}")
    print(f"아카이브 인덱스 업데이트 완료: {ARCHIVE_INDEX_PATH}")


if __name__ == "__main__":
    try:
        news_data = load_latest_newsletter()
        update_index_page(news_data)
        print("모든 퍼블리싱 단계가 성공적으로 완료되었습니다.")
    except Exception as exc:
        print(f"퍼블리싱 중 오류 발생: {exc}")
