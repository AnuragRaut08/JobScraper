CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_title TEXT,
    company_name TEXT,
    location TEXT,
    job_type TEXT,
    job_description TEXT,
    work_setting TEXT,
    apply_link TEXT UNIQUE,
    posting_time TEXT
);
