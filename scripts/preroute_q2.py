"""Place reviewed short Q2 capacitor/gate routes before general routing.

Run only on the separate freshly built unrouted Q2 board. Native DRC must check
these paths before and after general routing. Nothing here qualifies hardware.
"""
from pathlib import Path
import pcbnew as p

OUT = Path(__file__).resolve().parents[1] / 'electronics/q2'


def main():
    path = OUT/'click-counter-Q2.kicad_pcb'
    board = p.LoadBoard(str(path))
    assert not len(board.GetTracks()), 'Requires an intentionally rebuilt unrouted Q2 board'
    def xy(point):
        return p.VECTOR2I(p.FromMM(point[0]),p.FromMM(point[1]))
    def route(net, layer, points, width=.127):
        for a,b in zip(points,points[1:]):
            if a == b:
                continue
            item = p.PCB_TRACK(board)
            item.SetStart(xy(a)); item.SetEnd(xy(b))
            item.SetWidth(p.FromMM(width)); item.SetLayer(layer)
            item.SetNet(board.FindNet(net)); item.SetLocked(True)
            board.Add(item)
    def via(net, point):
        item = p.PCB_VIA(board)
        item.SetPosition(xy(point)); item.SetWidth(p.FromMM(.6))
        item.SetDrill(p.FromMM(.3)); item.SetViaType(p.VIATYPE_THROUGH)
        item.SetLayerPair(p.F_Cu,p.B_Cu); item.SetNet(board.FindNet(net))
        item.SetLocked(True); board.Add(item)
    paths = [
        ('LCD_R13',(17.55,10.8),[(18.25,12.4625),(18.25,11.5),(17.55,10.8)],[(17.55,10.8),(17.55,11.475),(17.8,11.725)]),
        ('LCD_R23',(18.4,10.8),[(18.75,12.4625),(18.75,11.15),(18.4,10.8)],[(18.4,10.8),(18.95,11.35),(19.4,11.725)]),
        ('LCD_R33',(19.25,10.8),[(19.25,12.4625),(19.25,10.8)],[(19.25,10.8),(19.25,11),(20.275,11),(21,11.725)]),
        ('LCDCAP1',(20,10.45),[(19.75,12.4625),(19.75,10.7),(20,10.45)],[(20,10.45),(19.225,9.675),(19.225,9.6)]),
        ('LCDCAP0',(20.75,10.55),[(20.25,12.4625),(20.25,11.05),(20.75,10.55)],[(20.75,10.55),(20.775,10.525),(20.775,9.6)]),
        ('V3',(22.25,10.8),[(22.25,12.4625),(22.25,10.8)],[(22.25,10.8),(22.25,11.375),(22.6,11.725)]),
    ]
    for net, point, front, back in paths:
        via(net,point)
        route(net,p.F_Cu,front,.2 if net=='V3' else .127)
        route(net,p.B_Cu,back,.2 if net=='V3' else .127)
    route('VBUS',p.B_Cu,[(19.2,7.975),(21,7.975),(21.1,8.075)],.25)
    # Local plane returns. Through vias are outside all solderable SMD lands.
    for point in [(18.45,14.15),(21,14.16),(23.55,14.15),(22.01,6.525),(13.6,6.125),(16.675,24.5),(16.675,30.55),(19.05,26.8)]:
        via('GND',point)
    for points in [[(17.8,13.275),(17.8,13.5),(18.45,14.15)],
                   [(19.4,13.275),(18.525,14.15),(18.45,14.15)],
                   [(21,13.275),(21,14.16)],
                   [(22.6,13.275),(23.475,14.15),(23.55,14.15)],
                   [(21.1,6.525),(22.01,6.525)],
                   [(14.8,6.025),(14.7,6.125),(13.6,6.125)],
                   [(16.675,25.45),(16.675,24.5)],
                   [(16.675,29.6),(16.675,30.55)],
                   [(20.0625,27.55),(19.05,26.8)]]:
        route('GND',p.B_Cu,points,.25)
    route('GND',p.F_Cu,[(21.75,12.4625),(21.75,13.41),(21,14.16)],.2)
    route('TEMP_COLD_OK',p.B_Cu,[(18.325,25.45),(20.0625,25.45)],.2)
    route('TEMP_HOT_OK',p.B_Cu,[(18.325,29.6),(19.9125,29.6),(20.0625,29.45)],.2)
    for fp in board.GetFootprints():
        if fp.GetReference()=='J1':
            for pad in fp.Pads():
                if pad.GetNumber()=='SH':
                    pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)
    p.SaveBoard(str(path),board)
    assert p.ExportSpecctraDSN(board,str(OUT/'click-counter-Q2.dsn'))
    print('Q2 critical paths pre-routed and locked; native DRC required.')


if __name__=='__main__':
    main()
