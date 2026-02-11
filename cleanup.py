import pandas as pd
import re
from datetime import datetime
import os

def clean_signup_data(input_file):
    """
    Clean and process signup data from Excel file according to business rules.
    
    Args:
        input_file (str): Path to the input Excel file
    
    Returns:
        tuple: (clean_df, quarantined_df, summary_stats)
    """
    print(f"Reading data from {input_file}...")
    
    # Read the Excel file
    df = pd.read_excel(input_file)
    
    # Print initial info about the dataset
    total_rows = len(df)
    print(f"Total rows in original file: {total_rows}")
    print(f"Columns in the dataset: {list(df.columns)}")
    
    # Create a copy for processing and add metadata columns
    df['original_index'] = df.index
    df['is_multi_plan'] = False
    
    # Initialize lists to track clean and quarantined records
    quarantined_records = []
    clean_records = []
    
    # Standardize dates - convert all signup dates to YYYY-MM-DD format
    print("Standardizing dates...")
    df['signup_date_standardized'] = None
    for idx, row in df.iterrows():
        try:
            # Attempt to parse the date using pandas - it handles many formats
            parsed_date = pd.to_datetime(row['signup_date'], errors='coerce')
            if pd.isna(parsed_date):
                # If parsing failed, mark for quarantine
                quarantined_records.append(idx)
            else:
                # Convert to standardized string format
                df.at[idx, 'signup_date_standardized'] = parsed_date.strftime('%Y-%m-%d')
        except:
            # If any exception occurs during date parsing, mark for quarantine
            quarantined_records.append(idx)
    
    # Identify and handle duplicate users (by email)
    print("Processing duplicates and multi-plan users...")
    
    # Group by email to identify users with multiple signups
    email_groups = df.groupby('email').groups
    
    for email, indices in email_groups.items():
        indices_list = list(indices)
        
        # If user has multiple signups, keep only the most recent one
        if len(indices_list) > 1:
            # Get the most recent signup based on standardized date
            recent_idx = None
            most_recent_date = None
            
            for idx in indices_list:
                if idx not in quarantined_records:  # Only consider non-quarantined records
                    date_str = df.at[idx, 'signup_date_standardized']
                    if date_str:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        if most_recent_date is None or date_obj > most_recent_date:
                            most_recent_date = date_obj
                            recent_idx = idx
            
            # Mark all but the most recent signup for this email as quarantined
            for idx in indices_list:
                if idx != recent_idx and idx not in quarantined_records:
                    quarantined_records.append(idx)
            
            # Set is_multi_plan flag for the remaining record
            if recent_idx is not None:
                df.at[recent_idx, 'is_multi_plan'] = True
    
    # Validate emails and other data quality checks
    print("Validating data quality...")
    for idx, row in df.iterrows():
        if idx in quarantined_records:
            continue  # Skip already quarantined records
            
        # Check if email is valid (contains @ and domain)
        email = str(row.get('email', '')).strip().lower()
        if not email or '@' not in email or '.' not in email.split('@')[1:]:
            quarantined_records.append(idx)
            continue
        
        # Check if name looks like test data
        name = str(row.get('name', '')).strip().lower()
        test_indicators = ['test', 'dummy', 'abc', 'sample', 'demo', 'placeholder']
        if any(indicator in name for indicator in test_indicators):
            quarantined_records.append(idx)
            continue
        
        # Check if important fields are empty
        important_fields = ['name', 'email', 'signup_date_standardized']
        if any(pd.isna(row.get(field)) or str(row.get(field)).strip() == '' for field in important_fields):
            quarantined_records.append(idx)
            continue
    
    # Separate clean and quarantined data
    quarantined_df = df.iloc[quarantined_records].copy()
    
    # Get clean records (those not quarantined and with valid standardized dates)
    clean_indices = [idx for idx in df.index if idx not in quarantined_records and 
                     pd.notna(df.at[idx, 'signup_date_standardized'])]
    clean_df = df.iloc[clean_indices].copy()
    
    # Select only the original columns plus our new 'is_multi_plan' column
    original_columns = [col for col in df.columns if col not in ['original_index', 'signup_date_standardized']]
    if 'signup_date_standardized' not in original_columns:
        original_columns.append('signup_date_standardized')
    
    clean_df = clean_df[original_columns]
    quarantined_df = quarantined_df[original_columns]
    
    # Rename the standardized date column back to signup_date for final output
    clean_df.rename(columns={'signup_date_standardized': 'signup_date'}, inplace=True)
    quarantined_df.rename(columns={'signup_date_standardized': 'signup_date'}, inplace=True)
    
    # Summary statistics
    clean_count = len(clean_df)
    quarantined_count = len(quarantined_df)
    
    summary = {
        'total_rows': total_rows,
        'clean_rows': clean_count,
        'quarantined_rows': quarantined_count
    }
    
    return clean_df, quarantined_df, summary


def main():
    """
    Main function to execute the data cleaning process.
    """
    input_file = 'signups.xls'
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found!")
        return
    
    # Clean the data
    clean_df, quarantined_df, summary = clean_signup_data(input_file)
    
    # Save the results
    print("\nSaving cleaned data...")
    clean_df.to_csv('members_final.csv', index=False)
    print(f"Saved {len(clean_df)} clean records to members_final.csv")
    
    print("Saving quarantined data...")
    quarantined_df.to_csv('quarantine.csv', index=False)
    print(f"Saved {len(quarantined_df)} quarantined records to quarantine.csv")
    
    # Print summary
    print("\n--- SUMMARY ---")
    print(f"Total rows processed: {summary['total_rows']}")
    print(f"Clean rows: {summary['clean_rows']}")
    print(f"Quarantined rows: {summary['quarantined_rows']}")
    print(f"Data quality rate: {summary['clean_rows']/summary['total_rows']*100:.1f}%")
    
    print("\n--- PROCESS COMPLETED ---")


if __name__ == "__main__":
    main()