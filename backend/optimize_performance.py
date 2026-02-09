"""
Quick response optimization script
Run this to apply immediate performance improvements
"""

import sqlite3
import logging

def optimize_database():
    """Add indexes to improve query performance"""
    
    conn = sqlite3.connect('admissions.db')
    cursor = conn.cursor()
    
    try:
        # Add indexes for faster placement queries
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_placements_student_name ON placements(student_name)",
            "CREATE INDEX IF NOT EXISTS idx_placements_package ON placements(package)",
            "CREATE INDEX IF NOT EXISTS idx_placements_graduation_year ON placements(graduation_year)",
            "CREATE INDEX IF NOT EXISTS idx_placements_company_id ON placements(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_placements_program ON placements(program)",
            "CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name)",
            "CREATE INDEX IF NOT EXISTS idx_placements_composite ON placements(graduation_year, package, company_id)",
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
            print(f"✅ Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
        
        # Optimize database
        cursor.execute("ANALYZE")
        cursor.execute("VACUUM")
        
        conn.commit()
        print("✅ Database optimized for faster queries")
        
    except Exception as e:
        print(f"❌ Error optimizing database: {e}")
    finally:
        conn.close()

def create_quick_stats_view():
    """Create a materialized view for quick stats"""
    
    conn = sqlite3.connect('admissions.db')
    cursor = conn.cursor()
    
    try:
        # Drop existing view if exists
        cursor.execute("DROP VIEW IF EXISTS placement_quick_stats")
        
        # Create quick stats view
        cursor.execute("""
        CREATE VIEW placement_quick_stats AS
        SELECT 
            COUNT(*) as total_placements,
            COUNT(DISTINCT company_id) as total_companies,
            ROUND(AVG(package), 2) as avg_package,
            MAX(package) as max_package,
            MIN(package) as min_package,
            graduation_year
        FROM placements 
        WHERE package > 0
        GROUP BY graduation_year
        """)
        
        conn.commit()
        print("✅ Created quick stats view for faster responses")
        
    except Exception as e:
        print(f"❌ Error creating stats view: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Optimizing VU Chatbot for faster responses...")
    optimize_database()
    create_quick_stats_view()
    print("🎉 Optimization complete! Responses should be much faster now.")