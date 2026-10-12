"""Import selected, traceable paper assets. Optional maintainer utility.

Requires PyMuPDF and Pillow. The served website has no Python dependencies.
Usage: python scripts/import_assets.py --paper-dir /path/to/paper \
    --dataset-dir /path/to/dataset --metrics-file /path/to/computed_metrics.json
"""
import argparse
import hashlib
import json
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--paper-dir', type=Path, required=True,
                    help='Paper source directory containing figures/*.pdf.')
parser.add_argument('--dataset-dir', type=Path, required=True,
                    help='Dataset directory containing T2V/ and Ref2V/.')
parser.add_argument('--metrics-file', type=Path, required=True)
args = parser.parse_args()
paper = args.paper_dir.resolve()
dataset = args.dataset_dir.resolve()
metrics_path = args.metrics_file.resolve()

import pymupdf
from PIL import Image

sources = []


def record(source, output, note):
    if source == metrics_path:
        relative_source = 'metrics/computed_metrics.json'
    elif source.is_relative_to(paper):
        relative_source = 'paper/' + source.relative_to(paper).as_posix()
    else:
        relative_source = 'dataset/' + source.relative_to(dataset).as_posix()
    sources.append({'source': relative_source,
                    'output': output.relative_to(SITE).as_posix(),
                    'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'note': note})


figures = [
    ('t2v_construction_pipeline', 't2v-construction', 2400),
    ('fig5_ref2v_construction', 'ref2v-construction', 1500),
    ('fig2_textvbench_overview', 'evaluation-overview', 2400),
    ('fig3_scaling_analysis', 'scaling-analysis', 1400),
]
for filename, slug, width in figures:
    source = paper / 'figures' / (filename + '.pdf')
    with pymupdf.open(source) as doc:
        page = doc[0]
        pix = page.get_pixmap(matrix=pymupdf.Matrix(width / page.rect.width, width / page.rect.width), alpha=False)
        im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
        output = SITE / 'assets/images' / (slug + '.webp')
        im.save(output, 'WEBP', quality=88, method=6)
        record(source, output, 'First page rendered to WebP quality 88; original aspect ratio, no content changes.')

examples = {'t2v': [], 'ref2v': []}
t2v_path = dataset / 'T2V/benchmark_300.jsonl'
t2v = [json.loads(line) for line in t2v_path.read_text(encoding='utf-8').splitlines()]
for sid, title in [('OPENVID_7e9a115b0717__easy', 'Two text targets. One shared carrier.'),
                   ('OPENVID_a7e08d3acbec__medium', 'Keep the right words on the right surface.')]:
    row = next(row for row in t2v if row['sample_id'] == sid)
    examples['t2v'].append({'title': title, **row})
ref_path = dataset / 'Ref2V/video_prompt_dataset.jsonl'
ref = [json.loads(line) for line in ref_path.read_text(encoding='utf-8').splitlines()]
for sid, title in [('0050', 'Preserve packaging, down to the small print.'),
                   ('0150', 'Keep a document readable as the camera moves.')]:
    row = next(row for row in ref if row['sample_id'] == sid)
    source = dataset / 'Ref2V/imgs' / row['reference_images'][0]['filename']
    output = SITE / 'assets/images' / ('reference-' + sid + '.webp')
    with Image.open(source) as im:
        width, height = im.size
        im.convert('RGB').save(output, 'WEBP', quality=88, method=6)
    examples['ref2v'].append({'title': title, **row, 'image': output.relative_to(SITE).as_posix(),
                             'width': width, 'height': height})
    record(source, output, 'Released reference input, converted to WebP quality 88; content and dimensions retained.')
(SITE / 'data/examples.json').write_text(json.dumps(examples, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
record(t2v_path, SITE / 'data/examples.json', 'Two selected input records. Prompts and labels are unchanged.')
record(ref_path, SITE / 'data/examples.json', 'Two selected reference input records, not generated model outputs.')

metrics = json.loads(metrics_path.read_text(encoding='utf-8'))
names = {'wan2.1-t2v-1.3b': 'Wan2.1 T2V-1.3B', 'wan2.2-t2v-a14b': 'Wan2.2 T2V-A14B',
         'wan2.2-ti2v-5b': 'Wan2.2 TI2V-5B', 'minimax-h3': 'MiniMax-H3',
         'longcat-video': 'LongCat-Video', 'cosmos3-nano': 'Cosmos3-Nano',
         'hunyuan-video15': 'HunyuanVideo-1.5'}
results = {'source_version': 'Local paper snapshot, 2026-10-08',
           'aggregation': 'Arithmetic mean over successfully evaluated videos, separately by track.',
           't2v': [], 'ref2v': []}
for track in ['t2v', 'ref2v']:
    for key in metrics['scope'][track + '_models']:
        row = metrics[track]['models'][key]
        results[track].append({'model': names[key], 'n': row['n'],
                                **{m: row['overall'][m]['mean'] for m in ['spatial', 'temporal', 'textv', 'extra']}})
(SITE / 'data/results.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8', newline='\n')
record(metrics_path, SITE / 'data/results.json', 'Full precision means; website tables display three decimals, matching the paper.')
manifest_path = SITE / 'docs/asset-sources.json'
previous = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else []
updated_outputs = {item['output'] for item in sources}
sources.extend(item for item in previous if item['output'] not in updated_outputs)
manifest_path.write_text(json.dumps(sources, indent=2) + '\n', encoding='utf-8', newline='\n')
print('Imported 4 paper figures, 4 input samples and 12 model/track result rows.')
