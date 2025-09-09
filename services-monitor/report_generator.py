#!/usr/bin/env python3
"""
Services Status Report Generator
Generates and sends Slack reports with the latest status from all active monitoring nodes
"""
import logging
import sys
from utils import DatabaseManager, SiteManager, SlackReporter

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
        logger.info("Starting Services Status Report Generator")

        # Initialize database connection
        db_manager = DatabaseManager()

        # Initialize site manager
        site_manager = SiteManager(db_manager)

        # Get active sites to collect data from
        sites = site_manager.get_active_sites()

        slack_reporter = SlackReporter()

        if not sites:
            logger.warning("No active sites configured for data collection")
            return

        logger.info(f"Found {len(sites)} active sites to process")

        # Collect data for each node
        node_reports = []

        for site in sites:
            try:
                node_name = site['node']
                logger.info(f"Processing site: {node_name} ({site['url']})")

                # Get latest data for this node
                latest_data = db_manager.get_latest_data_for_node(node_name)

                if not latest_data:
                    logger.warning(f"No data found for node {node_name}")
                    node_reports.append({
                        'node_name': node_name,
                        'offline_services': 0,
                        'total_services': 0,
                        'services_summary': 'No data available',
                        'last_update': None,
                        'has_issues': True
                    })
                    continue

                # Process services data
                services_data = latest_data.get('services_data', [])

                # Remove services with 'not-found' status
                services_data = [s for s in services_data if s.get('status') != 'not-found']

                if not services_data:
                    logger.warning(f"No services data found for node {node_name}")
                    node_reports.append({
                        'node_name': node_name,
                        'offline_services': 0,
                        'total_services': 0,
                        'services_summary': 'No services data',
                        'last_update': latest_data.get('timestamp'),
                        'has_issues': True
                    })
                    continue

                # Count offline services
                offline_services = len([s for s in services_data if s.get('status') == 'offline'])
                total_services = len(services_data)

                # Format services summary
                services_summary = slack_reporter.format_services_summary(services_data)

                node_reports.append({
                    'node_name': node_name,
                    'offline_services': offline_services,
                    'total_services': total_services,
                    'services_summary': services_summary,
                    'last_update': latest_data.get('timestamp'),
                    'has_issues': offline_services > 0
                })

                logger.info(f"Node {node_name}: {offline_services}/{total_services} services offline")

            except Exception as e:
                logger.error(f"Error processing site {site['node']}: {str(e)}")

        # Create and send Slack message
        message = slack_reporter.create_report_message(node_reports)
        success = slack_reporter.send_report(message)

        if success:
            logger.info("Report generation and sending completed successfully")
        else:
            logger.error("Report generation completed but sending failed")

    except Exception as e:
        logger.error(f"Fatal error in report generation: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
