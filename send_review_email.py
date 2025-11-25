#!/usr/bin/env python3
"""
Email Review Notification
=========================
Sends an email with the enriched data summary for review and approval.

The email includes:
- Period and date information
- Total records and statistics
- Sample data preview
- Approval instructions
"""

import json
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# === CONFIG ===
ENRICHED_JSON = "/Users/lvc/AI Scripts/2025_10 Consar Siefore Update Agent/consar_latest_month_enriched.json"
APPROVAL_FILE = "/Users/lvc/AI Scripts/2025_10 Consar Siefore Update Agent/approval_pending.json"

# Email configuration (from environment variables)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")


def load_enriched_data():
    """Load and analyze the enriched data."""
    with open(ENRICHED_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        raise ValueError("No data found in enriched JSON")

    # Get metadata
    period_year = data[0]["PeriodYear"]
    period_month = data[0]["PeriodMonth"]
    fx_rate = data[0]["FX_EOM"]

    # Calculate statistics
    total_records = len(data)
    total_mxn = sum(r.get("valueMXN", 0) for r in data)
    total_usd = sum(r.get("valueUSD", 0) for r in data)

    # Get unique values
    afores = sorted(set(r["Afore"] for r in data))
    siefores = sorted(set(r["Siefore"] for r in data))
    concepts = sorted(set(r["Concept"] for r in data))

    # Non-zero records
    nonzero_records = [r for r in data if r.get("valueMXN", 0) > 0]

    return {
        "period_year": period_year,
        "period_month": period_month,
        "fx_rate": fx_rate,
        "total_records": total_records,
        "total_mxn": total_mxn,
        "total_usd": total_usd,
        "afores": afores,
        "siefores": siefores,
        "concepts": concepts,
        "nonzero_count": len(nonzero_records),
        "sample_records": data[:10]
    }


def create_email_body(stats):
    """Create HTML email body with data summary."""

    month_names = {
        "01": "January", "02": "February", "03": "March", "04": "April",
        "05": "May", "06": "June", "07": "July", "08": "August",
        "09": "September", "10": "October", "11": "November", "12": "December"
    }

    month_name = month_names.get(stats["period_month"], stats["period_month"])

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; }}
            .section {{ margin: 20px 0; }}
            .stats {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            .approval {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }}
            .footer {{ color: #666; font-size: 12px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏦 CONSAR Data Review Request</h1>
            <p>New Siefore data ready for your approval</p>
        </div>

        <div class="section">
            <h2>📊 Data Period</h2>
            <div class="stats">
                <p><strong>Period:</strong> {month_name} {stats['period_year']}</p>
                <p><strong>FX Rate (EOM):</strong> {stats['fx_rate']:.4f} MXN/USD</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>

        <div class="section">
            <h2>📈 Statistics</h2>
            <div class="stats">
                <p><strong>Total Records:</strong> {stats['total_records']:,}</p>
                <p><strong>Non-zero Records:</strong> {stats['nonzero_count']:,}</p>
                <p><strong>Total MXN:</strong> ${stats['total_mxn']:,.0f}</p>
                <p><strong>Total USD:</strong> ${stats['total_usd']:,.0f}</p>
            </div>
        </div>

        <div class="section">
            <h2>🏢 Coverage</h2>
            <div class="stats">
                <p><strong>Afores ({len(stats['afores'])}):</strong> {', '.join(stats['afores'])}</p>
                <p><strong>Siefores ({len(stats['siefores'])}):</strong> {', '.join(stats['siefores'])}</p>
                <p><strong>Concepts ({len(stats['concepts'])}):</strong></p>
                <ul>
                    {''.join(f'<li>{c}</li>' for c in stats['concepts'])}
                </ul>
            </div>
        </div>

        <div class="section">
            <h2>📋 Sample Data (First 10 Records)</h2>
            <table>
                <tr>
                    <th>Afore</th>
                    <th>Siefore</th>
                    <th>Concept</th>
                    <th>MXN</th>
                    <th>USD</th>
                </tr>
    """

    for record in stats["sample_records"]:
        html += f"""
                <tr>
                    <td>{record['Afore']}</td>
                    <td>{record['Siefore']}</td>
                    <td>{record['Concept'][:30]}...</td>
                    <td>${record.get('valueMXN', 0):,.0f}</td>
                    <td>${record.get('valueUSD', 0):,.0f}</td>
                </tr>
        """

    html += f"""
            </table>
        </div>

        <div class="approval">
            <h2>✅ Approval Required</h2>
            <p>To approve this data for integration into the historical database:</p>
            <ol>
                <li><strong>Review</strong> the statistics and sample data above</li>
                <li><strong>Run the approval script:</strong></li>
            </ol>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 3px;">
cd "/Users/lvc/AI Scripts/2025_10 Consar Siefore Update Agent"
python3 approve_and_integrate.py
            </pre>
            <p>Or <strong>reject</strong> by running:</p>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 3px;">
python3 reject_data.py
            </pre>
        </div>

        <div class="footer">
            <p>Generated by CONSAR Siefore Update Agent</p>
            <p>File: {ENRICHED_JSON}</p>
        </div>
    </body>
    </html>
    """

    return html


def send_email(stats):
    """Send the review email."""

    if not SENDER_EMAIL or not RECIPIENT_EMAIL:
        print("⚠️  Email not configured. Please set environment variables:")
        print("   - SENDER_EMAIL: Your email address")
        print("   - SENDER_PASSWORD: Your email password/app password")
        print("   - RECIPIENT_EMAIL: Recipient email address")
        print("   - SMTP_SERVER (optional): SMTP server (default: smtp.gmail.com)")
        print("   - SMTP_PORT (optional): SMTP port (default: 587)")
        return False

    month_names = {
        "01": "January", "02": "February", "03": "March", "04": "April",
        "05": "May", "06": "June", "07": "July", "08": "August",
        "09": "September", "10": "October", "11": "November", "12": "December"
    }
    month_name = month_names.get(stats["period_month"], stats["period_month"])

    subject = f"CONSAR Data Review: {month_name} {stats['period_year']} - {stats['total_records']} records"

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL

    html_body = create_email_body(stats)
    msg.attach(MIMEText(html_body, 'html'))

    try:
        print(f"📧 Sending email to {RECIPIENT_EMAIL}...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


def create_approval_file(stats):
    """Create a pending approval file."""
    approval_data = {
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "period_year": stats["period_year"],
        "period_month": stats["period_month"],
        "total_records": stats["total_records"],
        "enriched_file": ENRICHED_JSON
    }

    with open(APPROVAL_FILE, "w", encoding="utf-8") as f:
        json.dump(approval_data, f, indent=2)

    print(f"✅ Created approval file: {APPROVAL_FILE}")


# === MAIN EXECUTION ===
if __name__ == "__main__":
    print("=" * 70)
    print("CONSAR Data Review Email")
    print("=" * 70)

    try:
        # Load and analyze data
        print("\n📊 Analyzing enriched data...")
        stats = load_enriched_data()

        print(f"   Period: {stats['period_month']}/{stats['period_year']}")
        print(f"   Records: {stats['total_records']:,}")
        print(f"   Total USD: ${stats['total_usd']:,.0f}")

        # Create approval file
        create_approval_file(stats)

        # Send email
        email_sent = send_email(stats)

        if email_sent:
            print("\n✅ Review request sent!")
            print(f"   Waiting for approval via approve_and_integrate.py")
        else:
            print("\n⚠️  Email not sent (not configured)")
            print(f"   You can still approve via: python3 approve_and_integrate.py")

        print("\n" + "=" * 70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
