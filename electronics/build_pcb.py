"""Generate the Rev Q1 quote prototype. Run with KiCad 10's pcbnew Python.
Not a release to fabricate; qualification requirements accompany the RFQ.
Coordinates: board top view, mm, origin at upper-left of 42 x 40 outline.
"""
import pcbnew as p
from pathlib import Path
import json, csv, os

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'electronics'
LIB=Path(os.environ.get('KICAD_FP_ROOT',str(ROOT.parent/'tooling/squashfs-root/share/kicad/footprints')))
b=p.BOARD(); b.SetCopperLayerCount(4)
ds=b.GetDesignSettings(); ds.SetBoardThickness(p.FromMM(1.0))
ds.m_MinClearance=p.FromMM(.127); ds.m_TrackMinWidth=p.FromMM(.127)
ds.m_ViasMinSize=p.FromMM(.55); ds.m_MinThroughDrill=p.FromMM(.30)
ds.m_CopperEdgeClearance=p.FromMM(.30)
ds.m_HoleClearance=p.FromMM(.15)
nc=b.GetDesignSettings().m_NetSettings.GetDefaultNetclass()
nc.SetClearance(p.FromMM(.15));nc.SetTrackWidth(p.FromMM(.15));nc.SetViaDiameter(p.FromMM(.6));nc.SetViaDrill(p.FromMM(.3))
nets={}; parts=[]; keepers=[]
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def net(n):
    if n not in nets:
        ni=p.NETINFO_ITEM(b,n);b.Add(ni);nets[n]=ni
    return nets[n]
def add(ref,value,mpn,mfr,fp,x,y,rot=0,side='top',pins=None,notes=''):
    adjust={'R1':(29.5,18.5,0),'R2':(31.5,20.2,0),'D1':(37.3,20.7,0),'R4':(39,6.5,0),'R19':(39,12.5,0),'C13':(39,15,0),'R6':(26.5,18.5,0),
      'R9':(12.3,12,90),'R10':(12.6,5.2,90),'R11':(11.5,18.5,0),
      'R12':(14.8,18.5,0),'R13':(18.1,18.5,0),'R14':(21,5.3,90),
      'R15':(21,9.7,90),'Q3':(22,19,0),'C1':(33,4.3,0),'C2':(29,4.3,0),
      'C7':(25,4.3,0),'C9':(17,4.3,0),'C5':(29.5,10.2,90),'C8':(15.5,11.3,0),
      'R17':(5.5,33.5,90),'C11':(8,34.5,90),'R18':(36.5,33.5,90),'C12':(34,33.5,90)}
    if ref in adjust:x,y,rot=adjust[ref]
    lib,name=fp.split(':'); f=p.FootprintLoad(str(LIB/(lib+'.pretty')),name)
    if not f:raise ValueError(fp)
    keepers.append(f)
    f.SetReference(ref);f.SetValue(value);b.Add(f)
    if side=='bottom': f.Flip(v(0,0),False)
    f.SetPosition(v(x,y)); f.SetOrientationDegrees(rot)
    f.Reference().SetVisible(False);f.Value().SetVisible(False)
    for g in list(f.GraphicalItems()):
        # Manufacturing reference drawing is supplied separately; avoid unreadable
        # sub-millimeter silk under the glass and on the dense reverse side.
        if g.GetLayer() in (p.F_SilkS,p.B_SilkS):
            f.Remove(g); keepers.append(g)
    pins={str(k):n for k,n in (pins or {}).items()}
    for pad in f.Pads():
        if pad.GetNumber() in pins:pad.SetNet(net(pins[pad.GetNumber()]))
    present={z.GetNumber() for z in f.Pads()}
    assert set(pins)<=present,(ref,set(pins)-present)
    parts.append(dict(ref=ref,value=value,mpn=mpn,manufacturer=mfr,footprint=fp,x=x,y=y,rotation=rot,side=side,pins=pins,notes=notes))
    return f
def line(x1,y1,x2,y2,layer=p.Edge_Cuts,width=.05):
    a=p.PCB_SHAPE();a.SetShape(p.SHAPE_T_SEGMENT);a.SetStart(v(x1,y1));a.SetEnd(v(x2,y2));a.SetLayer(layer);a.SetWidth(p.FromMM(width));b.Add(a)
def arc(x1,y1,xm,ym,x2,y2):
    a=p.PCB_SHAPE();a.SetShape(p.SHAPE_T_ARC);a.SetArcGeometry(v(x1,y1),v(xm,ym),v(x2,y2));a.SetLayer(p.Edge_Cuts);a.SetWidth(p.FromMM(.05));b.Add(a)
line(2,0,40,0);arc(40,0,41.414214,.585786,42,2)
line(42,2,42,38);arc(42,38,41.414214,39.414214,40,40)
line(40,40,2,40);arc(2,40,.585786,39.414214,0,38)
line(0,38,0,2);arc(0,2,.585786,.585786,2,0)

# User interface. Manufacturer DE188 Rev4 pin numbering viewed from display front.
f=p.FOOTPRINT(b);f.SetReference('DS1');f.SetFPID(p.LIB_ID('ClickCounter','DE188_20P_34.9x13mm'));f.SetValue('DE188-RU-30/7,5/V(3V)');f.SetAttributes(p.FP_THROUGH_HOLE);b.Add(f);f.SetPosition(v(21,8.75))
f.Reference().SetVisible(False);f.Value().SetVisible(False)
lcdpins={20:'COM0',1:'COM1',11:'COM2',10:'COM3'}
lcdpins.update({pin:'SEG'+str(i) for i,pin in enumerate(list(range(2,10))+list(range(12,20)))})
for i in range(10):
    for num,yy in [(i+1,6.75),(20-i,-6.75)]:
        pad=p.PAD(f);pad.SetNumber(str(num));pad.SetAttribute(p.PAD_ATTRIB_PTH);pad.SetShape(p.PAD_SHAPE_CIRCLE)
        pad.SetSize(v(2.2,2.2));pad.SetDrillSize(v(1.7,1.7));pad.SetLayerSet(p.LSET.AllCuMask());pad.SetLayerSet(p.PAD.PTHMask())
        pad.SetPosition(v(21-11.43+i*2.54,8.75+yy));pad.SetNet(net(lcdpins[num]));f.Add(pad)
parts.append(dict(ref='DS1',value=f.GetValue(),mpn='DE188-RU-30/7,5/V(3V)',manufacturer='Display Elektronik',footprint='ClickCounter:DE188_20P_34.9x13mm',x=21,y=8.75,rotation=0,side='top',pins={str(k):n for k,n in lcdpins.items()},notes='THT hand solder; glass rear 4.0 mm above PCB top; 260 C / 5 s maximum; quote-only display, sample qualification required'))
# Fab rectangle / assembly outline for custom glass.
for a in [(-17.45,-6.5,17.45,-6.5),(17.45,-6.5,17.45,6.5),(17.45,6.5,-17.45,6.5),(-17.45,6.5,-17.45,-6.5)]:line(a[0]+21,a[1]+8.75,a[2]+21,a[3]+8.75,p.F_Fab,.1)
add('SW1','COUNT','MX1A-E1NW','Cherry','Button_Switch_Keyboard:SW_Cherry_MX_1.00u_PCB',14.015,22.92,pins={1:'COUNT_N',2:'GND'},notes='Clicky blue; PCB-mount 5-pin solder version; full hand solder')
add('SW2','RESET','MX1A-E1NW','Cherry','Button_Switch_Keyboard:SW_Cherry_MX_1.00u_PCB',33.065,22.92,pins={1:'RESET_N',2:'GND'},notes='Same switch as SW1')
add('J1','USB-C charge','USB4105-GF-A','GCT','Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal',38.9,13.3,90,pins={'A1':'GND','A12':'GND','B1':'GND','B12':'GND','A4':'VBUS','A9':'VBUS','B4':'VBUS','B9':'VBUS','A5':'CC1','B5':'CC2','SH':'GND'},notes='0.95 mm standard stakes; D+/D-/SBU unconnected; shell grounded')
add('J2','Battery + NTC','SM04B-SRSS-TB(LF)(SN)','JST','Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal',5,16.8,90,pins={1:'CELL_P',2:'CELL_N_RAW',3:'TEMP_SENSE',4:'GND'},notes='Mating keyed custom pack CC-BAT-001; no bare coin-cell holder')
mp={6:'COM0',5:'COM1',4:'COM2',3:'COM3',14:'GND',15:'V3',16:'SBWTDIO',17:'SBWTCK',26:'COUNT_N',25:'RESET_N',10:'LCDCAP1',11:'LCDCAP0'}
for i,pin in enumerate([2,1,48,47,46,45,44,43,42,41,40,39,38,37,36,35]):mp[pin]='SEG'+str(i)
add('U1','MSP430FR4133','MSP430FR4133IG48R','Texas Instruments','Package_SO:TSSOP-48_6.1x12.5mm_P0.5mm',21,8.75,90,pins=mp,notes='48-pin TSSOP, not the earlier 64-pin draft; SBW program and verify')

# Power and protection on reverse side, clear of LCD leads and switch posts.
add('U2','Li-ion charger','BQ25185DLHR','Texas Instruments','Package_DFN_QFN:Texas_DLH0010A_WSON-10-1EP_2.2x2mm_P0.4mm_EP0.9x1.5mm',33,7,0,'bottom',{1:'SYS',2:'CELL_P',4:'CE_N',5:'GND',6:'TS_FIXED',7:'VSET',8:'ISET',10:'VBUS',11:'GND'},'4.2 V; 100 mA input limit; 18.2 mA nominal battery charge')
add('U3','3.0 V LDO','TPS7A0230DBVR','Texas Instruments','Package_TO_SOT_SMD:SOT-23-5',27,7,0,'bottom',{1:'SYS',2:'GND',3:'SYS',4:'GND',5:'V3'})
add('U4','Cell protector','BQ29700DSER','Texas Instruments','Package_SON:WSON-6_1.5x1.5mm_P0.5mm',7,6,0,'bottom',{2:'COUT',3:'DOUT',4:'CELL_N_RAW',5:'BAT_SENSE',6:'VMINUS'})
add('Q1','Discharge FET','DMN2056U-7','Diodes Incorporated','Package_TO_SOT_SMD:SOT-23',5,11,0,'bottom',{1:'DOUT',2:'CELL_N_RAW',3:'FET_DRAIN'})
add('Q2','Charge FET','DMN2056U-7','Diodes Incorporated','Package_TO_SOT_SMD:SOT-23',9,11,180,'bottom',{1:'COUT',2:'SENSE_FET',3:'FET_DRAIN'})
add('U5','Charge temperature window','TLV7042DGKR','Texas Instruments','Package_SO:VSSOP-8_3x3mm_P0.65mm',17,7,0,'bottom',{1:'TEMP_OK',2:'TEMP_SENSE',3:'TEMP_COLD',4:'GND',5:'TEMP_SENSE',6:'TEMP_HOT',7:'TEMP_OK',8:'VBUS'},'USB-powered independent conservative charge-temperature window')
add('Q3','Charge enable','2N7002','Nexperia','Package_TO_SOT_SMD:SOT-23',21.5,17.8,0,'bottom',{1:'TEMP_OK',2:'GND',3:'CE_N'})
add('D1','USB ESD','USBLC6-2SC6','STMicroelectronics','Package_TO_SOT_SMD:SOT-23-6',35,17.8,0,'bottom',{1:'CC1',2:'GND',3:'CC2',4:'CC2',5:'VBUS',6:'CC1'})

def R(ref,val,code,a,z,x,y,rot=0):return add(ref,val,'RC0603FR-07'+code+'L','Yageo','Resistor_SMD:R_0603_1608Metric',x,y,rot,'bottom',{1:a,2:z},'1%, 0603, 0.1 W')
R('R1','5.1k','5K1','CC1','GND',30,17.5,90)
R('R2','5.1k','5K1','CC2','GND',32,17.5,90)
R('R3','24k','24K','VSET','GND',36.6,5.5,90)
R('R4','16.5k','16K5','ISET','GND',36.6,9.5,90)
R('R5','10k','10K','TS_FIXED','GND',33.5,11,0)
R('R6','100k','100K','VBUS','CE_N',25,17.8,90)
R('R7','330','330R','CELL_P','BAT_SENSE',4,5.3,90)
R('R8','2.2k','2K2','GND','VMINUS',10,5.3,90)
R('R9','3.3','3R3','SENSE_FET','GND',12.5,10.5,90)
R('R10','10k','10K','VBUS','TEMP_SENSE',13.5,4.8,90)
R('R11','49.9k','49K9','VBUS','TEMP_COLD',14.2,17.8,90)
R('R12','40.2k','40K2','TEMP_COLD','TEMP_HOT',16.4,17.8,90)
R('R13','60.4k','60K4','TEMP_HOT','GND',18.6,17.8,90)
R('R14','100k','100K','VBUS','TEMP_OK',20.5,5.3,90)
R('R15','1M','1M','TEMP_OK','GND',20.5,10,90)
R('R16','47k','47K','V3','SBWTDIO',23.5,11.5,90)
R('R17','470k','470K','V3','COUNT_N',8,36.5,0)
R('R18','470k','470K','V3','RESET_N',32,36.5,0)
R('R19','2k','2K','ISET','RC_COMP',29.5,12.5,0)

def C(ref,val,mpn,a,z,x,y,rot=0,size='0603',notes=''):
    fp={'0603':'C_0603_1608Metric','0805':'C_0805_2012Metric'}[size]
    return add(ref,val,mpn,'Murata' if not mpn.startswith('C0603') else 'KEMET','Capacitor_SMD:'+fp,x,y,rot,'bottom',{1:a,2:z},notes)
for ref,a,z,x,y,rot in [('C4','BAT_SENSE','CELL_N_RAW',7,3,0),('C7','V3','GND',25,3,0),('C8','LCDCAP1','LCDCAP0',14,11,0),('C9','VBUS','GND',17,3,0)]:C(ref,'100n','GRM188R71H104KA93D',a,z,x,y,rot,notes='100 nF, 50 V, X7R')
C('C1','2.2u','GRM21BR71E225KA73L','VBUS','GND',33,3,0,'0805','2.2 uF, 25 V, X7R; effective >=1 uF at 5 V')
C('C2','10u','GRM21BR61E106KA73L','SYS','GND',29,3,0,'0805','10 uF, 25 V, X5R; effective >=1 uF at 4.5 V')
C('C3','2.2u','GRM21BR71E225KA73L','CELL_P','GND',38.5,3,90,'0805','2.2 uF, 25 V, X7R')
C('C5','2.2u','GRM21BR71E225KA73L','SYS','GND',29.5,9.5,90,'0805')
C('C6','2.2u','GRM21BR71E225KA73L','V3','GND',23.5,7,90,'0805')
for ref,a,x,y,rot in [('C10','SBWTDIO',25.5,11.5,90),('C11','COUNT_N',8,38.3,0),('C12','RESET_N',32,38.3,0)]:C(ref,'1n','GRM1885C1H102JA01D',a,'GND',x,y,rot,notes='1 nF, 50 V, C0G')
C('C13','4.7n','C0603C472J5RACTU','RC_COMP','GND',32.7,12.5,0,notes='TI EVM low-current series compensation: ISET -> 2k -> 4.7n -> GND')

# Flat bottom-side pogo lands: no connector mass, programming after full soldering.
for i,n in enumerate(['GND','V3','SBWTDIO','SBWTCK','VBUS','SYS','CELL_P','CELL_N_RAW','COUNT_N','RESET_N']):
    xx=9+(i%5)*3; yy=37.5 if i<5 else 31.7
    f=add('TP'+str(i+1),n,'PCB LAND','PCB','TestPoint:TestPoint_Pad_D1.5mm',xx,yy,0,'bottom',{1:n},'Not a fitted component; pogo contact after assembly')

# Mounts match enclosure geometry after fit-study revision. No conductive hardware.
for i,(x,y) in enumerate([(2.5,37.5),(39.5,37.5)]):add('H'+str(i+1),'M2 clearance','NPTH','PCB','MountingHole:MountingHole_2.2mm_M2',x,y,notes='Unplated mechanical hole; not fitted')
for text,x,y,layer,size in [('CLICK Q1',21,38.3,p.F_SilkS,1),('QUOTE PROTOTYPE',21,35.3,p.B_SilkS,.8)]:
    t=p.PCB_TEXT(b);t.SetText(text);t.SetPosition(v(x,y));t.SetTextSize(v(size,size));t.SetTextThickness(p.FromMM(.12));t.SetLayer(layer)
    if layer==p.B_SilkS:t.SetMirrored(True)
    b.Add(t)

assert nets['CELL_N_RAW']!=nets['GND']
b.SetFileName(str(OUT/'click-counter-Q1.kicad_pcb'))
p.SaveBoard(b.GetFileName(),b)
assert p.ExportSpecctraDSN(b,str(OUT/'click-counter-Q1.dsn'))
(OUT/'netlist.json').write_text(json.dumps(dict(board_mm=[42,40,1],layers=4,revision='Q1 quote prototype',parts=parts),indent=2))
with (ROOT/'procurement'/'BOM-Q1.csv').open('w',newline='') as out:
    w=csv.writer(out);w.writerow(['Comment','Designator','Footprint','Quantity','Manufacturer','Manufacturer Part Number','Assembly','Notes'])
    for d in parts:
        if d['ref'].startswith(('TP','H')):continue
        w.writerow([d['value'],d['ref'],d['footprint'],1,d['manufacturer'],d['mpn'],d['side'],d['notes']])
    w.writerow(['Battery + NTC lead assembly','BAT1','OFFBOARD',1,'Supplier custom with genuine EEMB cell','CC-BAT-001','Connect after electrical test','See CC-BAT-001 specification; includes LIR2032 45mAh, NCP18XH103F03RB NTC, SHR-04V-S housing, SSH-003T-P0.2 contacts and insulated wires; quote all fabrication and lithium shipping'])
    w.writerow(['Black DSA MX keycap','K1,K2','OFFBOARD',2,'Adafruit','4997','Press fit','4997 is a 10-pack: quote two individual caps/unit; pack remainder and MOQ explicitly'])
print('Generated',len(parts),'footprints,',len(nets),'nets')
