"""Build frozen pickup site and Valhalla matrix inputs from publicly licensed files.

See data/geography_sources.md for input provenance and Valhalla settings.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import re

from matplotlib.path import Path as Polygon
import numpy as np
import osmium
import requests


DEPOT = "165 The Queensway"
MIN_LON, MIN_LAT = -79.65, 43.55
MAX_LON, MAX_LAT = -79.09, 43.88
STREET_CLASSES = {
    "motorway", "motorway_link", "trunk", "trunk_link", "primary",
    "primary_link", "secondary", "secondary_link", "tertiary",
}
STORE = re.compile(
    r"\b(FOOD[S]?|MARKET|GROCERY|SUPERMARKET|BAKERY|BUTCHER|MEAT[S]?|PRODUCE|"
    r"CHEESE|DAIRY|CATERING|RESTAURANT|CAFE|BISTRO|PIZZA|KITCHEN|GRILL)\b",
    re.IGNORECASE,
)
OTHER_PREMISES = re.compile(
    r"\b(SCHOOL|ACADEMY|CHURCH|HOSPITAL|SHELTER|DAYCARE|CHILDCARE|CHILD CARE|"
    r"COMMUNITY CENTRE|COMMUNITY CENTER|HEALTH CENTRE|NURSING HOME|SENIOR|"
    r"LONG TERM CARE|LIBRARY|RECREATION CENTRE|FOOD TRUCK|MOBILE|PARK|"
    r"YACHT|TORONTO ISLAND|TENT|CHILDREN|STUDENT|SUMMER CAMP)\b",
    re.IGNORECASE,
)
POSTAL = re.compile(r"\s+[A-Z]\d[A-Z]\s?\d[A-Z]\d\s*$", re.IGNORECASE)
SUITE = re.compile(r"(?:,|\s+\b(?:UNIT|SUITE|FLOOR|NONE|LEVEL|RM|ROOM)\b|\s+#).*$", re.IGNORECASE)


def key(address):
    return " ".join(address.upper().replace(".", "").split())


def in_toronto(lon, lat):
    if not (MIN_LON <= lon <= MAX_LON and MIN_LAT <= lat <= MAX_LAT):
        return False
    return not (-79.425 < lon < -79.31 and lat < 43.634)


def grid(lon, lat):
    return (math.floor((lon - MIN_LON) / 0.005), math.floor((lat - MIN_LAT) / 0.005))


def region(item):
    lon, lat = item["lon"], item["lat"]
    return int(np.digitize(lon, [-79.48, -79.40, -79.31])) * 2 + int(lat >= 43.72)


def street_and_warehouse_layers(pbf):
    """Return major street polylines and a spatial index of mapped warehouse footprints."""
    streets, footprints = [], {}
    for way in osmium.FileProcessor(pbf).with_locations("flex_mem").with_filter(
        osmium.filter.EntityFilter(osmium.osm.WAY)
    ):
        road = way.tags.get("highway") in STREET_CLASSES
        building = way.tags.get("building")
        warehouse = building in {"warehouse", "industrial"}
        if not (road or warehouse):
            continue
        if not all(node.location.valid() for node in way.nodes):
            continue
        points = [(node.lon, node.lat) for node in way.nodes]
        if not any(in_toronto(*point) for point in points):
            continue
        if road:
            streets.append([[round(lon, 6), round(lat, 6)] for lon, lat in points])
        if warehouse and len(points) >= 4 and points[0] == points[-1]:
            min_x, min_y = grid(min(p[0] for p in points), min(p[1] for p in points))
            max_x, max_y = grid(max(p[0] for p in points), max(p[1] for p in points))
            polygon = Polygon(points, closed=True)
            mid_lon = (max(p[0] for p in points) + min(p[0] for p in points)) / 2
            mid_lat = (max(p[1] for p in points) + min(p[1] for p in points)) / 2
            for x in range(min_x, max_x + 1):
                for y in range(min_y, max_y + 1):
                    footprints.setdefault((x, y), []).append((int(way.id), polygon, mid_lon, mid_lat, building))
    return streets, footprints


def municipal_sites(csv_file):
    points = {}
    with csv_file.open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            if row["MAINT_STAGE"] != "REGULAR" or row["ADDRESS_CLASS_DESC"] != "Land":
                continue
            if not row["geometry"]:
                continue
            geometry = json.loads(row["geometry"])
            coords = geometry["coordinates"]
            lon, lat = coords[0] if geometry["type"] == "MultiPoint" else coords
            if in_toronto(lon, lat):
                address = row["ADDRESS_FULL"]
                points[key(address)] = {
                    "address": address, "lon": round(lon, 7), "lat": round(lat, 7),
                    "address_point_id": int(row["ADDRESS_POINT_ID"]),
                }
    return points


def commercial_food_sites(csv_file, municipal):
    candidates = {}
    with csv_file.open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            if not (row["inspectionDate"] >= "2025-01-01"
                    and STORE.search(row["estName"])
                    and not OTHER_PREMISES.search(row["estName"])
                    and row["latitude"] and row["longitude"]):
                continue
            name = key(SUITE.sub("", POSTAL.sub("", row["address"])))
            if name not in municipal or name == key(DEPOT):
                continue
            item = municipal[name]
            if not (
                abs(float(row["latitude"]) - item["lat"]) <= 0.001
                and abs(float(row["longitude"]) - item["lon"]) <= 0.001
            ):
                continue
            candidates[name] = {**item, "kind": "retail"}
    return candidates


def warehouse_sites(municipal, footprints):
    buildings = {}
    for name, item in municipal.items():
        if name == key(DEPOT):
            continue
        lon, lat = item["lon"], item["lat"]
        for osm_id, polygon, mid_lon, mid_lat, building in footprints.get(grid(lon, lat), []):
            if polygon.contains_point((lon, lat)):
                offset = (lon - mid_lon) ** 2 + (lat - mid_lat) ** 2
                prior = buildings.get(osm_id)
                if prior is None or offset < prior[0]:
                    buildings[osm_id] = (offset, {**item, "kind": "warehouse", "osm_way": osm_id, "osm_building": building})
    return {key(item["address"]): item for _, item in buildings.values()}


def sample_sites(candidates, counts, rng):
    """Sample each region in a round robin, then fill from regions with stock."""
    buckets = [[] for _ in range(8)]
    for item in sorted(candidates, key=lambda site: site["address"]):
        buckets[region(item)].append(item)
    for bucket in buckets:
        rng.shuffle(bucket)
    result = []
    for offset in range(counts):
        for bucket in buckets:
            if len(result) == counts:
                return result
            if len(bucket) > offset:
                result.append(bucket[offset])
    if len(result) < counts:
        raise ValueError(f"Only {len(result)} out of {counts} sites available")
    return result


def choose_locations(raw, output):
    street, footprints = street_and_warehouse_layers(raw / "toronto.osm.pbf")
    municipal = municipal_sites(raw / "address-points-4326.csv")
    depot = {**municipal[key(DEPOT)], "kind": "depot"}
    food = commercial_food_sites(raw / "dinesafe.csv", municipal)
    warehouses = warehouse_sites(municipal, footprints)
    print(f"Available warehouse sites: {len(warehouses)}. Available food premises: {len(food)}.", flush=True)
    for name in warehouses:
        food.pop(name, None)
    rng = random.Random(490127)
    # Include reserve candidates during acquisition so sites with unreachable road legs can be replaced.
    warehouse_pool = sample_sites(warehouses.values(), 72, rng)
    retail_pool = sample_sites(food.values(), 224, rng)
    locations = [depot, *warehouse_pool, *retail_pool]
    (raw / "candidates.json").write_text(json.dumps(locations, indent=2) + "\n", encoding="utf8")
    with (output / "streets.json.gz").open("wb") as streamed:
        with gzip.GzipFile(fileobj=streamed, mode="wb", mtime=0) as encoded:
            encoded.write(json.dumps(street, separators=(",", ":")).encode("ascii"))
    print(f"Wrote {len(locations)} candidates and {len(street)} street lines.", flush=True)


PROFILES = (
    ("auto", {"use_tolls": 0.0, "exclude_ferry": True}),
    ("truck", {
        "height": 3.35, "width": 2.55, "length": 7.3, "weight": 6.58,
        "axle_load": 4.0, "use_tolls": 0.0, "exclude_ferry": True,
    }),
)


def matrix_block(api, profile, all_points, source, target):
    mode, options = PROFILES[profile]
    response = requests.post(
        api + "/sources_to_targets", timeout=(5, 180), json={
            "sources": [all_points[i] for i in source],
            "targets": [all_points[i] for i in target],
            "costing": mode,
            "costing_options": {mode: options},
            "units": "kilometers",
            "verbose": True,
        }
    )
    if not response.ok:
        raise RuntimeError(f"{mode}, {source[0]}, {target[0]}: {response.status_code} {response.text[:300]}")
    cells = response.json()["sources_to_targets"]
    for offset_i, row in enumerate(cells):
        for offset_j, cell in enumerate(row):
            if (cell["from_index"], cell["to_index"]) != (offset_i, offset_j):
                raise ValueError("Valhalla returned an unexpected matrix index")
            if cell["time"] is not None:
                yield source[offset_i], target[offset_j], round(cell["time"]), round(1000 * cell["distance"])


def build_matrix(raw, output, api):
    candidate_bytes = (raw / "candidates.json").read_bytes()
    candidates = json.loads(candidate_bytes)
    coords = [{"lat": item["lat"], "lon": item["lon"]} for item in candidates]
    n = len(candidates)
    status = requests.get(api + "/status", timeout=5)
    status.raise_for_status()
    with (raw / "toronto.osm.pbf").open("rb") as osm_source:
        graph_id = hashlib.file_digest(osm_source, "sha256").digest()
    router_version = status.json()["version"].encode("ascii")
    snapshot_id = hashlib.sha256(
        candidate_bytes + graph_id + router_version + repr(PROFILES).encode("ascii")
    ).hexdigest()[:16]
    staging = raw / f"candidate_matrix-{snapshot_id}.npz"
    if staging.is_file():
        with np.load(staging) as cached:
            secs, meters = cached["seconds"], cached["meters"]
    else:
        secs = np.full((len(PROFILES), n, n), -1, dtype=np.int32)
        meters = secs.copy()
        blocks = [range(start, min(start + 40, n)) for start in range(0, n, 40)]
        work = [(profile, source, target) for profile in range(len(PROFILES))
                for source in blocks for target in blocks]

        def compute(item):
            profile, source, target = item
            return profile, list(matrix_block(api, profile, coords, source, target))

        with ThreadPoolExecutor(max_workers=4) as pool:
            for step, (profile, values) in enumerate(pool.map(compute, work), start=1):
                for i, j, seconds, distance in values:
                    secs[profile, i, j] = seconds
                    meters[profile, i, j] = distance
                if step % 8 == 0:
                    print(f"Matrix blocks {step}/{len(work)}", flush=True)
        np.savez_compressed(staging, seconds=secs, meters=meters)

    # Some OSM points along private roads cannot serve every matrix entry.
    # Require full reachability among all published locations and the depot.
    selected = [0]
    selected_kind = {"warehouse": 0, "retail": 0}
    rejected = []
    for index, candidate in enumerate(candidates[1:], start=1):
        kind = candidate["kind"]
        goal = 48 if kind == "warehouse" else 192
        if selected_kind[kind] == goal:
            continue
        if np.any(secs[:, index, selected] < 0) or np.any(secs[:, selected, index] < 0):
            rejected.append(candidate["address"])
            continue
        selected.append(index)
        selected_kind[kind] += 1
    if selected_kind != {"warehouse": 48, "retail": 192}:
        raise ValueError(f"Insufficient fully routable addresses: {selected_kind}")
    # Interleave categories/regions in the published row order so index prefixes include several suburbs and both site types.
    rng = random.Random(490128)
    pickup_indices = selected[1:]
    rng.shuffle(pickup_indices)
    selected = [0, *pickup_indices]
    seconds = secs[:, selected, :][:, :, selected]
    distance = meters[:, selected, :][:, :, selected]
    for profile in range(len(PROFILES)):
        np.fill_diagonal(seconds[profile], 0)
        np.fill_diagonal(distance[profile], 0)
    locations = [candidates[index] for index in selected]
    assert seconds.shape == distance.shape == (2, 241, 241)
    assert not np.any(seconds < 0) and not np.any(distance < 0)
    assert len({key(location["address"]) for location in locations}) == 241
    (output / "geography.json").write_text(json.dumps(locations, indent=2) + "\n", encoding="utf8")
    np.savez_compressed(output / "road_matrix.npz", seconds=seconds, meters=distance)
    print(f"Published {len(locations)} sites and {len(rejected)} inaccessible candidate exclusions.", flush=True)
    print(f"Profile time ranges (seconds): {[int(seconds[p].max()) for p in range(len(PROFILES))]}", flush=True)
    changed = np.count_nonzero(seconds[0] != seconds[1])
    print(f"Truck versus van seconds differ for {changed}/{241 * 240} directed non-self legs.", flush=True)
    print(f"Asymmetric van/box-truck leg times: {[int(np.count_nonzero(x != x.T)) for x in seconds]}.", flush=True)
    print(json.dumps({str(i): sum(region(site) == i for site in locations[1:]) for i in range(8)}), flush=True)
    print(json.dumps(rejected), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--api", default="http://127.0.0.1:8492")
    parser.add_argument("step", choices=("sites", "matrix"))
    args = parser.parse_args()
    if args.step == "sites":
        choose_locations(args.raw, args.output)
    else:
        build_matrix(args.raw, args.output, args.api)


if __name__ == "__main__":
    main()
