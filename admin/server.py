from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest
except Exception:  # pragma: no cover - graceful fallback when dependency is absent
    BetaAnalyticsDataClient = None
    DateRange = Metric = RunReportRequest = None


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
ARTICLES_DIR = PROJECT_ROOT / "articles"
SCRIPTS_DATA_DIR = PROJECT_ROOT / "scripts" / "data"
DEFAULT_WARNING = "Configuration is missing. Returning empty data."

app = FastAPI(title="Hanip AI Admin", version="1.0.0")
app.mount("/admin", StaticFiles(directory=BASE_DIR, html=True), name="admin-static")


class AuthRequest(BaseModel):
    password: str


def _warning_payload(message: str = DEFAULT_WARNING) -> dict[str, Any]:
    return {"warning": message}


def _safe_read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _latest_newsletter_file() -> Path | None:
    files = sorted(SCRIPTS_DATA_DIR.glob("newsletter_*.json"), reverse=True)
    return files[0] if files else None


async def _fetch_stibee_subscribers() -> dict[str, Any]:
    api_key = os.getenv("STIBEE_API_KEY", "").strip()
    address_book_id = os.getenv("STIBEE_ADDRESS_BOOK_ID", "").strip()
    if not api_key or not address_book_id:
        return {
            "count": 0,
            "subscribers": [],
            **_warning_payload("Missing STIBEE_API_KEY or STIBEE_ADDRESS_BOOK_ID."),
        }

    url = f"https://api.stibee.com/v1/lists/{address_book_id}/subscribers"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                url,
                headers={"AccessToken": api_key},
                params={"offset": 0, "limit": 20},
            )
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        return {
            "count": 0,
            "subscribers": [],
            **_warning_payload(f"Stibee request failed: {exc}"),
        }

    raw_items = (
        payload.get("subscribers")
        or payload.get("items")
        or payload.get("data")
        or []
    )
    subscribers = []
    for item in raw_items[:20]:
        subscribers.append(
            {
                "email": item.get("email") or item.get("subscriberEmail") or "",
                "name": item.get("name") or item.get("subscriberName") or "",
                "status": item.get("status") or item.get("state") or "",
                "created_at": item.get("createdAt") or item.get("created_at") or "",
            }
        )

    count = (
        payload.get("count")
        or payload.get("totalCount")
        or payload.get("total")
        or payload.get("subscriberCount")
        or len(subscribers)
    )

    return {"count": count, "subscribers": subscribers}


def _run_ga_report(days: int) -> int:
    property_id = os.getenv("GA_PROPERTY_ID", "").strip()
    credentials_path = os.getenv("GA_CREDENTIALS_PATH", "").strip()
    if not property_id or not credentials_path or not BetaAnalyticsDataClient:
        return 0

    client = BetaAnalyticsDataClient.from_service_account_file(credentials_path)
    start_date = "today" if days == 1 else f"{days - 1}daysAgo"
    request = RunReportRequest(
        property=f"properties/{property_id}",
        metrics=[Metric(name="activeUsers")],
        date_ranges=[DateRange(start_date=start_date, end_date="today")],
    )
    response = client.run_report(request)
    if not response.rows:
        return 0
    return int(response.rows[0].metric_values[0].value)


async def _fetch_adsense_summary() -> dict[str, Any]:
    credentials_path = os.getenv("ADSENSE_CREDENTIALS_PATH", "").strip()
    if not credentials_path:
        return {
            "today_revenue": 0.0,
            "month_revenue": 0.0,
            **_warning_payload("Missing ADSENSE_CREDENTIALS_PATH."),
        }

    # Graceful stub: credentials presence is acknowledged, but unsupported OAuth
    # setups still return empty values instead of failing the dashboard.
    return {
        "today_revenue": 0.0,
        "month_revenue": 0.0,
        **_warning_payload("AdSense API integration is configured as a graceful stub."),
    }


def _scan_articles() -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for article_path in sorted(ARTICLES_DIR.glob("*.html"), reverse=True):
        if article_path.name == "index.html":
            continue
        published_at = datetime.fromtimestamp(article_path.stat().st_mtime)
        entries.append(
            {
                "filename": article_path.name,
                "date": article_path.stem,
                "published_at": published_at.isoformat(),
            }
        )

    last_publish_date = entries[0]["date"] if entries else ""
    return {"last_publish_date": last_publish_date, "history": entries}


def _pipeline_status() -> dict[str, Any]:
    latest = _latest_newsletter_file()
    if not latest:
        return {
            "success": False,
            "last_run_time": "",
            "latest_file": "",
            **_warning_payload("No newsletter JSON files found."),
        }

    payload = _safe_read_json(latest)
    success = bool(payload)
    return {
        "success": success,
        "last_run_time": datetime.fromtimestamp(latest.stat().st_mtime).isoformat(),
        "latest_file": latest.name,
        "newsletter_date": (payload or {}).get("metadata", {}).get("date", ""),
    }


@app.get("/")
async def admin_index() -> FileResponse:
    return FileResponse(BASE_DIR / "index.html")


@app.post("/api/auth")
async def auth(body: AuthRequest) -> JSONResponse:
    admin_password = os.getenv("ADMIN_PASSWORD", "").strip()
    success = bool(admin_password) and body.password == admin_password
    return JSONResponse({"success": success})


@app.get("/api/subscribers")
async def subscribers() -> JSONResponse:
    return JSONResponse(await _fetch_stibee_subscribers())


@app.get("/api/analytics")
async def analytics() -> JSONResponse:
    property_id = os.getenv("GA_PROPERTY_ID", "").strip()
    credentials_path = os.getenv("GA_CREDENTIALS_PATH", "").strip()
    if not property_id or not credentials_path:
        return JSONResponse(
            {
                "today": 0,
                "last_7_days": 0,
                "last_30_days": 0,
                **_warning_payload("Missing GA_PROPERTY_ID or GA_CREDENTIALS_PATH."),
            }
        )

    try:
        return JSONResponse(
            {
                "today": _run_ga_report(1),
                "last_7_days": _run_ga_report(7),
                "last_30_days": _run_ga_report(30),
            }
        )
    except Exception as exc:
        return JSONResponse(
            {
                "today": 0,
                "last_7_days": 0,
                "last_30_days": 0,
                **_warning_payload(f"Google Analytics request failed: {exc}"),
            }
        )


@app.get("/api/adsense")
async def adsense() -> JSONResponse:
    return JSONResponse(await _fetch_adsense_summary())


@app.get("/api/articles")
async def articles() -> JSONResponse:
    return JSONResponse(_scan_articles())


@app.get("/api/pipeline/status")
async def pipeline_status() -> JSONResponse:
    return JSONResponse(_pipeline_status())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8765, reload=False)
