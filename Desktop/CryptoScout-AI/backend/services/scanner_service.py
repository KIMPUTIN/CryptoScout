
# backend/services/scanner_service.py

import logging
from typing import Dict, List

from services.market_service import fetch_top_projects
from services.sentiment_service import compute_sentiment
from services.ai_service import analyze_project, qualifies_for_ai
from services.ranking_service import compute_combined_score

from database.repository import (
    upsert_project,
    insert_project_history,
    get_project_by_symbol
)

from models.scan_status import ScanStatus
from database.repository import insert_alert, get_recent_alert
from services.ranking_service import get_rankings
import asyncio
from core.ws_manager import manager



logger = logging.getLogger(__name__)
_scan_status = ScanStatus()


# =====================================================
# PUBLIC STATUS ACCESS
# =====================================================

def get_scan_status():
    return _scan_status.snapshot()


# =====================================================
# MAIN SCAN FUNCTION
# =====================================================

def run_scan(limit: int = 50):
    """
    Full market scan.
    Safe, fault-tolerant, scheduler-ready.
    """

    logger.info("Starting market scan...")

    try:
        projects = fetch_top_projects(limit=limit)

        if not projects:
            _scan_status.api_failure()
            _scan_status.failure()
            logger.warning("Scan aborted — no market data")
            return

        # Optional: limit AI exposure to top 30 by market cap
        projects = sorted(
            projects,
            key=lambda x: x.get("market_cap", 0),
            reverse=True
        )[:30]

        processed_count = 0
        ai_count = 0

        for project in projects:

            symbol = project.get("symbol")
            if not symbol:
                continue

            # ==========================
            # SENTIMENT
            # ==========================

            sentiment_score = compute_sentiment(project)
            project["sentiment_score"] = sentiment_score

            # ==========================
            # AI FILTERING
            # ==========================

            if qualifies_for_ai(project):
                ai_result = analyze_project(project)
                project["ai_score"] = ai_result["score"]
                project["ai_verdict"] = ai_result["verdict"]
                ai_count += 1
            else:
                project["ai_score"] = 0
                project["ai_verdict"] = "NOT_QUALIFIED"

            # ==========================
            # PREVIOUS SCORE CHECK
            # ==========================

            existing = get_project_by_symbol(symbol)
            previous_score = 0

            if existing:
                previous_score = compute_combined_score(existing)

            # ==========================
            # COMPUTE NEW SCORE
            # ==========================

            combined_score = compute_combined_score(project)

            # ==========================
            # SMART ALERT DETECTION
            # ==========================

            if previous_score > 0:
                change_pct = abs(
                    (combined_score - previous_score) / previous_score
                ) * 100

                if change_pct >= 20:

                    # Prevent duplicate alert within 60 minutes
                    recent = get_recent_alert(symbol, "SCORE_JUMP", 60)

                    if not recent:
                        message = f"{symbol} score changed {change_pct:.2f}% in latest scan"

                        insert_alert(
                            symbol=symbol,
                            alert_type="SCORE_JUMP",
                            message=message
                        )

                        try:
                            asyncio.create_task(
                                manager.broadcast(
                                    "score_alert",
                                    {
                                        "symbol": symbol,
                                        "change_pct": round(change_pct, 2)
                                    }
                                )
                            )
                        except RuntimeError:
                            pass


                        logger.info(f"ALERT STORED: {message}")


            # ==========================
            # SAVE CURRENT STATE
            # ==========================

            upsert_project(project)

            # ==========================
            # SAVE HISTORY SNAPSHOT
            # ==========================

            insert_project_history({
                "symbol": symbol,
                "current_price": project.get("current_price", 0),
                "market_cap": project.get("market_cap", 0),
                "volume_24h": project.get("volume_24h", 0),
                "price_change_24h": project.get("price_change_24h", 0),
                "price_change_7d": project.get("price_change_7d", 0),
                "ai_score": project.get("ai_score", 0),
                "sentiment_score": project.get("sentiment_score", 0),
                "combined_score": combined_score
            })

            processed_count += 1

        _scan_status.success()


        # 🔥 Broadcast scan completion
        try:
            asyncio.create_task(
                manager.broadcast(
                    "scan_complete",
                    {
                        "processed": processed_count,
                        "ai_analyzed": ai_count
                    }
                )
            )
        except RuntimeError:
            # Happens if no event loop (safe fallback)
            pass


        logger.info(
            "Scan complete — %s processed, %s AI analyzed",
            processed_count,
            ai_count
        )

    except Exception as e:
        logger.error("Scan failed: %s", e)
        _scan_status.failure()



get_rankings("balanced")
get_rankings("aggressive")
get_rankings("conservative")