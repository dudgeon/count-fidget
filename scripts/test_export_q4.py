"""Adversarial Q4 exporter tests using synthetic native-output fixtures.

These exercise export guards only; they do not run KiCad, validate real routing
or qualify hardware. The actual production exporter requires saved native evidence.
"""
import argparse,collections,copy,csv,hashlib,importlib.util,json,sys,tempfile,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--report',type=Path)
args=parser.parse_args()
spec=importlib.util.spec_from_file_location('q4export',root/'scripts/export_q4.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
model=json.loads(e.MODEL.read_text());stock=json.loads(e.STOCK.read_text());hardware=json.loads(e.HARDWARE.read_text())
# Synthetic binding ONLY in memory: the real stock record remains pending routing.
stock['screening_plan']['final_model_sha256']=e.digest(e.MODEL)
stock['screening_plan']['native_layout_binding_pending']=False
passed=[]
checks=e.validate_sources(model,stock,hardware,e.digest(e.MODEL));passed.append('current identity/stock/reference/role and retail screen')
def rejects(name,fn):
 try:fn()
 except (ValueError,KeyError):passed.append(name)
 else:raise AssertionError('unexpected acceptance: '+name)
def source_mutation(name,kind,mutate):
 m,s,h=copy.deepcopy(model),copy.deepcopy(stock),copy.deepcopy(hardware)
 mutate({'model':m,'stock':s,'hardware':h}[kind])
 rejects(name,lambda:e.validate_sources(m,s,h,e.digest(e.MODEL)))
source_mutation('stale full-model binding rejected','stock',lambda s:s['screening_plan'].update(final_model_sha256='0'*64))
source_mutation('pending routing binding rejected','stock',lambda s:s['screening_plan'].update(native_layout_binding_pending=True))
source_mutation('stale identity digest rejected','stock',lambda s:s['screening_plan'].update(fitted_identity_sha256='0'*64))
source_mutation('duplicate native ref rejected','model',lambda m:m['parts'][0].update(ref=m['parts'][1]['ref']))
source_mutation('role swap with unchanged counts rejected','model',lambda m:[p.update(assembly='home_through_hole' if p['ref']=='U1' else 'jlc_smt') for p in m['parts'] if p['ref'] in ('U1','DS1')])
source_mutation('wrong exact MCU rejected','model',lambda m:next(p for p in m['parts'] if p['ref']=='U1').update(mpn='STM32L072CZT6'))
source_mutation('stale stock ref rejected','stock',lambda s:s['fitted_bom_screen'][0]['references'].append('R34'))
source_mutation('understated stock requirement rejected','stock',lambda s:s['fitted_bom_screen'][0].update(screening_required_quantity=1))
source_mutation('shortage despite passed flag rejected','stock',lambda s:s['fitted_bom_screen'][0].update(available_order_quantity=1))
source_mutation('fabricated observation rejected','stock',lambda s:s['fitted_bom_screen'][0].update(observed_at='2026-09-25T01:00:00Z'))
source_mutation('wrong catalog code rejected','stock',lambda s:s['fitted_bom_screen'][0].update(jlc_part='C1'))
source_mutation('duplicate catalog row rejected','stock',lambda s:s['fitted_bom_screen'].append(s['fitted_bom_screen'][0]))
source_mutation('missing home retail evidence rejected','stock',lambda s:s['retail_home_parts'].pop(0))
source_mutation('retail quantity/pack rounding rejected','stock',lambda s:s['retail_home_parts'][1].update(rounded_screening_quantity=22))
source_mutation('retail shortage rejected','stock',lambda s:s['retail_home_parts'][0].update(in_stock=1))
source_mutation('extra interposer quantity rejected','hardware',lambda h:h['items'][0].update(quantity_per_board=2))
source_mutation('header identity substitution rejected','hardware',lambda h:h['items'][0].update(mpn='PZ254V-11-08P'))
source_mutation('obsolete four-layer model rejected','model',lambda m:m.update(layers=4))

def fixture(out):
 e.write_tables(out,model,stock,hardware)
 positions=[[p['ref'],p['value'],p['footprint'].split(':')[1],f"{p['x']:.6f}",f"{-p['y']:.6f}",f"{p['rotation']:.6f}",p['side']] for p in e.selected_parts(model)[0]]
 e.write_csv(out/'placements-KiCad-Q4.csv',['Ref','Val','Package','PosX','PosY','Rot','Side'],positions)
 e.write_csv(out/'CPL-JLCPCB-Q4.csv',e.CPL_HEADER,e.cpl_rows(e.native_positions(out,model),model))
 g=out/'gerbers';g.mkdir(exist_ok=True)
 for suffix in e.GERBER_SUFFIXES:
  (g/('click-counter-Q4-'+suffix)).write_text('M02*\n' if suffix=='F_Paste.gtp' else 'D03*\nM02*\n')
 expected={'click-counter-Q4-'+x for x in e.GERBER_SUFFIXES}
 attrs=[]
 for n in sorted(expected-{'click-counter-Q4-'+s for s in ('PTH.drl','NPTH.drl','job.gbrjob')}):
  attrs.append({'Path':n,'FileFunction':'Copper,L1,Top' if 'F_Cu' in n else 'Copper,L2,Bot' if 'B_Cu' in n else 'Other'})
 (g/'click-counter-Q4-job.gbrjob').write_text(json.dumps({'GeneralSpecs':{'LayerNumber':2,'BoardThickness':1.0,'ProjectId':{'Name':'click-counter-Q4'}},'MaterialStackup':[{'Name':'F.Cu','Type':'Copper'},{'Name':'B.Cu','Type':'Copper'}],'FilesAttributes':attrs}))
 for side in ('top','bottom'):(out/f'assembly-{side}-Q4.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0L1 1"/></svg>')
 (out/'drill-report-Q4.txt').write_text('Synthetic test fixture, no actual native check.\n')
 (out/'REVIEW-EXPORTS-Q4.md').write_text(e.review_readme())
 e.deterministic_zip(out)

def csvmut(out,name,mutation):
 with (out/name).open(newline='') as f:rows=list(csv.reader(f))
 mutation(rows)
 e.write_csv(out/name,rows[0],rows[1:])

with tempfile.TemporaryDirectory(prefix='q4-export-test-') as name:
 out=Path(name);fixture(out);e.validate_exports(out,model,stock,hardware);passed.append('synthetic 70 native /67 SMT /3 home export split accepted')
 sha=e.digest(out/'click-counter-Q4-Gerbers.zip');e.deterministic_zip(out);assert sha==e.digest(out/'click-counter-Q4-Gerbers.zip');passed.append('ZIP deterministic for identical native input bytes')
 tabletests=[
 ('JLC MPN changed','BOM-JLCPCB-Q4.csv',lambda r:r[1].__setitem__(0,'WRONG')),
 ('JLC footprint receives Notes','BOM-JLCPCB-Q4.csv',lambda r:r[1].__setitem__(2,'Notes accidentally mapped')),
 ('missing JLC row','BOM-JLCPCB-Q4.csv',lambda r:r.pop()),
 ('duplicate JLC row','BOM-JLCPCB-Q4.csv',lambda r:r.append(r[1])),
 ('home ref in factory BOM','BOM-JLCPCB-Q4.csv',lambda r:r.append(['HS96L01W4S03','DS1','CountFidgetQ4:HS96L01W4S03_Module_7Pin','C5139758'])),
 ('all70 refs in factory CPL','CPL-JLCPCB-Q4.csv',lambda r:r.append(['DS1','21mm','-16.7mm','Top','0'])),
 ('CPL coordinate sign wrong','CPL-JLCPCB-Q4.csv',lambda r:r[1].__setitem__(2,'1mm')),
 ('CPL rotation wrong','CPL-JLCPCB-Q4.csv',lambda r:r[1].__setitem__(4,'180')),
 ('native placement missing','placements-KiCad-Q4.csv',lambda r:r.pop()),
 ('native position wrong','placements-KiCad-Q4.csv',lambda r:r[1].__setitem__(3,'999')),
 ('native footprint wrong','placements-KiCad-Q4.csv',lambda r:r[1].__setitem__(2,'obsolete_Q3')),
 ('home switch omitted','HOME-COMPLETION-Q4.csv',lambda r:r.pop()),
 ('home solder count wrong','HOME-COMPLETION-Q4.csv',lambda r:r[1].__setitem__(-2,'7')),
 ('header duplicate','SEPARATE-HARDWARE-Q4.csv',lambda r:r.append(r[1])),
 ('battery scope omitted','OFFBOARD-items-Q4.csv',lambda r:r.pop(1)),
 ('false exact battery selection','OFFBOARD-items-Q4.csv',lambda r:r[1].__setitem__(5,'CC-BAT-001')),
 ('combined full BOM omits header','BOM-Q4.csv',lambda r:r.pop(71)),
 ]
 for title,name,mut in tabletests:
  fixture(out);csvmut(out,name,mut);rejects(title+' rejected',lambda:e.validate_exports(out,model,stock,hardware))
 filetests=[
 ('top paste geometry',lambda:(out/'gerbers/click-counter-Q4-F_Paste.gtp').write_text('D03*\n')),
 ('empty bottom paste',lambda:(out/'gerbers/click-counter-Q4-B_Paste.gbp').write_text('M02*\n')),
 ('unexpected inner copper',lambda:(out/'gerbers/click-counter-Q4-In1_Cu.g1').write_text('D03*\n')),
 ('Gerber ZIP byte mismatch',lambda:(out/'gerbers/click-counter-Q4-B_Mask.gbs').write_text('D01*\n')),
 ('private filesystem path',lambda:(out/'drill-report-Q4.txt').write_text('/Users/private-person/secret\n')),
 ('empty assembly SVG',lambda:(out/'assembly-top-Q4.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')),
 ('extra private file',lambda:(out/'private-note.txt').write_text('not exportable')),
 ]
 for title,mut in filetests:
  for p in out.rglob('*'):
   if p.is_file():p.unlink()
  fixture(out);mut();rejects(title+' rejected',lambda:e.validate_exports(out,model,stock,hardware))
 result={'status':'PASS_BOUNDED_EXPORT_ADVERSARIAL_TESTS','test_count':len(passed),'tests':passed,'scope':'Synthetic native-output fixtures test exporter guards; this does not run KiCad or validate current routing/geometry/hardware. Production export remains gated on saved native validation.','inputs_sha256':{str(p.relative_to(root)):e.digest(p) for p in [root/'scripts/export_q4.py',Path(__file__).resolve(),e.MODEL,e.STOCK,e.HARDWARE]}}
 if args.report:
  args.report.parent.mkdir(parents=True,exist_ok=True)
  args.report.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
