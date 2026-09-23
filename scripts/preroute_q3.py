"""Seed short Q3 supply/return paths before incremental two-layer routing.

Requires the freshly rebuilt, unrouted Q3 candidate. Tracks and vias are locked
because Freerouting's incremental SES omits its fixed seeds. Native DRC and
physical first-article tests remain required; this is not a release action.
"""
from pathlib import Path
import pcbnew as p
from sync_q3_board import sync

OUT = Path(__file__).resolve().parents[1] / 'electronics/q3'


def main():
    path = OUT/'click-counter-Q3.kicad_pcb'
    board = p.LoadBoard(str(path))
    assert board.GetCopperLayerCount() == 2
    assert not len(board.GetTracks()), 'Rebuild the Q3 candidate intentionally before seeding routes'
    sync(board)
    def xy(point):
        return p.VECTOR2I(p.FromMM(point[0]),p.FromMM(point[1]))
    def route(net, points, width=.25, layer=p.B_Cu):
        for a,b in zip(points,points[1:]):
            if a == b: continue
            item=p.PCB_TRACK(board)
            item.SetStart(xy(a)); item.SetEnd(xy(b))
            item.SetWidth(p.FromMM(width)); item.SetLayer(layer)
            item.SetNet(board.FindNet(net)); item.SetLocked(True); board.Add(item)
    def via(net, point):
        item=p.PCB_VIA(board); item.SetPosition(xy(point))
        item.SetWidth(p.FromMM(.6)); item.SetDrill(p.FromMM(.3))
        item.SetViaType(p.VIATYPE_THROUGH); item.SetLayerPair(p.F_Cu,p.B_Cu)
        item.SetNet(board.FindNet(net)); item.SetLocked(True); board.Add(item)

    # TPS63900: contiguous bottom-layer switching loops, no signal via.
    # Keep the Murata center-body copper/via exclusions intact.
    route('OLED_LX1',[(22.15,12),(23.5,12),(23.8,11.7),(24.4,11.7)])
    route('OLED_LX2',[(22.15,11),(22.8,11),(23.7,10.1),(24.4,10.1)])
    route('SYS',[(22.15,12.5),(22.85,12.5),(23.6,13.25),(24.2,13.25)])
    route('OLED_4V',[(22.15,10.5),(22.15,9.5),(21.95,9.3),(21.95,8.6)])
    route('OLED_4V',[(21.95,8.6),(23.75,8.6),(24,8.35)],.4)
    route('GND',[(22.15,11.5),(21,11.5)],.3)
    route('GND',[(21,11.5),(21,12.8),(20.7,13.1),(20.7,13.3)],.5)
    route('GND',[(21,12.8),(21.4,13.2),(21.4,13.3)],.5)
    for point in [(20.7,13.3),(21.4,13.3),(23.2,15.15),(19.35,8.6),(24,5.45)]:
        via('GND',point)
    route('GND',[(24.2,15.15),(23.2,15.15)],.4)
    route('GND',[(20.05,8.6),(19.35,8.6)],.4)
    route('GND',[(24,6.45),(24,5.45)],.4)

    # MCU local decoupling and two close returns to the opposite ground pour.
    route('V3',[(22.25,31.2875),(22.25,30.25),(22.7,29.8),(22.7,29.375)],.2)
    route('V3',[(22.7,29.375),(25.575,29.375),(25.6,29.35)],.3)
    route('GND',[(21.75,31.2875),(21.75,30.3),(21.3,29.85)],.2)
    route('GND',[(22.7,27.825),(23.55,27.825)],.25)
    route('GND',[(25.6,27.45),(25.6,26.3)],.3)
    for point in [(21.3,29.85),(23.55,27.825),(25.6,26.3)]: via('GND',point)
    # USB-powered comparator bypass and independent, normally-off gate pulls.
    route('VBUS',[(18.2,6.475),(20.6,6.475),(21,6.075)])
    route('GND',[(21,4.525),(21,3.65)])
    route('GND',[(13.8,4.525),(12.7,4.525)])
    for point in [(21,3.65),(12.7,4.525),(15.675,24.5),(15.675,28.5),(18,25.55)]:
        via('GND',point)
    route('TEMP_COLD_OK',[(17.325,23.45),(19.0625,23.45)],.2)
    route('TEMP_HOT_OK',[(17.325,27.45),(19.0625,27.45)],.2)
    route('GND',[(15.675,23.45),(15.675,24.5)])
    route('GND',[(15.675,27.45),(15.675,28.5)])
    route('GND',[(19.0625,25.55),(18,25.55)])
    # Charger and regulator capacitors: local branches; wider common rail
    # joins are completed after global routing and checked by native DRC.
    route('SYS',[(30.9,12.1),(30.9,12.8)],.18)
    via('SYS',(30.9,12.8)); via('SYS',(27.6,12.45))
    route('SYS',[(30.9,12.8),(30.55,12.45),(27.6,12.45)],.3,p.F_Cu)
    route('SYS',[(27.6,12.45),(28.6,12.45)],.3)
    route('CELL_P',[(30.9,11.7),(30.15,11.7),(29.7,12.15),(29.7,13.2),(30.6,14.1),(31.05,14.1)],.15)
    route('GND',[(32,11.3),(32,12.7)],.5)
    via('GND',(32,12.7))
    for ref,num,point in [('C1','2',(33.05,9.1)),('C2','2',(28.6,15.25)),('C3','2',(33.85,14.1))]:
        fp=next(f for f in board.GetFootprints() if f.GetReference()==ref)
        pad=next(pad for pad in fp.Pads() if pad.GetNumber()==num)
        pos=pad.GetPosition(); route('GND',[(p.ToMM(pos.x),p.ToMM(pos.y)),point]);via('GND',point)
    # OLED flying capacitors: ordered FPC escapes and compact bottom paths.
    # No through via overlaps an OLED FPC or capacitor solder land.
    for net,point,y in [('OLED_C2P',(37.95,9.53),9.53),('OLED_C2N',(37.4,8.91),8.91),
                        ('OLED_C1P',(37.95,8.29),8.29),('OLED_C1N',(37.4,7.67),7.67),
                        ('OLED_VBAT',(37.95,7.05),7.05),('GND',(37.95,5.81),5.81)]:
        via(net,point);route(net,[(39.75,y),point],.15,p.F_Cu)
    route('OLED_C2P',[(37.95,9.53),(38.505,8.975),(39.3,8.975)],.15)
    route('OLED_C2N',[(37.4,8.91),(38.1,8.91),(38.55,8.46),(38.55,7.75),(38.875,7.425),(39.3,7.425)],.15)
    route('OLED_C1P',[(37.95,8.29),(36.885,8.29),(36.3,8.875),(36.3,9.125)],.15)
    route('OLED_C1N',[(37.4,7.67),(36.395,7.67),(36.3,7.575)],.15)
    route('OLED_VBAT',[(37.95,7.05),(37.025,6.125),(37.025,6.05)],.2)
    via('GND',(35.15,7));via('GND',(37.9,3.65))
    route('GND',[(35.475,6.05),(35.475,6.675),(35.15,7)],.2)
    route('GND',[(37.95,5.81),(37.5,6.26),(35.89,6.26),(35.15,7)],.2,p.F_Cu)
    route('GND',[(37.175,4.45),(37.9,3.725),(37.9,3.65)],.2)
    # Grounded connector shells use solid pours; solder heat demand is stated
    # in assembly guidance rather than weakening the connectivity checks.
    for fp in board.GetFootprints():
        if fp.GetReference()=='J1':
            for pad in fp.Pads():
                if pad.GetNumber()=='SH': pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)
    p.SaveBoard(str(path),board)
    assert p.ExportSpecctraDSN(board,str(OUT/'click-counter-Q3.dsn'))
    print('Q3 short power routes locked; requires fresh native DRC before global routing.')


if __name__=='__main__':main()
