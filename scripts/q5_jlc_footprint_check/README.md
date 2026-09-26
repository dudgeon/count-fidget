# Q5 footprint check against JLC's own (EasyEDA/LCSC) footprints

This check was added on 26 Sep 2026 to de-risk the first order. It works in four steps:
1. It fits each vendor-assembled KiCad footprint against the footprint JLC uses for that LCSC part. The fit is by pad number, over rotations 0/90/180/270, with and without a mirror.
2. It checks pin 1 and polarity through the LCSC pin names.
3. It predicts the rotation and offset corrections JLC's placement preview will need for our raw KiCad CPL.

The last run matched all 42 unique parts, with no pad-order or mirror error. The full report is `REPORT.md`.

The bottom-side convention used, rotation = 180 − KiCad θ with a mirrored X, is **community-documented, not JLC-documented**: KiKit, the Bouni kicad-jlcpcb-tools plugin and KiBot use it. Always confirm BT1 +, D4's cathode and U3's pin 1 in JLC's preview before accepting.

Run from this directory, with KiCad's Python for `kicad_dump.py`:

```sh
python3 fetch_easyeda.py      # downloads ./easyeda/ (gitignored)
python3 kicad_dump.py kicad.json   # our pads -> kicad.json, kicad_lib.json
python3 analyze.py            # fit -> results.json/csv
python3 corrections.py        # predicted JLC preview corrections -> corrections.json/csv
```
