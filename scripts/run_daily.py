"""
한입 AI — 일일 파이프라인 실행기
뉴스 크롤링 → AI 콘텐츠 생성 → HTML 빌드 & 퍼블리시
이 스크립트 하나만 실행하면 오늘의 뉴스레터가 완성됩니다.
"""

import sys
import os

# scripts 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from news_crawler import crawl_all_feeds, save_crawled_data
from content_generator import generate_newsletter, save_newsletter
from publisher import publish


def run_pipeline():
    """전체 파이프라인을 실행합니다."""
    print("=" * 50)
    print("🍪 한입 AI — 일일 뉴스레터 파이프라인")
    print("=" * 50)
    
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    
    # Step 1: 뉴스 크롤링
    print("\n📡 Step 1/3: 뉴스 크롤링")
    print("-" * 40)
    articles = crawl_all_feeds()
    
    if not articles:
        print("❌ 수집된 AI 관련 기사가 없습니다. 크롤링 소스를 확인해주세요.")
        return False
    
    save_crawled_data(articles, data_dir)
    
    # Step 2: AI 콘텐츠 생성
    print("\n🤖 Step 2/3: AI 콘텐츠 생성")
    print("-" * 40)
    try:
        newsletter = generate_newsletter(articles)
        save_newsletter(newsletter, data_dir)
    except Exception as e:
        print(f"❌ 콘텐츠 생성 실패: {e}")
        return False
    
    # Step 3: HTML 빌드 & 퍼블리시
    print("\n🚀 Step 3/3: HTML 빌드 & 퍼블리시")
    print("-" * 40)
    publish(newsletter)
    
    print("\n" + "=" * 50)
    print("✅ 파이프라인 완료! 오늘의 뉴스레터가 발행되었습니다.")
    print("=" * 50)
    return True


if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
