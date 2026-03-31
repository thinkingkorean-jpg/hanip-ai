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

SYSTEM_PROMPT = """당신은 "한닙(Hannip)"이라는 캐릭터입니다. 한닙은 귀여운 로봇 곰으로, 한국어 AI 뉴스레터 "한입 AI"의 진행자입니다.

## 한닙의 성격과 톤
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

NEWSLETTER_PROMPT = """아래 수집된 AI 뉴스 기사들을 바탕으로 오늘의 "한입 AI" 뉴스레터를 작성해주세요.

## 수집된 기사:
{articles_text}

## 작성 형식 (반드시 아래 JSON 형식으로 출력해주세요):

```json
{{
  "date": "{today}",
  "headline": {{
    "tag": "HOT ISSUE 또는 BREAKING 또는 DEEP DIVE",
    "title": "가장 중요한 뉴스의 매력적인 제목 (한국어)",
    "body": "3~4 문단으로 깊이 있는 해설 (300~500자). HTML <p> 태그로 감싸기. 중요 키워드는 <strong>으로 강조."
  }},
  "quick_news": [
    {{
      "title": "뉴스 제목 (한국어)",
      "summary": "1~2줄 핵심 요약"
    }},
    // 3~4개
  ],
  "tool": {{
    "category": "카테고리 (예: 생산성, 디자인, 개발, 마케팅)",
    "name": "도구 이름",
    "description": "왜 좋은지, 어떻게 쓸 수 있는지 설명 (2~3문장)",
    "url": "도구 공식 URL"
  }},
  "hannip_comment": "한닙이의 재치있는 마무리 한마디 (1~2문장, 이모지 포함)"
}}
```

중요: 반드시 유효한 JSON으로 출력하세요. 마크다운 코드 블록 없이 순수 JSON만 출력하세요.
"""


def init_gemini():
    """Gemini API를 초기화합니다."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT,
    )


def load_crawled_news(data_dir="data"):
    """가장 최근 크롤링된 뉴스 데이터를 로드합니다."""
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
    
    print("🤖 한닙이 뉴스레터를 작성하고 있어요...")
    
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 4096,
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
        print(f"원본 텍스트:\n{text[:500]}")
        
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
        print(f"  헤드라인: {newsletter['headline']['title']}")
        print(f"  빠른 뉴스: {len(newsletter['quick_news'])}건")
        print(f"  추천 도구: {newsletter['tool']['name']}")
        print(f"  한닙의 한마디: {newsletter['hannip_comment']}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
