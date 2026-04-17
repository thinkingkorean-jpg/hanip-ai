"""
한입 AI 뉴스레터 콘텐츠 생성기.
Gemini API를 사용해 수집한 뉴스를 발행용 콘텐츠로 가공합니다.
"""

from __future__ import annotations
from typing import Optional

import json
import os
from datetime import datetime

import google.generativeai as genai
from pydantic import BaseModel, Field


class DeepDive(BaseModel):
    tag: str = Field(description="예: [HOT ISSUE], [DEEP DIVE], [TREND] 같은 태그")
    title: str = Field(description="독자의 시선을 끄는 매력적인 제목")
    body: str = Field(description="<p> 태그로 감싼 2~3문단 분량의 상세 분석")
    source_url: Optional[str] = Field(description="근거로 삼은 기사 원문 URL (없으면 null)")


class QuickNews(BaseModel):
    title: str = Field(description="간결하고 선명한 단신 기사 제목")
    content: str = Field(description="무슨 일이 있었고 왜 중요한지 설명하는 2문장 요약")
    source_url: Optional[str] = Field(description="근거로 삼은 기사 원문 URL (없으면 null)")


class RecommendedTool(BaseModel):
    category: str = Field(description="도구 분류")
    name: str = Field(description="도구 이름")
    description: str = Field(description="오늘 뉴스 맥락과 연결된 추천 이유 2~3문장")
    url: str = Field(description="도구 공식 웹사이트 URL")


class CategoryNewsletter(BaseModel):
    deep_dives: list[DeepDive] = Field(description="해당 분야의 가장 크고 중요한 이슈 3개를 심층 분석한 기사들")
    quick_news: list[QuickNews] = Field(description="알아두면 좋을 핵심 단신 뉴스 5개")


class GlobalExtras(BaseModel):
    recommended_tools: list[RecommendedTool] = Field(description="오늘 기사 맥락과 연결된 도구 2개 추천")
    hannip_comment: str = Field(description="에디터 '한입이'의 친근하고 위트있는 오늘의 전체 코멘트")


def build_article_context(category_name, articles):
    lines = []
    for index, article in enumerate(articles, 1):
        lines.append(
            "\n".join(
                [
                    f"[{index}] 제목: {article['title']}",
                    f"링크: {article.get('link', '')}",
                    f"발행시각: {article.get('published', '')}",
                    f"요약: {article.get('summary', '')}",
                ]
            )
        )
    return "\n\n".join(lines)


def generate_category_content(category_name, articles, model):
    """단일 카테고리용 뉴스레터 섹션을 생성합니다."""
    if not articles:
        return {"deep_dives": [], "quick_news": []}

    news_text = build_article_context(category_name, articles)
    prompt = f"""
당신은 '{category_name}' 분야의 전문 에디터이자, MZ세대가 열광하는 뉴스레터 작가입니다.
아래 기사 목록을 보고 독자들이 "이건 꼭 읽어야 해!"라고 느끼는 콘텐츠를 만드세요.

[오늘의 {category_name} 수집 기사]
{news_text}

[핵심 원칙 — 반드시 지켜주세요]
1. **요약만 하지 마세요!** 기사 내용을 넘어서 "+한발자국 더" 인사이트를 반드시 포함하세요.
   - 예: "이게 왜 중요하냐면…", "다른 나라에선 이미…", "이 흐름이 계속되면…"
   - 독자가 "아 그래서 이게 나한테 어떤 영향을 주는 거지?" 에 대한 답을 줘야 합니다.

2. **말투는 에너지 넘치고 위트 있게!** 
   - ❌ "~했다.", "~됐다." → 딱딱한 기사 느낌 절대 금지
   - ✅ "~했어요!", "~라니까요?", "미쳤죠?", "장난 아니에요" → 친구한테 흥분해서 얘기하는 톤
   - 감탄사, 이모지, 비유를 적극 활용 (예: "테슬라가 또 한방 먹였어요 🥊")

3. **deep_dives는 3개, 각각 충분히 길게 작성하세요.**
   - body는 <p>...</p> 구조의 HTML 문단 **3~4개** (최소 300자 이상)
   - 첫 문단: 핵심 사실 (무슨 일이 있었는지)
   - 중간 문단: 맥락과 배경 (왜 이런 일이 생겼는지)
   - 마지막 문단: **+알파 인사이트** (앞으로 어떻게 될지, 독자에게 어떤 의미인지)

4. **quick_news는 5개, 한 줄이 아니라 2~3문장으로 작성하세요.**
   - "무슨 일이 있었고 → 왜 중요한지" 구조로 쓰세요.

5. 기사 정보는 제목뿐 아니라 링크, 발행시각, 요약까지 함께 참고하세요.
6. deep_dives와 quick_news의 source_url은 반드시 위 기사 목록 중 가장 직접적으로 근거가 된 링크를 넣으세요.
7. 사실을 꾸며내지 말고, 제공된 기사 정보 안에서만 정리하되 인사이트는 추가하세요.

응답은 반드시 JSON 형식이어야 합니다.
"""

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=CategoryNewsletter,
            temperature=0.7,
        ),
    )
    return json.loads(response.text)


def generate_global_extras(model, categorized_articles):
    """오늘 기사 맥락에 연결된 도구 추천과 마무리 코멘트를 생성합니다."""
    context_lines = []
    for category_name, articles in categorized_articles.items():
        if not articles:
            continue
        top_titles = ", ".join(article["title"] for article in articles[:3])
        context_lines.append(f"- {category_name}: {top_titles}")

    context_text = "\n".join(context_lines) or "- 기사 없음"
    prompt = f"""
당신은 친근하고 재치 있는 AI 뉴스레터 에디터 '한입이'입니다.

[오늘 기사 맥락]
{context_text}

[작성 지침]
1. recommended_tools는 오늘 기사 흐름과 직접 연결되는 실존 도구 2개만 추천하세요.
2. 각 도구 설명에는 오늘 어떤 뉴스 흐름을 따라 읽은 독자에게 왜 유용한지 분명히 연결해서 적으세요.
3. url은 반드시 공식 https 링크만 사용하세요.
4. hannip_comment는 뉴스레터를 마무리하는 다정한 2~3문장 인사말로 작성하세요.

응답은 반드시 JSON 형식이어야 합니다.
"""

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=GlobalExtras,
            temperature=0.3,
        ),
    )
    return json.loads(response.text)


def build_metadata(crawled_data):
    categories_data = crawled_data.get("categories", {})
    category_article_counts = {category_id: len(articles) for category_id, articles in categories_data.items()}
    input_titles = {
        category_id: [article.get("title", "") for article in articles]
        for category_id, articles in categories_data.items()
    }
    return {
        "date": crawled_data.get("date", datetime.now().strftime("%Y-%m-%d")),
        "crawled_at": crawled_data.get("crawled_at"),
        "category_article_counts": category_article_counts,
        "input_titles": input_titles,
    }


def generate_newsletter():
    """전체 카테고리를 순회하며 완성된 뉴스레터 데이터를 생성합니다."""
    try:
        from dotenv import load_dotenv

        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    except ImportError:
        pass

    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-flash")

    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    files = sorted([file for file in os.listdir(data_dir) if file.startswith("news_")], reverse=True)
    if not files:
        raise FileNotFoundError("크롤링된 뉴스 데이터(news_YYYY-MM-DD.json)가 없습니다.")

    filepath = os.path.join(data_dir, files[0])
    with open(filepath, "r", encoding="utf-8") as file:
        crawled_data = json.load(file)

    categories_data = crawled_data.get("categories", {})
    if not categories_data:
        raise ValueError("올바른 다중 카테고리 크롤링 데이터가 비어 있습니다.")

    print("다중 카테고리 콘텐츠 생성 시작...")

    final_newsletter = {}
    category_names = {
        "ai_tech": "AI & 테크",
        "economy": "경제 & 국제정세",
        "money": "머니 & 투자",
        "global": "글로벌 이슈",
        "mobility": "모빌리티 & 우주",
        "startup": "스타트업 & 혁신",
    }

    for category_id, category_name in category_names.items():
        articles = categories_data.get(category_id, [])
        if not articles:
            print(f"  - [{category_name}] 기사 0건, 발행 섹션에서 제외")
            continue

        print(f"  - [{category_name}] 섹션 생성 중...")
        final_newsletter[category_id] = generate_category_content(category_name, articles, model)

    extras = generate_global_extras(model, {category_names.get(key, key): value for key, value in categories_data.items()})
    final_newsletter["recommended_tools"] = extras["recommended_tools"]
    final_newsletter["hannip_comment"] = extras["hannip_comment"]
    final_newsletter["metadata"] = build_metadata(crawled_data)

    out_path = os.path.join(data_dir, f"newsletter_{final_newsletter['metadata']['date']}.json")
    with open(out_path, "w", encoding="utf-8") as file:
        json.dump(final_newsletter, file, ensure_ascii=False, indent=2)

    print(f"뉴스레터 마스터본 생성 완료: {out_path}")
    return out_path


if __name__ == "__main__":
    generate_newsletter()
