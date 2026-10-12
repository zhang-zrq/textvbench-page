"""Check portable assets, source data, and independently derived lesson scores."""
import argparse
import base64
from fractions import Fraction
import hashlib
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import struct
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        for key in ('src', 'href', 'poster'):
            if attrs.get(key):
                self.refs.append(attrs[key])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', type=Path,
                        help='Optional source archive containing paper/, dataset/, metrics/ and media/.')
    args = parser.parse_args()
    for path in [ROOT / 'index.html', *sorted((ROOT / 'assets/diagrams').glob('*.html'))]:
        p = References()
        source = path.read_text(encoding='utf-8')
        p.feed(source)
        assert len(p.ids) == len(set(p.ids)), f'Duplicate IDs in {path.name}'
        assert '{{' not in source, f'Unresolved template: {path}'
        for ref in p.refs:
            u = urlsplit(ref)
            if u.scheme or ref.startswith('//'):
                continue
            if u.path:
                assert not u.path.startswith('/'), f'Absolute project asset: {ref}'
                destination = (path.parent / unquote(u.path)).resolve()
                assert destination.is_relative_to(ROOT), f'Asset escapes site: {ref}'
                assert destination.is_file(), f'Missing asset: {ref}'
            elif u.fragment:
                assert u.fragment in p.ids, f'Broken anchor: {ref}'
    source = (ROOT / 'index.html').read_text(encoding='utf-8')
    config = json.loads((ROOT / 'data/site.json').read_text(encoding='utf-8'))
    video_path = ROOT / config['video']['src']
    assert '<video' in source and video_path.is_file(), 'Promotional video must ship with the site.'
    assert set((ROOT / 'assets').rglob('*.mp4')) == {video_path}, 'Only the supplied project video should be bundled.'
    video_record = next(a for a in json.loads((ROOT / 'docs/asset-sources.json').read_text(encoding='utf-8')) if a['output'] == config['video']['src'])
    assert hashlib.sha256(video_path.read_bytes()).hexdigest() == video_record['sha256'], 'Video copy differs from source.'
    data = json.loads((ROOT / 'data/walkthrough-audit.json').read_text(encoding='utf-8'))
    sequence_assets = json.loads((ROOT / 'data/sequence-assets.json').read_text(encoding='utf-8'))
    assert len(sequence_assets) == 8
    assert len({a['sha256'] for a in sequence_assets}) == 8, 'Frames must not be duplicates.'
    for track in ('t2v', 'ref2v'):
        records = [a for a in sequence_assets if a['track'] == track]
        assert [a['timestamp'] for a in records] == data[track]['timestamps']
        walkthrough = (ROOT / f'assets/diagrams/evaluation-{track}.html').read_text(encoding='utf-8')
        for asset in records:
            raw = (ROOT / asset['output']).read_bytes()
            assert raw[:4] == b'RIFF' and raw[8:12] == b'WEBP', 'Expected compressed WebP frame'
            assert raw[12:16] in (b'VP8 ', b'VP8X', b'VP8L'), 'Expected a WebP image payload'
            if raw[12:16] == b'VP8X':
                assert (1 + int.from_bytes(raw[24:27], 'little')) == 768
                assert (1 + int.from_bytes(raw[27:30], 'little')) == 512
            assert hashlib.sha256(raw).hexdigest() == asset['sha256']
            assert 'data:image/webp;base64,' + base64.b64encode(raw).decode('ascii') in walkthrough
    expected = {'t2v': {'spatial_fidelity': Fraction(53, 60), 'temporal_fidelity': Fraction(43, 50),
                        'textv_score': Fraction(45580, 523),
                        'extra_text_ratio': (Fraction(16,41)*2 + Fraction(16,25) + Fraction(1,2))/4},
                'ref2v': {'spatial_fidelity': Fraction(223, 264), 'temporal_fidelity': Fraction(107, 132),
                          'textv_score': Fraction(4772200, 57684),
                          'extra_text_ratio': (Fraction(11,31)*2 + Fraction(11,20) + Fraction(1,2))/4}}
    for track, values in expected.items():
        for metric, value in values.items():
            assert math.isclose(data[track]['metrics'][metric], float(value), abs_tol=1e-12), (track, metric)
        assert data[track]['sequences'][0][2] is None, 'Inactive observation must be excluded.'
        assert data[track]['sequences'][1][3] == '', 'Active missing observation must receive zero.'
        assert 'JU1CE' in data[track]['wrong'], 'Observed errors must remain uncorrected.'
    results = json.loads((ROOT / 'data/results.json').read_text(encoding='utf-8'))
    assert len(results['t2v']) == 7 and len(results['ref2v']) == 5
    assert sum(r['n'] for r in results['t2v']) == 2100
    assert sum(r['n'] for r in results['ref2v']) == 1000
    if args.source_root:
        examples = json.loads((ROOT / 'data/examples.json').read_text(encoding='utf-8'))
        files = {'t2v': 'T2V/benchmark_300.jsonl', 'ref2v': 'Ref2V/video_prompt_dataset.jsonl'}
        for track, filename in files.items():
            original = {x['sample_id']: x for x in map(json.loads, (args.source_root / 'dataset' / filename).read_text(encoding='utf-8').splitlines())}
            for sample in examples[track]:
                for key, value in original[sample['sample_id']].items():
                    assert sample[key] == value, f'Changed input: {sample["sample_id"]}/{key}'
        for asset in json.loads((ROOT / 'docs/asset-sources.json').read_text(encoding='utf-8')):
            assert hashlib.sha256((args.source_root / asset['source']).read_bytes()).hexdigest() == asset['sha256']
    print('PASS: portable links, original inputs, complete result coverage, and analytical correspondence/score fixtures.')


if __name__ == '__main__':
    main()
