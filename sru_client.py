import requests
from lxml import etree

# Namespace dictionary for overheid.nl SRU endpoint
NS = {
    'srw': 'http://docs.oasis-open.org/ns/search-ws/sruResponse',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
    'owms': 'http://standaarden.overheid.nl/owms/terms/',
    'w': 'http://standaarden.overheid.nl/wetgeving/',
    'ot': 'http://standaarden.overheid.nl/owms/terms/'
}

SRU_BASE_URL = "https://repository.overheid.nl/sru"

class SRUClient:
    """
    Client for querying the overheid.nl SRU endpoint for 'bekendmakingen'.
    """
    def __init__(self, base_url=SRU_BASE_URL):
        self.base_url = base_url

    def get_bekendmakingen(self, authority, max_records=30):
        """
        Fetches 'bekendmakingen' for a given authority.
        Returns a list of dictionaries with key fields.
        """
        cql = f'owms.authority="{authority}"'
        params = {
            "operation": "searchRetrieve",
            "query": cql,
            "maximumRecords": max_records,
            "sortKeys": "dcterms.modified/descending"
        }
        try:
            resp = requests.get(self.base_url, params=params, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []
        try:
            tree = etree.fromstring(resp.content)
        except Exception as e:
            print(f"Error parsing XML: {e}")
            print(resp.text)
            return []
        records = tree.findall('.//srw:record', namespaces=NS)
        def extract(record, xpath):
            el = record.find(xpath, namespaces=NS)
            return el.text if el is not None else None
        results = []
        for record in records:
            results.append({
                "title": extract(record, './/dcterms:title') or extract(record, './/dc:title'),
                "identifier": extract(record, './/dcterms:identifier') or extract(record, './/dc:identifier'),
                "date": extract(record, './/dcterms:modified') or extract(record, './/dcterms:date'),
                "type": extract(record, './/dcterms:type') or extract(record, './/dc:type'),
                "authority": extract(record, './/owms:authority'),
                "subject": extract(record, './/dcterms:subject'),
                "kamercommissie": extract(record, './/w:kamercommissie')
            })
        return results

if __name__ == "__main__":
    client = SRUClient()
    # Fetch 30 records for Ministerie van Onderwijs, Cultuur en Wetenschap
    # Fetch 30 records for Ministerie van Onderwijs, Cultuur en Wetenschap using ot.authority
    from_date = "2023-09-18"
    cql = f'ot.authority="Ministerie van Onderwijs, Cultuur en Wetenschap"'
    params = {
        "operation": "searchRetrieve",
        "query": cql,
        "maximumRecords": 30,
        "sortKeys": "w.datumNotificatie/descending"
    }
    try:
        resp = requests.get(SRU_BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        tree = etree.fromstring(resp.content)
        records = tree.findall('.//srw:record', namespaces=NS)
        results = []
        for record in records:
            meta = record.find('.//gzd:originalData/overheidwetgeving:meta', namespaces={**NS, 'gzd': 'http://standaarden.overheid.nl/sru', 'overheidwetgeving': 'http://standaarden.overheid.nl/wetgeving/'})
            if meta is not None:
                def extract(xpath, ns_extra={}):
                    el = meta.find(xpath, namespaces={**NS, **ns_extra})
                    return el.text if el is not None else None
                results.append({
                    "title": extract('.//dcterms:title'),
                    "identifier": extract('.//dcterms:identifier'),
                    "date": extract('.//dcterms:modified') or extract('.//dcterms:date'),
                    "type": extract('.//dcterms:type'),
                    "authority": extract('.//ot:authority', {'ot': 'http://standaarden.overheid.nl/owms/terms/'}),
                    "subject": extract('.//dcterms:subject'),
                    "kamercommissie": extract('.//w:kamercommissie', {'w': 'http://standaarden.overheid.nl/wetgeving/'})
                })
        if results:
            print(f"Fetched {len(results)} records for 'Ministerie van Onderwijs, Cultuur en Wetenschap' since {from_date}:\n")
            print("{:<3} {:<40} {:<18} {:<12} {:<20} {:<20} {:<20}".format(
                "#", "Title", "Identifier", "Date", "Type", "Authority", "Subject"))
            for idx, item in enumerate(results, 1):
                print("{:<3} {:<40} {:<18} {:<12} {:<20} {:<20} {:<20}".format(
                    idx,
                    (item['title'] or '')[:38],
                    (item['identifier'] or '')[:16],
                    (item['date'] or '')[:10],
                    (item['type'] or '')[:18],
                    (item['authority'] or '')[:18],
                    (item['subject'] or '')[:18]
                ))
            # Write RIS file
            with open("bekendmaking.ris", "w", encoding="utf-8") as risf:
                for item in results:
                    risf.write("TY  - GEN\n")  # Generic type, adjust if you want a more specific RIS type
                    if item['title']:
                        risf.write(f"TI  - {item['title']}\n")
                    if item['authority']:
                        risf.write(f"AU  - {item['authority']}\n")
                    if item['date']:
                        risf.write(f"PY  - {item['date'][:4]}\n")
                        risf.write(f"DA  - {item['date']}\n")
                    if item['type']:
                        risf.write(f"T2  - {item['type']}\n")
                    if item['subject']:
                        risf.write(f"KW  - {item['subject']}\n")
                    if item['identifier']:
                        risf.write(f"ID  - {item['identifier']}\n")
                    if item['kamercommissie']:
                        risf.write(f"N1  - Kamercommissie: {item['kamercommissie']}\n")
                    risf.write("ER  -\n\n")
            print(f"\nWrote RIS records to bekendmaking.ris (since {from_date})\n")
        else:
            print(f"No records found for Ministerie van Onderwijs, Cultuur en Wetenschap since {from_date}.")
    except Exception as e:
        print(f"Error fetching or parsing records: {e}")
