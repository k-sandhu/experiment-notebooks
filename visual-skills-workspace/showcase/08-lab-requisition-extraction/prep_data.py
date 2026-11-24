"""Build data.js for the explainer from notebook 08's saved data (read-only).

Every ordered test gets an upright crop of its box or Other Tests line, cut from the page image using the
ground-truth polygon (page corners TL, TR, BR, BL in image pixels). A test a model added by mistake has no
position on its page; when the same test is printed with a box on that layout, its position is taken from
another page where it was ordered and mapped onto this page with a homography fitted on shared field boxes.
"""
import base64, csv, io, json, collections, sys
from pathlib import Path
import numpy as np
from PIL import Image

NB = Path(sys.argv[1])
OUT = Path(sys.argv[2])
D = NB / 'data'

MODELS = ['Claude Opus 5.5', 'GPT-6.1', 'Muse Wonder', 'Muse Spark Open', 'Nemotron 3.5 Super VL',
          'Qwen3.8 Flash', 'Gemma 4 31B']
CSV_NAME = {'GPT-6.1': 'GPT-6.1'}

manifest = list(csv.DictReader(open(D / 'manifest.csv')))
DOCS = [m['doc_id'] for m in manifest]
gt = {d: json.load(open(D / 'ground_truth' / f'{d}.json')) for d in DOCS}
rows = list(csv.DictReader(open(D / 'scored_tests.csv')))
for r in rows: r['model'] = r['model'].replace(' (Codex)', '')
csv_models = sorted(set(r['model'] for r in rows))
print('models in csv:', csv_models)


def b64(img, q):
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=q, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


def frame(poly):
    tl, tr, br, bl = [np.array(p, float) for p in poly]
    u = (tr - tl) + (br - bl)
    v = (bl - tl) + (br - tr)
    return tl, u / 2, v / 2          # origin, page-x vector of one box width, page-y vector of one box height


def quad_crop(img, poly, a0, a1, b0, b1, out_w):
    tl, u, v = frame(poly)
    P = lambda a, b: tl + a * u + b * v
    # PIL QUAD: upper-left, lower-left, lower-right, upper-right of the source quad
    q = [*P(a0, b0), *P(a0, b1), *P(a1, b1), *P(a1, b0)]
    w_src = np.linalg.norm(u) * (a1 - a0)
    h_src = np.linalg.norm(v) * (b1 - b0)
    out_h = max(8, int(round(out_w * h_src / w_src)))
    return img.transform((out_w, out_h), Image.QUAD, data=tuple(float(x) for x in q), resample=Image.BICUBIC)


def crop_for(img, ann, test):
    if ann['semantic_type'] == 'checkbox':
        a1 = 23 if test == 'Glucose, fasting' and 'moh' in gt_variant_of(ann) else 13.5
        return quad_crop(img, ann['polygon'], -0.7, a1, -0.75, 1.75, 360 if a1 < 20 else 420)
    return quad_crop(img, ann['polygon'], -0.03, 0.66, -0.5, 1.5, 330)


def gt_variant_of(ann):
    return ann.get('_variant', '')


def tests_anns(d):
    out = {}
    for a in gt[d]['annotations']:
        if a['field_id'].startswith('tests.'):
            a = dict(a); a['_variant'] = gt[d]['document']['layout']['variant']
            out[a['field_id'][6:]] = a
    return out


def fixed_points(d):
    pts = {}
    for a in gt[d]['annotations']:
        f = a['field_id']
        if f.startswith('tests.') or f.startswith('_render.tests') or a['semantic_type'] in ('checkbox',):
            continue
        if 'polygon' in a:
            for i, p in enumerate(a['polygon']):
                pts[(f, i)] = p
    return pts


def homography(src, dst):
    A = []
    for (x, y), (X, Y) in zip(src, dst):
        A.append([-x, -y, -1, 0, 0, 0, x * X, y * X, X])
        A.append([0, 0, 0, -x, -y, -1, x * Y, y * Y, Y])
    _, _, Vt = np.linalg.svd(np.array(A))
    H = Vt[-1].reshape(3, 3)
    return H / H[2, 2]


def apply(H, p):
    x = H @ np.array([p[0], p[1], 1.0])
    return [x[0] / x[2], x[1] / x[2]]


def fit(src_doc, dst_doc):
    s, t = fixed_points(src_doc), fixed_points(dst_doc)
    keys = [k for k in s if k in t]
    S = np.array([s[k] for k in keys]); T = np.array([t[k] for k in keys])
    keep = np.ones(len(keys), bool)
    for _ in range(3):
        H = homography(S[keep], T[keep])
        res = np.array([np.linalg.norm(np.array(apply(H, p)) - q) for p, q in zip(S, T)])
        keep = res < max(12, np.median(res) * 3)
    return H, float(np.median(res[keep])), int(keep.sum())


imgs = {d: Image.open(D / 'images' / f'{d}.jpg').convert('RGB') for d in DOCS}
variant = {d: gt[d]['document']['layout']['variant'] for d in DOCS}
subset = {}
for m in manifest:
    subset[m['doc_id']] = ('Official-form scan' if m['doc_id'].startswith('form-scan') else
                           'Phone photo' if m['doc_id'].startswith('form-photo') else 'Ontario-style scan')

# reference positions for printed tests: prefer a flatbed scan of the same layout
ref = {}
for d in DOCS:
    if 'scan' not in d:
        continue
    for t, a in tests_anns(d).items():
        if a['semantic_type'] == 'checkbox':
            ref.setdefault((variant[d], t), (d, a))

crops, crop_ids = [], {}
def add_crop(img, key):
    crop_ids[key] = len(crops)
    crops.append(b64(img, 62))
    return crop_ids[key]

# thumbnails
THW = 150
thumbs = {}
for d in DOCS:
    im = imgs[d]
    th = im.resize((THW, int(im.height * THW / im.width)), Image.LANCZOS)
    thumbs[d] = b64(th, 55)

def norm_rect(poly, d):
    im = imgs[d]
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    return [round(min(xs) / im.width, 4), round(min(ys) / im.height, 4),
            round((max(xs) - min(xs)) / im.width, 4), round((max(ys) - min(ys)) / im.height, 4)]

by = collections.defaultdict(dict)
for r in rows:
    by[(r['doc_id'], r['test'])][r['model']] = r

# ordered tests in page order, boxes before written lines
ORD = []
for d in DOCS:
    anns = tests_anns(d)
    gold = gt[d]['order']['tests']
    for t in sorted(gold, key=lambda t: (anns[t]['semantic_type'] != 'checkbox', gold.index(t))):
        a = anns[t]
        cid = add_crop(crop_for(imgs[d], a, t), (d, t))
        rr = by[(d, t)]
        out = []
        for m in MODELS:
            r = rr[m]
            assert r['gold'] == 'True'
            if r['pred'] == 'True':
                out.append('f')
            elif m == 'Muse Spark Open' and d == 'form-scan-05':
                out.append('u')          # unreadable reply (empty text)
            elif m == 'Gemma 4 31B' and d in ('form-photo-04', 'form-photo-06'):
                out.append('b')          # readable reply with every value blank
            else:
                out.append('m')
        ORD.append({'d': d, 't': t, 'src': 'box' if a['semantic_type'] == 'checkbox' else 'line',
                    'font': a['fill_style'], 'c': cid, 'r': norm_rect(a['polygon'], d), 'o': ''.join(out)})

# added tests, per model
ADD = {m: [] for m in MODELS}
Hcache = {}
for r in rows:
    if r['gold'] != 'False':
        continue
    m, d, t = r['model'], r['doc_id'], r['test']
    item = {'d': d, 't': t, 'c': None, 'r': None}
    key = (variant[d], t)
    if key in ref:
        sd, sa = ref[key]
        if (d, t) in crop_ids:
            item['c'] = crop_ids[(d, t)]
        else:
            if (sd, d) not in Hcache:
                Hcache[(sd, d)] = fit(sd, d)
            H, err, n = Hcache[(sd, d)]
            poly = [apply(H, p) for p in sa['polygon']]
            a = dict(sa); a['polygon'] = poly
            item['c'] = add_crop(crop_for(imgs[d], a, t), (d, t))
        if item['c'] is not None:
            # rect from the mapped polygon
            if (sd, d) in Hcache:
                H = Hcache[(sd, d)][0]
                item['r'] = norm_rect([apply(H, p) for p in sa['polygon']], d) if sd != d else norm_rect(sa['polygon'], d)
    ADD[m].append(item)

for k, v in Hcache.items():
    print('homography', k, 'median residual px %.1f on %d points' % (v[1], v[2]))

# order adds by page order so a reply's block of adds sits together
for m in MODELS:
    ADD[m].sort(key=lambda it: (DOCS.index(it['d']), it['t']))

summary = list(csv.DictReader(open(D / 'summary_tests.csv')))
SUM = {}
for s in summary:
    name = s[''].replace(' (Codex)', '')
    SUM[name] = {'TP': int(float(s['TP'])), 'FP': int(float(s['FP'])), 'FN': int(float(s['FN'])),
                 'F1': round(float(s['F1']), 3), 'exact': round(float(s['all tests right']) * 24)}

# consistency checks against summary_tests.csv
for i, m in enumerate(MODELS):
    f = sum(o['o'][i] == 'f' for o in ORD)
    miss = sum(o['o'][i] != 'f' for o in ORD)
    assert f == SUM[m]['TP'] and miss == SUM[m]['FN'] and len(ADD[m]) == SUM[m]['FP'], (m, f, miss, len(ADD[m]))
print('counts match summary_tests.csv')
print('ordered', len(ORD), 'boxes', sum(o['src'] == 'box' for o in ORD))
print('adds with crop', sum(1 for m in MODELS for a in ADD[m] if a['c'] is not None), 'of', sum(len(v) for v in ADD.values()))

DOCINFO = {d: {'sub': subset[d], 'orient': next(m['orientation'] for m in manifest if m['doc_id'] == d),
               'n': int(next(m['n_tests'] for m in manifest if m['doc_id'] == d))} for d in DOCS}

js = ('// Generated by prep_data.py from notebooks/08-lab-requisition-extraction/data (scored_tests.csv, '
      'ground_truth/*.json, images/*.jpg, manifest.csv, summary_tests.csv)\n'
      'const DATA = ' + json.dumps({'models': MODELS, 'ordered': ORD, 'added': ADD, 'summary': SUM,
                                     'docs': DOCINFO}, separators=(',', ':')) + ';\n'
      'const CROPS = ' + json.dumps(crops) + ';\n'
      'const THUMBS = ' + json.dumps(thumbs) + ';\n')
OUT.write_text(js, encoding='utf-8')
print('data.js bytes', len(js))

# save a contact sheet of crops for checking
sheet_dir = OUT.parent / '_crops'
sheet_dir.mkdir(exist_ok=True)
for i, c in enumerate(crops[:400]):
    Image.open(io.BytesIO(base64.b64decode(c.split(',')[1]))).save(sheet_dir / f'{i:03d}.jpg')
