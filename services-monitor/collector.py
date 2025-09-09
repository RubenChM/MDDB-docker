#!/usr/bin/env python3
"""
Data Collector Script
Fetches data from configured endpoints and stores in MongoDB
"""

import sys
import logging
from utils import DatabaseManager, SiteManager, DataFetcher, SlackReporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main execution function"""
    try:
        logger.info("Starting data collection process...")

        # Initialize database connection
        db_manager = DatabaseManager()

        # Initialize site manager
        site_manager = SiteManager(db_manager)

        # Get active sites to collect data from
        sites = site_manager.get_active_sites()

        if not sites:
            logger.warning("No active sites configured for data collection")
            return

        logger.info(f"Found {len(sites)} active sites to process")

        # Initialize Slack reporter
        slack_reporter = SlackReporter()
        # Initialize data fetcher
        data_fetcher = DataFetcher(db_manager, slack_reporter)

        # Process each site
        successful_collections = 0
        failed_collections = 0

        for site in sites:
            try:
                logger.info(f"Processing site: {site['node']} ({site['url']})")

                # Fetch data from the site
                success = data_fetcher.fetch_and_store(site)

                if success:
                    successful_collections += 1
                    logger.info(f"Successfully collected data from {site['node']}")
                else:
                    failed_collections += 1
                    logger.error(f"Failed to collect data from {site['node']}")

            except Exception as e:
                failed_collections += 1
                logger.error(f"Error processing site {site['node']}: {str(e)}")

        # Log summary
        logger.info(f"Data collection completed. Success: {successful_collections}, Failed: {failed_collections}")

    except Exception as e:
        logger.error(f"Fatal error in data collection: {str(e)}")
        sys.exit(1)
    finally:
        # Cleanup
        if 'db_manager' in locals():
            db_manager.close()


if __name__ == "__main__":
    main()
