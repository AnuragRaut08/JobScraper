# JobScraper

> An automated, end‑to‑end pipeline that scrapes/ingests fresh *Data‑Engineer‑centric* job postings every hour, filters them for **H‑1B friendly U.S. companies**, deduplicates & loads them into SQLite database, and exports handy CSV/JSON/HTML reports – all with a single command.

---

## ✨ Key Features

| Step                 | What it Does                                                                                                                        | Tech                                            |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| **1. Web Scraping**  | Pulls jobs posted *within the last hour* from **LinkedIn** (Selenium) and optional **Google Jobs** (SerpAPI) & *fallback* RemoteOK. | `selenium`, `google-search-results`             |
| **2. Visa Filter**   | Cross‑references jobs with **21,114** companies that filed H‑1B petitions in the last 3 years.                                      | `fuzzywuzzy` (+ `python‑Levenshtein` for speed) |
| **3. Database Load** | Stores cleaned data in **SQLite** with a strong `UNIQUE` constraint to prevent duplicates.                                          | `sqlite3`, `pandas`                             |
| **4. Automation**    | `python main.py schedule` runs the whole flow hourly. Drop one cron/Task‑Scheduler line – done.                                     | plain Cron / Task Scheduler                     |
| **5. Reporting**     | Auto‑exports **CSV, JSON, HTML**, plus a mini **market analysis** (top companies, titles, locations).                               | `pandas`, `collections.Counter`                 |

---

## 📂 Project Structure

```
jobscraper/
├── main.py                           # CLI entry-point (run / test / schedule / interactive)
├── scraping/
│   └── scraper.py                    # Unified scraper handling LinkedIn, Google Jobs, RemoteOK, Indeed
├── db/
│   ├── db_loader.py                  # SQLite schema, insert logic, stats, cleanup
│   └── schema.sql                    # Database schema definition
├── utils/
│   ├── filters.py                    # Filtering logic, DB updates, export routines
│   └── logger.py                     # Centralized logging setup
├── data/
│   └── h1bcompanies_list.csv         # List of 21k+ visa-friendly companies 
├── README.md
└── requirements.txt

```

---

## ⚡ Quick Start

```bash
# 1⃣  Clone repo & enter env
$ git clone https://github.com/<your‑user>/jobscraper.git
$ cd jobscraper

# 2⃣  Install deps
$ pip install -r requirements.txt  # Python 3.10+

# 3⃣  (Optional) add Google Jobs key
$ export SERPAPI_API_KEY="<your‑serpapi‑key>"

# 4⃣  One‑shot scrape + load
$ python main.py run

# 5⃣  Interactive search (any keywords / location)
$ python main.py interactive

# 6⃣  Hourly automation (runs forever)
$ python main.py schedule
```

> **Windows Users**: replace `export` with `setx` or use Task Scheduler.

---

## ⚙️ CLI Modes

| Command                      | Purpose                                                  |
| ---------------------------- | -------------------------------------------------------- |
| `python main.py test`        | Smoke‑tests scrapers and DB init without inserting data. |
| `python main.py run`         | Full scrape ➜ visa filter ➜ DB load ➜ export once.       |
| `python main.py interactive` | Prompt‑driven search (keywords, location, source).       |
| `python main.py schedule`    | Infinite hourly loop; logs each run and deduplicates.    |

### Scheduling with Cron (Unix/macOS)

```cron
0 * * * * /usr/bin/python3 /path/to/jobscraper/main.py schedule >> /var/log/jobscraper.log 2>&1
```

### Scheduling with Windows Task Scheduler

1. *Create Basic Task* → **Trigger**: Daily, Recur every 1 day, Repeat task every 1 hour.
2. **Action**: *Start a Program* → `python`
   **Add args**: `main.py schedule`
   **Start in**: `C:\Users\<you>\visa_scraper`

---

## 🗄️ SQLite Schema

```sql
CREATE TABLE jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_name   TEXT NOT NULL,
  job_title      TEXT NOT NULL,
  posting_time   TEXT,
  job_location   TEXT,
  job_type       TEXT,
  job_description TEXT,
  work_setting   TEXT,
  ats_apply_link TEXT,
  scraped_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(company_name, job_title, job_location, posting_time)
);
```

* **Indexes** on `(company_name, job_title)` and `scraped_at` keep queries snappy.

---

## 🔑 Environment Variables

| Variable          | Purpose                                                               |
| ----------------- | --------------------------------------------------------------------- |
| `SERPAPI_API_KEY` | (Optional) Enables Google Jobs scraping. Free tier → 100 searches/mo. |

---

## 📊 Sample Market‑Analysis Output

```
🏆 Most Common Job Titles:
   data (8) • engineer (6) • analyst (4) ...
🏢 Top Companies:
   Stripe (1) • Postman (1) • PepsiCo (1) ...
📍 Locations:
   New York NY (3) • San Francisco CA (2) ...
```

---



## 🚧 Known Limitations

* Indeed blocks with **HTTP 403**; handled gracefully but yields 0 jobs without a proxy.
* Google Jobs needs a SerpAPI key; otherwise falls back to direct scraping which may time‑out.
* Selenium scrapes \~20 jobs/min; heavy use may hit LinkedIn rate limits.

---

## 🛠️ Future Improvements

* Swap SQLite → PostgreSQL for multi‑user deployments.
* Prefect or Airflow DAG for cloud‑native scheduling.
* Dockerfile & CI pipeline for one‑command provisioning.
* Telegram/Slack alerts for fresh matched jobs.

---

## 📄 License

MIT © 2025 
Connect:Anurag [anuragtraut2003@gmail.com](mailto:anuragtraut2003@gmail.com)
