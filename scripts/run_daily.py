"""
한입 AI — 일일 파이프라인 실행기 (다중 카테고리 지원)
이 스크립트 하나만 실행하면 오늘의 지식 매거진 코어 파이프라인이 완성됩니다.
"""

import sys
import os

# scripts 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from news_crawler import crawl_all_feeds, save_crawled_data
from content_generator import generate_newsletter
from publisher import load_latest_newsletter, update_index_page

def run_pipeline():
    """전체 파이프라인을 실행합니다."""
    print("=" * 50)
    print("🍪 한입 AI — 다중 카테고리 매거진 자동화 파이프라인")
    print("=" * 50)
    
    # Step 1: 뉴스 크롤링
    print("\n📡 Step 1/3: 구글 뉴스 RSS 크롤링 (4개 영역)")
    print("-" * 40)
    data = crawl_all_feeds()
    
    if not data:
        print("❌ 수집된 기사가 없습니다. 네트워크 상태를 확인해주세요.")
        return False
    
    save_crawled_data(data)
    
    # Step 2: AI 콘텐츠 생성 (Gemini)
    print("\n🤖 Step 2/3: AI 콘텐츠 생성 및 병합")
    print("-" * 40)
    try:
        generate_newsletter()
    except Exception as e:
        print(f"❌ 콘텐츠 생성 실패: {e}")
        return False
    
    # Step 3: 메인 템플릿(index) 렌더링
    print("\n🚀 Step 3/3: HTML 탭 템플릿 렌더링")
    print("-" * 40)
    try:
        news_data = load_latest_newsletter()
        update_index_page(news_data)
    except Exception as e:
        print(f"❌ HTML 렌더링 실패: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ 파이프라인 완료! 다중 탭 뉴스레터가 발행 준비되었습니다.")
    print("=" * 50)
    return True

if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
