"""Estimate a CircuitHub order for the locked Q5 board at 2, 5 and 10 boards (not a quote).

CircuitHub prices only inside a signed-in project, so this combines public inputs:
  * fabrication + assembly: CircuitHub's own published example for a comparable design
    ("2 layers, simple microcontroller"), per board, for its Fastest and Cheapest
    lead times (circuithub-price-examples-2026-10-26.json);
  * parts: the Q5 CircuitHub BOM priced at the Digi-Key breaks recorded in
    crossref-q5.json, with CircuitHub's published attrition extras
    (docs.circuithub.com "Part consignment": 0603/0805 passives at least 10 extra and
    25 minimum; small actives at least 5 extra; expensive ICs at least 1 extra);
  * Value Proto: 75 % off Priority (Fastest) fabrication and assembly for builds of
    ten boards or fewer with no through-hole/hybrid and no consigned parts.
Consigned or LCSC-sourced lines and shipping are listed separately.
Writes procurement/q5/circuithub/circuithub-cost-estimate.json.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'procurement/q5/circuithub'
CROSS = json.loads((DEST / 'crossref-q5.json').read_text())
EXAMPLES = json.loads((DEST / 'circuithub-price-examples-2026-10-26.json').read_text())
BOM = ROOT / 'procurement/q5/BOM-Q5.csv'
QUANTITIES = (2, 5, 10)
PASSIVE = ('0603', '0805')


def refs_per_mpn():
    import csv
    counts = {}
    for row in csv.DictReader(BOM.open(encoding='utf-8-sig', newline='')):
        if row['Assembly Role'] in ('jlc_smt', 'home_through_hole'):
            counts[row['Manufacturer Part Number']] = counts.get(row['Manufacturer Part Number'], 0) + 1
    return counts


def buy_quantity(entry, need):
    if entry['package'] in PASSIVE:
        return max(25, need + 10)
    if entry['package'] in ('SOT-23', 'SOT-23-6', 'SOT-23-8', 'SOD-323', 'WSON-6_1.5x1.5', 'WSON-6-1EP', 'WSON-10', 'TS-1088', 'CPG151101S11'):
        return need + 5
    return need + 1


def unit_price(evidence, qty):
    breaks = sorted((int(q), float(p)) for q, p in evidence['price_breaks_usd'].items())
    price = breaks[0][1]
    for q, p in breaks:
        if qty >= q:
            price = p
    return price


def main():
    counts = refs_per_mpn()
    result = dict(schema=1, kind='ESTIMATE, not a CircuitHub quote', inputs=dict(
        price_examples='procurement/q5/circuithub/circuithub-price-examples-2026-10-26.json',
        parts='procurement/q5/circuithub/crossref-q5.json (Digi-Key breaks)'), by_quantity={})
    for n in QUANTITIES:
        parts_usd, lines, separate = 0.0, [], []
        for original, entry in CROSS['lines'].items():
            need = counts[original] * n
            if entry['dnp']:
                separate.append(dict(mpn=entry['mpn'], refs=counts[original], handling='DNP: fitted at home'))
                continue
            if entry['action'] == 'consign':
                separate.append(dict(mpn=entry['mpn'], refs=counts[original], handling='consign or custom (LCSC) purchase source'))
                continue
            ev = entry['evidence']
            buy = buy_quantity(entry, need)
            if ev.get('pack_size'):  # sold in packs (e.g. 20 hot-swap sockets): price per pack
                buy = math.ceil(buy / ev['pack_size'])
            price = unit_price(ev, buy)
            parts_usd += buy * price
            lines.append(dict(mpn=entry['mpn'], need=need, buy=buy, buy_unit='pack' if ev.get('pack_size') else 'piece',
                              unit_usd=price, line_usd=round(buy * price, 2)))
        row = dict(parts_usd=round(parts_usd, 2), parts_usd_per_board=round(parts_usd / n, 2), parts_lines=lines,
                   not_bought_by_circuithub=separate)
        for mode in ('Fastest', 'Cheapest'):
            ex = EXAMPLES['examples'][f'Low-{mode}']['by_quantity'][str(n)]
            fab_asm = (ex['board_usd_per_board'] + ex['assembly_usd_per_board']) * n
            row[mode.lower()] = dict(lead_time_days=ex['lead_time_days'], fab_and_assembly_usd=round(fab_asm, 2),
                                     total_before_shipping_usd=round(fab_asm + parts_usd, 2),
                                     per_board_usd=round((fab_asm + parts_usd) / n, 2))
        priority = (EXAMPLES['examples']['Low-Fastest']['by_quantity'][str(n)]['board_usd_per_board'] +
                    EXAMPLES['examples']['Low-Fastest']['by_quantity'][str(n)]['assembly_usd_per_board']) * n
        row['value_proto_if_eligible'] = dict(
            fab_and_assembly_usd=round(0.25 * priority, 2), total_before_shipping_usd=round(0.25 * priority + parts_usd, 2),
            per_board_usd=round((0.25 * priority + parts_usd) / n, 2),
            eligible_today=False,
            blocker='J1 USB4105 has plated shell stakes (hybrid part); DS1 is through-hole (left unplaced)')
        result['by_quantity'][str(n)] = row
    (DEST / 'circuithub-cost-estimate.json').write_text(json.dumps(result, indent=1) + '\n')
    for n in QUANTITIES:
        r = result['by_quantity'][str(n)]
        print(f"{n:>2} boards: parts ${r['parts_usd']:.0f}; cheapest ${r['cheapest']['total_before_shipping_usd']:.0f} "
              f"({r['cheapest']['lead_time_days']:.0f} d), fastest ${r['fastest']['total_before_shipping_usd']:.0f} "
              f"({r['fastest']['lead_time_days']:.0f} d); Value Proto if eligible ${r['value_proto_if_eligible']['total_before_shipping_usd']:.0f}")


if __name__ == '__main__':
    main()
