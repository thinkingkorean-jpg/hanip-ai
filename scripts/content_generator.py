"""
한입 AI — AI 콘텐츠 생성기
Gemini API를 사용하여 수집된 뉴스를 기반으로 뉴스레터 콘텐츠를 생성합니다.
"""

import google.generativeai as genai
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Gemini 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

SYSTEM_PROMPT = """당신은 "한입이(Hannip)"이라는 캐릭터입니다. 한입이은 귀여운 로봇 곰으로, 한국어 AI 뉴스레터 "한입 AI"의 진행자입니다.

## 한입이의 성격과 톤
- 친근하고 캐주얼한 말투 (반말 X, 존댓말 사용하되 딱딱하지 않게)
- 복잡한 기술을 쉬운 비유로 설명
- 가끔 유머와 이모지를 섞어서 위트있게
- "~입니다", "~해요", "~거든요" 같은 부드러운 어미 사용
- 독자를 "여러분"이라고 부름
- AI 뉴스에 대한 열정이 느껴지는 톤

## 주의사항
- 정확한 정보 전달이 최우선
- 과장하지 않되, 흥미롭게 전달
- 어려운 기술 용어는 괄호 안에 쉬운 설명 추가
- 각 기사의 "왜 중요한지"를 반드시 포함
"""

NEWSLETTER_PROMPT = """아래 수집된 AI 뉴스 기사들을 바탕으로 오늘의 "한입 AI" 뉴스레터를 대폭 확장하여 아주 상세하게 작성해주세요.

## 수집된 기사:
{articles_text}

## 작성 형식 (반드시 아래 JSON 형식으로 출력해주세요):

```json
{{
  "date": "{today}",
  "deep_dives": [
    {{
      "tag": "HOT ISSUE 또는 BREAKING 또는 DEEP DIVE",
      "title": "가장 중요한 뉴스의 매력적인 제목 (한국어)",
      "body": "최소 3~5 문단으로 아주 깊이 있는 해설 (각 기사당 500~800자 이상). HTML <p> 태그로 문단을 완벽하게 나누기. 중요 키워드는 <strong>으로 강조. 해당 기술의 원리, 시장 영향, 시사점을 모두 포함하세요."
    }},
    // 반드시 중요도 순으로 3개를 작성하세요. (가장 핫한 뉴스 3개)
  ],
  "quick_news": [
    {{
      "title": "뉴스 제목 (한국어)",
      "summary": "핵심만 짚어주는 2~3줄 요약"
    }},
    // 최소 5개 이상의 단신 뉴스를 작성하세요.
  ],
  "recommended_tools": [
    {{
      "category": "카테고리 (예: 생산성, 디자인, 개발, 마케팅)",
      "name": "실제 존재하는 유명 AI 도구 이름",
      "description": "왜 좋은지, 어떻게 쓸 수 있는지 구체적인 예시와 함께 설명 (3~4문장)",
      "url": "실제 도구의 공식 URL (https://... 형태)"
    }},
    // 업무나 일상에 도움되는 '실제로 완전히 현존하는' AI 도구 2개를 소개하세요. (예: ChatGPT, Midjourney, Perplexity, Notion AI 등).
    // 주의: '한입 요약기', '한입 이미지 생성기' 등 가상의 도구를 절대로 지어내지 마세요!
  ],
  "hannip_comment": "한입이의 재치있는 마무리 한마디 (2~3문장, 이모지 듬뿍 포함, 오늘의 메인 테마를 요약하며 인사)"
}}
```

중요: 반드시 유효한 JSON으로 작성하세요. 마크다운 코드 블록 없이 순수 JSON만 출력하세요. 
치명적인 오류 방지: **절대** JSON 값(문자열 내부)에 큰따옴표(")를 포함하지 마세요! 만약 인용구나 단어 강조가 필요하다면 작은따옴표(')를 사용하세요. 각 `deep_dives` 본문은 반드시 500자 이상 800자 이하의 장문이어야 합니다.
"""


def init_gemini():
    """Gemini API를 초기화합니다."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT,
    )


def load_crawled_news(data_dir=None):
    """가장 최근 크롤링된 뉴스 데이터를 로드합니다."""
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = os.path.join(data_dir, f"news_{today}.json")
    
    if not os.path.exists(filepath):
        # 가장 최근 파일 찾기
        files = sorted([f for f in os.listdir(data_dir) if f.startswith("news_")], reverse=True)
        if not files:
            raise FileNotFoundError("크롤링된 뉴스 데이터가 없습니다. news_crawler.py를 먼저 실행하세요.")
        filepath = os.path.join(data_dir, files[0])
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data["articles"]


def format_articles_for_prompt(articles):
    """기사 목록을 프롬프트용 텍스트로 변환합니다."""
    lines = []
    for i, article in enumerate(articles, 1):
        lines.append(f"### 기사 {i}: [{article['source']}]")
        lines.append(f"제목: {article['title']}")
        lines.append(f"요약: {article['summary']}")
        lines.append(f"링크: {article['link']}")
        lines.append("")
    return "\n".join(lines)


def generate_newsletter(articles):
    """Gemini API로 뉴스레터 콘텐츠를 생성합니다."""
    model = init_gemini()
    
    articles_text = format_articles_for_prompt(articles)
    today = datetime.now().strftime("%Y년 %m월 %d일")
    
    prompt = NEWSLETTER_PROMPT.format(
        articles_text=articles_text,
        today=today,
    )
    
    print("🤖 한입이이 뉴스레터를 작성하고 있어요...")
    
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.5,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }
    )
    
    # JSON 파싱
    text = response.text.strip()
    
    # 마크다운 코드 블록 제거
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()
    
    try:
        newsletter = json.loads(text)
        print("✅ 뉴스레터 생성 완료!")
        return newsletter
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON 파싱 실패: {e}")
        # 전체 텍스트를 파일로 저장해서 디버깅
        with open("error_output.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print("디버깅을 위해 error_output.txt에 원본을 저장했습니다.")
        
        # 재시도: JSON 부분만 추출
        import re
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                newsletter = json.loads(json_match.group())
                print("✅ JSON 재파싱 성공!")
                return newsletter
            except:
                pass
        
        raise ValueError("뉴스레터 콘텐츠 생성에 실패했습니다.")


def save_newsletter(newsletter, output_dir="data"):
    """생성된 뉴스레터를 JSON으로 저장합니다."""
    os.makedirs(output_dir, exist_ok=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = os.path.join(output_dir, f"newsletter_{today}.json")
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(newsletter, f, ensure_ascii=False, indent=2)
    
    print(f"💾 뉴스레터 저장: {filepath}")
    return filepath


if __name__ == "__main__":
    try:
        articles = load_crawled_news()
        newsletter = generate_newsletter(articles)
        save_newsletter(newsletter)
        
        print("\n📋 생성된 뉴스레터 미리보기:")
        print(f"  심층 분석: {len(newsletter['deep_dives'])}건 (예: {newsletter['deep_dives'][0]['title']})")
        print(f"  빠른 뉴스: {len(newsletter['quick_news'])}건")
        print(f"  추천 도구: {len(newsletter['recommended_tools'])}건 (예: {newsletter['recommended_tools'][0]['name']})")
        print(f"  한입이의 한마디: {newsletter['hannip_comment']}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
