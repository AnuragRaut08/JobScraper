# import pandas as pd

# def filter_by_sponsorship(jobs_df, sponsor_csv="h1bcompanies_list.csv"):
#     sponsors = pd.read_csv(sponsor_csv)

#     # detect sponsor-name column
#     matched_cols = [c for c in sponsors.columns if 'employer' in c.lower() or 'company' in c.lower()]
#     if not matched_cols:
#         raise ValueError("No suitable sponsor name column found.")
#     sponsor_col = matched_cols[0]

#     sponsor_names = sponsors[sponsor_col].str.lower().str.strip().unique()

#     # detect company column in jobs_df
#     job_cols = [c for c in jobs_df.columns if 'company' in c.lower()]
#     if not job_cols:
#         raise ValueError("No company column in jobs DataFrame.")
#     jobs_df['Company Lower'] = jobs_df[job_cols[0]].str.lower().str.strip()

#     filtered_df = (
#         jobs_df[jobs_df['Company Lower'].isin(sponsor_names)]
#         .drop(columns=['Company Lower'])
#     )
#     return filtered_df



# utils/filters.py
import pandas as pd
from fuzzywuzzy import fuzz
import re

class CompanyFilter:
    def __init__(self, h1b_companies_file='h1bcompanies_list.csv'):
        """Initialize with H1B companies list"""
        self.h1b_companies = self.load_h1b_companies(h1b_companies_file)
        
    def load_h1b_companies(self, filepath):
        """Load H1B companies from CSV file"""
        try:
            df = pd.read_csv(filepath)
            # Assuming the CSV has a column with company names
            # Adjust column name based on your CSV structure
            if 'Company' in df.columns:
                companies = df['Company'].str.lower().str.strip().tolist()
            elif 'company' in df.columns:
                companies = df['company'].str.lower().str.strip().tolist()
            elif 'EMPLOYER_NAME' in df.columns:
                companies = df['EMPLOYER_NAME'].str.lower().str.strip().tolist()
            else:
                # Take the first column
                companies = df.iloc[:, 0].str.lower().str.strip().tolist()
            
            # Remove duplicates and empty values
            companies = list(set([c for c in companies if c and len(c) > 2]))
            print(f"✅ Loaded {len(companies)} H1B sponsor companies")
            return companies
            
        except Exception as e:
            print(f"❌ Error loading H1B companies: {e}")
            # Return some default tech companies known for H1B
            return [
                'google', 'microsoft', 'amazon', 'apple', 'meta', 'netflix',
                'uber', 'airbnb', 'tesla', 'nvidia', 'salesforce', 'oracle',
                'ibm', 'cisco', 'intel', 'adobe', 'twitter', 'linkedin'
            ]
    
    def normalize_company_name(self, company_name):
        """Normalize company name for better matching"""
        if not company_name:
            return ""
        
        # Convert to lowercase and strip
        name = company_name.lower().strip()
        
        # Remove common suffixes
        suffixes = [
            'inc', 'incorporated', 'corp', 'corporation', 'ltd', 'limited',
            'llc', 'company', 'co', 'enterprises', 'group', 'holdings',
            'technologies', 'tech', 'systems', 'solutions', 'services'
        ]
        
        for suffix in suffixes:
            # Remove suffix if it's at the end
            pattern = rf'\b{suffix}\.?$'
            name = re.sub(pattern, '', name).strip()
        
        # Remove extra whitespace and punctuation
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def fuzzy_match_company(self, job_company, threshold=80):
        """Check if job company matches any H1B company using fuzzy matching"""
        job_company_norm = self.normalize_company_name(job_company)
        
        if not job_company_norm:
            return False, None
        
        best_match = None
        best_score = 0
        
        for h1b_company in self.h1b_companies:
            h1b_company_norm = self.normalize_company_name(h1b_company)
            
            # Try different fuzzy matching methods
            scores = [
                fuzz.ratio(job_company_norm, h1b_company_norm),
                fuzz.partial_ratio(job_company_norm, h1b_company_norm),
                fuzz.token_sort_ratio(job_company_norm, h1b_company_norm),
                fuzz.token_set_ratio(job_company_norm, h1b_company_norm)
            ]
            
            max_score = max(scores)
            
            if max_score > best_score:
                best_score = max_score
                best_match = h1b_company
        
        return best_score >= threshold, best_match
    
    def filter_jobs(self, jobs_df):
        """Filter jobs to include only H1B sponsors"""
        if jobs_df.empty:
            return jobs_df
        
        print(f"🔍 Filtering {len(jobs_df)} jobs for H1B sponsors...")
        
        filtered_jobs = []
        match_details = []
        
        for idx, job in jobs_df.iterrows():
            company = job.get('company_name', '')
            is_match, matched_company = self.fuzzy_match_company(company)
            
            if is_match:
                filtered_jobs.append(job)
                match_details.append({
                    'original_company': company,
                    'matched_h1b_company': matched_company
                })
        
        filtered_df = pd.DataFrame(filtered_jobs)
        
        print(f"✅ Found {len(filtered_df)} jobs from H1B sponsors")
        
        # Print some match details for verification
        if match_details:
            print("\n📋 Sample matches:")
            for detail in match_details[:5]:
                print(f"  '{detail['original_company']}' → '{detail['matched_h1b_company']}'")
        
        return filtered_df

def main():
    """Test the filtering system"""
    # Create sample data for testing
    sample_jobs = pd.DataFrame({
        'company_name': ['Google LLC', 'Microsoft Corporation', 'Small Local Shop', 'Amazon.com Inc'],
        'job_title': ['Data Engineer', 'Senior Data Engineer', 'Data Analyst', 'Data Scientist'],
        'job_location': ['Mountain View, CA', 'Seattle, WA', 'Local City', 'Seattle, WA']
    })
    
    print("🧪 Testing company filter...")
    filter_system = CompanyFilter()
    filtered = filter_system.filter_jobs(sample_jobs)
    
    print(f"\nOriginal jobs: {len(sample_jobs)}")
    print(f"Filtered jobs: {len(filtered)}")
    print("\nFiltered companies:", filtered['company_name'].tolist())

if __name__ == "__main__":
    main()
