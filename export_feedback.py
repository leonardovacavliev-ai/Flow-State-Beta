#!/usr/bin/env python3
"""
Export feedback from production PostgreSQL database to CSV
"""
import psycopg2
import csv
from datetime import datetime

# Production database connection
DATABASE_URL = "postgresql://postgres:kWTbHNiMEoSTLJGdZWidWgVwMzplAuYH@tokaido.proxy.rlwy.net:14038/railway"

def export_feedback():
    """Export all feedback to CSV"""
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Fetch all feedback
        cursor.execute("""
            SELECT
                session_id,
                email,
                esp,
                rating,
                comments,
                submitted_at
            FROM feedback
            ORDER BY submitted_at DESC
        """)

        rows = cursor.fetchall()

        # Export to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'production_feedback_{timestamp}.csv'

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Session ID', 'Email', 'ESP', 'Rating', 'Comments', 'Submitted At'])
            writer.writerows(rows)

        print(f"✅ Exported {len(rows)} feedback entries to {filename}")

        # Print summary
        cursor.execute("SELECT rating, COUNT(*) FROM feedback GROUP BY rating ORDER BY rating DESC")
        ratings = cursor.fetchall()

        print("\n📊 Feedback Summary:")
        for rating, count in ratings:
            print(f"  {rating} stars: {count} responses")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    export_feedback()
