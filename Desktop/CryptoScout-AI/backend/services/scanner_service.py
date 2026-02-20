
# backend/services/scanner_service.py

import logging
from typing import Dict, List, Optional
import asyncio
from datetime import datetime

from services.market_service import fetch_top_projects
from services.sentiment_service import compute_sentiment
from services.ai_service import analyze_project, qualifies_for_ai
from services.ranking_service import compute_combined_score, get_rankings

from database.repository import (
    upsert_project,
    insert_project_history,
    get_project_by_symbol,
    insert_alert,
    get_recent_alert
)

from models.scan_status import ScanStatus
from core.ws_manager import manager


logger = logging.getLogger(__name__)
_scan_status = ScanStatus()


# =====================================================
# PUBLIC STATUS ACCESS
# =====================================================

def get_scan_status():
    """Return current scan status snapshot"""
    return _scan_status.snapshot()


# =====================================================
# HELPER FUNCTIONS
# =====================================================

async def broadcast_alert(symbol: str, change_pct: float):
    """Helper function to broadcast alerts asynchronously"""
    try:
        await manager.broadcast(
            "score_alert",
            {
                "symbol": symbol,
                "change_pct": round(change_pct, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Failed to broadcast alert for {symbol}: {e}")


async def broadcast_scan_completion(processed_count: int, ai_count: int):
    """Helper function to broadcast scan completion"""
    try:
        await manager.broadcast(
            "scan_complete",
            {
                "processed": processed_count,
                "ai_analyzed": ai_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Failed to broadcast scan completion: {e}")


def calculate_score_change(previous_score: float, new_score: float) -> float:
    """Calculate percentage change between scores"""
    if previous_score == 0:
        return 0.0
    return abs((new_score - previous_score) / previous_score) * 100


# =====================================================
# MAIN SCAN FUNCTION
# =====================================================

async def run_scan(limit: int = 50):
    """
    Full market scan.
    Safe, fault-tolerant, scheduler-ready.
    
    Args:
        limit: Maximum number of projects to fetch
    
    Returns:
        Dict with scan results or None if failed
    """
    logger.info(f"Starting market scan with limit={limit}...")
    scan_results = {
        "processed": 0,
        "ai_analyzed": 0,
        "errors": []
    }

    try:
        # Fetch market data
        projects = fetch_top_projects(limit=limit)

        if not projects:
            _scan_status.api_failure()
            _scan_status.failure()
            logger.warning("Scan aborted — no market data received")
            return None

        # Optional: limit AI exposure to top 30 by market cap
        projects = sorted(
            projects,
            key=lambda x: x.get("market_cap", 0) or 0,  # Handle None values
            reverse=True
        )[:30]

        processed_count = 0
        ai_count = 0

        for project in projects:
            try:
                symbol = project.get("symbol")
                if not symbol:
                    logger.debug("Skipping project without symbol")
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
                    try:
                        ai_result = analyze_project(project)
                        project["ai_score"] = ai_result.get("score", 0)
                        project["ai_verdict"] = ai_result.get("verdict", "UNKNOWN")
                        ai_count += 1
                    except Exception as e:
                        logger.error(f"AI analysis failed for {symbol}: {e}")
                        project["ai_score"] = 0
                        project["ai_verdict"] = "ANALYSIS_FAILED"
                        scan_results["errors"].append(f"AI analysis failed for {symbol}")
                else:
                    project["ai_score"] = 0
                    project["ai_verdict"] = "NOT_QUALIFIED"

                # ==========================
                # PREVIOUS SCORE CHECK
                # ==========================
                existing = get_project_by_symbol(symbol)
                previous_score = 0

                if existing:
                    previous_score = compute_combined_score(existing) or 0

                # ==========================
                # COMPUTE NEW SCORE
                # ==========================
                combined_score = compute_combined_score(project)
                project["combined_score"] = combined_score

                # ==========================
                # SMART ALERT DETECTION
                # ==========================
                if previous_score > 0:
                    change_pct = calculate_score_change(previous_score, combined_score)

                    if change_pct >= 20:  # 20% threshold
                        # Prevent duplicate alert within 60 minutes
                        recent = get_recent_alert(symbol, "SCORE_JUMP", 60)

                        if not recent:
                            message = f"{symbol} score changed {change_pct:.2f}% in latest scan"

                            # Store alert in database
                            insert_alert(
                                symbol=symbol,
                                alert_type="SCORE_JUMP",
                                message=message
                            )

                            # Broadcast alert via WebSocket
                            await broadcast_alert(symbol, change_pct)

                            logger.info(f"ALERT STORED: {message}")

                # ==========================
                # SAVE CURRENT STATE
                # ==========================
                upsert_project(project)

                # ==========================
                # SAVE HISTORY SNAPSHOT
                # ==========================
                history_data = {
                    "symbol": symbol,
                    "current_price": project.get("current_price", 0),
                    "market_cap": project.get("market_cap", 0),
                    "volume_24h": project.get("volume_24h", 0),
                    "price_change_24h": project.get("price_change_24h", 0),
                    "price_change_7d": project.get("price_change_7d", 0),
                    "ai_score": project.get("ai_score", 0),
                    "ai_verdict": project.get("ai_verdict", "UNKNOWN"),
                    "sentiment_score": project.get("sentiment_score", 0),
                    "combined_score": combined_score
                }
                
                insert_project_history(history_data)

                processed_count += 1

            except Exception as e:
                logger.error(f"Error processing project {project.get('symbol', 'UNKNOWN')}: {e}")
                scan_results["errors"].append(f"Project {project.get('symbol', 'UNKNOWN')}: {str(e)}")
                continue

        # Update scan status
        _scan_status.success()
        scan_results["processed"] = processed_count
        scan_results["ai_analyzed"] = ai_count

        # Broadcast scan completion
        await broadcast_scan_completion(processed_count, ai_count)

        logger.info(
            "Scan complete — %s processed, %s AI analyzed",
            processed_count,
            ai_count
        )
        
        return scan_results

    except Exception as e:
        logger.error(f"Scan failed with critical error: {e}", exc_info=True)
        _scan_status.failure()
        scan_results["errors"].append(f"Critical error: {str(e)}")
        return scan_results


# =====================================================
# SYNC WRAPPER FOR SCHEDULER COMPATIBILITY
# =====================================================

def run_scan_sync(limit: int = 50):
    """
    Synchronous wrapper for run_scan to be used with schedulers
    that don't support async functions.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, create a new one
        return asyncio.run(run_scan(limit))
    else:
        # Already in async context, create task
        return asyncio.create_task(run_scan(limit))


# =====================================================
# SCAN STATUS CHECK
# =====================================================

def is_scan_running() -> bool:
    """Check if a scan is currently running"""
    return _scan_status.is_running()


def get_last_scan_time() -> Optional[datetime]:
    """Get the timestamp of the last successful scan"""
    return _scan_status.last_success_time


# =====================================================
# PROJECT-SPECIFIC SCAN FUNCTIONS
# =====================================================

async def scan_single_project(symbol: str) -> Optional[Dict]:
    """
    Scan and update a single project by symbol
    """
    try:
        # Fetch single project data (you'll need to implement this in market_service)
        from services.market_service import fetch_project_by_symbol
        project = fetch_project_by_symbol(symbol)
        
        if not project:
            logger.warning(f"Project {symbol} not found")
            return None
        
        # Process the project (similar logic as above but for single project)
        sentiment_score = compute_sentiment(project)
        project["sentiment_score"] = sentiment_score
        
        if qualifies_for_ai(project):
            ai_result = analyze_project(project)
            project["ai_score"] = ai_result.get("score", 0)
            project["ai_verdict"] = ai_result.get("verdict", "UNKNOWN")
        else:
            project["ai_score"] = 0
            project["ai_verdict"] = "NOT_QUALIFIED"
        
        combined_score = compute_combined_score(project)
        project["combined_score"] = combined_score
        
        # Save to database
        upsert_project(project)
        
        # Save history
        history_data = {
            "symbol": symbol,
            "current_price": project.get("current_price", 0),
            "market_cap": project.get("market_cap", 0),
            "volume_24h": project.get("volume_24h", 0),
            "price_change_24h": project.get("price_change_24h", 0),
            "price_change_7d": project.get("price_change_7d", 0),
            "ai_score": project.get("ai_score", 0),
            "ai_verdict": project.get("ai_verdict", "UNKNOWN"),
            "sentiment_score": project.get("sentiment_score", 0),
            "combined_score": combined_score
        }
        
        insert_project_history(history_data)
        
        return project
        
    except Exception as e:
        logger.error(f"Failed to scan single project {symbol}: {e}")
        return None