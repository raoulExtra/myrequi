def extract_lines(input_filename, output_filename, include_pattern, exclude_pattern):
    with open(input_filename, 'r') as infile:
        lines = infile.readlines()

    with open(output_filename, 'w') as outfile:
        for line in lines:
            if include_pattern in line and exclude_pattern not in line:
                outfile.write(line)