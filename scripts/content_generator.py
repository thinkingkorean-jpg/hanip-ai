"""
한입 AI — 에디터 (콘텐츠 생성기) 다중 카테고리 지원
Gemini API를 활용해 수집된 뉴스를 한입 크기로 가공합니다.
"""

import json
import os
import google.generativeai as genai
from datetime import datetime
from pydantic import BaseModel, Field

# -----------------
# 1. Pydantic 스키마 (결과물 구조 강제 지정)
# -----------------
class DeepDive(BaseModel):
    tag: str = Field(description="예: [HOT ISSUE], [DEEP DIVE], [TREND] 등 짧은 태그")
    title: str = Field(description="독자의 시선을 끄는 매력적인 제목")
    body: str = Field(description="<p> 태그들로 감싸진 2~3문단의 상세한 분석 내용")

class QuickNews(BaseModel):
    title: str = Field(description="간결하고 흥미로운 단신 기사 제목")
    content: str = Field(description="어떤 일이 있었고 왜 중요한지 설명하는 2문장 요약")

class RecommendedTool(BaseModel):
    category: str = Field(description="도구 분류 (예: 생산성, 정보 검색, 코딩 등)")
    name: str = Field(description="도구 이름")
    description: str = Field(description="이 도구를 왜 써야 하는지 설명하는 2~3문장 소개")
    url: str = Field(description="도구의 실제 공식 웹사이트 접속 URL")

class CategoryNewsletter(BaseModel):
    deep_dives: list[DeepDive] = Field(description="해당 분야의 가장 크고 중요한 이슈 3개를 심층 분석한 기사들")
    quick_news: list[QuickNews] = Field(description="알아두면 좋을 핵심 단신 뉴스 5개")

class GlobalExtras(BaseModel):
    recommended_tools: list[RecommendedTool] = Field(description="실제로 유용하게 쓸 수 있는 도구 2개 추천")
    hannip_comment: str = Field(description="에디터 '한입이'의 친근하고 위트있는 오늘의 전체적인 코멘트")

# -----------------
# 2. 메인 생성 로직 
# -----------------
def generate_category_content(category_name, articles, model):
    """단일 카테고리에 대한 뉴스레터 섹션을 작성합니다."""
    if not articles:
         return {"deep_dives": [], "quick_news": []}
         
    news_text = ""
    for i, a in enumerate(articles, 1):
        news_text += f"[{i}] 제목: {a['title']}\n"
    
    prompt = f"""
당신은 '{category_name}' 분야의 전문 IT/비즈니스 에디터입니다.
오늘의 최신 뉴스 기사 리스트를 보고 독자들이 읽기 쉽고 흥미롭게 '한입 크기'로 가공해주세요.

[오늘의 {category_name} 수집 기사]
{news_text}

[작성 지침]
1. 위 기사들 중 가장 중요하고 파괴력이 큰 이슈 3개를 골라 'deep_dives' (심층 분석)로 작성하세요. 원문 내용만 살리지 말고, 이 사건이 왜 중요한지, 대중에게 어떤 영향을 미치는지 인사이트를 더해주세요. body는 반드시 <p>HTML 단락 태그</p> 구조로 2~3문단 작성하세요. 친근하고 위트있는 '해요체(했어요, 합니다)'를 사용하세요.
2. 나머지 기사나 자잘하게 알아야 할 뉴스 5개를 골라 'quick_news' (단신)로 작성하세요.
3. 주의: 작성 시 없는 이야기를 지어내지 말고, 제공된 기사 제목을 기반으로 아는 사실만 정리하세요.

응답은 반드시 JSON 형식으로만 해야 합니다.
"""

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=CategoryNewsletter,
            temperature=0.4,
        )
    )
    return json.loads(response.text)

def generate_global_extras(model):
    """전체적인 코멘트 및 도구 추천을 작성합니다."""
    prompt = """
당신은 친근하고 센스있는 AI 에디터 '한입이'입니다.
1. 'recommended_tools'에는 실제 존재하는 검증된 유용한 글로벌 도구 도메인 2개를 추천해주세요. (예: chatgpt, perplexity, github 등 절대로 가짜 도메인이나 없는 스타트업을 꾸며내지 마세요. url은 반드시 https 링크로 작성)
2. 'hannip_comment'에는 뉴스레터를 마치며 던지는, 다정하고 활기찬 인사말을 2~3문장으로 적어주세요.

응답은 반드시 JSON 형식으로만 해야 합니다.
"""
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=GlobalExtras,
            temperature=0.3,
        )
    )
    return json.loads(response.text)


def generate_newsletter():
    """모든 카테고리를 순회하며 완성된 뉴스레터 데이터를 조립합니다."""
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
    except ImportError:
        pass

    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # 1. 크롤링 데이터 로드
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    files = sorted([f for f in os.listdir(data_dir) if f.startswith("news_")], reverse=True)
    if not files:
        raise FileNotFoundError("크롤링된 뉴스 데이터 (news_YYYY-MM-DD.json) 가 없습니다.")
        
    filepath = os.path.join(data_dir, files[0])
    with open(filepath, "r", encoding="utf-8") as f:
        crawled_data = json.load(f)
        
    categories_data = crawled_data.get("categories", {})
    if not categories_data:
        raise ValueError("올바른 다중 카테고리 크롤링 데이터가 아닙니다.")
        
    print("🤖 다중 카테고리 콘텐츠 생성 시작...")
    
    final_newsletter = {}
    
    # 카테고리별 병렬 또는 순차 생성
    category_names = {
        "ai_tech": "AI & 테크",
        "economy": "경제 & 국제정세",
        "mobility": "모빌리티 & 우주",
        "startup": "스타트업 & 혁신"
    }
    
    for cat_id, cat_name in category_names.items():
        print(f"  ✍️ [{cat_name}] 원고 작성 중...")
        articles = categories_data.get(cat_id, [])
        cat_result = generate_category_content(cat_name, articles, model)
        final_newsletter[cat_id] = cat_result
    
    print("  🛠️ [도구 및 마무릿말] 작성 중...")
    extras = generate_global_extras(model)
    final_newsletter["recommended_tools"] = extras["recommended_tools"]
    final_newsletter["hannip_comment"] = extras["hannip_comment"]
    
    # 결과 저장
    out_path = os.path.join(data_dir, f"newsletter_{crawled_data['date']}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final_newsletter, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 뉴스레터 마스터본 생성 완료: {out_path}")
    return out_path

if __name__ == "__main__":
    generate_newsletter()
