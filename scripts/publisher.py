"""
한입 AI — HTML 페이지 빌더 & 퍼블리셔 (다중 카테고리 지원)
생성된 뉴스레터 콘텐츠를 HTML 페이지로 변환하고 사이트에 배포합니다.
"""

import json
import os
from datetime import datetime
from jinja2 import Template

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_latest_newsletter():
    """가장 최근 생성된 카테고리 뉴스레터 데이터를 불러옵니다."""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    files = sorted([f for f in os.listdir(data_dir) if f.startswith("newsletter_")], reverse=True)
    if not files:
        raise FileNotFoundError("뉴스레터 데이터가 없습니다. content_generator.py를 먼저 실행하세요.")
    filepath = os.path.join(data_dir, files[0])
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def render_deep_dives(deep_dives):
    html = ""
    for dive in deep_dives:
        body = dive['body']
        if not body.strip().startswith('<p>'):
            body = ''.join(f'<p>{p.strip()}</p>' for p in body.split('\n\n') if p.strip())
        html += f'''
        <article class="headline-card" style="margin-bottom: 2rem;">
          <div class="headline-tag">🔴 {dive.get("tag", "DEEP DIVE")}</div>
          <h3 class="headline-title">{dive["title"]}</h3>
          <div class="headline-body">{body}</div>
        </article>'''
    return html

def render_quick_news(quick_news):
    html = ""
    for i, news in enumerate(quick_news, 1):
        html += f"""
        <div class="news-item">
          <div class="news-bullet">{i}</div>
          <div class="news-content">
            <h3>{news['title']}</h3>
            <p>{news['content']}</p>
          </div>
        </div>"""
    return html

def update_index_page(newsletter):
    """메인 페이지(index.html)를 다중 카테고리 템플릿과 데이터로 렌더링합니다."""
    today = datetime.now()
    days_ko = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
    date_display = f"{today.year}년 {today.month}월 {today.day}일 {days_ko[today.weekday()]}"
    
    # 각 탭의 HTML을 준비
    tabs_html = {}
    for cat_id in ["ai_tech", "economy", "mobility", "startup"]:
        cat_data = newsletter.get(cat_id, {"deep_dives": [], "quick_news": []})
        tabs_html[cat_id] = {
            "deep_dives": render_deep_dives(cat_data.get("deep_dives", [])),
            "quick_news": render_quick_news(cat_data.get("quick_news", []))
        }
    
    # 툴 HTML
    tools_html = ""
    for tool in newsletter.get('recommended_tools', []):
        tools_html += f"""
        <div class="tool-card" style="margin-bottom: 1.5rem;">
          <div class="tool-icon">✨</div>
          <div class="tool-info">
            <div class="tool-category">{tool['category']}</div>
            <h3>{tool['name']}</h3>
            <p>{tool['description']}</p>
            <a href="{tool['url']}" target="_blank" class="tool-link">사이트 방문하기 →</a>
          </div>
        </div>"""
        
    # 템플릿 로딩 및 렌더링
    template_path = os.path.join(PROJECT_ROOT, "template_index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        template_str = f.read()
    
    template = Template(template_str)
    
    final_html = template.render(
        date_display=date_display,
        tabs=tabs_html,
        recommended_tools=tools_html,
        hannip_comment=newsletter.get('hannip_comment', "오늘도 수고 많으셨어요! 🐻")
    )
    
    # index.html 덮어쓰기
    index_path = os.path.join(PROJECT_ROOT, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(final_html)
        
    print(f"✨ 강력해진 4다중 탭 메인 페이지 업데이트 완료: {index_path}")

if __name__ == "__main__":
    try:
        news_data = load_latest_newsletter()
        update_index_page(news_data)
        print("✅ 모든 배포 단계가 성공적으로 완료되었습니다!")
    except Exception as e:
        print(f"❌ 배포 중 오류 발생: {e}")
