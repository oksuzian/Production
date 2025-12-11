## 🐍 Python Script Documentation: Log File Data Extractor `logchecker.py`

### **1. Overview**

This script automates the process of extracting tabular data blocks from multiple log files, combining the extracted information into a temporary text file, and then parsing that text file into a clean CSV format for easy import into spreadsheets or analytical tools. It is used to validate the out put of the ensembling process.

| Component | Description |
| :--- | :--- |
| **Purpose** | To efficiently gather structured event count or dataset summary tables embedded between specific markers in `.log` files and convert them into CSV format. |
| **Input** | Multiple `.log` files located in the fixed subdirectory `"logs"`. |
| **Output** | 1. `extracted_data.txt` (Temporary combined text file). <br> 2. `output_data.csv` (Final structured data file). |
| **Dependencies** | `csv`, `os` (Standard Python library modules). |

### **2. Configuration & Markers**

The script relies on fixed variables to locate input files and define the boundaries of the data block to be extracted.

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `log_directory` | `"logs"` | The subdirectory scanned for input files. |
| `start_marker` | `"Dataset         Counts"` | The line that signals the *beginning* of the data block. |
| `end_marker` | `"Total"` | The line that signals the *end* of the data block. |
| `output_file_name` | `"extracted_data.txt"` | Temporary file storing all raw extracted text. |
| `output_csv_file_name` | `"output_data.csv"` | The final output file ready for analysis. |

### **3. Execution Flow: Part 1 - Text Extraction**

This phase iterates through all log files and compiles the relevant blocks into a single text file.

1.  **File Iteration:** The script uses `os.listdir(log_directory)` to loop through all files in the designated directory and processes only those ending with `.log`.
2.  **Extraction Flag:** A boolean flag, `extracting`, is toggled when the `start_marker` is found.
3.  **Line Collection:** All lines read while `extracting` is `True` are appended to `all_extracted_lines`.
4.  **Extraction Stop:** The `extracting` flag is toggled back to `False` when the `end_marker` (`"Total"`) is found, completing the block capture. 
5.  **Output to Text File:** All collected lines are written sequentially to the temporary file, `extracted_data.txt`, with an `EOF` marker appended at the very end for later parsing reference.

### **4. Execution Flow: Part 2 - CSV Conversion**

This phase reads the temporary text file and converts the structured text into a comma-separated format.

1.  **Read Temporary File:** `extracted_data.txt` is read line by line.
2.  **Data Isolation:** The script assumes the raw data starts at index `2` (skipping the header marker and a separator line) and ends just before the `EOF` marker.
3.  **Header Definition:** A manual header is defined for the CSV:
    ```python
    header = ["Dataset", "Counts", "fraction_sampled", "fraction_expected", "weight"]
    ```
4.  **Line Parsing and Splitting:**
    * Each data line is split using whitespace (`line.split()`) into `row_data`.
    * A check ensures the line is a valid data row (i.e., `len(row_data) > 6` and the first element is not the header `Dataset`).
    * **Column Selection:** The script selectively chooses indices from the split list, implicitly handling complex table formatting where column data might be misaligned:
        * `row_data[0]`: `Dataset`
        * `row_data[1]`: `Counts`
        * `row_data[2]`: `fraction_sampled`
        * `row_data[4]`: `fraction_expected` (Note: skips index `3`, which is typically a separator character like `|`).
        * `row_data[5]`: `weight`
5.  **CSV Writing:** The cleaned and reordered `cleaned_row` is written to `output_data.csv` using the `csv.writer`.

## Plotting the outcomes

The `plot_log_stats.py` script is used to produce plots of the selected sampling means. Edit the list of expected means to reflect what was in the original SamplingInput .fcl file. The distributions should be centered on the means.
