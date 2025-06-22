import requests
import xml.etree.ElementTree as ET

url = 'https://repository.overheid.nl/sru?operation=searchRetrieve&version=1.2&query=cql.serverChoice="doorstroomtoetsen"&maximumRecords=1'
response = requests.get(url)
root = ET.fromstring(response.content)

print("Namespaces in root:")
print(root.nsmap if hasattr(root, 'nsmap') else "nsmap niet beschikbaar in ElementTree")

# Of print alle tags met namespace
for elem in root.iter():
    print(elem.tag)
