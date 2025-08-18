#!/usr/bin/env python3

import subprocess
# import json
# import re
import os
import sys
# from typing import Dict, List, Tuple, Optional
from typing import List, Tuple, Optional


class VersionChecker:
    def __init__(self):
        # Configuration: service_name -> (github_org, github_repo, docker_image)
        self.services = {
            "client": ("mmb-irb", "MDposit-client-build", "client_image"),
            "rest": ("mmb-irb", "MDDB-REST-API", "rest_image"),
            "vre_lite": ("mmb-irb", "MDDB-VRE", "vre_lite_image"),
            "loader": ("mmb-irb", "MDDB-loader", "loader_image"),
            "workflow": ("mmb-irb", "MDDB-workflow", "workflow_image"),
            # Add more services as needed
        }

        self.updatable_services = []
        self.service_versions = {}
        self.repo_versions = {}

    def run_command(self, command: List[str], shell: bool = False, stream_output: bool = False) -> Tuple[bool, str]:
        """Run a command and return success status and output."""
        try:
            if shell:
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
            else:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)

            output_lines = []

            if stream_output:
                # Real-time streaming with limited rolling display
                # Store cursor position and prepare for rolling display
                rolling_buffer = []
                max_display_lines = 15  # Configurable number of lines to show

                print(f"📺 Streaming output (showing last {max_display_lines} lines):")
                print("-" * 60)

                # Save current cursor position
                start_line = self.get_cursor_position()

                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        line = output.strip()
                        output_lines.append(line)
                        rolling_buffer.append(line)

                        # Keep only the last N lines in rolling buffer
                        if len(rolling_buffer) > max_display_lines:
                            rolling_buffer.pop(0)

                        # Clear previous display and show current buffer
                        self.update_rolling_display(rolling_buffer, max_display_lines)

                # Final cleanup - show completion message
                print("\n" + "=" * 60)
                print("✅ Command completed!")

            else:
                # Silent mode - just collect output
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        output_lines.append(output.strip())

            return_code = process.poll()
            full_output = '\n'.join(output_lines)

            if return_code == 0:
                return True, full_output
            else:
                return False, full_output

        except Exception as e:
            print(f"Command execution error: {e}")
            return False, str(e)

    def get_cursor_position(self):
        """Get current cursor position (simplified version)."""
        # This is a simplified approach - in practice you might want to use more sophisticated terminal control
        return 0

    def update_rolling_display(self, lines, max_lines):
        """Update the rolling display of command output."""
        import os

        # Clear the display area (move cursor up and clear lines)
        # This is a simple approach - you might want to use curses for more control
        for _ in range(min(len(lines), max_lines) + 1):
            print("\033[1A\033[2K", end="")  # Move up one line and clear it

        # Print current buffer
        for i, line in enumerate(lines[-max_lines:]):
            # Truncate long lines to fit terminal width
            terminal_width = os.get_terminal_size().columns - 5
            if len(line) > terminal_width:
                line = line[:terminal_width-3] + "..."
            print(f"  {line}")

        # Add padding if buffer is smaller than max_lines
        for _ in range(max_lines - len(lines)):
            print()

    # def run_command(self, command: List[str], shell: bool = False) -> Tuple[bool, str]:
    #     """Run a command and return success status and output."""
    #     try:
    #         if shell:
    #             result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
    #         else:
    #             result = subprocess.run(command, capture_output=True, text=True, check=True)
    #         return True, result.stdout.strip()
    #     except subprocess.CalledProcessError as e:
    #         return False, e.stderr.strip() if e.stderr else str(e)
    #     except Exception as e:
    #         return False, str(e)

    def get_repo_version(self, org: str, repo: str) -> Optional[str]:
        """Get the latest version from GitHub repo tags."""
        print(f"  📡 Fetching latest version for {org}/{repo}...")

        # Use the exact command from the prompt
        command = f'curl -s "https://api.github.com/repos/{org}/{repo}/tags" | grep -m 1 \'"name":\' | sed -E \'s/.*"name": "([^"]+)".*/\\1/\''

        success, output = self.run_command(command, shell=True, stream_output=False)

        if not success or not output:
            print(f"    ⚠️  Could not fetch version for {org}/{repo}")
            return "unknown"

        # Remove 'v' prefix if present (v1.1 -> 1.1)
        version = output.strip()
        if version.startswith('v'):
            version = version[1:]

        print(f"    ✅ Latest version: {version}")
        return version

    def get_service_version(self, service_name: str, image_name: str) -> Optional[str]:
        """Get version from Docker service's version.txt file."""
        print(f"  🐳 Checking Docker service version for {service_name}...")

        # Use the exact command from the prompt
        command = f'docker run --entrypoint "" --rm {image_name} sh -c "cat version.txt"'

        success, output = self.run_command(command, shell=True, stream_output=False)

        if not success:
            print(f"    ⚠️  Could not get version for {service_name}: version.txt not found or service not built")
            return "unknown"

        version = output.strip()
        print(f"    ✅ Current version: {version}")
        return version

    def compare_versions(self, repo_version: str, service_version: str) -> bool:
        """Compare versions and return True if repo version is newer."""
        try:
            # Simple version comparison assuming format like "1.2.3"
            repo_parts = [int(x) for x in repo_version.split('.')]
            service_parts = [int(x) for x in service_version.split('.')]

            # Pad with zeros if different lengths
            max_len = max(len(repo_parts), len(service_parts))
            repo_parts.extend([0] * (max_len - len(repo_parts)))
            service_parts.extend([0] * (max_len - len(service_parts)))

            return repo_parts > service_parts
        except (ValueError, AttributeError):
            # If version comparison fails, assume update is available
            return True

    def check_all_versions(self):
        """Check versions for all configured services."""
        print("🔍 Checking versions for all services...\n")

        for service_name, (org, repo, image) in self.services.items():
            print(f"📋 Checking {service_name}:")

            # Get repo version
            repo_version = self.get_repo_version(org, repo)
            self.repo_versions[service_name] = repo_version

            # Get service version
            service_version = self.get_service_version(service_name, image)
            self.service_versions[service_name] = service_version

            # Compare versions
            if repo_version and service_version:
                if self.compare_versions(repo_version, service_version):
                    print(f"    🆙 UPDATE AVAILABLE: {service_version} -> {repo_version}")
                    self.updatable_services.append(service_name)
                else:
                    print(f"    ✅ UP TO DATE: {service_version}")
            elif repo_version and not service_version:
                print(f"    🆕 NEW SERVICE: can install {repo_version}")
                self.updatable_services.append(service_name)
            elif not repo_version and service_version:
                print("    ⚠️  Cannot check updates (repo version unavailable)")
            else:
                print("    ❓ Cannot determine versions")

            print()

    def display_summary(self):
        """Display a summary of version status."""
        print("=" * 60)
        print("📊 VERSION SUMMARY")
        print("=" * 60)

        print(f"{'Service':<15} {'Current':<12} {'Latest':<12} {'Status':<15}")
        print("-" * 60)

        for service_name in self.services.keys():
            current = self.service_versions.get(service_name, "Unknown")
            latest = self.repo_versions.get(service_name, "Unknown")

            if service_name in self.updatable_services:
                status = "🆙 Updatable"
            elif current != "Unknown" and latest != "Unknown":
                status = "✅ Up to date"
            else:
                status = "❓ Unknown"

            print(f"{service_name:<15} {current:<12} {latest:<12} {status:<15}")

        print("\n" + "=" * 60)

        if self.updatable_services:
            print(f"🎯 {len(self.updatable_services)} service(s) can be updated:")
            for service in self.updatable_services:
                current = self.service_versions.get(service, "Unknown")
                latest = self.repo_versions.get(service, "Unknown")
                print(f"   • {service}: {current} -> {latest}")
        else:
            print("✅ All services are up to date!")

    def update_service(self, service_name: str, stack_name: str) -> bool:
        """Update a single service using rebuild.py script."""
        print(f"\n🔄 Updating {service_name}...")

        # Check if rebuild.py exists
        rebuild_script = os.path.join(os.path.dirname(__file__), "rebuild.py")
        if not os.path.exists(rebuild_script):
            print(f"❌ rebuild.py not found at {rebuild_script}")
            return False

        # Get the target version
        target_version = self.repo_versions.get(service_name)
        if not target_version:
            print(f"❌ No target version found for {service_name}")
            return False

        # Run rebuild.py for the service
        command = ["python3", rebuild_script, '-s', service_name, '-t', stack_name]

        print(f"   Running: {' '.join(command)}")
        success, output = self.run_command(command, shell=False, stream_output=False)

        if success:
            print(f"   ✅ Successfully updated {service_name}")
            # Update our local version tracking
            self.service_versions[service_name] = target_version
            if service_name in self.updatable_services:
                self.updatable_services.remove(service_name)
            return True
        else:
            print(f"   ❌ Failed to update {service_name}: {output}")
            return False

    def update_all_services(self, stack_name: str) -> int:
        """Update all updatable services."""
        if not self.updatable_services:
            print("✅ No services need updating!")
            return 0

        print(f"\n🚀 Updating all {len(self.updatable_services)} services...")

        successful_updates = 0
        for service in self.updatable_services.copy():
            if self.update_service(service, stack_name):
                successful_updates += 1
            print()  # Add spacing between updates

        print(f"📊 Update Summary: {successful_updates}/{len(self.updatable_services)} services updated successfully")
        return successful_updates

    def interactive_menu(self):
        """Interactive menu for updating services."""
        while True:
            print("\n" + "=" * 60)
            print("🛠️  INTERACTIVE UPDATE MENU")
            print("=" * 60)

            if not self.updatable_services:
                print("✅ No services need updating!")
                print("\n1. Re-check versions")
                print("2. Exit")
                choice = input("\nEnter your choice (1-2): ").strip()

                if choice == "1":
                    self.__init__()  # Reset state
                    self.check_all_versions()
                    self.display_summary()
                elif choice == "2":
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice!")
                continue

            print("Available actions:")
            print("1. Update all services")
            print("2. Update specific service")
            print("3. Show version summary")
            print("4. Re-check versions")
            print("5. Exit")

            choice = input("\nEnter your choice (1-5): ").strip()

            if choice == "1":
                confirm = input(f"\n⚠️  Update all {len(self.updatable_services)} services? (y/N): ").strip().lower()
                if confirm in ['y', 'yes']:
                    stack_name = input("\n🧱 Enter stack name (default: 'my_stack'): ").strip() or "my_stack"
                    self.update_all_services(stack_name)
                else:
                    print("❌ Update cancelled")

            elif choice == "2":
                print("\nUpdatable services:")
                for i, service in enumerate(self.updatable_services, 1):
                    current = self.service_versions.get(service, "Unknown")
                    latest = self.repo_versions.get(service, "Unknown")
                    print(f"{i}. {service} ({current} -> {latest})")

                try:
                    service_choice = int(input(f"\nSelect service to update (1-{len(self.updatable_services)}): "))
                    if 1 <= service_choice <= len(self.updatable_services):
                        service_name = self.updatable_services[service_choice - 1]
                        confirm = input(f"\n⚠️  Update {service_name}? (y/N): ").strip().lower()
                        if confirm in ['y', 'yes']:
                            stack_name = input("\n🧱 Enter stack name (default: 'my_stack'): ").strip() or "my_stack"
                            self.update_service(service_name, stack_name)
                        else:
                            print("❌ Update cancelled")
                    else:
                        print("❌ Invalid selection!")
                except (ValueError, IndexError):
                    print("❌ Invalid input!")

            elif choice == "3":
                self.display_summary()

            elif choice == "4":
                print("🔄 Re-checking versions...")
                self.__init__()  # Reset state
                self.check_all_versions()
                self.display_summary()

            elif choice == "5":
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice!")


def main():
    """Main entry point."""
    print("🚀 Docker Service Version Checker & Updater")
    print("=" * 60)

    checker = VersionChecker()

    try:
        # Initial version check
        checker.check_all_versions()
        checker.display_summary()

        # Start interactive menu
        checker.interactive_menu()

    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
