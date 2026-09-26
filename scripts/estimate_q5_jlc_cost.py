"""Estimate the JLCPCB order cost of the locked Q5 design for quote variants A and B.

Inputs: the stock screen (live public catalogue prices, minimum purchase quantities,
Basic/Extended library type), the routed board (SMT and hand-solder joint counts),
JLC's published PCBA fee schedule (dated below) and the PCB-only price and shipping
estimate observed on JLC's public quote page for the locked Gerbers. This is an
ESTIMATE: JLC's binding PCBA price appears only after the signed-in BOM/CPL step.
Writes procurement/q5/jlc-cost-estimate.json (10 boards) or, with --qty 5,
procurement/q5/jlc-cost-estimate-5.json.
"""
import hashlib
import json
import sys
from pathlib import Path
import pcbnew as p

ROOT = Path(__file__).resolve().parents[1]
MODEL, STOCK = ROOT / 'electronics/q5/netlist-Q5.json', ROOT / 'procurement/q5/stock.json'
BOARD, OUT = ROOT / 'electronics/q5/click-counter-Q5.kicad_pcb', ROOT / 'procurement/q5/jlc-cost-estimate.json'
N = int(sys.argv[sys.argv.index('--qty') + 1]) if '--qty' in sys.argv else 10
assert N in (2, 5, 10), 'observed PCB prices exist for 2 (5 bare PCBs), 5 and 10 boards'
if N != 10:
    OUT = OUT.with_name(f'jlc-cost-estimate-{N}.json')
# https://jlcpcb.com/help/article/pcb-assembly-price (read 25 Sep 2026)
FEES = dict(
    economic=dict(setup=8.18, stencil=1.53, per_joint=0.0016, feeder_extended=3.07, feeder_basic=0.0),
    standard=dict(setup=25.56, stencil=8.21, per_joint=0.0016, feeder_extended=1.53, feeder_basic=1.53),
    manual_per_joint=0.0164, hand_soldering_labor_per_order=3.58)
# Observed on https://cart.jlcpcb.com/quote with procurement/q5/click-counter-Q5-Gerbers.zip (25 Sep 2026):
# 2 layers, 42 x 54 mm, 1.6 mm FR-4 TG135, green/white, ENIG 1U", 10 pcs, 3-day build.
OBSERVED = dict(pcb_usd=22.10, pcb_quantity=10, pcb_breakdown=dict(board=5.00, enig=17.10),
                build_time_with_pcba='24 hours (PCBA only) at $0.00', shipping_dhl_ddp_usd=29.45,
                shipping_weight_kg=0.20, observed_utc='2026-09-25T20:05Z')
if N in (2, 5):
    # Same page and options, PCB Qty 5 (25 Sep 2026); PCBA qty offered 2 or 5.
    OBSERVED = dict(pcb_usd=20.90, pcb_quantity=5, pcb_breakdown=dict(board=4.00, enig=16.90),
                    build_time_with_pcba='24 hours (PCBA only) at $0.00', shipping_dhl_ddp_usd=29.45,
                    shipping_weight_kg=0.16, observed_utc='2026-09-25T21:10Z')


def price(o):
    # Below 10 boards most lines are bought below the 10-piece break: use the 1-piece price when known.
    first = ('unit_price_usd_at_1', 'unit_price_usd_at_10') if N < 5 else ('unit_price_usd_at_10', 'unit_price_usd_at_1')
    return o.get(first[0]) or o.get(first[1]) or 0.0


def main():
    stock, model = json.loads(STOCK.read_text()), json.loads(MODEL.read_text())
    parts = {q['ref']: q for q in model['parts']}
    obs = {(o['mpn'], o.get('jlc_part')): o for o in stock['observations'] if o.get('jlc_part')}
    board = p.LoadBoard(str(BOARD))
    smt_joints = sum(1 for f in board.GetFootprints() if parts[f.GetReference()]['assembly'] == 'jlc_smt'
                     for a in f.Pads() if a.GetNumber() and a.GetAttribute() != p.PAD_ATTRIB_NPTH)
    lines, basic, extended = [], 0, 0
    for row in stock['fitted_bom_screen']:
        if 'jlc_smt' not in row['assembly_roles']:
            continue
        o = obs[(row['mpn'], row['jlc_part'])]
        need = row['fitted_per_board'] * N
        buy = max(need, row['minimum_order'])
        lines.append(dict(mpn=row['mpn'], lcsc=row['jlc_part'], library=row['library_type'], per_board=row['fitted_per_board'],
                          buy=buy, unit_usd=price(o), cost_usd=round(buy * price(o), 3)))
        basic += row['library_type'] == 'base'; extended += row['library_type'] != 'base'
    components = sum(l['cost_usd'] for l in lines)
    ds1 = next(r for r in stock['variant_b_jlc_through_hole_screen'] if r['references'] == ['DS1'])
    header = next(o for o in stock['observations'] if o.get('jlc_part') == 'C492406')
    tht_components = N * price(obs[(ds1['mpn'], ds1['jlc_part'])]) + max(N, header['minimum_order']) * price(header)

    def order(kind, variant):
        f = FEES[kind]
        c = dict(pcb=OBSERVED['pcb_usd'], setup=f['setup'], stencil=f['stencil'],
                 smt_joints=round(smt_joints * N * f['per_joint'], 2),
                 feeder_loading=round(extended * f['feeder_extended'] + basic * f['feeder_basic'], 2),
                 components=round(components, 2))
        if variant == 'B':
            c['tht_components'] = round(tht_components, 2)
            c['tht_feeder_loading'] = round(2 * f['feeder_extended'], 2)
            c['manual_joints'] = round(14 * N * FEES['manual_per_joint'], 2)
            c['hand_soldering_labor'] = FEES['hand_soldering_labor_per_order']
        c['subtotal_before_shipping'] = round(sum(c.values()), 2)
        c['with_dhl_shipping'] = round(c['subtotal_before_shipping'] + OBSERVED['shipping_dhl_ddp_usd'], 2)
        c['per_board_with_shipping'] = round(c['with_dhl_shipping'] / N, 2)
        return c

    retail = {r['mpn']: r for r in stock['retail_home_parts']}

    def lcsc_cost(mpn):
        r = retail[mpn]
        u = r.get('unit_price_usd_at_10') or r.get('unit_price_usd_at_1')
        return (round(r['rounded_screening_quantity'] * u, 2) if u else None), r['rounded_screening_quantity']
    loose_both = {m: lcsc_cost(m) for m in ('CPG151101D13', 'PA2X6nie')}
    loose_a_only = {m: lcsc_cost(m) for m in ('HS96L01W4S03', 'PZ254V-11-07P')}
    result = dict(
        schema=1, status='ESTIMATE from published fees and live catalogue prices; binding PCBA price requires the signed-in JLC BOM/CPL step',
        quantity=N, model_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(), stock_sha256=hashlib.sha256(STOCK.read_bytes()).hexdigest(),
        board_sha256=hashlib.sha256(BOARD.read_bytes()).hexdigest(), fee_schedule=FEES,
        fee_source='https://jlcpcb.com/help/article/pcb-assembly-price (read 2026-09-25)', observed_jlc_quote_page=OBSERVED,
        smt_joints_per_board=smt_joints, smt_part_types=dict(basic=basic, extended=extended),
        variant_A=dict(description='JLC SMT only; user solders DS1 on its header (14 joints)',
                       economic=order('economic', 'A'), standard=order('standard', 'A')),
        variant_B=dict(description='JLC SMT plus JLC through-hole DS1 on header DS1H (acceptance of the stacked module is a quote question)',
                       economic=order('economic', 'B'), standard=order('standard', 'B')),
        lcsc_loose_parts_both_variants={m: dict(usd=c, quantity=q) for m, (c, q) in loose_both.items()},
        lcsc_loose_parts_variant_A_only={m: dict(usd=c, quantity=q) for m, (c, q) in loose_a_only.items()},
        not_included=['LCSC shipping', 'LIR2032 cells (user supplied, retail)', 'enclosure printing (home print per spec)',
                      'coupons/promotions (JLC advertises setup-fee coupons)', 'import tax beyond DDP', 'JLC component attrition surcharges'],
        component_lines=sorted(lines, key=lambda l: -l['cost_usd']))
    OUT.write_text(json.dumps(result, indent=1) + '\n')
    for v in ('variant_A', 'variant_B'):
        for k in ('economic', 'standard'):
            print(v, k, result[v][k]['subtotal_before_shipping'], 'with shipping', result[v][k]['with_dhl_shipping'],
                  'per board', result[v][k]['per_board_with_shipping'])
    print('extended types', extended, 'basic types', basic, 'SMT joints/board', smt_joints)
    print('LCSC loose (both):', loose_both, ' variant A only:', loose_a_only)


if __name__ == '__main__':
    main()
