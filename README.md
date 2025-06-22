# KamerBrieven

A Python toolkit for working with Dutch parliamentary documents from overheid.nl. It includes functionality to search, download, and process official publications from the 'Ministerie van Onderwijs, Cultuur en Wetenschap'.

## Features

- Search parliamentary documents using multiple keywords via the SRU API
- Export search results to CSV with document metadata
- Automatic PDF downloading with search term highlighting
- Detailed logging of all operations for tracking and debugging

## How To Use This Project

### 1. Install Python
This project requires Python 3.10 or newer.

#### Windows Installation:
1. Download Python from the [official website](https://www.python.org/downloads/)
2. Run the installer
3. **Important**: Check the box that says "Add Python to PATH" during installation
4. Open Command Prompt and verify the installation:
   ```cmd
   python --version
   pip --version
   ```

### 2. Clone the Repository

#### Windows using Git Bash:
```sh
git clone https://github.com/Halflink/KamerBrieven.git
cd KamerBrieven
```

#### Windows using Command Prompt:
```cmd
git clone https://github.com/Halflink/KamerBrieven.git
cd KamerBrieven
```

### 3. Create and Activate a Virtual Environment

#### Windows Command Prompt:
```cmd
python -m venv .venv
.venv\Scripts\activate
```

#### Windows PowerShell:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### Git Bash on Windows:
```sh
python -m venv .venv
source .venv/Scripts/activate
```

### 4. Install Requirements

#### Windows (all shells):
```sh
pip install -r requirements.txt
```

If you get SSL errors, try:
```sh
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### 5. Search for Documents and Download PDFs
Search for parliamentary documents using keywords and automatically download and highlight PDFs:

```sh
# Run with default settings (searches for "doorstroomtoets" and "doorstroomtoetsen")
python parldocs_trefwoord.py

# Search with a single term
python parldocs_trefwoord.py --search-terms "examens"

# Search with multiple terms (will highlight all terms in PDFs)
python parldocs_trefwoord.py --search-terms "examens" "toetsen"

# Specify output CSV and log level
python parldocs_trefwoord.py --search-terms "examens" --csv "my_results.csv" --log DEBUG
```

Options:
- `--search-terms`: One or more keywords to search for in documents (space-separated). Default: ["doorstroomtoets", "doorstroomtoetsen"]
- `--csv`: Output CSV filename (default: parlementaire_documenten.csv)
- `--log`: Logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO

The script will:
1. Search for documents containing any of the search terms
2. Export metadata to CSV
3. Download PDFs to `downloaded_pdfs/` directory
4. Create highlighted versions of PDFs with search terms marked in yellow

Highlighted PDFs will be saved with the prefix `highlighted_` in the same directory.

## Output Files

- **CSV file**: Contains document metadata including:
  - Identifier
  - Title
  - Type
  - Creator
  - Modified date
  - Dossier number
  - PDF URL
- **PDF files**: Downloaded documents in PDF format
- **Log files**: 
  - `parldocs.log`: Search operation logs
  - `pdf_downloads.log`: PDF download operation logs

## Customization

- Modify search parameters in `parldocs_trefwoord.py`
- Adjust PDF download settings in `download_pdf.py`
- Configure logging levels via command line arguments

---

If you have any issues or questions, please open an issue or contact the maintainer.

## testgit 