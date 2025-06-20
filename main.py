import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import random
import json
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import re

class EnhancedJobScraper:
    def __init__(self):
        self.min_delay = 3
        self.max_delay = 7
        self.session = None
        self.driver = None
        
    def create_session(self):
        """Create a session with rotating user agents and headers"""
        session = requests.Session()
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return session
    
    def setup_selenium_driver(self, headless=True):
        """Setup Selenium WebDriver with stealth options"""
        try:
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument('--headless')
            
            # Stealth options
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins-discovery')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            
            # Random user agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
            
            # Window size
            chrome_options.add_argument('--window-size=1920,1080')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return True
            
        except Exception as e:
            print(f" Failed to setup Selenium driver: {e}")
            print("💡 Make sure ChromeDriver is installed and in PATH")
            return False
    
    def add_delay(self, min_delay=None, max_delay=None):
        """Add random delay between requests"""
        min_d = min_delay or self.min_delay
        max_d = max_delay or self.max_delay
        delay = random.uniform(min_d, max_d)
        print(f"Waiting {delay:.1f}s...")
        time.sleep(delay)
    
    def scrape_linkedin_jobs(self, keywords=['data engineer', 'python developer', 'data analyst'], location='United States'):
        """
        Scrape LinkedIn jobs using multiple approaches
        Note: LinkedIn has strong anti-bot protection. Consider using their API or Selenium.
        """
        jobs = []
        
        try:
            print("🔍 Fetching jobs from LinkedIn...")
            
            # Method 1: Try LinkedIn's public job search (limited)
            jobs_method1 = self._scrape_linkedin_public(keywords, location)
            jobs.extend(jobs_method1)
            
            # Method 2: Try with Selenium (more reliable but requires setup)
            if self.setup_selenium_driver():
                jobs_method2 = self._scrape_linkedin_selenium(keywords, location)
                jobs.extend(jobs_method2)
                self.driver.quit()
            
            print(f" Found {len(jobs)} jobs from LinkedIn")
            
        except Exception as e:
            print(f" Error scraping LinkedIn: {e}")
        
        return jobs
    
    def _scrape_linkedin_public(self, keywords, location):
        """Scrape LinkedIn using public URLs (limited access)"""
        jobs = []
        
        try:
            session = self.create_session()
            
            for keyword in keywords:
                # LinkedIn public job search URL
                encoded_keyword = urllib.parse.quote(keyword)
                encoded_location = urllib.parse.quote(location)
                
                url = f"https://www.linkedin.com/jobs/search?keywords={encoded_keyword}&location={encoded_location}&f_TPR=r86400"  # Last 24 hours
                
                print(f"  Searching for '{keyword}' in {location}")
                
                response = session.get(url, timeout=30)
                
                if response.status_code != 200:
                    print(f"   LinkedIn returned status {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for job cards (LinkedIn's structure changes frequently)
                job_cards = soup.find_all('div', {'class': re.compile('job-search-card|base-search-card')})
                
                for card in job_cards[:10]:  # Limit to first 10 per keyword
                    try:
                        # Extract job details
                        title_elem = card.find('h3', {'class': re.compile('base-search-card__title')}) or card.find('a', {'class': re.compile('job-search-card__title-link')})
                        company_elem = card.find('h4', {'class': re.compile('base-search-card__subtitle')}) or card.find('a', {'class': re.compile('hidden-nested-link')})
                        location_elem = card.find('span', {'class': re.compile('job-search-card__location')})
                        link_elem = card.find('a', href=True)
                        
                        if title_elem and company_elem:
                            jobs.append({
                                'company_name': company_elem.get_text(strip=True),
                                'job_title': title_elem.get_text(strip=True),
                                'posting_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'job_location': location_elem.get_text(strip=True) if location_elem else location,
                                'job_type': 'Full-Time',
                                'job_description': f'LinkedIn job for {keyword}',
                                'work_setting': 'Unknown',
                                'ats_apply_link': link_elem['href'] if link_elem else '',
                                'source': 'LinkedIn'
                            })
                    except Exception as e:
                        continue
                
                self.add_delay(2, 4)  # Shorter delay for LinkedIn
        
        except Exception as e:
            print(f"Error in LinkedIn public scraping: {e}")
        
        return jobs
    
    def _scrape_linkedin_selenium(self, keywords, location):
        """Scrape LinkedIn using Selenium (more reliable but slower)"""
        jobs = []
        
        try:
            if not self.driver:
                return jobs
            
            for keyword in keywords[:2]:  # Limit keywords to avoid being blocked
                # Navigate to LinkedIn jobs
                encoded_keyword = urllib.parse.quote(keyword)
                encoded_location = urllib.parse.quote(location)
                url = f"https://www.linkedin.com/jobs/search?keywords={encoded_keyword}&location={encoded_location}&f_TPR=r86400"
                
                print(f"  Selenium search: '{keyword}' in {location}")
                
                self.driver.get(url)
                self.add_delay(3, 5)
                
                # Wait for job cards to load
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-job-id]"))
                    )
                except TimeoutException:
                    print("   Timeout waiting for job cards")
                    continue
                
                # Find job cards
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-job-id]")
                
                for i, card in enumerate(job_cards[:5]):  # Limit to 5 per keyword
                    try:
                        # Click on job card to load details
                        card.click()
                        self.add_delay(1, 2)
                        
                        # Extract job details
                        title = self.driver.find_element(By.CSS_SELECTOR, "h1").text
                        company = self.driver.find_element(By.CSS_SELECTOR, ".jobs-unified-top-card__company-name a").text
                        location_text = self.driver.find_element(By.CSS_SELECTOR, ".jobs-unified-top-card__bullet").text
                        
                        # Try to get job description
                        try:
                            description_elem = self.driver.find_element(By.CSS_SELECTOR, ".jobs-description-content__text")
                            description = description_elem.text[:500]
                        except:
                            description = f"LinkedIn job for {keyword}"
                        
                        jobs.append({
                            'company_name': company,
                            'job_title': title,
                            'posting_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'job_location': location_text,
                            'job_type': 'Full-Time',
                            'job_description': description,
                            'work_setting': 'Unknown',
                            'ats_apply_link': self.driver.current_url,
                            'source': 'LinkedIn'
                        })
                        
                    except Exception as e:
                        continue
                
                self.add_delay(5, 8)  # Longer delay between keyword searches
        
        except Exception as e:
            print(f"Error in LinkedIn Selenium scraping: {e}")
        
        return jobs
    
    def scrape_indeed_jobs(self, keywords=['data engineer', 'python developer', 'data analyst'], location='United States'):
        """Scrape Indeed jobs using requests and BeautifulSoup"""
        jobs = []
        
        try:
            print(" Fetching jobs from Indeed...")
            
            session = self.create_session()
            
            for keyword in keywords:
                print(f"  Searching for '{keyword}' in {location}")
                
                # Indeed search URL
                params = {
                    'q': keyword,
                    'l': location,
                    'fromage': '1',  # Last 1 day
                    'limit': 20
                }
                
                url = "https://www.indeed.com/jobs?" + urllib.parse.urlencode(params)
                
                response = session.get(url, timeout=30)
                
                if response.status_code != 200:
                    print(f" Indeed returned status {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find job cards (Indeed's structure)
                job_cards = soup.find_all('div', {'class': re.compile('job_seen_beacon|slider_container|jobsearch-SerpJobCard')})
                
                if not job_cards:
                    # Try alternative selectors
                    job_cards = soup.find_all('td', {'class': 'resultContent'})
                
                print(f" Found {len(job_cards)} job cards")
                
                for card in job_cards[:10]:
                    try:
                        # Extract job details - Indeed structure varies
                        title_elem = (card.find('h2', {'class': re.compile('jobTitle')}) or 
                                    card.find('a', {'data-jk': True}) or
                                    card.find('span', {'title': True}))
                        
                        company_elem = (card.find('span', {'class': re.compile('companyName')}) or
                                      card.find('a', {'class': re.compile('companyName')}) or
                                      card.find('div', {'class': re.compile('companyName')}))
                        
                        location_elem = card.find('div', {'class': re.compile('companyLocation')})
                        
                        snippet_elem = card.find('div', {'class': re.compile('job-snippet')})
                        
                        # Extract link
                        link_elem = card.find('a', {'data-jk': True}) or title_elem
                        
                        if title_elem and company_elem:
                            # Clean up title
                            if title_elem.find('span'):
                                title = title_elem.find('span').get('title', title_elem.get_text(strip=True))
                            else:
                                title = title_elem.get_text(strip=True)
                            
                            # Build job URL
                            job_url = ''
                            if link_elem and link_elem.get('href'):
                                job_url = 'https://www.indeed.com' + link_elem['href']
                            elif link_elem and link_elem.get('data-jk'):
                                job_url = f"https://www.indeed.com/viewjob?jk={link_elem['data-jk']}"
                            
                            jobs.append({
                                'company_name': company_elem.get_text(strip=True),
                                'job_title': title,
                                'posting_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'job_location': location_elem.get_text(strip=True) if location_elem else location,
                                'job_type': 'Full-Time',
                                'job_description': snippet_elem.get_text(strip=True)[:500] if snippet_elem else f'Indeed job for {keyword}',
                                'work_setting': 'Unknown',
                                'ats_apply_link': job_url,
                                'source': 'Indeed'
                            })
                    
                    except Exception as e:
                        continue
                
                self.add_delay(3, 6)  # Delay between searches
        
        except Exception as e:
            print(f"Error scraping Indeed: {e}")
        
        print(f" Found {len(jobs)} jobs from Indeed")
        return jobs
    
    def scrape_google_jobs(self, keywords=['data engineer', 'python developer', 'data analyst'], location='United States'):
        """
        Scrape Google Jobs using SerpApi (requires API key) or direct scraping
        Note: Google has strong anti-bot protection
        """
        jobs = []
        
        try:
            print(" Fetching jobs from Google Jobs...")
            
            # Method 1: Try SerpApi (recommended - requires API key)
            serpapi_key = os.getenv('SERPAPI_KEY')
            if serpapi_key:
                jobs_serpapi = self._scrape_google_jobs_serpapi(keywords, location, serpapi_key)
                jobs.extend(jobs_serpapi)
            else:
                print(" Set SERPAPI_KEY environment variable for better Google Jobs access")
            
            # Method 2: Try direct scraping (limited success due to anti-bot measures)
            jobs_direct = self._scrape_google_jobs_direct(keywords, location)
            jobs.extend(jobs_direct)
            
            print(f" Found {len(jobs)} jobs from Google Jobs")
            
        except Exception as e:
            print(f" Error scraping Google Jobs: {e}")
        
        return jobs
    
    def _scrape_google_jobs_serpapi(self, keywords, location, api_key):
        """Use SerpApi to scrape Google Jobs"""
        jobs = []
        
        try:
            session = self.create_session()
            
            for keyword in keywords[:2]:  # Limit to avoid API costs
                params = {
                    'engine': 'google_jobs',
                    'q': keyword,
                    'location': location,
                    'api_key': api_key,
                    'chips': 'date_posted:today'  # Recent jobs
                }
                
                response = session.get('https://serpapi.com/search', params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    jobs_results = data.get('jobs_results', [])
                    
                    for job in jobs_results[:10]:  # Limit per keyword
                        jobs.append({
                            'company_name': job.get('company_name', 'Unknown'),
                            'job_title': job.get('title', 'Unknown'),
                            'posting_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'job_location': job.get('location', location),
                            'job_type': 'Full-Time',
                            'job_description': job.get('description', '')[:500],
                            'work_setting': 'Unknown',
                            'ats_apply_link': job.get('apply_options', [{}])[0].get('link', ''),
                            'source': 'Google Jobs (SerpApi)'
                        })
                    
                    print(f" SerpApi found {len(jobs_results)} jobs for '{keyword}'")
                
                self.add_delay(1, 2)  # Short delay for API calls
        
        except Exception as e:
            print(f" Error with SerpApi: {e}")
        
        return jobs
    
    def _scrape_google_jobs_direct(self, keywords, location):
        """Direct scraping of Google Jobs (limited success)"""
        jobs = []
        
        try:
            # Setup Selenium for Google Jobs
            if not self.setup_selenium_driver():
                return jobs
            
            for keyword in keywords[:1]:  # Very limited to avoid blocks
                print(f"    Google direct search: '{keyword}' in {location}")
                
                # Google Jobs search URL
                query = f"{keyword} jobs in {location}"
                url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&ibp=htl;jobs"
                
                self.driver.get(url)
                self.add_delay(5, 8)  # Longer delay for Google
                
                try:
                    # Wait for job results
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-jibp]"))
                    )
                    
                    # Find job elements (Google's structure is complex and changes)
                    job_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-jibp] h3")
                    
                    for elem in job_elements[:5]:  # Very limited
                        try:
                            title = elem.text
                            
                            # Try to find parent container for more details
                            parent = elem.find_element(By.XPATH, "./ancestor::div[contains(@class, 'job')]")
                            company_elem = parent.find_element(By.CSS_SELECTOR, ".vNEEBe")
                            
                            jobs.append({
                                'company_name': company_elem.text if company_elem else 'Unknown',
                                'job_title': title,
                                'posting_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'job_location': location,
                                'job_type': 'Full-Time',
                                'job_description': f'Google Jobs result for {keyword}',
                                'work_setting': 'Unknown',
                                'ats_apply_link': '',
                                'source': 'Google Jobs'
                            })
                        
                        except Exception as e:
                            continue
                
                except TimeoutException:
                    print("  Google Jobs timeout - may be blocked")
            
            self.driver.quit()
        
        except Exception as e:
            print(f" Error in Google direct scraping: {e}")
        
        return jobs
    
    def scrape_remoteok(self, keywords=['data engineer', 'python', 'sql', 'analyst', 'scientist']):
        """Scrape jobs from RemoteOK API (from original code)"""
        jobs = []
        
        try:
            print(" Fetching jobs from RemoteOK...")
            
            session = self.create_session()
            response = session.get("https://remoteok.io/api", timeout=30)
            
            if response.status_code != 200:
                print(f" RemoteOK API returned status {response.status_code}")
                return jobs
            
            data = response.json()
            print(f" Retrieved {len(data)} total items from RemoteOK")
        
            job_count = 0
            for job_data in data[1:]:  # Skip first metadata item
                if not isinstance(job_data, dict):
                    continue
                
                position = job_data.get('position', '').lower()
                description = job_data.get('description', '').lower()
                tags = job_data.get('tags', [])
                tag_text = ' '.join([str(tag).lower() for tag in tags if tag])
                
                search_text = f"{position} {description} {tag_text}"
                keyword_match = any(keyword.lower() in search_text for keyword in keywords)
                
                if keyword_match:
                    epoch_time = job_data.get('epoch', time.time())
                    try:
                        posting_time = datetime.fromtimestamp(epoch_time)
                    except (ValueError, OSError):
                        posting_time = datetime.now()
                    
                    if datetime.now() - posting_time <= timedelta(days=7):
                        job_count += 1
                        jobs.append({
                            'company_name': job_data.get('company', 'Unknown'),
                            'job_title': job_data.get('position', 'Unknown'),
                            'posting_time': posting_time.strftime('%Y-%m-%d %H:%M:%S'),
                            'job_location': 'Remote',
                            'job_type': 'Full-Time',
                            'job_description': (description[:500] + '...' if len(description) > 500 else description),
                            'work_setting': 'Remote',
                            'ats_apply_link': job_data.get('url', ''),
                            'salary_min': job_data.get('salary_min'),
                            'salary_max': job_data.get('salary_max'),
                            'tags': ', '.join([str(tag) for tag in tags[:5]]),
                            'source': 'RemoteOK'
                        })
            
            print(f" Found {len(jobs)} relevant jobs from RemoteOK")
                
        except Exception as e:
            print(f" Error scraping RemoteOK: {e}")
        
        return jobs
    
    def scrape_all_sources(self, keywords=['data engineer', 'python developer', 'data analyst'], location='United States'):
        """Scrape from all available sources"""
        all_jobs = []
        
        print(" Starting comprehensive job scraping...")
        print(f" Keywords: {', '.join(keywords)}")
        print(f" Location: {location}")
        
        # Scrape LinkedIn
        print("\n" + "="*50)
        print("LinkedIn Jobs")
        print("="*50)
        linkedin_jobs = self.scrape_linkedin_jobs(keywords, location)
        all_jobs.extend(linkedin_jobs)
        self.add_delay()
        
        # Scrape Indeed
        print("\n" + "="*50)
        print("Indeed Jobs")
        print("="*50)
        indeed_jobs = self.scrape_indeed_jobs(keywords, location)
        all_jobs.extend(indeed_jobs)
        self.add_delay()
        
        # Scrape Google Jobs
        print("\n" + "="*50)
        print("Google Jobs")
        print("="*50)
        google_jobs = self.scrape_google_jobs(keywords, location)
        all_jobs.extend(google_jobs)
        self.add_delay()
        
        # Scrape RemoteOK (from original code)
        print("\n" + "="*50)
        print("RemoteOK Jobs")
        print("="*50)
        remoteok_jobs = self.scrape_remoteok()
        all_jobs.extend(remoteok_jobs)
        
        print(f"\n Total jobs scraped: {len(all_jobs)}")
        
        if all_jobs:
            # Create DataFrame and remove duplicates
            df = pd.DataFrame(all_jobs)
            initial_count = len(df)
            df = df.drop_duplicates(subset=['company_name', 'job_title'], keep='first')
            final_count = len(df)
            
            if initial_count != final_count:
                print(f" Removed {initial_count - final_count} duplicate jobs")
            
            return df
        else:
            return pd.DataFrame()
    
    def __del__(self):
        """Cleanup"""
        if self.driver:
            self.driver.quit()

def setup_instructions():
    """Print setup instructions for the scraper"""
    print("SETUP INSTRUCTIONS")
    print("="*50)
    print("1. Install required packages:")
    print("   pip install requests pandas beautifulsoup4 selenium")
    print("")
    print("2. For Selenium (LinkedIn, Google Jobs):")
    print("   - Install Chrome browser")
    print("   - Download ChromeDriver from https://chromedriver.chromium.org/")
    print("   - Add ChromeDriver to your PATH")
    print("")
    print("3. For Google Jobs API access (optional but recommended):")
    print("   - Get API key from https://serpapi.com/")
    print("   - Set environment variable: export SERPAPI_KEY='your-key'")
    print("")
    print("4. For LinkedIn API access (enterprise):")
    print("   - Apply for LinkedIn API access")
    print("   - Use official LinkedIn Jobs API")
    print("")
    print(" IMPORTANT NOTES:")
    print("- These sites have anti-bot protection")
    print("- Use responsibly and respect robots.txt")
    print("- Consider using official APIs when available")
    print("- Add delays between requests to avoid being blocked")
    print("="*50)

def test_individual_scrapers():
    """Test each scraper individually"""
    scraper = EnhancedJobScraper()
    
    keywords = ['data engineer', 'python developer']
    location = 'United States'
    
    print(" Testing LinkedIn scraper...")
    linkedin_jobs = scraper.scrape_linkedin_jobs(keywords, location)
    print(f"LinkedIn results: {len(linkedin_jobs)} jobs\n")
    
    scraper.add_delay()
    
    print(" Testing Indeed scraper...")
    indeed_jobs = scraper.scrape_indeed_jobs(keywords, location)
    print(f"Indeed results: {len(indeed_jobs)} jobs\n")
    
    scraper.add_delay()
    
    print(" Testing Google Jobs scraper...")
    google_jobs = scraper.scrape_google_jobs(keywords, location)
    print(f"Google Jobs results: {len(google_jobs)} jobs\n")
    
    return linkedin_jobs, indeed_jobs, google_jobs

def main():
    """Main function to run the enhanced scraper"""
    print(" Enhanced Job Scraper v3.0")
    print("LinkedIn • Indeed • Google Jobs • RemoteOK")
    
    setup_instructions()
    
    # Configuration
    keywords = ['data engineer', 'python developer', 'data analyst', 'machine learning engineer']
    location = 'United States'
    
    scraper = EnhancedJobScraper()
    
    try:
        # Run comprehensive scraping
        jobs_df = scraper.scrape_all_sources(keywords, location)
        
        if not jobs_df.empty:
            print("\n Sample of scraped jobs:")
            print(jobs_df[['company_name', 'job_title', 'job_location', 'source']].head(15))
            
            # Save to CSV with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'enhanced_scraped_jobs_{timestamp}.csv'
            jobs_df.to_csv(filename, index=False)
            print(f"\n Jobs saved to '{filename}'")
            
            # Show summary statistics
            print(f"\n Summary:")
            print(f"   Total jobs found: {len(jobs_df)}")
            print(f"   Sources breakdown:")
            source_counts = jobs_df['source'].value_counts()
            for source, count in source_counts.items():
                print(f"     - {source}: {count} jobs")
            
            # Show locations
            print(f"   Top locations:")
            location_counts = jobs_df['job_location'].value_counts().head(5)
            for location, count in location_counts.items():
                print(f"     - {location}: {count} jobs")
            
            # Show companies
            print(f"   Top companies:")
            company_counts = jobs_df['company_name'].value_counts().head(5)
            for company, count in company_counts.items():
                print(f"     - {company}: {count} jobs")
            
        else:
            print("\n No jobs found. Running individual tests...")
            test_individual_scrapers()
    
    except KeyboardInterrupt:
        print("\n Scraping interrupted by user")
    except Exception as e:
        print(f"\n Unexpected error: {e}")
    finally:
        # Cleanup
        if hasattr(scraper, 'driver') and scraper.driver:
            scraper.driver.quit()
    
    return jobs_df if 'jobs_df' in locals() else pd.DataFrame()

# Additional utility functions

def create_job_alert_system():
    """Create a simple job alert system"""
    print(" Job Alert System")
    print("="*30)
    
    class JobAlert:
        def __init__(self):
            self.keywords = []
            self.locations = []
            self.email = None
        
        def add_keyword(self, keyword):
            self.keywords.append(keyword)
            print(f" Added keyword: {keyword}")
        
        def add_location(self, location):
            self.locations.append(location)
            print(f" Added location: {location}")
        
        def set_email(self, email):
            self.email = email
            print(f" Email set: {email}")
        
        def run_alert(self):
            """Run job search and send alerts"""
            if not self.keywords or not self.locations:
                print(" Please add keywords and locations first")
                return
            
            scraper = EnhancedJobScraper()
            jobs_df = scraper.scrape_all_sources(self.keywords, self.locations[0])
            
            if not jobs_df.empty:
                print(f" Found {len(jobs_df)} new jobs!")
                
                # Here you would implement email sending logic
                # For now, just save to file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'job_alert_{timestamp}.csv'
                jobs_df.to_csv(filename, index=False)
                print(f" Alert results saved to: {filename}")
                
                return jobs_df
            else:
                print(" No new jobs found")
                return pd.DataFrame()
    
    return JobAlert()

def analyze_job_market(jobs_df):
    """Analyze job market trends from scraped data"""
    if jobs_df.empty:
        print("No data to analyze")
        return
    
    print("\n JOB MARKET ANALYSIS")
    print("="*50)
    
    # Most common job titles
    print(" Most Common Job Titles:")
    title_words = []
    for title in jobs_df['job_title'].str.lower():
        title_words.extend(title.split())
    
    from collections import Counter
    common_words = Counter(title_words).most_common(10)
    for word, count in common_words:
        if len(word) > 3:  # Filter out short words
            print(f"   {word}: {count} mentions")
    
    # Company analysis
    print(f"\n Company Distribution:")
    company_stats = jobs_df['company_name'].value_counts().head(10)
    for company, count in company_stats.items():
        print(f"   {company}: {count} jobs")
    
    # Location analysis
    print(f"\n Location Distribution:")
    location_stats = jobs_df['job_location'].value_counts().head(10)
    for location, count in location_stats.items():
        print(f"   {location}: {count} jobs")
    
    # Source analysis
    print(f"\n Source Distribution:")
    source_stats = jobs_df['source'].value_counts()
    for source, count in source_stats.items():
        percentage = (count / len(jobs_df)) * 100
        print(f"   {source}: {count} jobs ({percentage:.1f}%)")

def export_to_multiple_formats(jobs_df, base_filename="scraped_jobs"):
    """Export jobs data to multiple formats"""
    if jobs_df.empty:
        print(" No data to export")
        return
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # CSV export
    csv_file = f"{base_filename}_{timestamp}.csv"
    jobs_df.to_csv(csv_file, index=False)
    print(f" CSV exported: {csv_file}")
    
    # JSON export
    json_file = f"{base_filename}_{timestamp}.json"
    jobs_df.to_json(json_file, orient='records', indent=2)
    print(f" JSON exported: {json_file}")
    
    # Excel export (if openpyxl is available)
    try:
        excel_file = f"{base_filename}_{timestamp}.xlsx"
        jobs_df.to_excel(excel_file, index=False, sheet_name='Jobs')
        print(f"Excel exported: {excel_file}")
    except ImportError:
        print(" Install openpyxl for Excel export: pip install openpyxl")
    
    # HTML export for viewing
    html_file = f"{base_filename}_{timestamp}.html"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Job Scraping Results</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .job-title {{ font-weight: bold; color: #2c5aa0; }}
            .company {{ color: #666; }}
        </style>
    </head>
    <body>
        <h1>Job Scraping Results</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total jobs found: {len(jobs_df)}</p>
        {jobs_df.to_html(escape=False, classes='job-table')}
    </body>
    </html>
    """
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f" HTML exported: {html_file}")

def run_scheduled_scraping():
    """Run scraping on a schedule"""
    import schedule
    
    def job_scraping_task():
        print(f"\n Scheduled scraping started at {datetime.now()}")
        scraper = EnhancedJobScraper()
        keywords = ['data engineer', 'python developer', 'data analyst']
        location = 'United States'
        
        jobs_df = scraper.scrape_all_sources(keywords, location)
        
        if not jobs_df.empty:
            export_to_multiple_formats(jobs_df, "scheduled_jobs")
            analyze_job_market(jobs_df)
        
        print(f" Scheduled scraping completed at {datetime.now()}")
    
    # Schedule the job (uncomment and modify as needed)
    schedule.every().hour.do(job_scraping_task)  # Every hour
    schedule.every().day.at("09:00").do(job_scraping_task)  # Daily at 9 AM
    
    print(" Scheduling system ready!")
    
    
    # Run once immediately for testing
    job_scraping_task()

def interactive_mode():
    """Interactive mode for customized scraping"""
    print(" INTERACTIVE JOB SCRAPER")
    print("="*40)
    
    # Get user preferences
    print("Enter your job search preferences:")
    
    keywords_input = input("Keywords (comma-separated): ").strip()
    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()] if keywords_input else ['data engineer', 'python developer']
    
    location = input("Location (default: United States): ").strip() or 'United States'
    
    print(f"\n Searching for: {', '.join(keywords)}")
    print(f" Location: {location}")
    
    # Source selection
    print("\nSelect sources to scrape:")
    print("1. LinkedIn")
    print("2. Indeed") 
    print("3. Google Jobs")
    print("4. RemoteOK")
    print("5. All sources")
    
    source_choice = input("Enter choice (1-5, default: 5): ").strip() or '5'
    
    scraper = EnhancedJobScraper()
    
    try:
        if source_choice == '1':
            jobs_df = pd.DataFrame(scraper.scrape_linkedin_jobs(keywords, location))
        elif source_choice == '2':
            jobs_df = pd.DataFrame(scraper.scrape_indeed_jobs(keywords, location))
        elif source_choice == '3':
            jobs_df = pd.DataFrame(scraper.scrape_google_jobs(keywords, location))
        elif source_choice == '4':
            jobs_df = pd.DataFrame(scraper.scrape_remoteok())
        else:
            jobs_df = scraper.scrape_all_sources(keywords, location)
        
        if not jobs_df.empty:
            print(f"\n Found {len(jobs_df)} jobs!")
            
            # Show preview
            print("\n Preview:")
            print(jobs_df[['company_name', 'job_title', 'job_location', 'source']].head(10))
            
            # Export options
            export_choice = input("\nExport results? (y/n, default: y): ").strip().lower()
            if export_choice != 'n':
                export_to_multiple_formats(jobs_df)
            
            # Analysis option
            analysis_choice = input("Show market analysis? (y/n, default: y): ").strip().lower()
            if analysis_choice != 'n':
                analyze_job_market(jobs_df)
        
        else:
            print("\n No jobs found. Try different keywords or locations.")
    
    except KeyboardInterrupt:
        print("\n Scraping interrupted")
    finally:
        if hasattr(scraper, 'driver') and scraper.driver:
            scraper.driver.quit()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'interactive':
            interactive_mode()
        elif sys.argv[1] == 'test':
            test_individual_scrapers()
        elif sys.argv[1] == 'schedule':
            run_scheduled_scraping()
        elif sys.argv[1] == 'alert':
            alert = create_job_alert_system()
            # Example usage:
            alert.add_keyword('data engineer')
            alert.add_keyword('machine learning')
            alert.add_location('United States')
            alert.run_alert()
        else:
            main()
    else:
        main()
