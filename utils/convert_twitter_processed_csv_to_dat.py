"""
Convert twitter-processed.csv to .dat format
- sentiment column is the target
- tokens column contains the sequence itemsets separated by -1
"""

import csv
import ast
import argparse
import sys
import random
from collections import defaultdict


def convert_twitter_processed_csv_to_dat(input_filepath, output_filepath, sample_per_class=10000, random_seed=42):
    """Convert twitter-processed.csv to .dat format with sampling per class"""
    random.seed(random_seed)
    
    print(f"Step 1: Reading from {input_filepath}...")
    
    # First pass: collect rows by sentiment class
    rows_by_class = defaultdict(list)
    error_count = 0
    total_rows = 0
    
    with open(input_filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        reader = csv.DictReader(infile)
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is header
            total_rows += 1
            try:
                # Get sentiment (target class)
                sentiment = row['sentiment'].strip()
                
                # Get tokens column and parse it (it's a string representation of a Python list)
                tokens_str = row['tokens'].strip()
                
                # Parse the string representation of the list
                try:
                    tokens = ast.literal_eval(tokens_str)
                except (ValueError, SyntaxError) as e:
                    print(f"Warning: Could not parse tokens on line {row_num}: {e}", file=sys.stderr)
                    error_count += 1
                    continue
                
                # Filter out empty tokens and whitespace-only tokens, and replace Twitter handles with USER
                processed_tokens = []
                for token in tokens:
                    token_str = str(token).strip()
                    if token_str:
                        # Replace Twitter handles (starting with @) with USER
                        if token_str.startswith('@'):
                            processed_tokens.append('USER')
                        else:
                            processed_tokens.append(token_str)
                
                tokens = processed_tokens
                
                # Skip if no valid tokens
                if not tokens:
                    continue
                
                # Store the row data
                rows_by_class[sentiment].append((sentiment, tokens))
                
                # Progress indicator
                if total_rows % 100000 == 0:
                    print(f"  Read {total_rows} rows...", file=sys.stderr)
                    
            except KeyError as e:
                print(f"Error: Missing column on line {row_num}: {e}", file=sys.stderr)
                error_count += 1
                continue
            except Exception as e:
                print(f"Error processing line {row_num}: {e}", file=sys.stderr)
                error_count += 1
                continue
    
    print(f"  Total rows read: {total_rows}")
    print(f"  Rows by class:")
    for cls in sorted(rows_by_class.keys()):
        print(f"    Class {cls}: {len(rows_by_class[cls])} rows")
    
    # Sample rows from each class
    print(f"\nStep 2: Sampling up to {sample_per_class} rows per class...")
    sampled_rows = []
    
    for cls in sorted(rows_by_class.keys()):
        class_rows = rows_by_class[cls]
        if len(class_rows) > sample_per_class:
            sampled = random.sample(class_rows, sample_per_class)
            print(f"  Class {cls}: sampled {len(sampled)} from {len(class_rows)}")
        else:
            sampled = class_rows
            print(f"  Class {cls}: using all {len(class_rows)} (less than {sample_per_class})")
        
        sampled_rows.extend(sampled)
    
    # Shuffle the sampled rows
    random.shuffle(sampled_rows)
    print(f"  Total sampled rows: {len(sampled_rows)}")
    
    # Second pass: write sampled rows to output file
    print(f"\nStep 3: Writing sequences to {output_filepath}...")
    processed_count = 0
    
    with open(output_filepath, 'w', encoding='utf-8') as outfile:
        for sentiment, tokens in sampled_rows:
            # Format: <sentiment> <token1> -1 <token2> -1 ... -2
            seq_str = f"{sentiment} {' -1 '.join(tokens)} -2"
            outfile.write(seq_str + '\n')
            processed_count += 1
            
            # Progress indicator
            if processed_count % 10000 == 0:
                print(f"  Written {processed_count} sequences...", file=sys.stderr)
    
    print(f"\nConversion complete!")
    print(f"Sequences written: {processed_count}")
    if error_count > 0:
        print(f"Errors encountered: {error_count}")
    print(f"Output written to {output_filepath}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert twitter-processed.csv to DAT format.")
    parser.add_argument("input_csv_file", help="Path to the input CSV file (twitter-processed.csv).")
    parser.add_argument("-o", "--output_file", help="Path to the output DAT file.", default=None)
    parser.add_argument("-s", "--sample", type=int, default=10000, 
                        help="Number of rows to sample per class (default: 10000)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for sampling (default: 42)")
    args = parser.parse_args()
    
    output_file = args.output_file if args.output_file else args.input_csv_file.replace('.csv', '.dat')
    convert_twitter_processed_csv_to_dat(args.input_csv_file, output_file, 
                                        sample_per_class=args.sample, 
                                        random_seed=args.seed)

