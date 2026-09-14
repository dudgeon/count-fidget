from pathlib import Path
import base64,html,re,json,zipfile,shutil
P=Path(__file__).resolve().parent
OUT=P.parent

def inline(s):
 s=html.escape(s)
 s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<a href="\2">\1</a>',s)
 s=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s)
 s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
 return s

def md(s):
 lines=s.splitlines();out=[];i=0
 while i<len(lines):
  line=lines[i]
  if not line.strip():i+=1;continue
  if line.startswith('#'):
   n=min(len(line)-len(line.lstrip('#'))+1,6);out.append(f'<h{n}>'+inline(line.lstrip('#').strip())+f'</h{n}>');i+=1
  elif line.startswith('|'):
   table=[]
   while i<len(lines) and lines[i].startswith('|'):
    cells=[x.strip() for x in lines[i].strip('|').split('|')]
    if not all(re.fullmatch(r':?-+:?',x.replace(' ','')) for x in cells):table.append(cells)
    i+=1
   out.append('<div class="scroll"><table>')
   for j,row in enumerate(table):
    tag='th' if j==0 else 'td';out.append('<tr>'+''.join(f'<{tag}>{inline(c)}</{tag}>' for c in row)+'</tr>')
   out.append('</table></div>')
  elif line.startswith('- ') or re.match(r'^\d+\. ',line):
   out.append('<ul>')
   while i<len(lines) and (lines[i].startswith('- ') or re.match(r'^\d+\. ',lines[i])):
    out.append('<li>'+inline(re.sub(r'^(?:- |\d+\. )','',lines[i]))+'</li>');i+=1
   out.append('</ul>')
  else:
   para=[]
   while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','- ')):
    para.append(lines[i]);i+=1
   out.append('<p>'+inline(' '.join(para))+'</p>')
 return '\n'.join(out)

def pic(name):return 'data:image/png;base64,'+base64.b64encode((P/'mechanical'/name).read_bytes()).decode()
style='''*{box-sizing:border-box}body{margin:0;background:#f4f6f8;color:#183343;font:17px/1.6 system-ui,-apple-system,sans-serif}main{max-width:940px;margin:auto;padding:28px 20px 70px}header{padding:18px 0 8px}.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:12px;font-weight:750;color:#486c79}h1{font-size:clamp(32px,7vw,56px);line-height:1.05;letter-spacing:-.04em;margin:16px 0}h2{font-size:27px;line-height:1.2;margin:30px 0 14px}h3{font-size:21px;line-height:1.3}h4{font-size:18px}p{margin:10px 0 18px}.lede{font-size:21px;max-width:690px;color:#44616e}.notice{border-left:4px solid #b98024;background:#fff5df;padding:18px 20px;border-radius:0 12px 12px 0;margin:22px 0}.card{background:white;border:1px solid #dde5e9;border-radius:16px;padding:22px;margin:20px 0}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.stat{background:#e6eff1;border-radius:12px;padding:16px}.stat strong{display:block;font-size:25px;line-height:1.2}.stat span{font-size:13px;color:#4c6873}img{display:block;width:100%;height:auto;border-radius:12px}figure{margin:20px 0}figcaption,small{font-size:13px;color:#5a717b}table{border-collapse:collapse;width:100%;font-size:15px}th,td{text-align:left;padding:12px 10px;border-bottom:1px solid #e0e7ea;vertical-align:top}th{background:#edf2f4}.scroll{overflow-x:auto}a{color:#006b87;text-decoration-thickness:1px;text-underline-offset:3px}details{background:white;border:1px solid #dde5e9;padding:18px;border-radius:12px;margin:16px 0}summary{font-size:18px;font-weight:700;cursor:pointer}code{font-size:.86em;background:#eef2f4;padding:2px 4px;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px;background:#edf2f4;padding:14px;border-radius:8px}li{margin-bottom:10px}footer{margin-top:35px;font-size:13px;color:#566e79}@media(max-width:520px){main{padding:18px 14px 50px}.card{padding:17px}.grid{gap:7px}.stat{padding:12px 9px}.stat strong{font-size:20px}.lede{font-size:18px}th,td{padding:10px 8px}}'''
report='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Click-counter fidget — design review</title><style>'''+style+'''</style></head><body><main><header><div class="eyebrow">Geoff's click-counter fidget · Engineering draft 0 · 14 September 2026</div><h1>A click you can count.</h1><p class="lede">Two mechanical keys, a saved count, and USB-C charging in a small printed enclosure.</p></header>
<div class="notice"><strong>Design in progress.</strong> Both vendor website calculators have been checked; full assembly quotes require the unfinished manufacturing files. Display qualification, the finished PCB, target firmware and physical validation remain before ordering.</div>
<div class="grid"><div class="stat"><strong>46 × 44</strong><span>mm body footprint</span></div><div class="stat"><strong>25–30 g</strong><span>assembled target, unmeasured</span></div><div class="stat"><strong>8 digits</strong><span>0 to 99,999,999</span></div></div>
<figure><img alt="Dimensioned CAD fit study of a two-key counter with front display and side charging port" src="'''+pic('assembled-cad.png')+'''"><figcaption>Generated from the actual STEP geometry. Bought components are simplified envelopes; displayed digits and key legends are illustrative.</figcaption></figure>
<section class="card"><h2>How it will behave</h2><table><tr><th>Action</th><th>Result</th></tr><tr><td>Press +1</td><td>Add one, save it, then display the accepted count.</td></tr><tr><td>Press reset</td><td>Reset to zero on a single press.</td></tr><tr><td>Leave it for 30 seconds</td><td>Blank the screen and enter low-power sleep.</td></tr><tr><td>Click after sleep</td><td>Wake and count that first click.</td></tr><tr><td>Battery goes flat</td><td>Previously committed counts remain in nonvolatile FRAM.</td></tr></table><p><small>An interrupted, not-yet-committed update can lose its latest click. Holding a key does not auto-repeat. The eight-digit limit requires an overflow indication rather than silent rollover.</small></p></section>
<section class="card"><h2>The display is the unresolved choice</h2><p>A reflective calculator-style LCD fits the low-power goal. However, the candidate DE188's full datasheet lists <strong>440 ms combined on/off response</strong>. Rapidly changing digits could blur, despite correct electronic counting.</p><p>Both vendors have been asked to confirm current response data or identify a faster compact LCD. A small OLED is the fallback; it would need revised electronics and a shorter battery-life estimate. The rendered display is not a demonstration of actual refresh performance.</p><p><a href="https://display-elektronik.de/filter/DE188-RU-30_75_3V.pdf">Manufacturer's DE188 specification</a></p></section>
<section class="card"><h2>Electronics baseline</h2><table><tr><th>Function</th><th>Candidate</th><th>Why</th></tr><tr><td>Controller + memory</td><td>TI MSP430FR4133</td><td>LCD controller and durable FRAM in one chip.</td></tr><tr><td>Rechargeable coin cell</td><td>EEMB LIR2032, 45 mAh</td><td>2.6 g; documented charging requirements. Prepared battery lead assembly still to confirm.</td></tr><tr><td>USB charger</td><td>TI BQ25185</td><td>Hardware-set charging and power-path control, with battery-contact thermistor.</td></tr><tr><td>Power rail</td><td>TPS7A02, 3.0 V</td><td>Very low standby overhead.</td></tr><tr><td>Cell protection</td><td>BQ29700 + FETs</td><td>Independent protection; exact FETs, sensing and tolerance review pending.</td></tr><tr><td>Keys</td><td>Two Cherry MX Blue</td><td>Familiar click and removable keycaps. Low-profile alternatives remain a weight-optimization option.</td></tr></table><p>The LCD version has a provisional <strong>2–4-month charging interval target</strong> at ten minutes' use a day. This is calculated from a conservative current budget; it is not a measured claim and does not apply to an OLED.</p></section>
<figure><img alt="Exploded CAD fit study showing the lid, keycaps, switches, LCD and board layers" src="'''+pic('exploded-cad.png')+'''"><figcaption>Printed shell solids total about 10 g in PLA. LCD leads, battery harness/NTC, most small components and fasteners are not modeled yet.</figcaption></figure>
<section class="card">'''+md((P/'procurement/website-quotes.md').read_text())+'''</section><section class="card"><h2>Earlier email inquiries</h2><table><tr><th>Vendor</th><th>Requested</th><th>Status</th></tr><tr><td><a href="https://mail.google.com/">JLCPCB email thread</a></td><td>5 and 10 complete electronics assemblies</td><td>Budget RFQ sent; response pending</td></tr><tr><td><a href="https://mail.google.com/">PCBWay email thread</a></td><td>5 and 10 complete electronics assemblies</td><td>Budget RFQ sent; response pending</td></tr></table><p>Requests cover all PCB soldering, LCD and switch installation, battery preparation, programming, test fixtures/testing and delivery to 20815. Any exclusions must be explicit. These are preliminary inquiries; <strong>no firm totals or paid order exist yet.</strong></p></section>
<section class="card"><h2>Verified in this pass</h2><ul><li>The portable C counter handles bounce, held keys, first wake click, reset priority, counter overflow and timer wrap in host tests.</li><li>The journal recovers the previous committed count at every tested interruption between its writes, and detects tested corruption. 100,000 simulated journal commits passed.</li><li>The DE188 segment encoder was checked against its pin matrix for zero, one, eight and digit order.</li><li>Both printed CAD parts are valid single solids and their modeled intersection is zero.</li></ul><p><strong>Still required:</strong> display selection, final battery and protection design, native schematic and routed PCB, ERC/DRC, a compiled MCU image, assembled prototype tests and final mechanical fit. Host software tests do not validate charging or physical hardware.</p></section>
<details><summary>Product spec, printing notes and project status</summary>'''+md((P/'README.md').read_text())+'''</details><details><summary>Electrical design and source references</summary>'''+md((P/'electronics/design.md').read_text())+'''</details><details><summary>Host test results and CAD checks</summary><pre>'''+html.escape((P/'verification/firmware-host-tests.txt').read_text()+(P/'verification/lcd-host-tests.txt').read_text()+'\n'+(P/'mechanical/geometry-check.json').read_text())+'''</pre></details><footer>The accompanying source archive contains the fit-study STEP/STLs, editable CadQuery model, C source, tests, engineering notes and exact supplier inquiries. Fit-study files are clearly labeled and are not manufacturing releases.</footer></main></body></html>'''
(OUT/'click-counter-design-review.html').write_text(report)
shutil.copy2(P/'mechanical/assembled-cad.png',OUT/'click-counter-cad.png')
with zipfile.ZipFile(OUT/'click-counter-rev0.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(P.rglob('*')):
  if not f.is_file() or 'reference' in f.parts or f.name in ['test_counter','test_lcd'] or '__pycache__' in f.parts:continue
  z.write(f,Path('click-counter')/f.relative_to(P))
 z.write(OUT/'click-counter-design-review.html','click-counter-design-review.html')
print('Created self-contained HTML review, source archive, CAD preview')
for name in ['click-counter-design-review.html','click-counter-rev0.zip','click-counter-cad.png']:
 print(name,(OUT/name).stat().st_size)
