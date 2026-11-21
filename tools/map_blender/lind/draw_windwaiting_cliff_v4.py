"""Assemble V4 design and measured section plates from its render checkpoint."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.collections import LineCollection, PolyCollection
import matplotlib.pyplot as plt


def photo(axis, image, title):
    axis.imshow(plt.imread(image))
    axis.set_title(title, loc="left", fontsize=10)
    axis.axis("off")


def save_svg(figure, path):
    figure.savefig(path)
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    folder = args.output
    targets = json.loads((folder / "design-targets.json").read_text())
    qa = json.loads((folder / "qa.json").read_text())
    official = Path("assets/approved/game/cliff/sunset_background.png")
    with PdfPages(folder / "precision-blueprint.pdf") as pdf:
        fig, axes = plt.subplots(2, 2, figsize=(13, 8), layout="constrained")
        photo(axes[0, 0], official, "Official CG | 836 × 471 landmarks rescaled")
        for x, y in (point for point in targets["image_measurement"]["official_836x471"].values()
                     if isinstance(point, list)):
            axes[0, 0].plot(x * 2, y * (941 / 471), "o", color="gold", ms=3)
        photo(axes[0, 1], folder / "clay-sunset.png", "V4 B | held sunset camera")
        photo(axes[1, 0], folder / "visible-ids.png", "First camera hits | masks by provisional Y bands")
        photo(axes[1, 1], folder / "cliff-v4-photo-spawn.png", "Game camera | candidate mesh")
        fig.suptitle("01  Projection and depths | CG lens and invisible surfaces unresolved")
        pdf.savefig(fig)
        plt.close(fig)

        fig, axes = plt.subplots(1, 3, figsize=(15, 7), layout="constrained")
        for ax, mode in zip(axes, ("A", "B")):
            rows = targets["authored_provisional"][mode]["sections"]
            y, west, east, crest, wb, eb, twist = zip(*rows)
            ax.fill_betweenx(y, west, east, fc="#e7ebed")
            ax.plot(west, y, color="#21445c")
            ax.plot(east, y, color="#21445c")
            ax.scatter([(a+b)/2 + .2*t for a, b, t in zip(west, east, twist)], y, c=crest,
                       cmap="viridis", vmin=0, vmax=9)
            for row in rows:
                ax.plot(row[1:3], [row[0]]*2, color="#91a3ab", lw=.6)
                ax.text(row[2]+.2, row[0], f"{row[3]:.2f}", fontsize=7)
            ax.set_title(f"{mode} | provisional plan + crest elevation")
        mesh = qa["authoring_mesh"]
        vertices = mesh["vertices"]
        faces = sorted(mesh["faces"], key=lambda f: sum(vertices[i][2] for i in f["vertices"])/len(f["vertices"]))
        colors = ("#b3a38e", "#909979", "#677789", "#3d4a58")
        polygons = [[vertices[i][:2] for i in face["vertices"]] for face in faces]
        axes[2].add_collection(PolyCollection(polygons, facecolors=[colors[f["material_id"]] for f in faces],
                                             edgecolors="none"))
        axes[2].set_title("B | measured authoring mesh plan")
        for ax in axes:
            ax.set(xlim=(-8, 15), ylim=(-31, 3), xlabel="X (BU)", ylabel="Y (BU)", aspect="equal")
            ax.axhline(0, ls=":", color="#35485e", lw=.6)
        fig.suptitle("02  Plan | inland +Y, sea -Y | BU provisional, not official placement")
        pdf.savefig(fig)
        save_svg(fig, folder / "plan.svg")
        plt.close(fig)

        for axis in ("X", "Y"):
            fig, grid = plt.subplots(3, 2, figsize=(14, 8), layout="constrained")
            sections = (item for item in qa["transverse_and_longitudinal_reference_sections"]
                        if item["plane"] == axis)
            for ax, item in zip(grid.flat, sections):
                for variant, color in (("v3d", "#b27655"), ("v4", "#276079")):
                    ax.add_collection(LineCollection(item["segments"][variant], colors=color, linewidths=.8))
                ax.axhline(0, color="#81878e", ls="--", lw=.7)
                ax.set(xlim=((-34, 8) if axis == "X" else (-16, 16)), ylim=(-3, 12),
                       xlabel=f"{item['coordinates'][0]} (BU)", ylabel="Z (BU)",
                       title=f"{axis} = {item['station_BU']:.2f} BU")
            fig.suptitle(f"Measured {axis}-plane sections | V3-D orange, V4 blue | water datum dashed")
            pdf.savefig(fig)
            save_svg(fig, folder / f"sections-{axis.lower()}.svg")
            plt.close(fig)

        fig, grid = plt.subplots(2, 3, figsize=(15, 7), layout="constrained")
        for ax, view in zip(grid.flat, ("front", "rear", "left", "right", "overhead", "underside")):
            photo(ax, folder / f"clay-{view}.png", view.capitalize())
        fig.suptitle("05  Inspection elevations | measured model and underside support")
        pdf.savefig(fig)
        plt.close(fig)


if __name__ == "__main__":
    main()
