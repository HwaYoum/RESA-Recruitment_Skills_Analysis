import pandas as pd
import matplotlib.pyplot as plt
import os
from collections import Counter

def analyze():
    """
    Analyzes the preprocessed job data CSV file:
    1. Counts the frequencies of keywords in requirements, preferred, and requirements_preferred.
    2. Outputs these frequencies into a single CSV.
    3. Visualizes the top 8 keywords for each column as a percentage bar chart.
    4. Analyzes and visualizes the count of job postings by filtered_division.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, 'jobdata_after_preprocessing.csv')
    output_dir = os.path.join(base_dir, 'EDA')
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Read preprocessed CSV
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} does not exist. Please run process_data.py first.")
        return
        
    df = pd.read_csv(csv_path, encoding='utf-8')
    total_rows = len(df)
    print(f"Total rows to analyze: {total_rows}")
    
    # Helper function to count keywords in a column
    def count_keywords(series):
        counter = Counter()
        for val in series.dropna():
            if not isinstance(val, str):
                continue
            keywords = [k.strip() for k in val.split(',') if k.strip()]
            counter.update(keywords)
        return counter

    # Count frequencies for the three columns
    req_counts = count_keywords(df['requirements'])
    pref_counts = count_keywords(df['preferred'])
    req_pref_counts = count_keywords(df['requirements_preferred'])
    
    # Get union of all keywords
    all_keywords = set(req_counts.keys()) | set(pref_counts.keys()) | set(req_pref_counts.keys())
    
    # Organize counts into list of dicts
    freq_data = []
    for kw in sorted(all_keywords):
        freq_data.append({
            'keyword': kw,
            'requirements': req_counts.get(kw, 0),
            'preferred': pref_counts.get(kw, 0),
            'requirements_preferred': req_pref_counts.get(kw, 0)
        })
        
    # Create DataFrame and sort by requirements_preferred descending
    freq_df = pd.DataFrame(freq_data)
    freq_df = freq_df.sort_values(by='requirements_preferred', ascending=False)
    
    # Save keyword frequencies to a CSV
    freq_csv_path = os.path.join(output_dir, 'keyword_frequencies.csv')
    freq_df.to_csv(freq_csv_path, index=False, encoding='utf-8')
    print(f"Saved keyword frequencies to {freq_csv_path}")
    
    # Set Korean font for Matplotlib
    plt.rc('font', family='Malgun Gothic')
    plt.rcParams['axes.unicode_minus'] = False
    
    # 2. Visualize Top 8 keywords for each column
    cols_to_visualize = {
        'requirements': ('requirements_top8.png', '주요 요구 기술/자격 (Requirements) 상위 8개 비중'),
        'preferred': ('preferred_top8.png', '우대 기술/자격 (Preferred) 상위 8개 비중'),
        'requirements_preferred': ('requirements_preferred_top8.png', '통합 기술/자격 (Requirements & Preferred) 상위 8개 비중')
    }
    
    for col, (filename, title) in cols_to_visualize.items():
        # Get top 8 keywords for this column
        if col == 'requirements':
            top_k = freq_df.sort_values(by='requirements', ascending=False).head(8)
            counts = top_k['requirements']
        elif col == 'preferred':
            top_k = freq_df.sort_values(by='preferred', ascending=False).head(8)
            counts = top_k['preferred']
        else:
            top_k = freq_df.sort_values(by='requirements_preferred', ascending=False).head(8)
            counts = top_k['requirements_preferred']
            
        labels = list(top_k['keyword'])
        percentages = (counts / total_rows) * 100
        
        plt.figure(figsize=(10, 6))
        # Draw bar chart
        bars = plt.bar(labels, percentages, color='skyblue', edgecolor='black', alpha=0.8)
        
        # Add value labels on top of the bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2.0, height + 0.5, f'{height:.1f}%', ha='center', va='bottom', fontsize=10)
            
        plt.title(title, fontsize=14, fontweight='bold', pad=15)
        plt.xlabel('키워드', fontsize=12)
        plt.ylabel('비중 (%)', fontsize=12)
        plt.ylim(0, max(percentages) * 1.15)  # Leave room for labels
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        save_path = os.path.join(output_dir, filename)
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"Saved chart to {save_path}")
        
    # 3. Analyze filtered_division
    div_counter = Counter()
    for val in df['filtered_division'].dropna():
        if not isinstance(val, str):
            continue
        divisions = [d.strip() for d in val.split(',') if d.strip()]
        div_counter.update(divisions)
        
    # Convert to DataFrame
    div_data = [{'division': k, 'count': v} for k, v in div_counter.items()]
    div_df = pd.DataFrame(div_data).sort_values(by='count', ascending=False)
    
    # Save division frequencies to a CSV
    div_csv_path = os.path.join(output_dir, 'division_frequencies.csv')
    div_df.to_csv(div_csv_path, index=False, encoding='utf-8')
    print(f"Saved division frequencies to {div_csv_path}")
    
    # Save division counts to log/console
    print("\n=== Division Counts ===")
    for idx, row_div in div_df.iterrows():
        print(f"{row_div['division']}: {row_div['count']}건")
        
    # Visualizing divisions with absolute counts
    plt.figure(figsize=(12, 7))
    bars = plt.bar(div_df['division'], div_df['count'], color='salmon', edgecolor='black', alpha=0.8)
    
    # Add absolute count labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, height + 3, f'{int(height)}개', ha='center', va='bottom', fontsize=9)
        
    plt.title('직무(filtered_division)별 채용 공고 수', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('직무', fontsize=12)
    plt.ylabel('총 개수 (건)', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, max(div_df['count']) * 1.1)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    div_chart_path = os.path.join(output_dir, 'filtered_division_counts.png')
    plt.savefig(div_chart_path, dpi=300)
    plt.close()
    print(f"Saved division count chart to {div_chart_path}")

if __name__ == '__main__':
    analyze()
