# 한입 AI (Hannip) 🍪🐻

> 매일 한입, AI 세상을 떠먹여드립니다

AI 뉴스를 매일 자동으로 수집·분석·작성하여 발행하는 한국어 AI 뉴스레터 서비스입니다.

## 🏗️ 프로젝트 구조

```
hanip-ai/
├── index.html          # 메인 페이지 (오늘의 뉴스레터)
├── archive.html        # 뉴스레터 아카이브
├── style.css           # 디자인 시스템
├── app.js              # 프론트엔드 로직
├── articles/           # 날짜별 뉴스레터 HTML
├── assets/             # 이미지, 캐릭터 등
│   └── hannip.png      # 마스코트 캐릭터
├── scripts/            # 자동화 스크립트
│   ├── run_daily.py    # 전체 파이프라인 실행
│   ├── news_crawler.py # RSS 뉴스 수집
│   ├── content_generator.py # Gemini AI 콘텐츠 생성
│   ├── publisher.py    # HTML 빌드 & 배포
│   └── requirements.txt
├── .env.example        # 환경변수 템플릿
└── .gitignore          # Git 제외 파일 목록
```

## 🚀 시작하기

### 1. 의존성 설치
```bash
pip install -r scripts/requirements.txt
```

### 2. API 키 설정
```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일에 Gemini API 키 입력
# Google AI Studio (https://aistudio.google.com)에서 발급
```

### 3. 뉴스레터 생성 실행
```bash
python scripts/run_daily.py
```

이 명령 하나로:
1. 📡 AI/테크 뉴스 RSS 크롤링
2. 🤖 Gemini API로 뉴스레터 콘텐츠 생성
3. 📄 HTML 페이지 빌드 & 사이트 업데이트

## 📡 뉴스 소스
- TechCrunch AI, The Verge, VentureBeat, MIT Tech Review
- OpenAI Blog, Google AI Blog, Anthropic Blog
- AI타임스, ZDNet Korea

## 🛡️ 보안
- `.env` 파일은 Git에 포함되지 않습니다
- API 키를 절대 코드에 하드코딩하지 마세요
- `.env.example`을 참고하여 로컬에서 `.env`를 생성하세요

## 📝 라이선스
MIT License © 2026 한입 AI
