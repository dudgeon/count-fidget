"""Package actual Q1 manufacturing inputs for quotation, with explicit limits."""
from pathlib import Path
import ast,base64,csv,hashlib,html,json,re,zipfile,datetime
P=Path(__file__).resolve().parent;OUT=P.parent
# Reuse only the local Markdown rendering functions; do not execute the old report.
tree=ast.parse((P/'build_review.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('inline','md')],type_ignores=[]),'markdown_helpers','exec'))
def embed(f):return 'data:image/svg+xml;base64,'+base64.b64encode(f.read_bytes()).decode()
style='''body{font:16px/1.55 system-ui,sans-serif;color:#182f3a;max-width:1080px;margin:40px auto;padding:0 24px}h1,h2,h3{line-height:1.2}h1{font-size:34px}h2{margin-top:40px}table{width:100%;border-collapse:collapse;font-size:14px}td,th{text-align:left;padding:9px;border-bottom:1px solid #dae4e9;vertical-align:top}th{background:#eaf1f5}code{font-size:13px;overflow-wrap:anywhere}.status{background:#eaf3f4;border-left:5px solid #25818b;padding:20px}.warning{background:#fff3dc;padding:18px}.drawings{display:grid;grid-template-columns:1fr 1fr;gap:26px}.drawings img{width:100%;height:auto}a{color:#076d97}pre{white-space:pre-wrap}footer{margin:40px 0;color:#586b76}details{border-top:1px solid #ccdce2;padding:18px 0}summary{cursor:pointer;font-weight:650}@media(max-width:700px){.drawings{grid-template-columns:1fr}body{padding:0 14px}}@media print{body{margin:0}details{display:block}table{break-inside:auto}tr{break-inside:avoid}}'''
drawings='<div class="drawings">'+''.join('<figure><img alt="'+name+'" src="'+embed(P/'procurement'/f)+'"><figcaption>'+name+'</figcaption></figure>' for name,f in [('Top assembly, LCD raised over MCU','assembly-top.svg'),('Bottom assembly, viewed from below','assembly-bottom.svg')])+'</div>'
rfq='<html><head><meta charset="utf-8"><title>Click Counter Q1 RFQ</title><style>'+style+'</style></head><body><h1>Click Counter · Q1 prototype RFQ</h1>'+drawings+md((P/'procurement/RFQ-Q1.md').read_text())+'</body></html>'
(P/'procurement/RFQ-Q1.html').write_text(rfq)
drc=json.loads((P/'verification/routed-drc.json').read_text())
assert not drc['violations'] and not drc['unconnected_items']
bom=list(csv.DictReader((P/'procurement/BOM-Q1.csv').open()));pos=list(csv.DictReader((P/'procurement/placements-KiCad-Q1.csv').open()))
pcbrefs={r['Designator'] for r in bom if r['Assembly'] in ('top','bottom')}
assert pcbrefs=={r['Ref'] for r in pos};assert len(pos)==46
checks={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pcb_drc_violations':0,'pcb_unconnected_items':0,'pcb_fitted_components':46,'placement_bom_reference_match':True,'target':'MSP430FR4133IG48R','firmware_compiled':True,'hardware_tested':False,'production_released':False,'gerber_layers':['F.Cu','In1.Cu','In2.Cu','B.Cu'],'notes':'No ERC-cleared native schematic is claimed. Neutral connectivity source is netlist.json; component/charge safety and physical fit require engineering review.'}
(P/'verification/Q1-status.json').write_text(json.dumps(checks,indent=2))
gerberzip=P/'procurement/click-counter-Q1-Gerbers.zip'
with zipfile.ZipFile(gerberzip,'w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted((P/'electronics/gerbers').iterdir()):
        if f.is_file():z.write(f,f.name)
rfqzip=OUT/'click-counter-Q1-RFQ.zip'
vendorfiles=[P/'procurement'/f for f in ['RFQ-Q1.md','RFQ-Q1.html','BOM-Q1.csv','placements-KiCad-Q1.csv','CPL-JLCPCB-Q1.csv','assembly-top.svg','assembly-bottom.svg','click-counter-Q1-Gerbers.zip']]
vendorfiles += [P/'firmware'/f for f in ['click-counter-Q1.hex','factory-display-info.hex','SHA256.json','main_msp430.c','counter.h','counter.c','lcd_de188.c','lcd_de188.h']]
vendorfiles += [P/'electronics/click-counter-Q1.kicad_pcb',P/'electronics/netlist.json',P/'verification/routed-drc.json',P/'verification/Q1-status.json']
with zipfile.ZipFile(rfqzip,'w',zipfile.ZIP_DEFLATED) as z:
    for f in vendorfiles:z.write(f,f.relative_to(P))
summary='''<h1>Click Counter · Q1 quote package</h1><p>46 × 44 mm enclosure study · 42 × 40 mm four-layer PCB · rechargeable coin-cell counter</p><div class="status"><strong>Actual manufacturing inputs are now prepared.</strong><p>The routed PCB passes KiCad DRC with zero violations and zero unconnected nets. The BOM and placements match all 46 fitted PCB components. The MSP430 firmware compiles, and the host counter/journal and LCD tests pass. The RFQ includes a custom cell/NTC harness, two keycaps, programming, fixtures, first-article checks and recurring functional tests.</p></div><h2>Vendor quote status</h2><table><tr><th>Vendor</th><th>Website response</th><th>Complete price</th></tr><tr><td><a href="https://cart.jlcpcb.com/quote">JLCPCB</a></td><td>Will review Gerber/BOM/CPL. Battery assembly unsupported. Functional-test review only after payment; pre-payment exception declined in chat.</td><td>Not received. Full requested scope is not available as a firm pre-payment quote.</td></tr><tr><td><a href="https://www.pcbway.com/orderonline.aspx">PCBWay</a></td><td>Can quote the battery harness, programming and testing. Requires files through the existing account. Stated review time: 1–2 days after submission.</td><td>Not received; account submission is the next step.</td></tr></table><p>Earlier calculator totals were partial fabrication/assembly estimates. They are not complete quotes and are superseded as purchasing evidence by a future written vendor review. No order has been paid or released.</p><h2>Assembly drawings</h2>'''
limits='''<div class="warning"><strong>Prototype quotation only.</strong><p>The circuit has not been built. Display speed, charging stability/termination, the custom sensor attachment, cell-protection limits and physical fit remain open. In particular, the protector's minimum undervoltage threshold needs reconciliation with the cell's discharge specification. These issues must be resolved before a production release.</p><p>The earlier enclosure STLs remain a fit study and do not yet match Q1's changed mounting holes and USB position. Do not print them as the final enclosure. No native schematic ERC or hardware qualification is claimed.</p></div>'''
report='<html><head><meta charset="utf-8"><title>Click Counter Q1 design and quote status</title><style>'+style+'</style></head><body>'+summary+drawings+limits+'<details open><summary>Exact RFQ, assembly and test requirements</summary>'+md((P/'procurement/RFQ-Q1.md').read_text())+'</details><details><summary>Electrical connectivity and changes</summary>'+md((P/'electronics/design.md').read_text())+'</details><footer>Editable native PCB, source generator, Gerbers, BOM, placements, compiled firmware and test records are in the source archive. The smaller RFQ archive contains the vendor submission package.</footer></body></html>'
(OUT/'click-counter-design-review.html').write_text(report)
with zipfile.ZipFile(OUT/'click-counter-rev0.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(P.rglob('*')):
        if not f.is_file() or 'reference' in f.parts or '__pycache__' in f.parts or f.suffix=='.kicad_prl' or f.name in ['test_counter','test_lcd','assembly-view.kicad_pcb']:continue
        z.write(f,Path('click-counter')/f.relative_to(P))
    z.write(OUT/'click-counter-design-review.html','click-counter-design-review.html')
for f in [rfqzip,gerberzip,OUT/'click-counter-design-review.html',OUT/'click-counter-rev0.zip']:print(f,f.stat().st_size,hashlib.sha256(f.read_bytes()).hexdigest())
