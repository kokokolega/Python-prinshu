# Member Cleanup Script

This script cleans and standardizes a messy marketing export file (`signups.xls`) and produces a CRM-ready "Golden Record" CSV.

It applies business rules around date formatting, deduplication, plan handling, and low-quality lead filtering.

---

## 📂 Input

- `signups.xls`  
  Raw Excel file exported from multiple landing pages.

---

## 📤 Output

The script generates two files:

1. `members_final.csv`  
   Cleaned and deduplicated list of valid members.

2. `quarantine.csv`  
   Low-quality, invalid, or test data separated for review.

---

## 🧠 Business Rules Applied

### 1. Date Standardization
All signup dates are converted into `YYYY-MM-DD` format.  
Rows with unparseable dates are treated as low quality.

---

### 2. Deduplication
Users are uniquely identified by email address.

If duplicate emails exist:
- Only one record is kept in the final file.
- The most recent signup is preserved.

---

### 3. Plan Context Rule
If a user signed up for both **Plan A** and **Plan B**:
- The most recent signup is retained.
- A new column `is_multi_plan` is set to `True`.

If a user signed up only once:
- `is_multi_plan` is set to `False`.

---

### 4. Low Quality Lead Filtering
Rows are moved to `quarantine.csv` if they contain:

- Invalid or missing email addresses
- Test/dummy names (e.g., "test", "dummy", etc.)
- Missing required fields
- Invalid or unparseable dates
- Clearly fake or placeholder data

This prevents poor data from entering the CRM.

---

## ⚙️ Installation

Create a virtual environment (recommended):

