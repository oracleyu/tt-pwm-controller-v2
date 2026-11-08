"""Render the actual final GDS using KLayout's headless LayoutView."""
from pathlib import Path
import os
root=Path(__file__).resolve().parents[1]
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import klayout.db as db
import klayout.lay as lay
files=list((root/'src/runs/tutorial/final/gds').glob('*.gds'))
if not files:
    raise SystemExit('No final GDS exists; refusing to draw a substitute layout.')
gds=files[0]
view=lay.LayoutView()
view.load_layout(str(gds),0)
pdk=Path(os.environ.get('PDK_ROOT',root/'.pdk'))
lyps=list((pdk/'sky130A/libs.tech/klayout/tech').glob('*.lyp'))
if lyps: view.load_layer_props(str(lyps[0]))
view.max_hier()
view.zoom_fit()
view.set_config('background-color','#10151f')
view.set_config('grid-visible','false')
view.save_image(str(root/'reports/layout.png'),1600,1100)
# An additional view of actual metal geometry, hiding diffusion/filler detail.
for it in view.each_layer():
    props=it
    props.visible=props.source_layer in (68,69,70,71) and props.source_datatype in (20,44)
view.set_config('text-visible','false')
view.save_image(str(root/'reports/layout-routing.png'),1600,1100)
layout=db.Layout();layout.read(str(gds))
top=layout.top_cell()
box=top.dbbox()
(root/'reports/gds-inspection.txt').write_text(f'file={gds.name}\ntop={top.name}\ndbu_um={layout.dbu}\nbbox_um={box}\nsize_um={box.width()} x {box.height()}\ncell_definitions={layout.cells()}\n')
print(root/'reports/layout.png')
