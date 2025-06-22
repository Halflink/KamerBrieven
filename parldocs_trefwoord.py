import requests
import xml.etree.ElementTree as ET
import csv
import logging
import argparse
import sys
import os
from typing import List, Dict, Optional, Union

class ParliamentaryDocuments:
    SRU_ENDPOINT = "https://repository.overheid.nl/sru"

    def __init__(self, search_terms: Union[str, List[str]], max_per_page: int = 50):
        self.search_terms = [search_terms] if isinstance(search_terms, str) else search_terms
        self.max_per_page = max_per_page
        self.start_record = 1
        self.ns = {
            'sru': 'http://docs.oasis-open.org/ns/search-ws/sruResponse',
            'dcterms': 'http://purl.org/dc/terms/',
            'wetgeving': 'http://standaarden.overheid.nl/wetgeving/',
            'gzd': 'http://standaarden.overheid.nl/sru'
        }
        
        # Build OR query for multiple terms
        query_parts = [f'cql.serverChoice="{term}"' for term in self.search_terms]
        query = ' OR '.join(query_parts)
        
        self.params = {
            "operation": "searchRetrieve",
            "version": "1.2",
            "query": query,
            "maximumRecords": self.max_per_page,
            "startRecord": self.start_record
        }

    def _fetch_and_parse_xml(self) -> Optional[ET.Element]:
        """Make HTTP request to SRU endpoint and parse the XML response.

        Returns:
            ET.Element or None: The root element of the XML response if successful, None if failed
        """
        try:
            response = requests.get(self.SRU_ENDPOINT, params=self.params, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Networkerror: {e}")
            return None

        try:
            return ET.fromstring(response.content)
        except ET.ParseError as e:
            logging.error(f"XML Parse error: {e}")
            return None

    def _build_record(self, rec: ET.Element) -> Dict:
        """Build a record dictionary from an XML record element.

        Args:
            rec: XML element containing a single record

        Returns:
            Dict containing the record data with empty strings for missing fields
        """
        empty_record = {
            "identifier": "", "title": "", "type": "", "creator": "", "modified": "",
            "dossiernummer": "", "ondernummer": "", "publicatienaam": "", "vergaderjaar": ""
        }

        recorddata = rec.find("sru:recordData", self.ns)
        if recorddata is None:
            return empty_record

        # Find all fields
        fields = {
            "identifier": recorddata.find(".//dcterms:identifier", self.ns),
            "title": recorddata.find(".//dcterms:title", self.ns),
            "type": recorddata.find(".//dcterms:type", self.ns),
            "creator": recorddata.find(".//dcterms:creator", self.ns),
            "modified": recorddata.find(".//dcterms:modified", self.ns),
            "dossiernummer": recorddata.find(".//wetgeving:dossiernummer", self.ns),
            "ondernummer": recorddata.find(".//wetgeving:ondernummer", self.ns),
            "publicatienaam": recorddata.find(".//wetgeving:publicatienaam", self.ns),
            "vergaderjaar": recorddata.find(".//wetgeving:vergaderjaar", self.ns)
        }

        # Build record with data or empty strings
        record = {
            field: element.text.strip() if element is not None and element.text else ""
            for field, element in fields.items()
        }
        
        # Add PDF URL if we have an identifier
        if record["identifier"]:
            record["pdf_url"] = f"https://zoek.officielebekendmakingen.nl/{record['identifier']}.pdf"
        else:
            record["pdf_url"] = ""
            
        return record

    def _has_diagnostic_error(self, root: ET.Element) -> bool:
        """Check if the XML response contains a diagnostic error message.

        Args:
            root: The root element of the XML response

        Returns:
            bool: True if a diagnostic error was found and logged, False otherwise
        """
        diag = root.find(".//{http://docs.oasis-open.org/ns/search-ws/diagnostic}diagnostic")
        if diag is not None:
            msg = diag.findtext("{http://docs.oasis-open.org/ns/search-ws/diagnostic}message", default="Unknown error")
            details = diag.findtext("{http://docs.oasis-open.org/ns/search-ws/diagnostic}details", default="")
            logging.error(f"SRU diagnostic: {msg} ({details})")
            return True
        return False

    def fetch_records(self) -> tuple[List[Dict], List[str]]:
        """Fetch all records matching the search term.

        Returns:
            Tuple containing:
            - List of dictionaries containing the record data
            - List of PDF URLs
        """
        records = []
        pdf_urls = []
        while True:
            root = self._fetch_and_parse_xml()
            if root is None:
                break
            if self._has_diagnostic_error(root):
                break
            recs = root.findall(".//sru:record", self.ns)
            if not recs:
                break
            for rec in recs:
                record = self._build_record(rec)
                records.append(record)
                if record["pdf_url"]:
                    pdf_urls.append(record["pdf_url"])
            total = int(root.findtext(".//sru:numberOfRecords", default="0", namespaces=self.ns))
            logging.info(f"Fetched {len(records)} of {total} records (startRecord={self.start_record}, maxPerPage={self.max_per_page})")
            
            # Calculate next start record
            self.start_record += len(recs)  # Only increment by actual records received
            if self.start_record > total:  # Stop if we've processed all records
                break
                
            self.params["startRecord"] = self.start_record
        return records, pdf_urls

    def write_csv(self, records: List[Dict], csv_path: str):
        """Write records to CSV file.

        Args:
            records: List of records to write
            csv_path: Path to the output CSV file
        """
        # Remove existing CSV if it exists
        if os.path.exists(csv_path):
            os.remove(csv_path)
            logging.info(f"Removed existing file: {csv_path}")
            
        with open(csv_path, mode="w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "identifier", "title", "type", "creator", "modified",
                "dossiernummer", "ondernummer", "publicatienaam", "vergaderjaar", "pdf_url"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                writer.writerow(record)
        logging.info(f"✅ Done! {len(records)} records saved to {csv_path}")

    @classmethod
    def _set_parser(cls) -> argparse.ArgumentParser:
        """Set up the argument parser.
        
        Returns:
            ArgumentParser: Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description="Zoek parlementaire documenten via overheid.nl SRU en exporteer naar CSV."
        )
        parser.add_argument(
            "--search-terms",
            type=str,
            nargs="+",  # Accept one or more arguments
            default=["doorstroomtoets","doorstroomtoetsen"],
            help="Een of meer zoektermen voor de documenten (gescheiden door spaties)"
        )
        parser.add_argument(
            "--csv", 
            type=str, 
            default="parlementaire_documenten.csv", 
            help="Naam van het CSV-bestand"
        )
        parser.add_argument(
            "--log", 
            type=str, 
            default="INFO", 
            help="Logniveau (DEBUG, INFO, WARNING, ERROR)"
        )
        return parser
   
    @classmethod
    def main(cls):
        """Main entry point for the script.
        Sets up argument parsing, logging, and executes the search and CSV export.
        """
        parser = cls._set_parser()
        args = parser.parse_args()
        
        # Print command line arguments for debugging
        print("Command line arguments:")
        print(f"  --search-terms: {args.search_terms}")
        print(f"  --csv: {args.csv}")
        print(f"  --log: {args.log}")
        print()

        # Set up logging to both file and console
        log_file = 'parldocs.log'
        logging.basicConfig(
            level=getattr(logging, args.log.upper(), logging.INFO),
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),  # Log to file
                logging.StreamHandler()  # Log to console
            ]
        )
        logging.info(f"Starting new search session")

        try:
            logging.info(f"Fetching records via cql.serverChoice for terms: {', '.join(args.search_terms)}")
            parldocs = cls(args.search_terms)
            records, pdf_urls = parldocs.fetch_records()
            
            # Write CSV
            parldocs.write_csv(records, args.csv)
            
            # Download PDFs
            if pdf_urls:
                logging.info(f"Found {len(pdf_urls)} PDFs to download")
                from download_pdf import PDFDownloader
                downloader = PDFDownloader("downloaded_pdfs")
                downloaded = downloader.download_pdfs(pdf_urls, highlight_words=args.search_terms)
                logging.info(f"Downloaded {len(downloaded)} PDFs to {downloader.target_folder} with highlighting for: {', '.join(args.search_terms)}")
        except KeyboardInterrupt:
            print("\nInterrupted by user.")
            sys.exit(0)


if __name__ == "__main__":
    ParliamentaryDocuments.main()

