"""Optional content refresh: generate static HTML using only Python's standard library."""
import hashlib
import html
import json
from pathlib import Path
from urllib.parse import urlsplit

from build_walkthrough import build_walkthroughs

ROOT = Path(__file__).resolve().parents[1]
esc = html.escape


def url(value):
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    parsed = urlsplit(value)
    if parsed.scheme not in ('', 'http', 'https') or value.startswith(('//', '/', '\\')) or '\\' in value:
        raise ValueError(f'Use a relative path or an https/http URL: {value!r}')
    if '..' in parsed.path.split('/'):
        raise ValueError('Asset paths must stay inside the site.')
    return esc(value, quote=True)


def icon(kind):
    paths = {'paper': '<path d="M5 3h9l5 5v13H5zM14 3v6h5M9 13h6M9 17h6"/>',
             'code': '<path d="m8 6-6 6 6 6m8-12 6 6-6 6m-3-15-2 18"/>',
             'dataset': '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0"/>'}
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">{paths[kind]}</svg>'


def render_resources(config):
    result = []
    for key, title in [('paper', 'Paper'), ('code', 'Code'), ('dataset', 'Dataset')]:
        link = url(config['links'].get(key))
        inner = icon(key) + title
        if link:
            result.append(f'<a class="resource-link" href="{link}">{inner}<span aria-hidden="true">↗</span></a>')
        else:
            result.append(f'<span class="resource-link" role="link" aria-disabled="true" aria-label="{title}: coming soon">{inner}<small>Coming soon</small></span>')
    return ''.join(result)


def render_authors(config):
    authors = config.get('authors', [])
    parts = []
    for author in authors:
        name = esc(author['name'])
        indices = author.get('affiliations', [])
        if indices:
            name += '<sup>' + ','.join(esc(str(i)) for i in indices) + '</sup>'
        if author.get('equal'):
            name += '<sup class="equal-mark" title="Equal contribution">*</sup>'
        link = url(author.get('url'))
        parts.append(f'<a href="{link}">{name}</a>' if link else f'<span>{name}</span>')
    names = ''.join(parts) if parts else '<span>Authors to be announced</span>'
    affiliations = config.get('affiliations', [])
    units = ' · '.join(f'<sup>{i + 1}</sup> {esc(s)}' for i, s in enumerate(affiliations)) if affiliations else 'Affiliations to be announced'
    equal_note = '<p class="author-note"><sup>*</sup> Equal contribution</p>' if any(a.get('equal') for a in authors) else ''
    return f'<div class="author-names">{names}</div><p class="affiliations">{units}</p>{equal_note}'


def citation_authors(config):
    authors = config.get('authors', [])
    return ' and '.join(author['name'].replace(',', '') for author in authors) or 'AUTHOR INFORMATION TO BE ADDED'


def render_video(config):
    video = config['video']
    src = url(video.get('src'))
    if not src:
        return '<div class="video-placeholder"><div class="video-symbol" aria-hidden="true"><span></span><span></span><span></span></div><h2 id="video-title">Project video</h2><p>Coming soon</p></div>'
    poster = url(video.get('poster'))
    poster_attr = f' poster="{poster}"' if poster else ''
    captions = url(video.get('captions'))
    track = f'<track kind="captions" srclang="en" label="English" src="{captions}">' if captions else ''
    media_type = ' type="video/mp4"' if urlsplit(video['src']).path.lower().endswith('.mp4') else ''
    return f'<h2 id="video-title" class="sr-only">Project video</h2><video class="project-video" controls playsinline preload="none" aria-labelledby="video-title"{poster_attr}><source src="{src}"{media_type}>{track}<a href="{src}">Download the project video</a></video>'


def samples(data, track):
    result = []
    for sample in data[track]:
        sid = esc(sample['sample_id'])
        badge = f'<span class="difficulty">{esc(sample["difficulty"].capitalize())}</span>' if track == 't2v' else '<span class="difficulty">Reference input</span>'
        content = f'<article class="sample-card"><div class="sample-meta">{badge}<span class="sample-id">{sid}</span></div><h4>{esc(sample["title"])}</h4>'
        if track == 't2v':
            carriers = {slot['slot_id']: c for c in sample['carriers'] for slot in c['slots']}
            content += '<div class="target-rows">'
            for target in sample['texts']:
                c = carriers[target['slot_id']]
                content += f'<div class="target-row"><span class="target-id">{esc(target["slot_id"])}</span><div><q>{esc(target["text_en"])}</q><small>{esc(c["type"].capitalize())} · {esc(c["position"])}</small></div></div>'
            content += '</div><details><summary>Read the generation prompt</summary><p>' + esc(sample['prompt_en']) + '</p></details>'
            content += '<details><summary>Chinese counterpart</summary><p class="zh" lang="zh">' + esc(sample['prompt_zh']) + '</p></details>'
        else:
            content += f'<button type="button" class="figure-button reference-image-button" data-enlarge aria-label="Enlarge reference {sid}"><img class="reference-image" src="{url(sample["image"])}" width="{sample["width"]}" height="{sample["height"]}" loading="lazy" alt="Released reference image for Ref2V sample {sid}: {esc(sample["title"])}"><span class="zoom-hint">View original ↗</span></button>'
            content += '<p class="reference-note">Targets are extracted from this reference by OCR at evaluation time.</p><details><summary>Read the generation instruction</summary><p>' + esc(sample['prompt']) + '</p></details>'
        result.append(content + '</article>')
    return ''.join(result)


def results_tables(data):
    result = []
    for track in ['t2v', 'ref2v']:
        rows = data[track]
        keys = ['spatial', 'temporal', 'textv', 'extra']
        best = {key: (min if key == 'extra' else max)(x[key] for x in rows) for key in keys}
        title = 'T2V · Text creation' if track == 't2v' else 'Ref2V · Text preservation'
        content = f'<div class="result-group"><h3>{title}<small>{len(rows)} models · {rows[0]["n"]} samples / model</small></h3><div class="table-scroll" tabindex="0" role="region" aria-label="{title} results, scroll horizontally on small screens"><table class="results-table"><thead><tr><th scope="col">Model</th><th scope="col">Spatial ↑</th><th scope="col">Temporal ↑</th><th class="score" scope="col">TextVScore ↑</th><th scope="col">Extra ↓</th></tr></thead><tbody>'
        for row in sorted(rows, key=lambda x: x['textv'], reverse=True):
            content += '<tr><td>' + esc(row['model']) + '</td>'
            for key in keys:
                classes = ('score ' if key == 'textv' else '') + ('best' if row[key] == best[key] else '')
                value = f'{row[key]:.3f}'
                value = f'<strong>{value}</strong>' if row[key] == best[key] else value
                content += f'<td class="{classes}">{value}</td>'
            content += '</tr>'
        result.append(content + '</tbody></table></div></div>')
    return ''.join(result)


def main():
    config = json.loads((ROOT / 'data/site.json').read_text(encoding='utf-8'))
    examples = json.loads((ROOT / 'data/examples.json').read_text(encoding='utf-8'))
    results = json.loads((ROOT / 'data/results.json').read_text(encoding='utf-8'))
    title = config['title'].strip()
    project, separator, subtitle = title.partition(': ')
    citation = config.get('citation') or ('@misc{textvbench,\n  title = {' + title + '},\n'
        '  author = {' + citation_authors(config) + '},\n'
        '  year = {YEAR TO BE ADDED},\n  note = {Draft citation; publication details forthcoming}\n}')
    canonical = url(config.get('canonical_url'))
    values = {'PAPER_TITLE': esc(title), 'PROJECT_NAME': esc(project), 'PAPER_SUBTITLE': esc(subtitle if separator else ''),
              'AUTHORS': render_authors(config), 'RESOURCES': render_resources(config), 'VIDEO': render_video(config),
              'T2V_SAMPLES': samples(examples, 't2v'), 'REF2V_SAMPLES': samples(examples, 'ref2v'),
              'RESULTS': results_tables(results), 'CITATION': esc(citation),
              'CITATION_NOTE': 'Please cite our work using the entry below.' if config.get('citation') else 'Draft template. Author and publication details will be added before release.',
              'CANONICAL': f'<link rel="canonical" href="{canonical}"><meta property="og:url" content="{canonical}">' if canonical else '',
              'ABSTRACT': esc((ROOT / 'data/abstract.txt').read_text(encoding='utf-8').strip())}
    build_walkthroughs(ROOT)
    for track in ('t2v', 'ref2v'):
        path = f'assets/diagrams/evaluation-{track}.html'
        version = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()[:12]
        values[f'WALKTHROUGH_{track.upper()}'] = f'{path}?v={version}'
    page = (ROOT / 'templates/index.html').read_text(encoding='utf-8')
    for key, value in values.items():
        page = page.replace('{{' + key + '}}', value)
    if '{{' in page:
        raise ValueError('Unresolved template field.')
    (ROOT / 'index.html').write_text(page, encoding='utf-8', newline='\n')
    print('Generated index.html and two standalone evaluation walkthroughs.')


if __name__ == '__main__':
    main()
