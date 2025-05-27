import sqlite3
import pandas as pd
from datetime import datetime
import os

class JobDatabase:
    def __init__(self, db_path='job_data.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create jobs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    job_title TEXT NOT NULL,
                    posting_time TEXT,
                    job_location TEXT,
                    job_type TEXT,
                    job_description TEXT,
                    work_setting TEXT,
                    ats_apply_link TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_name, job_title, job_location, posting_time)
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_company_title 
                ON jobs(company_name, job_title)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_scraped_at 
                ON jobs(scraped_at)
            ''')
            
            conn.commit()
            conn.close()
            print("✅ Database initialized successfully")
            
        except Exception as e:
            print(f" Error initializing database: {e}")
    
    def insert_jobs(self, jobs_df):
        """Insert jobs into database, avoiding duplicates"""
        if jobs_df.empty:
            print("No jobs to insert")
            return 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Add scraped_at timestamp
            jobs_df['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert jobs, ignoring duplicates
            inserted_count = 0
            for _, job in jobs_df.iterrows():
                try:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR IGNORE INTO jobs 
                        (company_name, job_title, posting_time, job_location, 
                         job_type, job_description, work_setting, ats_apply_link, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        job['company_name'],
                        job['job_title'],
                        job['posting_time'],
                        job['job_location'],
                        job['job_type'],
                        job['job_description'],
                        job['work_setting'],
                        job['ats_apply_link'],
                        job['scraped_at']
                    ))
                    
                    if cursor.rowcount > 0:
                        inserted_count += 1
                        
                except Exception as e:
                    print(f"Error inserting job: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            print(f"✅ Inserted {inserted_count} new jobs into database")
            return inserted_count
            
        except Exception as e:
            print(f"❌ Error inserting jobs: {e}")
            return 0
    
    def get_all_jobs(self):
        """Retrieve all jobs from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT * FROM jobs ORDER BY scraped_at DESC", conn)
            conn.close()
            return df
        except Exception as e:
            print(f"❌ Error retrieving jobs: {e}")
            return pd.DataFrame()
    
    def get_recent_jobs(self, hours=24):
        """Get jobs scraped in the last N hours"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = '''
                SELECT * FROM jobs 
                WHERE scraped_at >= datetime('now', '-{} hours')
                ORDER BY scraped_at DESC
            '''.format(hours)
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"❌ Error retrieving recent jobs: {e}")
            return pd.DataFrame()
    
    def get_stats(self):
        """Get database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total jobs
            cursor.execute("SELECT COUNT(*) FROM jobs")
            total_jobs = cursor.fetchone()[0]
            
            # Unique companies
            cursor.execute("SELECT COUNT(DISTINCT company_name) FROM jobs")
            unique_companies = cursor.fetchone()[0]
            
            # Jobs by work setting
            cursor.execute('''
                SELECT work_setting, COUNT(*) 
                FROM jobs 
                GROUP BY work_setting
            ''')
            work_settings = cursor.fetchall()
            
            # Recent jobs (last 24 hours)
            cursor.execute('''
                SELECT COUNT(*) FROM jobs 
                WHERE scraped_at >= datetime('now', '-24 hours')
            ''')
            recent_jobs = cursor.fetchone()[0]
            
            conn.close()
            
            stats = {
                'total_jobs': total_jobs,
                'unique_companies': unique_companies,
                'work_settings': dict(work_settings),
                'recent_jobs_24h': recent_jobs
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {}
    
    def cleanup_old_jobs(self, days=7):
        """Remove jobs older than N days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM jobs 
                WHERE scraped_at < datetime('now', '-{} days')
            '''.format(days))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            print(f"🗑️ Cleaned up {deleted_count} old jobs")
            return deleted_count
            
        except Exception as e:
            print(f"❌ Error cleaning up old jobs: {e}")
            return 0

def main():
    """Test the database system"""
    print("🧪 Testing database system...")
    
    # Initialize database
    db = JobDatabase()
    
    # Create sample data
    sample_jobs = pd.DataFrame({
        'company_name': ['Google LLC', 'Microsoft Corporation'],
        'job_title': ['Data Engineer', 'Senior Data Engineer'],
        'posting_time': ['2024-01-20 10:00:00', '2024-01-20 11:00:00'],
        'job_location': ['Mountain View, CA', 'Seattle, WA'],
        'job_type': ['Full-Time', 'Full-Time'],
        'job_description': ['Build data pipelines', 'Design data architecture'],
        'work_setting': ['Remote', 'Hybrid'],
        'ats_apply_link': ['https://google.com/jobs/1', 'https://microsoft.com/jobs/1']
    })
    
    # Test insertion
    inserted = db.insert_jobs(sample_jobs)
    print(f"Inserted {inserted} jobs")
    
    # Test retrieval
    all_jobs = db.get_all_jobs()
    print(f"Total jobs in database: {len(all_jobs)}")
    
    # Test stats
    stats = db.get_stats()
    print("Database stats:", stats)

if __name__ == "__main__":
    main()
