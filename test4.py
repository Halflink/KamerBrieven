import requests
import xml.etree.ElementTree as ET
import csv
import logging
import argparse
import sys
from typing import List, Dict

SRU_ENDPOINT = "https://repository.overheid.nl/sru"

def fetch_records_for_index(zoekterm: str, max_per_page: int = 50) -> List[Dict]:
    records = []
    start_record = 1
    ns = {
        'sru': 'http://docs.oasis-open.org/ns/search-ws/sruResponse',
        'dcterms': 'http://purl.org/dc/terms/',
        'overheidwetgeving': 'https://standaarden.overheid.nl/owms/terms/'
    }

    while True:
        params = {
            "operation": "searchRetrieve",
            "version": "1.2",
            "query": f'cql.serverChoice="{zoekterm}"',
            "maximumRecords": max_per_page,
            "startRecord": start_record
        }
        try:
            response = requests.get(SRU_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Netwerkfout: {e}")
            break

        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            logging.error(f"XML Parse-fout: {e}")
            break

        diag = root.find(".//{http://docs.oasis-open.org/ns/search-ws/diagnostic}diagnostic")
        if diag is not None:
            msg = diag.findtext("{http://docs.oasis-open.org/ns/search-ws/diagnostic}message", default="Onbekende fout")
            details = diag.findtext("{http://docs.oasis-open.org/ns/search-ws/diagnostic}details", default="")
            logging.error(f"SRU-diagnose: {msg} ({details})")
            break

        recs = root.findall(".//sru:record", ns)
        if not recs:
            break

        for rec in recs:
            recorddata = rec.find("sru:recordData", ns)
            if recorddata is not None:
                identifier = recorddata.find(".//dcterms:identifier", ns)
                title = recorddata.find(".//dcterms:title", ns)
                type_ = recorddata.find(".//dcterms:type", ns)
                creator = recorddata.find(".//dcterms:creator", ns)
                modified = recorddata.find(".//dcterms:modified", ns)
                dossiernummer = recorddata.find(".//overheidwetgeving:dossiernummer", ns)
                ondernummer = recorddata.find(".//overheidwetgeving:ondernummer", ns)
                publicatienaam = recorddata.find(".//overheidwetgeving:publicatienaam", ns)
                vergaderjaar = recorddata.find(".//overheidwetgeving:vergaderjaar", ns)

                records.append({
                    "identifier": identifier.text.strip() if identifier is not None and identifier.text else "",
                    "title": title.text.strip() if title is not None and title.text else "",
                    "type": type_.text.strip() if type_ is not None and type_.text else "",
                    "creator": creator.text.strip() if creator is not None and creator.text else "",
                    "modified": modified.text.strip() if modified is not None and modified.text else "",
                    "dossiernummer": dossiernummer.text.strip() if dossiernummer is not None and dossiernummer.text else "",
                    "ondernummer": ondernummer.text.strip() if ondernummer is not None and ondernummer.text else "",
                    "publicatienaam": publicatienaam.text.strip() if publicatienaam is not None and publicatienaam.text else "",
                    "vergaderjaar": vergaderjaar.text.strip() if vergaderjaar is not None and vergaderjaar.text else ""
                })
            else:
                records.append({
                    "identifier": "", "title": "", "type": "", "creator": "", "modified": "",
                    "dossiernummer": "", "ondernummer": "", "publicatienaam": "", "vergaderjaar": ""
                })

        total = int(root.findtext(".//sru:numberOfRecords", default="0", namespaces=ns))
        if start_record + max_per_page > total:
            break
        start_record += max_per_page

    return records

def schrijf_csv(records: List[Dict], csv_path: str):
    with open(csv_path, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "identifier", "title", "type", "creator", "modified",
            "dossiernummer", "ondernummer", "publicatienaam", "vergaderjaar"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record)

def main():
    parser = argparse.ArgumentParser(description="Zoek parlementaire documenten via overheid.nl SRU en exporteer naar CSV.")
    parser.add_argument("--zoekterm", type=str, default="doorstroomtoetsen", help="Zoekterm voor de documenten")
    parser.add_argument("--csv", type=str, default="parlementaire_documenten.csv", help="Naam van het CSV-bestand")
    parser.add_argument("--log", type=str, default="INFO", help="Logniveau (DEBUG, INFO, WARNING, ERROR)")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log.upper(), logging.INFO),
        format='%(levelname)s: %(message)s'
    )

    logging.info(f"Ophalen records via cql.serverChoice...")
    records = fetch_records_for_index(args.zoekterm)
    if records:
        logging.info(f"Gevonden {len(records)} records.")
    else:
        logging.info("Geen resultaten gevonden.")

    schrijf_csv(records, args.csv)
    logging.info(f"\n✅ Klaar! {len(records)} records opgeslagen in {args.csv}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAfgebroken door gebruiker.")
        sys.exit(0)
