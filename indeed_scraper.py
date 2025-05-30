import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import random

class JobScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_remoteok(self, keywords=['data engineer', 'python', 'sql']):
        """Scrape jobs from RemoteOK API"""
        jobs = []
        
        try:
            print(" Fetching jobs from RemoteOK...")
            response = self.session.get("https://remoteok.io/api", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Skip first item (metadata)
                for job_data in data[1:]:
                    if not isinstance(job_data, dict):
                        continue
                    
                    # Filter for data engineering related jobs
                    position = job_data.get('position', '').lower()
                    description = job_data.get('description', '').lower()
                    
                    # Check if job is relevant to data engineering
                    if any(keyword in position or keyword in description 
                           for keyword in keywords):
                        
                        # Parse posting time (RemoteOK provides epoch timestamp)
                        epoch_time = job_data.get('epoch', time.time())
                        posting_time = datetime.fromtimestamp(epoch_time)
                        
                        # Only include jobs from last 24 hours (since hourly filtering is hard)
                        if datetime.now() - posting_time <= timedelta(hours=24):
                            jobs.append({
                                'company_name': job_data.get('company', 'Unknown'),
                                'job_title': job_data.get('position', 'Unknown'),
                                'posting_time': posting_time.strftime('%Y-%m-%d %H:%M:%S'),
                                'job_location': 'Remote',  # RemoteOK is all remote
                                'job_type': 'Full-Time',   # Default assumption
                                'job_description': job_data.get('description', '')[:500],  # Truncate
                                'work_setting': 'Remote',
                                'ats_apply_link': job_data.get('url', '')
                            })
                
                print(f" Found {len(jobs)} relevant jobs from RemoteOK")
                
        except Exception as e:
            print(f"❌ Error scraping RemoteOK: {e}")
        
        return jobs
    
    def scrape_usajobs(self):
        """Scrape jobs from USAJobs API"""
        jobs = []
        
        try:
            print(" Fetching jobs from USAJobs...")
            headers = {
                'Host': 'data.usajobs.gov',
                'User-Agent': 'your-email@example.com'
            }
            
            params = {
                'Keyword': 'Data Engineer',
                'ResultsPerPage': 50,
                'WhoMayApply': 'All'
            }
            
            response = requests.get("https://data.usajobs.gov/api/search", 
                                  headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('SearchResult', {}).get('SearchResultItems', [])
                
                for item in items:
                    job_data = item.get('MatchedObjectDescriptor', {})
                    
                    # Parse posting date
                    pub_date_str = job_data.get('PublicationStartDate', '')
                    try:
                        pub_date = datetime.strptime(pub_date_str[:10], '%Y-%m-%d')
                        # Only include recent jobs
                        if datetime.now() - pub_date <= timedelta(days=1):
                            jobs.append({
                                'company_name': job_data.get('OrganizationName', 'US Government'),
                                'job_title': job_data.get('PositionTitle', 'Unknown'),
                                'posting_time': pub_date.strftime('%Y-%m-%d %H:%M:%S'),
                                'job_location': ', '.join(job_data.get('PositionLocationDisplay', [])),
                                'job_type': 'Full-Time',
                                'job_description': job_data.get('QualificationSummary', '')[:500],
                                'work_setting': 'Onsite',  # Government jobs usually onsite
                                'ats_apply_link': job_data.get('ApplyURI', [''])[0]
                            })
                    except:
                        continue
                        
                print(f" Found {len(jobs)} relevant jobs from USAJobs")
                
        except Exception as e:
            print(f" Error scraping USAJobs: {e}")
        
        return jobs
    
    def scrape_all_sources(self):
        """Scrape from all available sources"""
        all_jobs = []
        
        # Scrape RemoteOK
        remoteok_jobs = self.scrape_remoteok()
        all_jobs.extend(remoteok_jobs)
        
        # Add delay between API calls
        time.sleep(random.uniform(2, 4))
        
        # Scrape USAJobs
        usajobs_jobs = self.scrape_usajobs()
        all_jobs.extend(usajobs_jobs)
        
        print(f"🎯 Total jobs scraped: {len(all_jobs)}")
        return pd.DataFrame(all_jobs)

def main():
    scraper = JobScraper()
    jobs_df = scraper.scrape_all_sources()
    
    if not jobs_df.empty:
        print("\n Sample of scraped jobs:")
        print(jobs_df[['company_name', 'job_title', 'job_location']].head())
        
        # Save to CSV for inspection
        jobs_df.to_csv('scraped_jobs.csv', index=False)
        print("💾 Jobs saved to 'scraped_jobs.csv'")
    else:
        print(" No jobs found")
    
    return jobs_df

if __name__ == "__main__":
    main()
