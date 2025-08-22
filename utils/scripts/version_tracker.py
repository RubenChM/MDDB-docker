#!/usr/bin/env python3

import argparse
import os
import sys
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


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

            # Create unique index on service field to ensure only one version per service
            try:
                self.collection.create_index(
                    [("service", 1)],
                    unique=True,
                    name="unique_service"
                )
                print("📊 Unique index created on service field")
            except Exception:
                # Index might already exist, that's fine
                print("📊 Service index already exists or creation failed (continuing anyway)")

            # Create regular index for performance on timestamp
            try:
                self.collection.create_index([("timestamp", -1)])
                print("📊 Index created on timestamp field")
            except Exception:
                print("📊 Timestamp index already exists or creation failed")

            return True

        except Exception as e:
            print(f"❌ Error accessing/creating collection: {e}")
            return False

    def insert_version_document(self, service: str, version: str) -> bool:
        """Insert or update version document for a service (only one version per service)."""
        try:
            # Check if this service already exists with any version
            existing_doc = self.collection.find_one({"service": service})

            # Prepare document
            document = {
                "service": service,
                "version": version,
                "timestamp": datetime.utcnow(),
            }

            if existing_doc:
                old_version = existing_doc.get('version', 'unknown')
                if old_version == version:
                    print(f"⚠️  Service '{service}' already has version '{version}' (inserted on {existing_doc.get('timestamp', 'unknown')})")
                    print("📋 Skipping - same version already exists")
                    return True
                else:
                    print(f"🔄 Updating service '{service}' from version '{old_version}' to '{version}'")

                    # Update existing document
                    result = self.collection.update_one(
                        {"service": service},
                        {"$set": document}
                    )

                    if result.modified_count > 0:
                        print(f"✅ Version updated successfully for service '{service}'")
                    else:
                        print("⚠️  No changes made - document might be identical")
            else:
                print(f"📝 Creating new version document for service '{service}' version '{version}'")

                # Insert new document
                result = self.collection.insert_one(document)
                print(f"✅ Document inserted successfully with ID: {result.inserted_id}")

            # Show current version for this service
            current_doc = self.collection.find_one({"service": service})
            if current_doc:
                print(f"📊 Current version for '{service}': {current_doc.get('version', 'unknown')}")

            return True

        except Exception as e:
            print(f"❌ Error inserting/updating document: {e}")
            return False

    def get_service_version(self, service: str) -> dict:
        """Get the current version for a service."""
        try:
            version_doc = self.collection.find_one({"service": service})
            return version_doc if version_doc else {}

        except Exception as e:
            print(f"❌ Error retrieving version: {e}")
            return {}

    def get_all_services(self) -> list:
        """Get all services and their current versions."""
        try:
            services = list(self.collection.find({}).sort("service", 1))
            return services

        except Exception as e:
            print(f"❌ Error retrieving services: {e}")
            return []

    def show_service_info(self, service: str = None):
        """Show current version info for a service or all services."""
        if service:
            version_doc = self.get_service_version(service)
            if version_doc:
                timestamp = version_doc.get('timestamp', 'Unknown')
                version = version_doc.get('version', 'Unknown')
                print(f"\n📈 Current version for '{service}':")
                print("-" * 50)
                print(f"  Version: {version}")
                print(f"  Updated: {timestamp}")
            else:
                print(f"📋 No version found for service '{service}'")
        else:
            services = self.get_all_services()
            if services:
                print(f"\n📈 All tracked services ({len(services)}):")
                print("-" * 60)
                for svc in services:
                    service_name = svc.get('service', 'Unknown')
                    version = svc.get('version', 'Unknown')
                    timestamp = svc.get('timestamp', 'Unknown')
                    print(f"  {service_name:15} | {version:10} | {timestamp}")
            else:
                print("📋 No services found in version tracking")

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
  python3 version_tracker.py rest 1.0.0 --show-info
  python3 version_tracker.py client 2.0.0 --show-all
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
        '--show-info',
        action='store_true',
        help='Show current version info for the service after update'
    )

    parser.add_argument(
        '--show-all',
        action='store_true',
        help='Show all tracked services and their versions'
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

        # Insert/update version document
        if not tracker.insert_version_document(args.service, args.version):
            sys.exit(1)

        # Show service info if requested
        if args.show_info:
            tracker.show_service_info(args.service)

        # Show all services if requested
        if args.show_all:
            tracker.show_service_info()

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
