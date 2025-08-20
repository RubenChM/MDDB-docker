#!/usr/bin/env python3

import argparse
import os
import sys
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError


class VersionTracker:
    def __init__(self, db_server: str, db_port: int, db_name: str,
                 auth_user: str, auth_password: str, auth_source: str):
        """Initialize MongoDB connection with authentication."""
        self.db_server = db_server
        self.db_port = db_port
        self.db_name = db_name
        self.auth_user = auth_user
        self.auth_password = auth_password
        self.auth_source = auth_source

        self.client = None
        self.db = None
        self.collection = None

    def connect(self) -> bool:
        """Establish connection to MongoDB."""
        try:
            print(f"🔌 Connecting to MongoDB at {self.db_server}:{self.db_port}")

            # Build connection URI
            if self.auth_user and self.auth_password:
                uri = f"mongodb://{self.auth_user}:{self.auth_password}@{self.db_server}:{self.db_port}/{self.auth_source}"
            else:
                uri = f"mongodb://{self.db_server}:{self.db_port}"

            # Connect to MongoDB
            self.client = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000
            )

            # Test connection
            self.client.admin.command('ping')
            print("✅ Successfully connected to MongoDB")
            return True

        except ConnectionFailure as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error connecting to MongoDB: {e}")
            return False

    def ensure_database(self) -> bool:
        """Ensure database exists, create if not."""
        try:
            # Check if database exists
            existing_databases = self.client.list_database_names()

            if self.db_name in existing_databases:
                print(f"✅ Database '{self.db_name}' already exists")
            else:
                print(f"🆕 Creating database '{self.db_name}'")

            # Access/create database
            self.db = self.client[self.db_name]
            return True

        except Exception as e:
            print(f"❌ Error accessing/creating database: {e}")
            return False

    def ensure_collection(self, collection_name: str = "version") -> bool:
        """Ensure collection exists, create if not."""
        try:
            # Check if collection exists
            existing_collections = self.db.list_collection_names()

            if collection_name in existing_collections:
                print(f"✅ Collection '{collection_name}' already exists")
            else:
                print(f"🆕 Creating collection '{collection_name}'")

            # Access/create collection
            self.collection = self.db[collection_name]

            # Create index for better performance
            self.collection.create_index([("service", 1), ("timestamp", -1)])
            print("📊 Index created on service and timestamp fields")

            return True

        except Exception as e:
            print(f"❌ Error accessing/creating collection: {e}")
            return False

    def insert_version_document(self, service: str, version: str) -> bool:
        """Insert a new version document."""
        try:
            # Prepare document
            document = {
                "service": service,
                "version": version,
                "timestamp": datetime.utcnow(),
                # "node": os.getenv('NODE', 'unknown'),
                # "environment": os.getenv('ENVIRONMENT', 'unknown'),
                # "inserted_by": "version_tracker_script"
            }

            print(f"📝 Inserting version document for service '{service}' version '{version}'")

            # Insert document
            result = self.collection.insert_one(document)

            print(f"✅ Document inserted successfully with ID: {result.inserted_id}")

            # Show document count for this service
            service_count = self.collection.count_documents({"service": service})
            print(f"📊 Total versions tracked for '{service}': {service_count}")

            return True

        except DuplicateKeyError as e:
            print(f"⚠️  Duplicate document detected: {e}")
            return False
        except Exception as e:
            print(f"❌ Error inserting document: {e}")
            return False

    def get_service_versions(self, service: str, limit: int = 5) -> list:
        """Get recent versions for a service."""
        try:
            versions = list(self.collection.find(
                {"service": service}
            ).sort("timestamp", -1).limit(limit))

            return versions

        except Exception as e:
            print(f"❌ Error retrieving versions: {e}")
            return []

    def show_recent_versions(self, service: str, limit: int = 5):
        """Show recent versions for a service."""
        versions = self.get_service_versions(service, limit)

        if versions:
            print(f"\n📈 Recent versions for '{service}' (last {len(versions)}):")
            print("-" * 60)
            for version in versions:
                timestamp = version.get('timestamp', 'Unknown')
                ver = version.get('version', 'Unknown')
                node = version.get('node', 'Unknown')
                print(f"  {timestamp} | {ver} | Node: {node}")
        else:
            print(f"📋 No previous versions found for '{service}'")

    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            print("🔌 MongoDB connection closed")


def get_build_args() -> dict:
    """Get build arguments from environment variables."""
    build_args = {
        'db_server': os.getenv('DB_SERVER', 'localhost'),
        'db_port': int(os.getenv('DB_PORT', '27017')),
        'db_name': os.getenv('DB_VRE_NAME', 'vre_db'),
        'auth_user': os.getenv('DB_VRE_AUTH_USER', ''),
        'auth_password': os.getenv('DB_VRE_AUTH_PASSWORD', ''),
        'auth_source': os.getenv('DB_VRE_AUTHSOURCE', 'admin')
    }

    print("🔧 Build arguments loaded:")
    print(f"  DB Server: {build_args['db_server']}")
    print(f"  DB Port: {build_args['db_port']}")
    print(f"  DB Name: {build_args['db_name']}")
    print(f"  Auth User: {build_args['auth_user'] or 'None'}")
    print(f"  Auth Source: {build_args['auth_source']}")

    return build_args


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Track service versions in MongoDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 version_tracker.py client v1.2.0
  python3 version_tracker.py --service vre_lite --version v2.1.3
  python3 version_tracker.py rest 1.0.0 --show-recent
        """
    )

    parser.add_argument(
        'service',
        help='Service name to track'
    )

    parser.add_argument(
        'version',
        help='Version to record'
    )

    parser.add_argument(
        '--show-recent',
        action='store_true',
        help='Show recent versions for the service after insertion'
    )

    parser.add_argument(
        '--collection',
        default='version',
        help='Collection name to use (default: version)'
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    print("🚀 MongoDB Version Tracker")
    print("=" * 50)

    try:
        # Parse command line arguments
        args = parse_arguments()

        # Get build arguments from environment
        build_args = get_build_args()

        # Initialize version tracker
        tracker = VersionTracker(
            db_server=build_args['db_server'],
            db_port=build_args['db_port'],
            db_name=build_args['db_name'],
            auth_user=build_args['auth_user'],
            auth_password=build_args['auth_password'],
            auth_source=build_args['auth_source']
        )

        # Connect to MongoDB
        if not tracker.connect():
            sys.exit(1)

        # Ensure database exists
        if not tracker.ensure_database():
            sys.exit(1)

        # Ensure collection exists
        if not tracker.ensure_collection(args.collection):
            sys.exit(1)

        # Insert version document
        if not tracker.insert_version_document(args.service, args.version):
            sys.exit(1)

        # Show recent versions if requested
        if args.show_recent:
            tracker.show_recent_versions(args.service)

        print("\n✅ Version tracking completed successfully!")

    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        if 'tracker' in locals():
            tracker.close()


if __name__ == "__main__":
    main()
