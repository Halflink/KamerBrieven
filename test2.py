import requests
import xml.etree.ElementTree as ET
import csv

SRU_ENDPOINT = "https://repository.overheid.nl/sru"

def fetch_records_for_index(doc_type, zoekterm, index, max_per_page=50):
    """
    Haalt alle records op voor één CQL-index (bv. cql.serverChoice of dc.title)
    """
    records = []
    start_record = 1

    while True:
        params = {
            "operation": "searchRetrieve",
            "version": "1.2",
            "query": f'{index}="{zoekterm}" and type="{doc_type}"',
            "maximumRecords": max_per_page,
            "startRecord": start_record
        }
        response = requests.get(SRU_ENDPOINT, params=params)
        if response.status_code != 200:
            print(f"  ⚠️ Fout bij {doc_type} / {index}: {response.status_code}")
            break

        root = ET.fromstring(response.content)
        recs = root.findall(".//record")
        if not recs:
            break

        # Process records
        for rec in recs:
            title = rec.find(".//{http://purl.org/dc/elements/1.1/}title")
            identifier = rec.find(".//{http://purl.org/dc/elements/1.1/}identifier")
            date = rec.find(".//{http://purl.org/dc/elements/1.1/}date")
            records.append({
                "type":       doc_type,
                "title":      title.text       if title is not None       else "",
                "identifier": identifier.text  if identifier is not None  else "",
                "date":       date.text        if date is not None        else ""
            })

        # Pagination
        total = int(root.findtext(".//numberOfRecords", default="0"))
        if start_record + max_per_page > total:
            break
        start_record += max_per_page

    return records

def fetch_records(doc_type, zoekterm):
    """
    Probeer eerst met serverChoice, valt terug op dc.title als er geen resultaten zijn.
    """
    # Probeer full-text serverChoice
    for index in ["cql.serverChoice", "dc.title"]:
        print(f"Ophalen {doc_type} via index {index}...", end="")
        recs = fetch_records_for_index(doc_type, zoekterm, index)
        if recs:
            print(f" gevonden {len(recs)} records.")
            return recs
        print(" geen resultaten.")
    return []

def main():
    document_types = ["KST", "HAN", "MOT", "AMEN"]
    zoekterm = "doorstroomtoetsen"
    all_records = []

    for doc_type in document_types:
        print(f"\n=== Documenttype: {doc_type} ===")
        recs = fetch_records(doc_type, zoekterm)
        all_records.extend(recs)

    # Schrijf alles naar CSV
    csv_path = "parlementaire_documenten.csv"
    with open(csv_path, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["type", "title", "identifier", "date"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for record in all_records:
            writer.writerow(record)

    print(f"\n✅ Klaar! {len(all_records)} records opgeslagen in {csv_path}")

if __name__ == "__main__":
    main()
