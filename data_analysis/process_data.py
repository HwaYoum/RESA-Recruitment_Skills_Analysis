import csv
import json
import os

def process_job_data():
    """
    Reads the job data CSV and maps keywords in the 'category' column to divisions
    using the jobkorea_job_classifier.json mapping.
    
    If 'job_id' is greater than 10000, it retains the original 'division' value.
    Otherwise, it determines the division based on keyword matching.
    
    The output is written to a new CSV file.
    """
    # Define file paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_csv_path = os.path.join(base_dir, 'job_data_xAI수정본_260609.csv')
    classifier_json_path = os.path.join(base_dir, 'jobkorea_job_classifier.json')
    output_csv_path = os.path.join(base_dir, 'jobdata_after_preprocessing.csv')

    # 1. Load job classifier mapping
    print(f"Loading classifier from {classifier_json_path}...")
    with open(classifier_json_path, 'r', encoding='utf-8') as f:
        classifier = json.load(f)

    # 2. Read job data CSV
    print(f"Reading job data from {input_csv_path}...")
    rows = []
    fieldnames = []
    
    # The input file is encoded in CP949
    with open(input_csv_path, 'r', encoding='cp949') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
        for row in reader:
            rows.append(row)

    # 3. Add new columns to headers
    new_column = 'filtered_division'
    if new_column not in fieldnames:
        fieldnames.append(new_column)
        
    req_pref_column = 'requirements_preferred'
    if req_pref_column not in fieldnames:
        fieldnames.append(req_pref_column)

    # 4. Map divisions and combine requirements/preferred based on requirements
    print("Processing rows...")
    for idx, row in enumerate(rows):
        # Clean requirements and preferred, removing '신입' and '경력'
        req_str = row.get('requirements', '') or ''
        pref_str = row.get('preferred', '') or ''
        
        req_items = [k.strip() for k in req_str.split(',') if k.strip()]
        req_items_filtered = [k for k in req_items if k not in ('신입', '경력')]
        
        pref_items = [k.strip() for k in pref_str.split(',') if k.strip()]
        pref_items_filtered = [k for k in pref_items if k not in ('신입', '경력')]
        
        # Update original columns with filtered keywords
        row['requirements'] = ', '.join(req_items_filtered)
        row['preferred'] = ', '.join(pref_items_filtered)
        
        # Combine requirements and preferred, removing duplicates
        combined_seen = set()
        combined_items = []
        for item in req_items_filtered + pref_items_filtered:
            if item not in combined_seen:
                combined_seen.add(item)
                combined_items.append(item)
        row[req_pref_column] = ', '.join(combined_items)

        job_id_str = row.get('job_id', '')
        
        # Parse job_id
        try:
            job_id = int(float(job_id_str))
        except ValueError:
            job_id = 0

        if job_id > 10000:
            # If job_id is greater than 10000, copy division value directly
            row[new_column] = row.get('division', '')
        else:
            # Map based on category keywords
            category_str = row.get('category', '')
            # Split and clean the category keywords
            category_keywords = [k.strip() for k in category_str.split(',') if k.strip()]
            
            matched_divisions = []
            for division, keywords in classifier.items():
                if not keywords:
                    continue
                # If any of the division's keywords are present in the row's category keywords,
                # add this division to the matched list
                if any(kw in category_keywords for kw in keywords):
                    matched_divisions.append(division)
            
            # Combine matched divisions into a comma-separated string
            row[new_column] = ', '.join(matched_divisions)

    # 5. Write the results to a new CSV file
    print(f"Writing output to {output_csv_path}...")
    with open(output_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Processing complete!")

if __name__ == '__main__':
    process_job_data()
