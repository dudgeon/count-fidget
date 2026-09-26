"""Download the EasyEDA/LCSC footprint JSON JLC uses for every LCSC part in the Q5 full-assembly BOM
into ./easyeda/ (read-only public endpoint; the cache is gitignored third-party data).
The endpoint answers 403 to rapid or non-browser requests, so this uses curl with pauses and retries."""
import csv, json, os, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__))
BOM = os.path.join(HERE, '../../procurement/q5/BOM-JLCPCB-Q5-FULL-ASSEMBLY.csv')
os.makedirs(os.path.join(HERE, 'easyeda'), exist_ok=True)
for row in csv.DictReader(open(BOM, newline='', encoding='utf-8-sig')):
    lcsc = row['LCSC Part #']
    path = os.path.join(HERE, 'easyeda', f'{lcsc}.json')
    if os.path.exists(path):
        continue
    url = f'https://easyeda.com/api/products/{lcsc}/components?version=6.4.19.5'
    for attempt in range(6):
        time.sleep(3 + 10 * attempt)
        r = subprocess.run(['curl', '-s', '--max-time', '60', '-w', '\n%{http_code}', url], capture_output=True, text=True)
        body, _, code = r.stdout.rpartition('\n')
        if code == '200':
            data = json.loads(body)
            json.dump(data, open(path, 'w'))
            print(lcsc, data['result']['title'] if data.get('result') else 'NOT FOUND')
            break
    else:
        raise SystemExit(f'{lcsc}: EasyEDA endpoint kept refusing (HTTP {code})')
