import csv

input_file_name = "log.mu2e.ensembleMDS2b.MDC2020az.001201_00000000.log"  # Replace with the actual name of your input file
output_file_name = "extracted_data.txt"
output_csv_file_name = "output_data.csv"

start_marker = "Dataset        Counts"
end_marker = "Total"

extracting = False  # A flag to indicate whether we are currently extracting lines
extracted_lines = []

# First extract the lines we want from the log files:
try:
    with open(input_file_name, 'r') as input_file:
        for line in input_file:
            if start_marker in line:
                extracting = True  # Start extracting when the start marker is found

            if extracting:
                extracted_lines.append(line.strip()) # Add the current line to the list

            if end_marker in line and extracting: # Check if the end marker is found and we are extracting
                extracting = False # Stop extracting when the end marker is found
                # If you want to include the line with the end_marker itself, you're done.
                # If you want to *exclude* the end_marker, then you would need to adjust the logic to only append lines *before* encountering it.

except FileNotFoundError:
    print(f"Error: The file '{input_file_name}' was not found.")
else:
    if extracted_lines:
        with open(output_file_name, "a") as output_file:
            for line in extracted_lines:
                output_file.write(line + "\n")
        print(f"The lines from '{start_marker}' to '{end_marker}' were extracted and added to '{output_file_name}'.")
    else:
        print(f"The block of text between '{start_marker}' and '{end_marker}' was not found in '{input_file_name}'.")


# Now tranfer what we need to the csv
# Manually define the header since it's a bit tricky to parse automatically
header = ["Dataset", "Counts", "fraction_sampled", "fraction_expected", "weight"]

data_lines = []
try:
    with open(output_file_name, 'r') as input_file:
        lines = input_file.readlines() # Read all lines into a list
        
        # Find the start and end of the table data
        # Skip header and separator line
        start_index = 2 
        # Find the index of the "Total" line to determine the end of the data rows
        end_index = -1
        for i, line in enumerate(lines):
            if "Total" in line:
                end_index = i
                break
        
        # Extract only the data lines from the table
        if end_index != -1:
            data_lines = [line.strip() for line in lines[start_index:end_index] if line.strip()]
        else:
            print("Warning: 'Total' line not found, processing all lines after header.")
            data_lines = [line.strip() for line in lines[start_index:] if line.strip()]

except FileNotFoundError:
    print(f"Error: The file '{output_file_name}' was not found.")
    exit() # Exit if the input file isn't found

with open(output_csv_file_name, 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile)

    # Write the header row
    csv_writer.writerow(header)

    # Write the data rows
    
    for line in data_lines:
        
        # Split the line by whitespace
        row_data = line.split()
        if(len(row_data) > 6 ):
          # Reconstruct the row for CSV
          cleaned_row = []
          print(row_data)
          cleaned_row.append(row_data[0]) # Dataset
          cleaned_row.append(row_data[1]) # Counts
          cleaned_row.append(row_data[2]) # fraction_sampled
          cleaned_row.append(row_data[4]) # fraction_expected (skip '|' and first fraction of the second block)
          cleaned_row.append(row_data[5]) # weight

          # The 'Next event' column might have multiple words
          #next_event_data = " ".join(row_data[6:])
          #cleaned_row.append(next_event_data)
          
          csv_writer.writerow(cleaned_row)

print(f"Data has been written to {output_csv_file_name}")

