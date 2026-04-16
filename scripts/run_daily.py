"""
한입 AI 일일 파이프라인 실행기.
크롤링, 콘텐츠 생성, 퍼블리싱을 순차 실행합니다.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from content_generator import generate_newsletter
from news_crawler import crawl_all_feeds, save_crawled_data
from publisher import load_latest_newsletter, update_index_page

MAX_STAGE_RETRIES = 2
MIN_TOTAL_ARTICLES = 3
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
# pipeline_log.json은 프로젝트 루트에 저장 (scripts/data/ 는 .gitignore 제외)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPELINE_LOG_PATH = os.path.join(PROJECT_ROOT, "pipeline_log.json")


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


def save_pipeline_log(entry: dict):
    """파이프라인 실행 결과를 pipeline_log.json에 누적 저장합니다."""
    logs = []
    if os.path.exists(PIPELINE_LOG_PATH):
        try:
            with open(PIPELINE_LOG_PATH, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    logs.append(entry)
    logs = logs[-30:]  # 최근 30개만 유지
    with open(PIPELINE_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


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
    pipeline_start = time.time()
    today = datetime.now().strftime("%Y-%m-%d")
    log_entry = {"date": today, "success": False, "stages": {}, "error": None}

    logger.info("=" * 50)
    logger.info("한입 AI 일일 파이프라인 시작")
    logger.info("=" * 50)

    try:
        # Step 1: 크롤링
        t0 = time.time()
        data = run_stage("crawler", logger, crawl_all_feeds)
        log_entry["stages"]["crawler"] = round(time.time() - t0, 2)

        total_articles = sum(len(articles) for articles in data.values())
        logger.info("수집된 기사 총합: %d건", total_articles)

        if total_articles < MIN_TOTAL_ARTICLES:
            msg = f"수집 기사 총합 {total_articles}건 — 최소 {MIN_TOTAL_ARTICLES}건 미달, 발행 중단."
            logger.error(msg)
            log_entry["error"] = msg
            save_pipeline_log(log_entry)
            return False

        # Step 2: 저장
        t0 = time.time()
        run_stage("save_crawled_data", logger, save_crawled_data, data)
        log_entry["stages"]["save"] = round(time.time() - t0, 2)

        # Step 3: AI 생성
        t0 = time.time()
        run_stage("generate_newsletter", logger, generate_newsletter)
        log_entry["stages"]["generate"] = round(time.time() - t0, 2)

        # Step 4: 발행
        t0 = time.time()
        news_data = run_stage("load_latest_newsletter", logger, load_latest_newsletter)
        run_stage("publisher", logger, update_index_page, news_data)
        log_entry["stages"]["publish"] = round(time.time() - t0, 2)

    except Exception as exc:
        logger.error("파이프라인 실패: %s", exc)
        log_entry["error"] = str(exc)
        save_pipeline_log(log_entry)
        return False

    log_entry["success"] = True
    log_entry["total_seconds"] = round(time.time() - pipeline_start, 2)
    save_pipeline_log(log_entry)

    logger.info("=" * 50)
    logger.info("파이프라인 완료 (%.1f초)", log_entry["total_seconds"])
    logger.info("=" * 50)
    return True


if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
