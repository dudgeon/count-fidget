# Q5A render pipeline

This folder makes the renders and assembly films for the Q5A acrylic-lid enclosure (`mechanical/q5-acrylic/`). Everything is driven from the native files:
- the locked Q5 board;
- the Q5A enclosure generator;
- the Q5 firmware's own OLED renderer.

Only the appearance models listed below are hand-made. Intermediates go to `build/render-q5-acrylic/`, which is gitignored.

Tools used: Blender 5.2.2 (Cycles, CPU), KiCad 10.0.6 (`kicad-cli`, `pcbnew`), CadQuery 2.8, rsvg-convert, ffmpeg 6, Pillow.
- Studio HDRIs `studio_small_09` and `photo_studio_loft_hall` (4K) are CC0 from Poly Haven.
- Inter and JetBrains Mono (OFL) come from Google Fonts. The render steps expect both HDRIs (`*_4k.exr`), `Inter-{300,400,500,600,700}.ttf` and `JetBrainsMono-{400,500}.ttf` in `build/render-q5-acrylic/assets/`.
- The KiCad 10 STEP models the board references come from `kicad-packages3D` (for example under `/opt/kicad3d`).

| Step | Command | Output |
|---|---|---|
| 1. Board textures + GLB | `python3 pcb_textures.py --px-per-mm 100` (KiCad Python) | Copper, mask, silk, paste and drill layers as packed RGBA maps (100 px/mm); `board.glb` holds the board body and component STEP models |
| 2. Enclosure | `python3 ../build_q5_acrylic_enclosure.py --kicad-python ...` | Checked tray, lid, keycaps (`mechanical/q5-acrylic/`) |
| 3. Render parts | `python3 build_render_assets.py --kicad-python ...` | `q5a-parts.glb` |
| 4. Display frames | `python3 oled_frames.py` | 128 × 64 PNGs from `firmware/q5-stm32/oled.c` |
| 5. Decals | `python3 decals.py` | Cell marking, OLED module silk |
| 6. Stills | `blender -b --python render_stills.py -- --shots hero,display,... --samples 256` | `stills-final/*.png` |
| 7. Film scene | `blender -b --python animate.py` | `film.blend` and `anchors.json` (screen positions of labelled parts per frame) |
| 8. Film frames | `blender -b film.blend --python render_film.py -- --start 1 --end 984` | 1920 × 1080 PNGs, 16 spp + OIDN, resumable |
| 9. Cuts | `python3 compose_videos.py [--crf 20]` | `mechanical/q5-acrylic/video/*.mp4`: the film (opening title, end card) and the explainer (captions, labels that track the parts, holds), H.264 |

`step 3` contents:
- the enclosure parts from the generator;
- appearance models of the CPG151101D13 switch (clear PC top housing, black PA base, cyan stem, white click jacket, spring), the HS96L01W4S03 module (blue PCB, glass stack, chip-on-glass driver, FPC, header), the CR2032-BS-6-1 holder with an LIR2032 cell, the purple CPG151101S11 sockets, the TS-1088 tact switch, M2 × 14 screws and brass spacers.

Materials:
- **Soldermask** is shaded from the textures rather than modelled as a translucent coating. It is lighter over copper and darker over bare FR-4, with a clear coat, and copper and silk height come from blurred masks. ENIG is shown where the mask opens, and SAC solder where the paste layer puts it.
- **Acrylic** and the switch housings are transmissive, but pass shadow and diffuse rays straight through (no caustics), so the parts under the lid stay lit without long render times.
- **Printed plastic** carries 0.16 mm layer lines as a bump.
- **The OLED** is an emissive plane textured with the firmware bitmap and a 0.88-fill pixel grid.

Render cost on a 4-core CPU: a still takes about 4–5 minutes at 1080p/256 spp. A film frame takes 31–80 s (mean 43 s) at 1080p/16 spp, so the 984 frames took 11.8 hours.
