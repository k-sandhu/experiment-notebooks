# Toronto geography and road times

This study uses commercial addresses as map locations for a fictional carrier. The pickup requests, freight, dock rules, vehicle configurations and operating hours are experimental inputs. The source datasets describe sites and roads. A street address here does not imply participation by a business or identify a real shipment.

## Files used by the notebook

- `geography.json` contains 241 addressed locations in matrix order. Row 0 is the Ontario Food Terminal, 165 The Queensway. The other rows contain 192 food premises and 48 municipal addresses whose points fall inside OpenStreetMap buildings tagged industrial. The industrial candidate pool also allowed warehouse footprints, but the 48 selected were tagged industrial. `kind: warehouse` is the experiment's label for those industrial pickup sites. Retail food premises include restaurants, grocers, bakeries and other food businesses. `address_point_id` identifies the municipal address record. The industrial entries also record the OpenStreetMap way ID and building tag.
- `road_matrix.npz` contains integer arrays named `seconds` and `meters`, each with shape `(2, 241, 241)`. Profile 0 is Valhalla auto for vans. Profile 1 is Valhalla truck for the box trucks. Row index is departure and column index is arrival. Every published pair is routable under both profiles, and self legs are zero. The distance and time for a leg come from the same path.
- `streets.json.gz` is gzipped JSON containing polylines. Each polyline is a list of `[longitude, latitude]` pairs. It shows the main road classes from the same OpenStreetMap extract. The basemap is intentionally simplified and the routing engine uses the full routable road graph.

## Source snapshots

| Source | Retrieved | SHA-256 of downloaded file |
|---|---|---|
| [Municipal Address Points, WGS84 CSV](https://open.toronto.ca/dataset/address-points-municipal-toronto-one-address-repository/) ([download](https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/abedd8bc-e3dd-4d45-8e69-79165a76e4fa/resource/64d4e54b-738f-4cd9-a9e7-8050fac8a52f/download/address-points-4326.csv)) | 2026-11-18 | `7bd5156c43d7f2860c9f24e435b268cd695ef1743fd4e160b291bf4f6c2c9825` |
| [DineSafe](https://open.toronto.ca/dataset/dinesafe/) ([CSV dump](https://ckan0.cf.opendata.inter.prod-toronto.ca/datastore/dump/75dbb3ff-8281-4f03-9de2-bd1214761302)) | 2026-11-18 | `2739d5724782fb3a6a1b947764cb59e9c645f3e4d0c8c3a92dbb3fb299ca30c9` |
| [Toronto OpenStreetMap PBF from BBBike](https://download.bbbike.org/osm/bbbike/Toronto/) ([download](https://download.bbbike.org/osm/bbbike/Toronto/Toronto.osm.pbf)) | 2026-11-18, server snapshot dated 2026-11-14 at 17:04 UTC | `36e436f892a13b88a8da803c45b201062d223cf0a2d1c1ed0df13a6382901bc6` |
| [Ontario Food Terminal address](https://www.oftb.com/location-hours) | Checked 2026-11-18 | Coordinates from Municipal Address Points |

Contains information licensed under the [Open Government Licence – Toronto](https://open.toronto.ca/open-data-licence/). OpenStreetMap-derived road lines, travel matrices and building information are © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), available under the [Open Data Commons Open Database License v1.0](https://opendatacommons.org/licenses/odbl/1-0/). The notebook uses the frozen derivatives so reruns need no download or geocoding.

## Sampling and router settings

Food candidates had a DineSafe inspection dated 2025-01-01 or later and a facility name consistent with a food business. We removed mobile and institutional names, stripped postal codes and units, matched the remaining text to a city address, and kept matches within 0.001 degree of the DineSafe coordinates on both axes. We publish the city address and coordinates and omit business names, inspection results and phone numbers. We matched industrial candidates by containing OpenStreetMap building footprint and retained the closest municipal address to each footprint's bounding-box centre. We excluded the ferry-dependent island band and took a reproducibly shuffled panel round-robin across eight longitude/latitude zones. Each candidate had to be reachable in both directions for both vehicle profiles from the already-selected panel and depot.

We ran [Valhalla](https://valhalla.github.io/valhalla/) locally, version `3.9.3-5c7f918e6`, image `ghcr.io/valhalla/valhalla-scripted@sha256:693617873d42f24d9023eaa9aa002dccd832c9629c9ce8b60eb4ff30547215e1`. We built the graph from the frozen OpenStreetMap extract and requested directed blocks from [`/sources_to_targets`](https://valhalla.github.io/valhalla/api/matrix/). We used the static default speeds with tolls disfavoured. The simulated box-truck profile had 3.35 m height, 2.55 m width, 7.30 m length, 6.58 t gross weight and 4.00 t axle load. These dimensions are modelling assumptions for an upfitted box truck. All pickups use address-point snapping, so loading access and the position at the curb are modelled by the manifest rules.

The matrices estimate driving on the road graph. They do not incorporate traffic observations or certify truck legality. A spot check against the city’s by-laws found a heavy-vehicle restriction tag on Via Italia south of St. Clair Avenue West (OpenStreetMap way 43153794) and on the checked Collier Street segments (ways 4281698 and 1092221109). The checked Blue Ridge Road segment (way 23498139) lacked a heavy-vehicle restriction tag even though the city lists a prohibition there. These checks examine OSM tags and do not establish compliance by a particular route. [Via Italia by-law](https://www.toronto.ca/legdocs/bylaws/2026/law0033.pdf) · [Collier Street by-law](https://www.toronto.ca/legdocs/bylaws/2026/law0177.pdf) · [Blue Ridge Road by-law](https://www.toronto.ca/legdocs/bylaws/2024/law0183.pdf)

OSM coverage of municipal restrictions varies, and the road graph may include routes a live dispatcher would avoid. In particular the depot board [reports a temporary truck departure detour](https://www.oftb.com/) during part of 2026. The experiment did not explicitly apply that construction detour.

## Frozen panel checks

The eight geographic bands contribute 29 to 31 pickups each. Five candidate addresses were excluded because at least one directed leg was unavailable. All 241 published sites have distinct coordinates and nonzero time and distance for every non-self leg. A fresh four-site matrix request reproduced the matching cells in the frozen van matrix.

Of 57,840 directed non-self legs, 23,698 (41.0%) had different travel times for the van and truck. The truck time was higher on 14,430 legs and lower on 9,268. Among legs with a difference, the median absolute difference was 31 seconds. Both profiles can choose different paths and apply different costs. These counts measure the whole profile's effect, including routing preferences and speed assumptions, so they do not count regulated road segments. For example, Valhalla estimates 24 minutes 38 seconds by van and 33 minutes 56 seconds by box truck from 2795 Danforth Ave to 1468 Queen St W, with path lengths of 15.578 and 23.125 km respectively. For the van between the depot and 2 St Andrews Blvd, the outbound estimate was 20 minutes 32 seconds and the inbound estimate was 26 minutes 11 seconds.

| Frozen derivative | SHA-256 |
|---|---|
| `geography.json` | `af7c4229264f21cff141a2e8b4b60242311c0a96b350c622c431b094bda73512` |
| `road_matrix.npz` | `28d241a66507032799799ae762c8b30dd6745756795f455a47e771c050d96213` |
| `streets.json.gz` | `c03195369ef8777265adc0fa1f6224098f020358ee4d90ae02374524d2d85ea0` |
