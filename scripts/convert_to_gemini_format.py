"""
Convert exported JSON emails to Markdown format for Gemini File Search.

This script processes daily JSON exports and creates markdown batches optimized
for Gemini's RAG system. Batches are sized under 100MB and organized by month
or topic for efficient semantic search.

Usage:
    python convert_to_gemini_format.py
    python convert_to_gemini_format.py --start-date 2025-01-01 --end-date 2025-03-31
    python convert_to_gemini_format.py --batch-by topic --max-size 50
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import re

# Configuration
DAILY_JSON_DIR = Path(__file__).parent.parent / "warehouse" / "daily"
GEMINI_OUTPUT_DIR = Path(__file__).parent.parent / "warehouse" / "gemini"
MAX_BATCH_SIZE_MB = 95  # Stay under 100MB limit with margin
BATCH_BY = "month"  # Options: "month", "topic", "property", "all"

# Create output directory
GEMINI_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def format_email_as_markdown(email: dict, file_date: str) -> str:
    """
    Convert a single email to markdown format with metadata.

    Args:
        email: Email dict from JSON export
        file_date: Date from the JSON filename

    Returns:
        Markdown string representation
    """
    lines = []

    # Header with metadata
    lines.append("---")
    lines.append(f"# Email ID: {email.get('id', 'unknown')}")
    lines.append(f"**Date**: {email.get('date', file_date)}")
    lines.append(f"**Type**: {email.get('type', 'unknown')}")
    lines.append(f"**From**: {email.get('from', {}).get('name', '')} <{email.get('from', {}).get('email', '')}>")

    # Recipients
    to_recipients = email.get('to', [])
    if to_recipients:
        lines.append(f"**To**: {', '.join(to_recipients)}")

    cc_recipients = email.get('cc', [])
    if cc_recipients:
        lines.append(f"**CC**: {', '.join(cc_recipients)}")

    # Subject and conversation info
    subject = email.get('subject', '(no subject)')
    lines.append(f"**Subject**: {subject}")

    conversation_topic = email.get('conversation_topic', '')
    if conversation_topic and conversation_topic != subject:
        lines.append(f"**Thread**: {conversation_topic}")

    # Metadata
    importance = email.get('importance', 'normal')
    if importance != 'normal':
        lines.append(f"**Importance**: {importance.upper()}")

    categories = email.get('categories', [])
    if categories:
        lines.append(f"**Categories**: {', '.join(categories)}")

    if email.get('is_reply'):
        lines.append("**Reply**: Yes")

    if email.get('is_forwarded'):
        lines.append("**Forwarded**: Yes")

    if email.get('has_attachments'):
        attachments = email.get('attachments', [])
        attachment_names = [att.get('filename', '') for att in attachments]
        lines.append(f"**Attachments**: {', '.join(attachment_names)}")

    lines.append("---")
    lines.append("")

    # Email body
    body_text = email.get('body_text', '')
    if body_text:
        lines.append("## Email Content")
        lines.append("")
        # Clean up body text - remove excessive whitespace
        cleaned_body = re.sub(r'\n{3,}', '\n\n', body_text.strip())
        lines.append(cleaned_body)
    else:
        lines.append("*(No content)*")

    lines.append("")
    lines.append("=" * 80)
    lines.append("")

    return '\n'.join(lines)


def detect_email_topics(email: dict) -> list:
    """
    Detect topics/categories for an email (contamination, billing, vendor, etc.)

    Args:
        email: Email dict from JSON export

    Returns:
        List of topic strings
    """
    topics = []

    # Combine subject and body preview for analysis
    text = f"{email.get('subject', '')} {email.get('body_preview', '')}".lower()

    # Topic keywords
    topic_keywords = {
        'contamination': ['contamination', 'contaminated', 'trash', 'recycle', 'sorting'],
        'billing': ['invoice', 'bill', 'payment', 'charge', 'cost', 'pricing', 'rate'],
        'vendor': ['vendor', 'service provider', 'contract', 'proposal', 'quote'],
        'maintenance': ['repair', 'broken', 'damaged', 'fix', 'maintenance', 'service call'],
        'compliance': ['compliance', 'regulation', 'permit', 'violation', 'inspection'],
        'urgent': ['urgent', 'asap', 'emergency', 'critical', 'immediate'],
    }

    for topic, keywords in topic_keywords.items():
        if any(keyword in text for keyword in keywords):
            topics.append(topic)

    # Check email importance
    if email.get('importance') == 'high':
        topics.append('urgent')

    # Default topic
    if not topics:
        topics.append('general')

    return topics


def get_batch_key(email: dict, file_date: str, batch_by: str) -> str:
    """
    Determine which batch this email belongs to.

    Args:
        email: Email dict from JSON export
        file_date: Date from the JSON filename
        batch_by: Batching strategy ("month", "topic", "property", "all")

    Returns:
        Batch key string
    """
    if batch_by == "month":
        # Extract year-month from date
        date_str = email.get('date', file_date)
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.strftime("%Y-%m")
        except:
            return file_date[:7]  # YYYY-MM

    elif batch_by == "topic":
        # Use first detected topic
        topics = detect_email_topics(email)
        return topics[0] if topics else "general"

    elif batch_by == "property":
        # Extract property name from subject/body
        # This would need your config with known properties
        return "all-properties"

    else:  # "all"
        return "all-emails"


def process_json_files(start_date: str = None, end_date: str = None, batch_by: str = "month"):
    """
    Process all JSON files and create Gemini markdown batches.

    Args:
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        batch_by: Batching strategy
    """
    print("=" * 80)
    print("Converting Email JSON to Gemini Markdown Format")
    print("=" * 80)
    print(f"Source: {DAILY_JSON_DIR}")
    print(f"Output: {GEMINI_OUTPUT_DIR}")
    print(f"Batch strategy: {batch_by}")
    print(f"Max batch size: {MAX_BATCH_SIZE_MB}MB")
    print()

    # Find all JSON files
    json_files = sorted(DAILY_JSON_DIR.glob("*.json"))

    if not json_files:
        print("ERROR: No JSON files found in daily export directory")
        return

    # Filter by date range if specified
    if start_date or end_date:
        filtered_files = []
        for json_file in json_files:
            file_date = json_file.stem  # YYYY-MM-DD
            if start_date and file_date < start_date:
                continue
            if end_date and file_date > end_date:
                continue
            filtered_files.append(json_file)
        json_files = filtered_files

    print(f"Processing {len(json_files)} JSON files...")
    print()

    # Group emails by batch key
    batches = defaultdict(list)
    batch_sizes = defaultdict(int)
    batch_counts = defaultdict(int)

    total_emails = 0
    skipped_emails = 0

    for json_file in json_files:
        file_date = json_file.stem
        print(f"Processing {json_file.name}...", end=" ")

        try:
            # Use utf-8-sig to handle BOM from PowerShell
            with open(json_file, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)

            emails = data.get('emails', [])
            print(f"{len(emails)} emails")

            for email in emails:
                total_emails += 1

                # Convert to markdown
                md_content = format_email_as_markdown(email, file_date)
                md_size = len(md_content.encode('utf-8'))

                # Determine batch
                batch_key = get_batch_key(email, file_date, batch_by)

                # Check if adding this email would exceed batch size
                if batch_sizes[batch_key] + md_size > (MAX_BATCH_SIZE_MB * 1024 * 1024):
                    # Start a new batch with a sequence number
                    batch_num = batch_counts[batch_key] + 1
                    batch_counts[batch_key] = batch_num
                    batch_key_with_num = f"{batch_key}_{batch_num:03d}"

                    batches[batch_key_with_num].append(md_content)
                    batch_sizes[batch_key_with_num] = md_size
                else:
                    # Add to existing batch
                    if batch_key not in batch_counts:
                        batch_counts[batch_key] = 1
                        batch_key_with_num = f"{batch_key}_001"
                    else:
                        batch_num = batch_counts[batch_key]
                        batch_key_with_num = f"{batch_key}_{batch_num:03d}"

                    batches[batch_key_with_num].append(md_content)
                    batch_sizes[batch_key_with_num] += md_size

        except Exception as e:
            print(f"  ERROR: {e}")
            skipped_emails += 1

    print()
    print("=" * 80)
    print(f"Total emails processed: {total_emails}")
    print(f"Total batches created: {len(batches)}")
    print()

    # Write batches to files
    for batch_key, emails_md in batches.items():
        output_file = GEMINI_OUTPUT_DIR / f"batch_{batch_key}.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            # Write batch header
            f.write(f"# Email Batch: {batch_key}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Total Emails: {len(emails_md)}\n")
            f.write("\n" + "=" * 80 + "\n\n")

            # Write all emails
            for email_md in emails_md:
                f.write(email_md)

        file_size_mb = batch_sizes[batch_key] / (1024 * 1024)
        print(f"Created: {output_file.name} ({len(emails_md)} emails, {file_size_mb:.2f}MB)")

    print()
    print("=" * 80)
    print("Conversion complete!")
    print(f"Markdown files saved to: {GEMINI_OUTPUT_DIR}")
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert email JSON to Gemini markdown format")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--batch-by", default="month",
                       choices=["month", "topic", "property", "all"],
                       help="Batching strategy")
    parser.add_argument("--max-size", type=int, default=95,
                       help="Maximum batch size in MB (default: 95)")

    args = parser.parse_args()

    # Update global config
    MAX_BATCH_SIZE_MB = args.max_size

    process_json_files(
        start_date=args.start_date,
        end_date=args.end_date,
        batch_by=args.batch_by
    )
