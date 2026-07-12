"""
NepCompare — Scheduler
APScheduler background jobs for automatic periodic scraping.
"""

import logging
import time
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from config import Config

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def scrape_all_stores(app):
    """Run scrapers for all stores with default queries."""
    with app.app_context():
        from database import db
        from models import ScrapingLog
        from scrapers import get_all_scrapers

        logger.info("=== Scheduled scraping started ===")

        for scraper in get_all_scrapers():
            for query in Config.DEFAULT_SCRAPE_QUERIES:
                log = ScrapingLog(
                    store=scraper.store_name,
                    query=query,
                    status="running",
                )
                db.session.add(log)
                db.session.commit()

                start = time.time()
                try:
                    products = scraper.search_products(query)
                    stats = scraper.save_to_database(products, db.session)
                    log.status = "success"
                    log.products_found = stats["total"]
                    log.products_new = stats["new"]
                    log.products_updated = stats["updated"]
                    logger.info(
                        f"[{scraper.store_name}] '{query}': "
                        f"{stats['new']} new, {stats['updated']} updated"
                    )
                except Exception as e:
                    log.status = "failed"
                    log.error_message = str(e)[:500]
                    logger.error(f"Scrape failed [{scraper.store_name}] '{query}': {e}")
                finally:
                    log.duration_seconds = round(time.time() - start, 2)
                    db.session.commit()

        logger.info("=== Scheduled scraping completed ===")


def init_scheduler(app):
    """Initialize and start the background scheduler."""
    scheduler.add_job(
        func=scrape_all_stores,
        trigger="interval",
        hours=Config.SCHEDULER_INTERVAL_HOURS,
        args=[app],
        id="scrape_all",
        name="Scrape all stores",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        f"Scheduler started: scraping every {Config.SCHEDULER_INTERVAL_HOURS} hours"
    )
