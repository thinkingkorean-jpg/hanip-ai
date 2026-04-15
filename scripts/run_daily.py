"""
한입 AI 일일 파이프라인 실행기.
크롤링, 콘텐츠 생성, 퍼블리싱을 순차 실행합니다.
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from content_generator import generate_newsletter
from news_crawler import crawl_all_feeds, save_crawled_data
from publisher import load_latest_newsletter, update_index_page

MAX_STAGE_RETRIES = 2


def configure_logging():
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    log_path = os.path.join(logs_dir, f"run_{datetime.now().strftime('%Y%m%d')}.log")
    logger = logging.getLogger("hanip.daily")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger, log_path


def run_stage(stage_name, logger, func, *args, **kwargs):
    last_error = None
    for attempt in range(MAX_STAGE_RETRIES + 1):
        try:
            logger.info("[%s] 시작 (attempt=%s)", stage_name, attempt + 1)
            result = func(*args, **kwargs)
            logger.info("[%s] 완료", stage_name)
            return result
        except Exception as exc:
            last_error = exc
            logger.exception("[%s] 실패", stage_name)
            if attempt < MAX_STAGE_RETRIES:
                logger.warning("[%s] 재시도합니다.", stage_name)

    raise RuntimeError(f"{stage_name} 단계 실패: {last_error}") from last_error


def run_pipeline():
    """전체 파이프라인을 실행합니다."""
    logger, log_path = configure_logging()
    logger.info("=" * 50)
    logger.info("한입 AI 일일 파이프라인 시작")
    logger.info("로그 파일: %s", log_path)
    logger.info("=" * 50)

    try:
        data = run_stage("crawler", logger, crawl_all_feeds)
        total_articles = sum(len(articles) for articles in data.values())
        if total_articles <= 0:
            logger.error("수집된 기사 총합이 0건입니다.")
            return False

        run_stage("save_crawled_data", logger, save_crawled_data, data)
        run_stage("generate_newsletter", logger, generate_newsletter)
        news_data = run_stage("load_latest_newsletter", logger, load_latest_newsletter)
        run_stage("publisher", logger, update_index_page, news_data)
    except Exception as exc:
        logger.error("파이프라인 실패: %s", exc)
        return False

    logger.info("=" * 50)
    logger.info("파이프라인 완료")
    logger.info("=" * 50)
    return True


if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
