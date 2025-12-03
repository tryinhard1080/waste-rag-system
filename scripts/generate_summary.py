#!/usr/bin/env python3
"""
Daily Email Summary Generator

Generates actionable markdown summaries from daily email exports.
Extracts action items, questions, commitments, and deadlines.
"""

import json
import os
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict


class SummaryGenerator:
    """Generates daily email summaries with action items and insights."""

    def __init__(self, warehouse_path: str, config_path: str):
        self.warehouse_path = Path(warehouse_path)
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.today_emails = []
        self.threads = {}
        self.action_items = []
        self.questions = []
        self.commitments = []
        self.project_updates = defaultdict(list)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return {}

    def load_today_emails(self, date: str = None) -> None:
        """Load emails for a specific date (default: today)."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        daily_file = self.warehouse_path / 'daily' / f'{date}.json'

        if not daily_file.exists():
            print(f"Warning: No export found for {date}")
            return

        try:
            with open(daily_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.today_emails = data.get('emails', [])
            print(f"Loaded {len(self.today_emails)} emails from {date}")
        except Exception as e:
            print(f"Error loading emails: {e}")

    def load_threads(self) -> None:
        """Load thread context for additional insights."""
        threads_file = self.warehouse_path / 'threads' / 'threads_current.json'

        if not threads_file.exists():
            print("Warning: Thread aggregation not found. Run aggregate_threads.py first.")
            return

        try:
            with open(threads_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert threads list to dict keyed by thread_id
                for thread in data.get('threads', []):
                    self.threads[thread['thread_id']] = thread
            print(f"Loaded {len(self.threads)} threads")
        except Exception as e:
            print(f"Error loading threads: {e}")

    def _extract_action_items(self, email: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract action items from email content."""
        body = email.get('body_text', '')
        subject = email.get('subject', '')
        items = []

        # Action item patterns
        patterns = [
            r'can you\s+([^.?!]+)',
            r'could you\s+([^.?!]+)',
            r'please\s+([^.?!]+)',
            r'need\s+(?:you\s+)?to\s+([^.?!]+)',
            r'would you\s+([^.?!]+)',
            r'action required:?\s*([^.?!]+)',
            r'(?:please\s+)?(?:send|provide|share|forward)\s+([^.?!]+)',
            r'(?:need|needed)\s+by\s+([^.?!]+)',
            r'follow up\s+(?:on|with|about)\s+([^.?!]+)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, body, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                action_text = match.group(0).strip()
                # Limit to reasonable length
                if len(action_text) > 150:
                    action_text = action_text[:147] + '...'

                items.append({
                    'text': action_text,
                    'from': email.get('from', {}).get('email', ''),
                    'from_name': email.get('from', {}).get('name', ''),
                    'subject': subject,
                    'date': email.get('date', ''),
                    'priority': 'high' if email.get('importance') == 'high' else 'normal'
                })

        return items

    def _extract_questions(self, email: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract questions from email content."""
        body = email.get('body_text', '')
        subject = email.get('subject', '')
        questions = []

        # Split into sentences and find questions
        sentences = re.split(r'[.!]\s+', body)

        for sentence in sentences:
            if '?' in sentence:
                # Clean up
                question = sentence.strip()
                if len(question) > 200:
                    question = question[:197] + '...'

                # Avoid email signatures and footers
                if any(skip in question.lower() for skip in ['unsubscribe', 'privacy policy', 'opt out']):
                    continue

                questions.append({
                    'text': question,
                    'from': email.get('from', {}).get('email', ''),
                    'from_name': email.get('from', {}).get('name', ''),
                    'subject': subject,
                    'date': email.get('date', '')
                })

        return questions

    def _extract_commitments(self, email: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract commitments made in sent emails."""
        # Only check sent emails
        if email.get('type') != 'sent':
            return []

        body = email.get('body_text', '')
        subject = email.get('subject', '')
        commitments = []

        # Commitment patterns
        patterns = [
            r"I(?:'ll| will)\s+([^.?!]+)",
            r"I(?:'m| am)\s+going to\s+([^.?!]+)",
            r"I(?:'ve| have)\s+committed to\s+([^.?!]+)",
            r"will have\s+(?:this\s+)?(?:to you|ready)\s+by\s+([^.?!]+)",
            r"I can\s+([^.?!]+)\s+by\s+([^.?!]+)",
            r"(?:we|I)\s+(?:will|can)\s+provide\s+([^.?!]+)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, body, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                commitment_text = match.group(0).strip()
                if len(commitment_text) > 150:
                    commitment_text = commitment_text[:147] + '...'

                commitments.append({
                    'text': commitment_text,
                    'to': email.get('to', []),
                    'subject': subject,
                    'date': email.get('date', '')
                })

        return commitments

    def _detect_project(self, email: Dict[str, Any]) -> str:
        """Detect primary project/property from email."""
        if not self.config.get('projects'):
            return 'General'

        text = f"{email.get('subject', '')} {email.get('body_preview', '')}"
        text_lower = text.lower()

        # Check properties first
        for prop in self.config['projects'].get('known_properties', []):
            if prop.lower() in text_lower:
                return prop

        # Then vendors
        for vendor in self.config['projects'].get('known_vendors', []):
            if vendor.lower() in text_lower:
                return f"Vendor: {vendor}"

        # Then contacts
        sender_email = email.get('from', {}).get('email', '').lower()
        for contact_name, identifier in self.config['projects'].get('known_contacts', {}).items():
            if identifier.lower() in sender_email:
                return f"Contact: {contact_name}"

        return 'General'

    def process_emails(self) -> None:
        """Process all emails and extract insights."""
        for email in self.today_emails:
            # Extract action items
            self.action_items.extend(self._extract_action_items(email))

            # Extract questions (from received emails)
            if email.get('type') == 'received':
                self.questions.extend(self._extract_questions(email))

            # Extract commitments (from sent emails)
            self.commitments.extend(self._extract_commitments(email))

            # Categorize by project
            project = self._detect_project(email)
            self.project_updates[project].append(email)

        # Sort by priority
        self.action_items.sort(key=lambda x: (0 if x['priority'] == 'high' else 1, x['date']), reverse=True)

        print(f"\nExtracted insights:")
        print(f"  Action items: {len(self.action_items)}")
        print(f"  Questions: {len(self.questions)}")
        print(f"  Commitments: {len(self.commitments)}")
        print(f"  Projects: {len(self.project_updates)}")

    def _get_thread_status(self, email: Dict[str, Any]) -> Tuple[int, str]:
        """Get thread status and message count."""
        conv_id = email.get('conversation_id', '')

        if conv_id and conv_id in self.threads:
            thread = self.threads[conv_id]
            return thread['message_count'], thread['status']

        return 1, 'new'

    def generate_markdown(self, date: str = None) -> str:
        """Generate markdown summary."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        date_formatted = datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y')

        # Calculate stats
        received_count = sum(1 for e in self.today_emails if e.get('type') == 'received')
        sent_count = sum(1 for e in self.today_emails if e.get('type') == 'sent')

        # Get thread stats
        active_threads = set()
        new_threads = set()

        for email in self.today_emails:
            conv_id = email.get('conversation_id', '')
            if conv_id:
                msg_count, status = self._get_thread_status(email)
                if status == 'active':
                    active_threads.add(conv_id)
                elif msg_count == 1:
                    new_threads.add(conv_id)

        # Build markdown
        md = []
        md.append(f"# Daily Email Summary — {date_formatted}\n")
        md.append("## Quick Stats\n")
        md.append(f"- **Emails Received:** {received_count}")
        md.append(f"- **Emails Sent:** {sent_count}")
        md.append(f"- **Active Threads:** {len(active_threads)}")
        md.append(f"- **New Threads:** {len(new_threads)}\n")
        md.append("---\n")

        # Action items
        if self.action_items:
            md.append("## Action Items Identified\n")

            high_priority = [a for a in self.action_items if a['priority'] == 'high']
            normal_priority = [a for a in self.action_items if a['priority'] == 'normal']

            if high_priority:
                md.append("### High Priority\n")
                for item in high_priority[:10]:  # Limit to 10
                    from_name = item['from_name'] or item['from']
                    md.append(f"- [ ] {item['text']}")
                    md.append(f"  - From: {from_name}")
                    md.append(f"  - Subject: {item['subject']}\n")

            if normal_priority:
                md.append("### Follow-ups Needed\n")
                for item in normal_priority[:10]:  # Limit to 10
                    from_name = item['from_name'] or item['from']
                    md.append(f"- [ ] {item['text']}")
                    md.append(f"  - From: {from_name}\n")

            md.append("---\n")

        # Commitments
        if self.commitments:
            md.append("## Commitments Made Today\n")
            for commitment in self.commitments[:10]:
                md.append(f"- {commitment['text']}")
                if commitment['to']:
                    md.append(f"  - To: {', '.join(commitment['to'][:3])}\n")
            md.append("---\n")

        # Questions
        if self.questions:
            md.append("## Questions Pending Response\n")
            for question in self.questions[:10]:
                from_name = question['from_name'] or question['from']
                md.append(f"- **From:** {from_name}")
                md.append(f"  - \"{question['text']}\"\n")
            md.append("---\n")

        # Project updates
        if self.project_updates:
            md.append("## Project Updates\n")
            for project, emails in sorted(self.project_updates.items()):
                if project == 'General' and len(self.project_updates) > 1:
                    continue  # Skip General if there are specific projects

                md.append(f"### {project}\n")
                md.append(f"- {len(emails)} email(s) exchanged today")

                # Show key subjects
                subjects = list(set(e.get('subject', '') for e in emails if e.get('subject')))[:3]
                if subjects:
                    md.append(f"- Key topics: {', '.join(subjects)}")

                md.append("")

            md.append("---\n")

        # Raw email log
        md.append("## Email Log\n")
        md.append("<details>")
        md.append("<summary>Click to expand full email list</summary>\n")

        # Group by received/sent
        received = [e for e in self.today_emails if e.get('type') == 'received']
        sent = [e for e in self.today_emails if e.get('type') == 'sent']

        if received:
            md.append("### Received\n")
            for email in received:
                time = email.get('date', '').split('T')[1][:5] if 'T' in email.get('date', '') else ''
                from_name = email.get('from', {}).get('name', 'Unknown')
                subject = email.get('subject', '(no subject)')
                md.append(f"- **{time}** — From: {from_name} — {subject}")

        if sent:
            md.append("\n### Sent\n")
            for email in sent:
                time = email.get('date', '').split('T')[1][:5] if 'T' in email.get('date', '') else ''
                to_list = email.get('to', [])
                to_display = to_list[0] if to_list else 'Unknown'
                subject = email.get('subject', '(no subject)')
                md.append(f"- **{time}** — To: {to_display} — {subject}")

        md.append("\n</details>\n")

        # Footer
        md.append("---\n")
        md.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}*\n")

        return '\n'.join(md)

    def save_summary(self, markdown: str, date: str = None) -> None:
        """Save markdown summary to file."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        summary_dir = self.warehouse_path / 'summaries'
        summary_dir.mkdir(parents=True, exist_ok=True)

        summary_file = summary_dir / f'{date}.md'

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(markdown)

        print(f"\nSummary saved to: {summary_file}")


def main():
    """Main execution function."""
    # Determine paths
    script_dir = Path(__file__).parent
    warehouse_path = script_dir.parent / 'warehouse'
    config_path = script_dir.parent / 'config' / 'settings.json'

    # Support date argument
    date = None
    if len(sys.argv) > 1:
        date = sys.argv[1]
    else:
        date = datetime.now().strftime('%Y-%m-%d')

    print("Daily Email Summary Generator")
    print("="*60)
    print(f"Date: {date}")
    print(f"Warehouse path: {warehouse_path}")
    print("="*60 + "\n")

    # Create generator
    generator = SummaryGenerator(warehouse_path, config_path)

    # Load data
    print("Loading emails...")
    generator.load_today_emails(date)

    if not generator.today_emails:
        print(f"\nNo emails found for {date}.")
        print("Run Export-DailyEmails.ps1 first to export emails.")
        sys.exit(1)

    print("Loading thread context...")
    generator.load_threads()

    # Process emails
    print("\nProcessing emails...")
    generator.process_emails()

    # Generate summary
    print("\nGenerating markdown summary...")
    markdown = generator.generate_markdown(date)

    # Save summary
    generator.save_summary(markdown, date)

    print("\nSummary generation completed successfully!")


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
