# KamerBrieven

A Python client for querying the overheid.nl SRU endpoint to retrieve and process official publications (bekendmakingen) from the 'Ministerie van Onderwijs, Cultuur en Wetenschap'.

## How To Use This Project

### 1. Install Python
This project requires Python 3.10 or newer. Download and install Python from the [official website](https://www.python.org/downloads/) if you don't have it yet.

### 2. Clone the Repository
```sh
git clone <repository-url>
cd KamerBrieven
```

### 3. Create and Activate a Virtual Environment (Recommended)
```sh
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 4. Install Requirements
```sh
pip install -r requirements.txt
```

### 5. Run the SRU Client
```sh
python sru_client.py
```

The script will fetch the latest publications for the specified ministry, print a summary table, and save the results in RIS format to `bekendmaking.ris`.

## Output
- **bekendmaking.ris**: Bibliographic records in RIS format, suitable for import into reference managers.

## Customization
- You can edit `sru_client.py` to change the ministry, date range, or output fields as needed.

---

If you have any issues or questions, please open an issue or contact the maintainer.

## testgit 