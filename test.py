import requests
import xml.etree.ElementTree as ET
import csv

def fetch_records(doc_type, zoekterm, max_per_page=50):
    start_record = 1
    records = []

    while True:
        params = {
            "operation": "searchRetrieve",
            "version": "1.2",
            "query": f'type="{doc_type}" and all="{zoekterm}"',
            "maximumRecords": max_per_page,
            "startRecord": start_record
        }
        response = requests.get("https://repository.overheid.nl/sru", params=params)
        if response.status_code != 200:
            print(f"Fout bij ophalen records {doc_type}: {response.status_code}")
            break

        root = ET.fromstring(response.content)
        recs = root.findall(".//record")
        if not recs:
            break

        for record in recs:
            title = record.find(".//{http://purl.org/dc/elements/1.1/}title")
            identifier = record.find(".//{http://purl.org/dc/elements/1.1/}identifier")
            date = record.find(".//{http://purl.org/dc/elements/1.1/}date")

            records.append({
                "type": doc_type,
                "title": title.text if title is not None else "",
                "identifier": identifier.text if identifier is not None else "",
                "date": date.text if date is not None else ""
            })

        number_of_records = int(root.findtext(".//numberOfRecords", default="0"))
        if start_record + max_per_page > number_of_records:
            break
        else:
            start_record += max_per_page

    return records

def main():
    document_types = ["KST", "HAN", "MOT", "AMEN"]
    zoekterm = "doorstroomtoetsen"

    all_records = []

    for doc_type in document_types:
        print(f"Ophalen van records voor type {doc_type}...")
        records = fetch_records(doc_type, zoekterm)
        all_records.extend(records)

    with open("parlementaire_documenten.csv", mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["type", "title", "identifier", "date"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for record in all_records:
            writer.writerow(record)

    print(f"Klaar! {len(all_records)} records opgeslagen in parlementaire_documenten.csv")

if __name__ == "__main__":
    main()
