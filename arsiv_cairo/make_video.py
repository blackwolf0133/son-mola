"""Kullanım:
  python make_video.py episodes/001_istanbul_fethi.json            -> output/001.mp4
  python make_video.py episodes/001_istanbul_fethi.json --preview  -> her sahneden PNG
"""
import argparse
import json
import os

import cairo

from engine import render as R
from engine import draw as D

VOICE = os.environ.get("COPTARIH_VOICE", "models/tr_TR-fahrettin-medium.onnx")


def preview(ep_path, outdir="output/preview"):
    os.makedirs(outdir, exist_ok=True)
    ep = json.load(open(ep_path, encoding="utf-8"))
    paper = D.make_paper()
    header = R.make_header(ep, paper)
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, D.W, D.H)
    ctx = cairo.Context(surf)
    for i, sc in enumerate(ep["scenes"]):
        vd = 5.0
        chunks = R.chunk_words(R.word_timings(sc["text"], vd), ctx)
        for tt in (0.4 * vd, 0.85 * vd):
            ctx.set_source_surface(header)
            ctx.paint()
            R.draw_scene(ctx, sc, tt, vd + 0.4, vd)
            R.draw_year_tag(ctx, ep["year"])
            R.draw_caption(ctx, chunks, tt)
            surf.write_to_png(f"{outdir}/s{i:02d}_{tt:.1f}.png")
    print("Önizlemeler:", outdir)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.preview:
        preview(a.episode)
    else:
        ep = json.load(open(a.episode, encoding="utf-8"))
        os.makedirs("output", exist_ok=True)
        out = a.out or f"output/{ep['id']}.mp4"
        R.render_episode(a.episode, out, VOICE, workdir=f"build/{ep['id']}")
