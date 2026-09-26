"""Download the EasyEDA/LCSC footprint JSON JLC uses for every LCSC part in the Q5 full-assembly BOM
into ./easyeda/ (read-only public endpoint; the cache is gitignored third-party data)."""
import csv, json, os, time, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
BOM = os.path.join(HERE, '../../procurement/q5/BOM-JLCPCB-Q5-FULL-ASSEMBLY.csv')
os.makedirs(os.path.join(HERE, 'easyeda'), exist_ok=True)
for row in csv.DictReader(open(BOM, newline='', encoding='utf-8-sig')):
    lcsc = row['LCSC Part #']
    if os.path.exists(os.path.join(HERE, 'easyeda', f'{lcsc}.json')):
        continue
    time.sleep(3)   # the endpoint answers 403 when polled quickly
    url = f'https://easyeda.com/api/products/{lcsc}/components?version=6.4.19.5'
    data = json.load(urllib.request.urlopen(url, timeout=60))
    json.dump(data, open(os.path.join(HERE, 'easyeda', f'{lcsc}.json'), 'w'))
    print(lcsc, data['result']['title'] if data.get('result') else 'NOT FOUND')
