"""
Utility classes for data collection service
"""

import os
import logging
import requests
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages MongoDB connections and operations"""

    def __init__(self):
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        """Establish connection to MongoDB"""
        try:
            # Get connection parameters from environment
            db_server = os.getenv('DB_SERVER')
            db_port = int(os.getenv('DB_PORT'))
            db_name = os.getenv('DB_NAME')
            db_user = os.getenv('DB_AUTH_USER')
            db_password = os.getenv('DB_AUTH_PASSWORD')
            db_authsource = os.getenv('DB_AUTHSOURCE')

            # Build connection string
            if db_user and db_password:
                connection_string = f"mongodb://{db_user}:{db_password}@{db_server}:{db_port}/{db_name}?authSource={db_authsource}"
            else:
                connection_string = f"mongodb://{db_server}:{db_port}/{db_name}"

            self.client = MongoClient(connection_string)
            self.db = self.client[db_name]

            # Test connection
            self.client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB at {db_server}:{db_port}")

        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise

    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()

    def get_collection(self, collection_name: str):
        """Get a MongoDB collection"""
        return self.db[collection_name]

    def insert_collected_data(self, data: Dict[str, Any]) -> str:
        """Insert collected data into the database"""
        try:
            collection = self.get_collection('collected_data')
            result = collection.insert_one(data)
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Error inserting data: {str(e)}")
            raise

    def get_latest_data_for_node(self, node: str) -> Optional[Dict[str, Any]]:
        """Get the latest collected data for a specific node"""
        try:
            collection = self.get_collection('collected_data')
            latest_data = collection.find_one(
                {'node': node},
                sort=[('timestamp', -1)]
            )
            return latest_data
        except PyMongoError as e:
            logger.error(f"Error fetching latest data for node {node}: {str(e)}")
            return None


class SiteManager:
    """Manages site configurations"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.collection = db_manager.get_collection('data_collection_sites')

    def get_active_sites(self) -> List[Dict[str, Any]]:
        """Get all active sites for data collection"""
        try:
            sites = list(self.collection.find({'active': True}))
            return sites
        except PyMongoError as e:
            logger.error(f"Error fetching active sites: {str(e)}")
            return []


class SlackReporter:
    """Handles Slack message formatting and sending"""

    def __init__(self):
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not configured")

    def format_services_summary(self, services_data: List[Dict[str, Any]]) -> str:
        """Format services data into a readable summary"""
        if not services_data:
            return "No service data available"

        # Group services by status
        running = []
        offline = []
        idle = []

        for service in services_data:
            status = service.get('status', 'unknown')
            name = service.get('name', service.get('service', 'Unknown'))

            if status == 'running':
                replicas = service.get('replicas', {})
                running_count = replicas.get('running', 0)
                desired_count = replicas.get('desired', 0)
                if service.get('service') == 'db':
                    running.append(f"{name}")
                else:
                    running.append(f"{name} ({running_count}/{desired_count})")
            elif status == 'offline':
                offline.append(name)
            elif status == 'idle':
                idle.append(name)

        summary_parts = []
        if running:
            summary_parts.append(f"🟢 Running: {', '.join(running)}")
        if idle:
            summary_parts.append(f"⚪ Idle: {', '.join(idle)}")
        if offline:
            summary_parts.append(f"🔴 Offline: {', '.join(offline)}")

        return "\n".join(summary_parts) if summary_parts else "No services found"

    def create_report_message(self, node_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a formatted Slack message with the services report"""

        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

        # Create the main message
        message = {
            "text": "🔍 MDDB Services Status Report",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🔍 MDDB Services Status Report"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Generated on {current_time}"
                        }
                    ]
                },
                {
                    "type": "divider"
                }
            ]
        }

        if not node_reports:
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "⚠️ No active nodes found or no data available"
                }
            })
            return message

        # Summary section
        total_nodes = len(node_reports)
        nodes_with_issues = sum(1 for report in node_reports if report['offline_services'] > 0 or report.get('has_issues'))
        total_offline_services = sum(report['offline_services'] for report in node_reports)

        summary_text = f"📊 *Summary:* {total_nodes} nodes monitored"
        if nodes_with_issues > 0:
            summary_text += f" | 🚨 {nodes_with_issues} nodes with issues | {total_offline_services} services offline"
        else:
            summary_text += " | ✅ All services running normally"

        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": summary_text
            }
        })

        message["blocks"].append({
            "type": "divider"
        })

        # Node details
        for report in node_reports:
            node_name = report['node_name']
            offline_count = report['offline_services']
            total_count = report['total_services']
            services_summary = report['services_summary']
            last_update = report['last_update']

            # Determine status icon
            if offline_count > 0:
                status_icon = "🔴"
                # color = "danger"
            elif report.get('has_issues', False):
                status_icon = "🟡"
                # color = "warning"
            else:
                status_icon = "🟢"
                # color = "good"

            # Create node section
            node_text = f"{status_icon} *{node_name}*\n"
            node_text += f"Services: {offline_count}/{total_count} offline"

            if last_update:
                time_ago = self._format_time_ago(last_update)
                node_text += f"\nLast update: {time_ago}"

            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": node_text
                }
            })

            # Services details
            if services_summary:
                message["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{services_summary}```"
                    }
                })

            message["blocks"].append({
                "type": "divider"
            })

        return message

    def create_service_alert_message(self, node_name: str, service: Dict[str, Any]):
        """Create notification for offline service"""
        return {
            "text": f"🚨 Service Alert: *{service['name']}* in *{node_name}* is OFFLINE",
            "attachments": [
                {
                    "color": "danger",
                    "fields": [
                        {
                            "title": "Node",
                            "value": node_name,
                            "short": True
                        },
                        {
                            "title": "Service",
                            "value": service['name'],
                            "short": True
                        },
                        {
                            "title": "Type",
                            "value": service.get('type', 'Unknown'),
                            "short": True
                        },
                        {
                            "title": "Replicas",
                            "value": f"{service.get('replicas', {}).get('running', 0)}/{service.get('replicas', {}).get('desired', 0)}",
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                            "short": True
                        }
                    ]
                }
            ]
        }

    def _format_time_ago(self, timestamp: datetime) -> str:
        """Format timestamp as time ago"""
        try:
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

            now = datetime.utcnow()
            if timestamp.tzinfo is not None:
                # If timestamp has timezone info, make now timezone-aware
                from datetime import timezone
                now = now.replace(tzinfo=timezone.utc)
                if timestamp.tzinfo != timezone.utc:
                    timestamp = timestamp.astimezone(timezone.utc)

            diff = now - timestamp

            if diff.days > 0:
                return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:
                return "Just now"
        except Exception as e:
            logger.error(f"Error formatting time: {e}")
            return "Unknown"

    def send_report(self, message: Dict[str, Any]) -> bool:
        """Send the report message to Slack"""
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured, cannot send report")
            logger.info("Report content:")
            logger.info(json.dumps(message, indent=2))
            return False

        try:
            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=30
            )
            response.raise_for_status()
            logger.info("Successfully sent Slack report")
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack report: {str(e)}")
            return False


class DataFetcher:
    """Handles data fetching from external endpoints"""

    def __init__(self, db_manager: DatabaseManager, slack_reporter: SlackReporter):
        self.db_manager = db_manager
        self.slack_reporter = slack_reporter
        self.session = requests.Session()
        self.session.timeout = 30  # 30 seconds timeout

    def fetch_and_store(self, site_config: Dict[str, Any]) -> bool:
        """Fetch data from a site and store it in the database"""
        try:
            # Extract site configuration
            url = site_config['url']

            # Prepare request for services
            request_params_services = {
                'url': f'{url}vre_lite/api/services',
                'timeout': 30
            }

            response1 = self.session.get(**request_params_services)

            # Check response1
            response1.raise_for_status()

            services_data = response1.json()

            # Prepare request for database
            request_params_db = {
                'url': f'{url}vre_lite/api/services/rest',
                'timeout': 30
            }

            response2 = self.session.get(**request_params_db)

            # Check response2
            response2.raise_for_status()

            # Temporary placeholder for database info
            db = {
                'service': 'db',
                'name': 'Database',
                'version': 'N/A',
                'latestTag': 'N/A',
                'update': 'no-repo',
                'type': 'core',
                'status': 'checking'
            }

            if response2.status_code == 200:
                db['status'] = 'running'
            else:
                db['status'] = 'offline'

            services_data.append(db)

            # Check for offline services and send Slack notifications
            offline_services = [service for service in services_data if service.get('status') == 'offline']

            if offline_services:
                for service in offline_services:
                    message = self.slack_reporter.create_service_alert_message(site_config['node'], service)
                    success = self.slack_reporter.send_report(message)
                    if success:
                        logger.info(f"Sent Slack notification for offline service {service['name']} on {site_config['node']}")
                    else:
                        logger.error(f"Failed to send Slack notification for offline service {service['name']} on {site_config['node']}")

            # Prepare data for storage
            collected_data = {
                'site_id': str(site_config['_id']),
                'node': site_config['node'],
                'url': url,
                'timestamp': datetime.utcnow(),
                'status_code': response1.status_code,
                'response_headers': dict(response1.headers),
                'services_data': services_data,
                'offline_services_count': len(offline_services),
                'total_services_count': len(services_data),
                'success': True
            }

            # Store in database
            self.db_manager.insert_collected_data(collected_data)

            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {site_config['node']}: {str(e)}")
            self._store_error_data(site_config, str(e))
            return False
        except Exception as e:
            logger.error(f"Unexpected error for {site_config['node']}: {str(e)}")
            self._store_error_data(site_config, str(e))
            return False

    def _store_error_data(self, site_config: Dict[str, Any], error_message: str):
        """Store error information in the database"""
        try:
            error_data = {
                'site_id': str(site_config['_id']),
                'site_name': site_config['node'],
                'url': site_config['url'],
                'timestamp': datetime.utcnow(),
                'error_message': error_message,
                'success': False
            }
            self.db_manager.insert_collected_data(error_data)
        except Exception as e:
            logger.error(f"Failed to store error data: {str(e)}")
