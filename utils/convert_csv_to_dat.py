import csv
import argparse
import sys


def convert_csv_to_dat(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        reader = csv.DictReader(infile)
        
        for row in reader:
            sequence = row['sequence'].strip()
            class_label = row['class'].strip()
            
            if not sequence:
                continue
            
            output_line = f"{class_label}"
            
            for char in sequence:
                if char.strip():
                    output_line += f" {char} -1"
            
            output_line += " -2\n"
            
            outfile.write(output_line)
    
    print(f"Conversion complete! Output written to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert CSV file with sequence,class,species to .dat format'
    )
    parser.add_argument(
        'input_file',
        help='Path to input CSV file'
    )
    args = parser.parse_args()

    if args.input_file.endswith('.csv'):
        output_file = args.input_file[:-4] + '.dat'
    else:
        output_file = args.input_file + '.dat'

    try:
        convert_csv_to_dat(args.input_file, output_file)
    except:
        sys.exit(1)


if __name__ == '__main__':
    main()

