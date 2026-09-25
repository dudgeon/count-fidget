"""Read-only public stock screen for the exact Q5 fitted BOM (quote pause: no vendor contact).

Queries JLCPCB's public parts search for every fitted MPN/catalog code in the
Q5 model and LCSC's public product API for the loose home-completion parts
(DS1 module, the two switches and the separate seven-pin header). Writes
procurement/q5/stock.json bound to the exact model hash. Observations are
timestamped, unreserved catalog states - not allocations, quotes or purchases.
"""
import hashlib
import json
import math
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'electronics/q5/netlist-Q5.json'
OUT = ROOT / 'procurement/q5/stock.json'
HEADER = dict(mpn='PZ254V-11-07P', jlc_part='C492406', manufacturer='XFCN')
JLC = 'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'


def curl(args):
    for attempt in range(4):
        r = subprocess.run(['curl', '-sS', '--max-time', '60', *args], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip().startswith('{'):
            return json.loads(r.stdout)
        time.sleep(2 ** attempt)
    raise RuntimeError('catalog request failed: ' + ' '.join(args[-1:]))


def now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def jlc(code):
    body = json.dumps({'keyword': code, 'currentPage': 1, 'pageSize': 5, 'searchSource': 'search'})
    data = curl(['-X', 'POST', JLC, '-H', 'Content-Type: application/json', '-H', 'User-Agent: Mozilla/5.0', '-d', body])
    rows = [c for c in (data.get('data') or {}).get('componentPageInfo', {}).get('list', []) or [] if c.get('componentCode') == code]
    if len(rows) != 1:
        raise RuntimeError(f'JLC catalog code {code} not uniquely found')
    c = rows[0]
    prices = c.get('componentPrices') or []
    def price(q):
        return next((p['productPrice'] for p in prices if p['startNumber'] <= q and (p['endNumber'] == -1 or q <= p['endNumber'])), None)
    return dict(jlc_part=code, mpn=c.get('componentModelEn'), observed_at=now(), source=f'https://jlcpcb.com/partdetail/{code}',
                method='JLCPCB public parts-search API (read-only)', library_type=c.get('componentLibraryType'),
                in_stock=c.get('stockCount'), available_order_quantity=c.get('stockCount'),
                minimum_order=max(1, c.get('minPurchaseNum') or 1), unit_price_usd_at_1=price(1), unit_price_usd_at_10=price(10))


def lcsc(code):
    data = curl(['-A', 'Mozilla/5.0', f'https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={code}'])
    r = data['result']
    ladder = r.get('productPriceList') or []
    def price(q):
        rows = [p for p in ladder if p['ladder'] <= q]
        return rows[-1]['usdPrice'] if rows else None
    return dict(lcsc_part=code, mpn=r['productModel'], observed_at=now(), source=f'https://www.lcsc.com/product-detail/{code}.html',
                method='LCSC public product API (read-only)', in_stock=r['stockNumber'],
                minimum_order=r.get('minBuyNumber') or 1, order_multiple=r.get('minPacketNumber') or 1,
                unit_price_usd_at_1=price(1) if (r.get('minBuyNumber') or 1) <= 1 else None, unit_price_usd_at_10=price(10))


def fitted_identity_digest(fitted):
    fields = ('ref', 'mpn', 'lcsc', 'manufacturer', 'assembly')
    ids = [{f: p[f] for f in fields} for p in sorted(fitted, key=lambda p: p['ref'])]
    return hashlib.sha256(json.dumps(ids, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def main():
    model = json.loads(MODEL.read_text())
    fitted = sorted((p for p in model['parts'] if p['assembly'] != 'pcb_feature'), key=lambda p: p['ref'])
    groups = defaultdict(list)
    for p in fitted:
        groups[(p['mpn'], p['lcsc'])].append(p)
    observations, screen = [], []
    for (mpn, code), parts in sorted(groups.items()):
        o = jlc(code)
        if o['mpn'] != mpn:
            raise RuntimeError(f'{code}: catalog MPN {o["mpn"]} differs from model {mpn}')
        observations.append(o)
        need = 10 * len(parts); spares = max(2, math.ceil(need / 10))
        screen.append(dict(mpn=mpn, jlc_part=code, references=sorted(p['ref'] for p in parts), fitted_per_board=len(parts),
                           assembly_roles=dict(Counter(p['assembly'] for p in parts)), quantity_for_10=need,
                           screening_attrition=spares, screening_required_quantity=need + spares,
                           available_order_quantity=o['available_order_quantity'], minimum_order=o['minimum_order'],
                           library_type=o['library_type'], observed_at=o['observed_at'],
                           passes_stock_screen=o['available_order_quantity'] >= max(need + spares, o['minimum_order'])))
    h = jlc(HEADER['jlc_part'])
    observations.append(h)
    separate = [dict(mpn=HEADER['mpn'], jlc_part=HEADER['jlc_part'], role='Separate stacked OLED interposer header; one per board',
                     quantity_for_10=10, screening_attrition=2, screening_required_quantity=12,
                     available_order_quantity=h['available_order_quantity'], minimum_order=h['minimum_order'],
                     passes_stock_screen=h['available_order_quantity'] >= 12)]
    retail = []
    home = defaultdict(list)
    for p in fitted:
        if p['assembly'] == 'home_through_hole':
            home[(p['mpn'], p['lcsc'])].append(p['ref'])
    home[(HEADER['mpn'], HEADER['jlc_part'])] = ['DS1-INTERPOSER']
    for (mpn, code), refs in sorted(home.items()):
        r = lcsc(code)
        need = 10 * len(refs); spares = max(2, math.ceil(need / 10))
        rounded = math.ceil(max(need + spares, r['minimum_order']) / r['order_multiple']) * r['order_multiple']
        r.update(references=sorted(refs), quantity_per_board=len(refs), quantity_for_10=need, screening_spares=spares,
                 rounded_screening_quantity=rounded, passes_retail_stock_screen=r['in_stock'] >= rounded)
        retail.append(r)
    roles = Counter(p['assembly'] for p in model['parts'])
    record = dict(schema_version=1, record_status='current_Q5_model_fitted_BOM_screen_complete',
                  scope='Read-only public inventory screen of the exact fitted parts in the bound Q5 engineering model. Native design and physical qualification remain separate.',
                  quote_pause=True, no_vendor_contact_or_quote_changes=True, manufacture_release=False,
                  price_scope='Parts only; excludes PCB, assembly, feeder, attrition, shipping, tax, testing and programming.',
                  screening_plan=dict(boards=10, attrition='max(2, ceil(10% of fitted quantity)) extra per exact MPN, for screening only',
                                      final_model_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(), final_bom_screen_complete=True,
                                      model_path='electronics/q5/netlist-Q5.json', fitted_identity_sha256=fitted_identity_digest(fitted),
                                      fitted_positions=len(fitted), exact_fitted_types=len(groups), assembly_role_positions=dict(roles),
                                      native_layout_binding_pending=False),
                  observations=observations, fitted_bom_screen=screen, separate_hardware_screen=separate, retail_home_parts=retail,
                  user_supplied=[dict(item='LIR2032 rechargeable Li-ion coin cell', quantity_per_board=1,
                                      note='Consumable inserted by the user into BT1; not a JLC/LCSC assembly part; never a primary CR2032/ML2032.')])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=2) + '\n')
    fails = [s['mpn'] for s in screen if not s['passes_stock_screen']] + [r['mpn'] for r in retail if not r['passes_retail_stock_screen']]
    print(f'{len(screen)} fitted MPNs screened; {len(retail)} retail home parts; failures: {fails or "none"}')
    for s in sorted(screen, key=lambda s: s['available_order_quantity'])[:6]:
        print('  lowest', s['mpn'], s['jlc_part'], s['available_order_quantity'], s['library_type'])


if __name__ == '__main__':
    main()
