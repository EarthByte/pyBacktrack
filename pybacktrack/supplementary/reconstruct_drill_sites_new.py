#!/usr/bin/env python3
"""
Reconstruct DSDP/ODP/IODP drill-site paleocoordinates through time.

Two ways to specify the plate model:
  (a) PlateModelManager (default).  Fetches a named, version-pinned model
      from the EarthByte registry — e.g. alfonso2024, Muller2019,
      Merdith2021, Clennett2020.  See `pmm ls` or
      https://gwsdoc.gplates.org/models/ for the current list.
  (b) Custom files.  Pass --rotation FILE [FILE ...] and
      --static-polygons FILE [FILE ...] for project-internal models that
      aren't in PlateModelManager (e.g. unpublished Merdith v6-2 iterations).

Drill-site parsing uses pybacktrack.read_well_file() — the canonical tool
for these files.  Handles the full stratigraphic schema (lithology
fractions, well attributes) properly.  We read SiteLongitude /
SiteLatitude from the well attributes and use the bottom_age of the
oldest stratigraphic unit as the per-site time-range cap.

Anchor plate is an explicit CLI flag.  For Alfonso 2024 paired with
Merdith v6-2 paleogeography, use --anchor-plate-id 701701 (matches
Merdith's anchor=000 reference frame; non-standard but correct, see
docs/lithology_project_log.md §4.5).  Default is 701701 because that
is the project's current pairing.

Output (one file per drill site):
    Site<id>_paleocoords_<TAG>.tsv    tab-delimited, with #-comment header
        Columns: paleolon  paleolat  age_ma  plate_id
And a combined file:
    drill_sites_paleocoords_<TAG>.tsv    site_id paleolon paleolat age_ma plate_id

Usage:
    pip install gplately pybacktrack
    python scripts/reconstruct_drill_sites.py
    # Custom plate model:
    python scripts/reconstruct_drill_sites.py \\
        --rotation data/lithology/Merdith_etal_plate_model_1Ga-present_rev6-2/1000_0_rotfile_MER21.rot \\
        --static-polygons data/lithology/Merdith_etal_plate_model_1Ga-present_rev6-2/250-0_plate_boundaries_MER21.gpml \\
        --anchor-plate-id 0 \\
        --tag merdith2021_rev6_2
    # Sensitivity test (different anchor):
    python scripts/reconstruct_drill_sites.py --anchor-plate-id 0 --tag alfonso2024_anchor000
"""

from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

REPO  = Path(__file__).resolve().parent.parent
DATA  = REPO / "data" / "lithology"
DRILL = DATA / "DSDP-ODP-IODP-lithology"

DEFAULT_MODEL  = "alfonso2024"   # gplately's dev branch uses lowercase canonical names
DEFAULT_ANCHOR = 701701          # Alfonso 2024 ↔ Merdith anchor=000 — non-standard but correct
DEFAULT_TAG    = "alfonso2024_anchor701701"


def parse_args():
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    src = p.add_mutually_exclusive_group()
    src.add_argument(
        "--model", default=os.environ.get("PLATE_MODEL", DEFAULT_MODEL),
        help=f"PlateModelManager model name (default: {DEFAULT_MODEL}).  "
             f"Mutually exclusive with --rotation/--static-polygons.",
    )
    p.add_argument(
        "--rotation", nargs="+", type=Path, default=None,
        help="Custom rotation file(s).  If given, --static-polygons is "
             "also required and PlateModelManager is bypassed.",
    )
    p.add_argument(
        "--static-polygons", nargs="+", type=Path, default=None,
        help="Custom static-polygon file(s).  Use with --rotation.",
    )
    p.add_argument(
        "--anchor-plate-id", type=int, default=DEFAULT_ANCHOR,
        help=f"Anchor plate ID for the rotation model (default: {DEFAULT_ANCHOR}).  "
             f"701701 in Alfonso 2024 matches Merdith's anchor=000 reference "
             f"frame — non-standard looking but correct, see project log §4.5.  "
             f"Use 0 for Merdith-native rotations.",
    )
    p.add_argument(
        "--tag", default=DEFAULT_TAG,
        help=f"Suffix for output filenames (default: {DEFAULT_TAG}).  "
             f"Choose a new tag if rotation model or anchor changes so old "
             f"output is preserved alongside.",
    )
    p.add_argument(
        "--start-time", type=float, default=0.0,
        help="Start of time range, Ma (default: 0).",
    )
    p.add_argument(
        "--end-time", type=float, default=170.0,
        help="End of time range, Ma (default: 170 — Alfonso 2024 limit).",
    )
    p.add_argument(
        "--time-increment", type=float, default=1.0,
        help="Time step, Ma (default: 1).",
    )
    p.add_argument(
        "--site-glob", default="Site*_age_depth_litho.txt",
        help="Glob for drill-site input files in the DSDP-ODP-IODP-lithology "
             "directory (default: Site*_age_depth_litho.txt).  Use "
             "*_amended.txt if you prefer the amended files.",
    )
    return p.parse_args()


def main():
    args = parse_args()

    if (args.rotation is not None) ^ (args.static_polygons is not None):
        print("ERROR: pass --rotation AND --static-polygons together (or neither).",
              file=sys.stderr)
        sys.exit(1)

    # ── Imports gated so the script is syntax-checkable without GPlately ───
    try:
        import pygplates
        import pybacktrack
        import numpy as np
    except ImportError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("Install with:", file=sys.stderr)
        print("    conda install -c conda-forge gplately pybacktrack", file=sys.stderr)
        print("or", file=sys.stderr)
        print("    pip install gplately pybacktrack", file=sys.stderr)
        sys.exit(2)

    # ── Build rotation model + static polygons ─────────────────────────────
    if args.rotation is not None:
        print(f"Loading custom plate model:")
        for f in args.rotation:
            print(f"  rotation:        {f.relative_to(REPO) if REPO in f.parents else f}")
        for f in args.static_polygons:
            print(f"  static polygons: {f.relative_to(REPO) if REPO in f.parents else f}")
        rotation_model = pygplates.RotationModel([str(f) for f in args.rotation])
        static_polygon_features = pygplates.FeatureCollection(
            [str(f) for f in args.static_polygons]
        )
        model_label = "custom"
    else:
        try:
            from gplately import PlateModelManager
        except ImportError:
            print("ERROR: gplately not installed (needed for PlateModelManager).",
                  file=sys.stderr)
            print("Install with: pip install gplately", file=sys.stderr)
            sys.exit(2)
        print(f"Loading plate model '{args.model}' via PlateModelManager...")
        pmm = PlateModelManager()
        available = pmm.get_available_model_names()
        # Newer gplately uses lowercase canonical names; older versions
        # may use mixed/upper case (e.g. "alfonso2024").  Match
        # case-insensitively against whatever the registry exposes.
        canonical = {name.lower(): name for name in available}
        key = args.model.lower()
        if key not in canonical:
            print(f"ERROR: model '{args.model}' not registered.", file=sys.stderr)
            print(f"Available models: {', '.join(sorted(available))}",
                  file=sys.stderr)
            sys.exit(1)
        resolved = canonical[key]
        if resolved != args.model:
            print(f"  (resolved '{args.model}' -> '{resolved}')")
        model = pmm.get_model(resolved)

        # Dev gplately (>= 2.0.0.post19) changed PlateModel.get_rotation_model()
        # to return a list of files/features rather than a pygplates.RotationModel.
        # Same for get_static_polygons().  Wrap defensively so the script
        # works against either shape.
        rm_raw = model.get_rotation_model()
        if isinstance(rm_raw, pygplates.RotationModel):
            rotation_model = rm_raw
        else:
            rotation_model = pygplates.RotationModel(rm_raw)

        # Flatten whatever shape the dev gplately returns into a single
        # FeatureCollection.  pygplates.FeatureCollection's constructor only
        # accepts (single filename | sequence of Features | single Feature),
        # so a list-of-filenames or list-of-FeatureCollections needs to be
        # expanded by hand.
        sp_raw = model.get_static_polygons()

        def _to_feature_collection(raw):
            if isinstance(raw, pygplates.FeatureCollection):
                return raw
            if isinstance(raw, pygplates.Feature):
                return pygplates.FeatureCollection([raw])
            if isinstance(raw, (str, os.PathLike)):
                return pygplates.FeatureCollection(str(raw))
            feats: list = []
            for item in raw:
                if isinstance(item, pygplates.Feature):
                    feats.append(item)
                elif isinstance(item, pygplates.FeatureCollection):
                    feats.extend(list(item))
                elif isinstance(item, (str, os.PathLike)):
                    feats.extend(list(pygplates.FeatureCollection(str(item))))
                else:
                    raise TypeError(
                        f"unexpected item in static-polygons input: "
                        f"{type(item).__name__}"
                    )
            return pygplates.FeatureCollection(feats)

        static_polygon_features = _to_feature_collection(sp_raw)

        model_label = resolved

    print(f"  anchor plate: {args.anchor_plate_id}")
    print(f"  output tag:   {args.tag}")

    plate_partitioner = pygplates.PlatePartitioner(
        static_polygon_features, rotation_model
    )

    # ── Read all bundled lithologies (needed for pybacktrack well parsing) ──
    lithologies = pybacktrack.read_lithologies_files(
        pybacktrack.BUNDLE_LITHOLOGY_FILENAMES
    )

    # ── Iterate over drill-site input files ────────────────────────────────
    drill_files = sorted(DRILL.glob(args.site_glob))
    if not drill_files:
        print(f"ERROR: no drill-site files matched {args.site_glob} in {DRILL}",
              file=sys.stderr)
        sys.exit(1)
    print(f"\nFound {len(drill_files)} drill-site files matching '{args.site_glob}'.")

    combined_rows = []
    n_done = n_skip = 0
    for drill_file in drill_files:
        try:
            site = pybacktrack.read_well_file(
                str(drill_file),
                lithologies,
                well_attributes={
                    "SiteLongitude": ("longitude", float),
                    "SiteLatitude":  ("latitude",  float),
                },
            )
        except Exception as e:
            print(f"  [skip] {drill_file.name}: pybacktrack.read_well_file failed: {e}",
                  file=sys.stderr)
            n_skip += 1
            continue

        if not site.stratigraphic_units:
            print(f"  [skip] {drill_file.name}: no stratigraphic layers",
                  file=sys.stderr)
            n_skip += 1
            continue

        site_age = site.stratigraphic_units[-1].bottom_age
        if args.start_time > site_age:
            print(f"  [skip] {drill_file.name}: start_time > site_age "
                  f"({args.start_time} > {site_age})", file=sys.stderr)
            n_skip += 1
            continue

        # Per-site time range
        end_time = min(args.end_time, site_age)
        time_range = np.arange(
            args.start_time, end_time + 1e-6, args.time_increment
        ).tolist()

        # Plate ID at present-day
        location = pygplates.PointOnSphere(site.latitude, site.longitude)
        partitioning_plate = plate_partitioner.partition_point(location)
        if not partitioning_plate:
            print(f"  [skip] {drill_file.name}: no plate at modern location",
                  file=sys.stderr)
            n_skip += 1
            continue
        plate_id = partitioning_plate.get_feature().get_reconstruction_plate_id()

        # Reconstruct through time
        site_id = drill_file.stem.split("_age")[0]
        out_path = DRILL / f"{site_id}_paleocoords_{args.tag}.tsv"
        rows = []
        for t in time_range:
            rotation = rotation_model.get_rotation(
                t, plate_id, from_time=0,
                anchor_plate_id=args.anchor_plate_id,
            )
            paleo_pt = rotation * location
            paleolat, paleolon = paleo_pt.to_lat_lon()
            rows.append((round(paleolon, 5), round(paleolat, 5),
                         round(float(t), 3), int(plate_id)))

        # Per-site TSV
        with out_path.open("w") as fh:
            fh.write(f"# Site file: {out_path.name}\n")
            fh.write(f"# Modern longitude: {site.longitude}\n")
            fh.write(f"# Modern latitude:  {site.latitude}\n")
            fh.write(f"# Plate model:      {model_label}\n")
            fh.write(f"# Anchor plate ID:  {args.anchor_plate_id}\n")
            fh.write(f"# Plate ID:         {plate_id}\n")
            fh.write(f"# Columns:          paleolon\tpaleolat\tage_ma\tplate_id\n")
            fh.write("#\n")
            for r in rows:
                fh.write("\t".join(str(x) for x in r) + "\n")

        for r in rows:
            combined_rows.append((site_id, *r))
        n_done += 1
        if n_done % 25 == 0 or n_done == len(drill_files):
            print(f"  {n_done:4d}/{len(drill_files):4d} sites processed")

    # ── Combined TSV ───────────────────────────────────────────────────────
    out_combined = DATA / f"drill_sites_paleocoords_{args.tag}.tsv"
    with out_combined.open("w") as fh:
        fh.write(f"# Combined drill-site paleocoords\n")
        fh.write(f"# Plate model:     {model_label}\n")
        fh.write(f"# Anchor plate ID: {args.anchor_plate_id}\n")
        fh.write(f"# Columns:         site_id\tpaleolon\tpaleolat\tage_ma\tplate_id\n")
        fh.write("#\n")
        for r in combined_rows:
            fh.write("\t".join(str(x) for x in r) + "\n")

    print(f"\nDone.  {n_done} sites reconstructed, {n_skip} skipped.")
    print(f"  → per-site TSVs in {DRILL.relative_to(REPO)}/")
    print(f"  → combined        {out_combined.relative_to(REPO)}")


if __name__ == "__main__":
    main()
