#!/usr/bin/env python3
"""
Email Thread Aggregator

Reads daily email exports and groups them into conversation threads.
Identifies projects, tracks participants, and generates thread metadata.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Set
import re


class ThreadAggregator:
    """Aggregates emails into conversation threads and detects projects."""

    def __init__(self, warehouse_path: str, config_path: str):
        self.warehouse_path = Path(warehouse_path)
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.emails = []
        self.threads = {}
        self.projects = defaultdict(list)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return {}

    def load_daily_exports(self, days_back: int = 90) -> None:
        """Load all daily export files from the warehouse."""
        daily_path = self.warehouse_path / 'daily'

        if not daily_path.exists():
            print(f"Error: Daily exports path not found: {daily_path}")
            return

        # Get all JSON files in the daily folder
        json_files = sorted(daily_path.glob('*.json'), reverse=True)

        # Load files within the retention period
        cutoff_date = datetime.now() - timedelta(days=days_back)

        for json_file in json_files:
            try:
                # Parse date from filename (YYYY-MM-DD.json)
                file_date_str = json_file.stem
                file_date = datetime.strptime(file_date_str, '%Y-%m-%d')

                if file_date < cutoff_date:
                    continue

                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.emails.extend(data.get('emails', []))

                print(f"Loaded {len(data.get('emails', []))} emails from {json_file.name}")

            except Exception as e:
                print(f"Warning: Could not load {json_file}: {e}")

        print(f"\nTotal emails loaded: {len(self.emails)}")

    def _normalize_topic(self, topic: str) -> str:
        """Normalize conversation topic for grouping."""
        if not topic:
            return ""

        # Remove RE:, FW:, FWD: prefixes
        normalized = re.sub(r'^(RE:|Re:|FW:|Fw:|FWD:)\s*', '', topic, flags=re.IGNORECASE)
        normalized = normalized.strip()

        return normalized

    def _detect_project(self, email: Dict[str, Any]) -> List[str]:
        """Detect projects/properties/vendors mentioned in email."""
        detected = []

        if not self.config.get('projects'):
            return detected

        # Combine subject and preview for detection
        text = f"{email.get('subject', '')} {email.get('body_preview', '')}"
        text_lower = text.lower()

        # Check for known properties
        for prop in self.config['projects'].get('known_properties', []):
            if prop.lower() in text_lower:
                detected.append(f"Property: {prop}")

        # Check for known vendors
        for vendor in self.config['projects'].get('known_vendors', []):
            if vendor.lower() in text_lower:
                detected.append(f"Vendor: {vendor}")

        # Check for known contacts
        sender_email = email.get('from', {}).get('email', '').lower()
        sender_name = email.get('from', {}).get('name', '').lower()

        for contact_name, identifier in self.config['projects'].get('known_contacts', {}).items():
            identifier_lower = identifier.lower()
            if identifier_lower in sender_email or identifier_lower in text_lower:
                detected.append(f"Contact: {contact_name}")

        return detected

    def _get_thread_status(self, thread: Dict[str, Any]) -> str:
        """Determine thread status based on activity."""
        last_date = datetime.strptime(thread['last_message_date'], '%Y-%m-%d')
        days_since = (datetime.now() - last_date).days

        if days_since <= 2:
            return "active"
        elif days_since <= 7:
            return "recent"
        elif days_since <= 14:
            return "aging"
        else:
            return "stale"

    def aggregate_threads(self) -> None:
        """Group emails into conversation threads."""
        # Group by conversation_id and topic
        conversation_groups = defaultdict(list)

        for email in self.emails:
            conv_id = email.get('conversation_id', '')
            conv_topic = self._normalize_topic(email.get('conversation_topic', ''))

            # Use conversation_id as primary key, fall back to topic
            key = conv_id if conv_id else conv_topic

            if key:
                conversation_groups[key].append(email)
            else:
                # No grouping info, create individual thread
                individual_key = f"single_{email.get('id', '')}"
                conversation_groups[individual_key].append(email)

        # Build thread objects
        for thread_id, emails_in_thread in conversation_groups.items():
            # Sort by date
            emails_in_thread.sort(key=lambda x: x.get('date', ''))

            # Extract participants
            participants = set()
            for email in emails_in_thread:
                sender = email.get('from', {}).get('email', '')
                if sender:
                    participants.add(sender)

                for recipient in email.get('to', []):
                    if recipient:
                        participants.add(recipient)

            # Get dates
            dates = [email.get('date', '') for email in emails_in_thread if email.get('date')]
            first_date = min(dates)[:10] if dates else ''
            last_date = max(dates)[:10] if dates else ''

            # Detect projects
            projects_detected = set()
            for email in emails_in_thread:
                projects_detected.update(self._detect_project(email))

            # Build thread object
            thread = {
                'thread_id': thread_id,
                'topic': self._normalize_topic(emails_in_thread[0].get('conversation_topic', '')),
                'participants': sorted(list(participants)),
                'message_count': len(emails_in_thread),
                'first_message_date': first_date,
                'last_message_date': last_date,
                'status': '',  # Will be set below
                'projects_detected': sorted(list(projects_detected)),
                'messages': [
                    {
                        'date': email.get('date', ''),
                        'from': email.get('from', {}).get('email', ''),
                        'from_name': email.get('from', {}).get('name', ''),
                        'subject': email.get('subject', ''),
                        'preview': email.get('body_preview', '')[:200],
                        'type': email.get('type', ''),
                        'has_attachments': email.get('has_attachments', False)
                    }
                    for email in emails_in_thread
                ]
            }

            # Set status
            thread['status'] = self._get_thread_status(thread)

            self.threads[thread_id] = thread

            # Map to projects
            for project in projects_detected:
                self.projects[project].append(thread_id)

        print(f"\nThreads aggregated: {len(self.threads)}")
        print(f"Projects detected: {len(self.projects)}")

    def generate_statistics(self) -> Dict[str, Any]:
        """Generate statistics about threads and projects."""
        stats = {
            'total_threads': len(self.threads),
            'total_emails': len(self.emails),
            'threads_by_status': defaultdict(int),
            'projects': {}
        }

        for thread in self.threads.values():
            stats['threads_by_status'][thread['status']] += 1

        for project, thread_ids in self.projects.items():
            stats['projects'][project] = {
                'thread_count': len(thread_ids),
                'active_threads': sum(1 for tid in thread_ids
                                     if self.threads[tid]['status'] == 'active')
            }

        return dict(stats)

    def save_results(self, output_path: str) -> None:
        """Save aggregated threads to JSON file."""
        output = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.generate_statistics(),
            'threads': list(self.threads.values()),
            'projects': dict(self.projects)
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\nThread aggregation saved to: {output_file}")

    def print_summary(self) -> None:
        """Print summary of aggregation results."""
        stats = self.generate_statistics()

        print("\n" + "="*60)
        print("THREAD AGGREGATION SUMMARY")
        print("="*60)
        print(f"\nTotal Emails: {stats['total_emails']}")
        print(f"Total Threads: {stats['total_threads']}")
        print("\nThreads by Status:")
        for status, count in stats['threads_by_status'].items():
            print(f"  {status.capitalize()}: {count}")

        if stats['projects']:
            print("\nProjects Detected:")
            for project, info in stats['projects'].items():
                print(f"  {project}: {info['thread_count']} threads "
                      f"({info['active_threads']} active)")

        print("="*60 + "\n")


def main():
    """Main execution function."""
    # Determine paths
    script_dir = Path(__file__).parent
    warehouse_path = script_dir.parent / 'warehouse'
    config_path = script_dir.parent / 'config' / 'settings.json'
    output_path = warehouse_path / 'threads' / 'threads_current.json'

    print("Email Thread Aggregator")
    print("="*60)
    print(f"Warehouse path: {warehouse_path}")
    print(f"Config path: {config_path}")
    print(f"Output path: {output_path}")
    print("="*60 + "\n")

    # Create aggregator
    aggregator = ThreadAggregator(warehouse_path, config_path)

    # Load configuration to get retention days
    days_to_retain = 90
    if aggregator.config.get('outlook', {}).get('days_to_retain'):
        days_to_retain = aggregator.config['outlook']['days_to_retain']

    # Load daily exports
    print(f"Loading emails from last {days_to_retain} days...")
    aggregator.load_daily_exports(days_back=days_to_retain)

    if not aggregator.emails:
        print("\nNo emails found. Run Export-DailyEmails.ps1 first to export emails.")
        sys.exit(1)

    # Aggregate into threads
    print("\nAggregating emails into threads...")
    aggregator.aggregate_threads()

    # Save results
    aggregator.save_results(output_path)

    # Print summary
    aggregator.print_summary()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
