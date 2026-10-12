"""Render deterministic, self-contained educational walkthroughs (no runtime model calls)."""
import base64
import html
import json
from pathlib import Path
import unicodedata

e = html.escape
STEPS = ['Define targets', 'Observe frames', 'Ground carriers', 'Select & group', 'Follow targets', 'Score & diagnose']


def normalize(text):
    return ''.join(c for c in text if not c.isspace() and not unicodedata.category(c).startswith('P'))


def similarity(a, b):
    a, b = normalize(a), normalize(b)
    if not a and not b:
        return 1.0
    previous = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        current = [i]
        for j, y in enumerate(b, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (x != y)))
        previous = current
    return 1 - previous[-1] / max(len(a), len(b))


def lesson_data(track):
    ref = track == 'ref2v'
    targets = ['ORANGE JUICE', 'ZERO SUGAR'] if ref else ['FRESH ORANGE JUICE', 'OPEN DAILY']
    ids = ['T0001', 'T0002'] if ref else ['T1', 'T2']
    carriers = ['R01 carton', 'R02 can'] if ref else ['C1 storefront sign', 'C2 window poster']
    wrong = targets[0].replace('JUICE', 'JU1CE')
    sequences = [[targets[0], wrong, None, wrong], [targets[1], targets[1], targets[1], '']]
    target_metrics = []
    for target, sequence in zip(targets, sequences):
        active = [s for s in sequence if s is not None]
        spatial = sum(similarity(target, s) if s else 0 for s in active) / len(active)
        temporal = sum(similarity(a, b) if a and b else 0 for a, b in zip(active, active[1:])) / (len(active) - 1)
        target_metrics.append({'spatial': spatial, 'temporal': temporal, 'length': len(normalize(target))})
    weights = [1, 1] if ref else [m['length'] for m in target_metrics]
    spatial = sum(m['spatial'] * w for m, w in zip(target_metrics, weights)) / sum(weights)
    temporal = sum(m['temporal'] * w for m, w in zip(target_metrics, weights)) / sum(weights)
    extra_length = len(normalize(targets[0]))
    extra_frames = []
    for i in range(4):
        matched_length = sum(len(normalize(seq[i])) for seq in sequences if seq[i])
        extra_frames.append(extra_length / (extra_length + matched_length))
    return {'track': track, 'targets': targets, 'ids': ids, 'carriers': carriers, 'wrong': wrong,
            'sequences': sequences, 'target_metrics': target_metrics,
            'metrics': {'spatial_fidelity': spatial, 'temporal_fidelity': temporal,
                        'textv_score': 100 * 2 * spatial * temporal / (spatial + temporal),
                        'extra_text_ratio': sum(extra_frames) / len(extra_frames)},
            'timestamps': [0, .5, 1, 1.5], 'extra_per_frame': extra_frames}


def text(x, y, label, size=20, fill='#263449', weight=500, anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{e(label)}</text>'


def define_targets_scene(track, step):
    """Show generated target illustrations with lettering inside the RGB image."""
    ref = track == 'ref2v'
    filename = 'ref2v-define-targets-layout.webp' if ref else 'define-targets-layout.webp'
    title = ('Two illustrative product references with their intended text' if ref
             else 'Two intended text targets on distinct storefront carriers')
    description = ('Two AI-generated reference illustrations with lettering generated within the image: the R01 carton on the left reads ORANGE JUICE, and the R02 can on the right reads ZERO SUGAR. These illustrate reference targets, not observed video outputs.' if ref
                   else 'AI-generated storefront illustration with lettering generated within the image: T1 is FRESH ORANGE JUICE on the C1 storefront sign; T2 is OPEN DAILY on the separate C2 window poster. This is a target specification illustration, not an observed model output.')
    caption = ('AI-generated reference illustrations · R01 left, R02 right' if ref
               else 'AI-generated illustration · intended targets')
    slug = f'{track}-target-layout-{step}'
    image = Path(__file__).resolve().parents[1] / 'assets/images' / filename
    uri = 'data:image/webp;base64,' + base64.b64encode(image.read_bytes()).decode('ascii')
    return ''.join([
        f'<svg class="target-layout" viewBox="0 0 1536 1024" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{slug}-title {slug}-desc">',
        f'<title id="{slug}-title">{e(title)}</title>',
        f'<desc id="{slug}-desc">{e(description)}</desc>',
        f'<image href="{uri}" width="1536" height="1024"/>',
        f'</svg><p class="visual-note">{e(caption)}</p>',
    ])


def scene_svg(track, step):
    if step in (0, 1):
        return define_targets_scene(track, step)
    ref = track == 'ref2v'
    slug = f'{track}-scene-{step}'
    observed = step >= 2
    markers = step >= 2 and not (ref and step == 3)
    ground = step >= 3
    select = step >= 4
    parts = [f'<svg viewBox="0 0 640 420" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{slug}-title {slug}-desc"><title id="{slug}-title">{("Reference-grounded" if ref else "Carrier-grounded")} correspondence, step {step}</title><desc id="{slug}-desc">A target is split across two OCR regions on its intended carrier. An identical phrase on a different carrier is not valid evidence for that target.</desc><rect width="640" height="420" fill="#f8fafc"/>']
    if not ref:
        parts += ['<rect x="48" y="48" width="544" height="332" rx="8" fill="#edf0f3" stroke="#cfd7e2"/><rect x="64" y="64" width="512" height="100" rx="4" fill="#fff" stroke="#c9d5e7"/><rect x="72" y="188" width="224" height="168" fill="#e3ebf4" stroke="#bdccdf"/><path d="M184 188V356M72 264H296" stroke="#c1cede" stroke-width="4"/><path d="M88 204L136 252M204 280L252 328" stroke="#f6f9fc" stroke-width="8"/><rect x="336" y="184" width="240" height="176" rx="4" fill="#fffaf0" stroke="#d6d1c4"/>',
                  text(320, 108, 'FRESH ORANGE', 28, anchor='middle'), text(320, 148, 'JU1CE' if observed else 'JUICE', 28, anchor='middle'),
                  text(456, 236, 'FRESH ORANGE' if observed else 'WINDOW POSTER', 16, '#7a7468', anchor='middle'),
                  text(456, 260, 'JUICE' if observed else ' ', 16, '#7a7468', anchor='middle'),
                  text(456, 324, 'OPEN DAILY', 24, anchor='middle')]
        boxes = [(168, 80, 304, 36), (264, 120, 112, 36), (348, 212, 216, 56), (348, 296, 216, 36)]
        boundaries = [(56, 56, 528, 116), (328, 176, 256, 192)]
        parts += [text(64, 32, 'C1 · STOREFRONT SIGN', 16, '#285bc4'), text(336, 400, 'C2 · WINDOW POSTER', 16, '#6f7f94')]
    else:
        # Reference thumbnails contain only their original target; the duplicate occurs in the generated scene.
        parts += ['<rect x="48" y="12" width="240" height="92" rx="4" fill="#fff" stroke="#dbe3ed"/><rect x="352" y="12" width="240" height="92" rx="4" fill="#fff" stroke="#dbe3ed"/><rect x="64" y="24" width="40" height="64" rx="4" fill="#f4dba6" stroke="#d5b870"/><rect x="368" y="24" width="40" height="64" rx="12" fill="#d1e0dd" stroke="#9cbab3"/>',
                  text(116, 44, 'R01 · REFERENCE', 16, '#285bc4'), text(116, 76, 'ORANGE JUICE', 16),
                  text(420, 44, 'R02 · REFERENCE', 16, '#285bc4'), text(420, 76, 'ZERO SUGAR', 16),
                  text(48, 136, 'ILLUSTRATED OBSERVATION' if observed else 'REFERENCE-DERIVED TARGETS', 16, '#718096'),
                  '<path d="M48 384H592" stroke="#c9d4e1" stroke-width="4"/><path d="M96 176L124 152H256L280 176V376H96Z" fill="#f4dba6" stroke="#c4aa76" stroke-width="2"/><rect x="108" y="200" width="160" height="140" rx="4" fill="#fff9ed"/><rect x="360" y="156" width="200" height="220" rx="28" fill="#d1e0dd" stroke="#a8c1ba" stroke-width="2"/><rect x="372" y="196" width="176" height="148" rx="4" fill="#f8fbfa"/>',
                  text(188, 240, 'ORANGE', 28, anchor='middle'), text(188, 280, 'JU1CE' if observed else 'JUICE', 28, anchor='middle'),
                  text(460, 232, 'ORANGE JUICE' if observed else 'R02', 16, '#6a7e77', anchor='middle'),
                  text(460, 316, 'ZERO SUGAR', 24, anchor='middle')]
        boxes = [(116, 212, 144, 36), (132, 252, 112, 36), (380, 208, 160, 40), (372, 288, 176, 36)]
        boundaries = [(88, 144, 200, 240), (352, 144, 216, 240)]
    if ground:
        for i, (x, y, w, h) in enumerate(boundaries):
            color = '#285bc4' if i == 0 else '#8a9bb2'
            parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="none" stroke="{color}" stroke-width="3" stroke-dasharray="8 4"/>')
    if markers:
        if select:
            if ref:
                parts.append('<path d="M260 230H300Q308 230 308 238V264Q308 272 300 272H244" fill="none" stroke="#285bc4" stroke-width="2"/>' + text(320, 304, 'T0001', 16, '#285bc4', 650, 'middle'))
            else:
                parts.append('<path d="M472 98H496Q504 98 504 106V132Q504 140 496 140H376" fill="none" stroke="#285bc4" stroke-width="2"/>' + text(524, 124, 'T1', 16, '#285bc4', 650))
        for i, (x, y, w, h) in enumerate(boxes):
            selected = select and i in [0, 1, 3]
            color = '#285bc4' if selected or not select else '#929bab'
            dashed = ' stroke-dasharray="4 4"' if select and i == 2 else ''
            tx, ty = (x - 64, y + 8) if i == 1 else (x, y - 20)
            parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="none" stroke="{color}" stroke-width="2"{dashed}/><rect x="{tx}" y="{ty}" width="56" height="20" rx="2" fill="{color}"/>' + text(tx + 28, ty + 15, f'P00{i + 1}', 16, '#fff', 650, 'middle'))
    parts.append('</svg>')
    result = ''.join(parts)
    return result.replace('>JU1CE</text>', '>JU<tspan fill="#a85619" font-weight="700">1</tspan>CE</text>') if select else result


def json_view(data):
    return '<details class="example-data"><summary>View example data <span aria-hidden="true">↗</span></summary><p class="data-note">Simplified fields from this illustrative example.</p><pre><code>' + e(json.dumps(data, indent=2, ensure_ascii=False)) + '</code></pre></details>'


def frame_sequence(d):
    ref = d['track'] == 'ref2v'
    motion = [
        ('Establish', 'Both references are visible on the counter.' if ref else 'A wide view establishes the sign and window poster.'),
        ('Move', 'The carton slides and turns; the can moves forward. JU1CE remains matched to the carton.' if ref else 'The camera moves along the facade. The sign now reads JU1CE.'),
        ('Leave view', 'The carton leaves the shot. R01 is inactive; the can remains visible.' if ref else 'The camera tilts down to the poster. The storefront sign leaves the active view.'),
        ('Return', 'The carton returns with JU1CE. The can stays visible, but ZERO SUGAR is missing.' if ref else 'The camera pulls back up. The sign returns with JU1CE; OPEN DAILY is missing from the visible poster.'),
    ]
    parts = ['<div class="frame-player"><div class="sampled-frames">']
    for index, (title, description) in enumerate(motion):
        filename = f'{d["track"]}-follow-{index}.webp'
        raw = (Path(__file__).resolve().parents[1] / 'assets/images/sequences' / filename).read_bytes()
        uri = 'data:image/webp;base64,' + base64.b64encode(raw).decode('ascii')
        timestamp = f'{d["timestamps"][index]:.1f} s'
        slug = f'{d["track"]}-observation-{index}'
        parts.append(f'<figure class="sampled-frame" id="{slug}" data-sequence-frame="{index}" aria-label="{timestamp}: {e(title)}"><img width="768" height="512" src="{uri}" alt="{e(timestamp + ": " + description)}"><figcaption><strong>{timestamp} · {e(title)}</strong><p>{e(description)}</p></figcaption></figure>')
    parts.append('</div><div class="frame-controls" data-frame-controls role="group" aria-label="Sampled observation controls">')
    parts.append('<button type="button" class="frame-play" data-frame-play aria-pressed="false" disabled>Play frames</button><div class="frame-times" role="group" aria-label="Choose observation">')
    for index, timestamp in enumerate(d['timestamps']):
        parts.append(f'<button type="button" data-frame-select="{index}" aria-controls="{d["track"]}-observation-{index}" aria-pressed="false" disabled>{timestamp:.1f} s</button>')
    parts.append('</div></div><p class="visual-note">AI-generated sampled frames · illustrative motion</p><p class="sr-only" data-frame-status role="status" aria-live="polite" aria-atomic="true"></p></div>')
    return ''.join(parts)


def timeline(d):
    parts = ['<div class="timeline-data"><div class="sequence-heading"><span>Four sampled observations</span><span>Same target identity →</span></div><div class="sequence-scroll" tabindex="0" role="region" aria-label="Target observations, scroll horizontally on small screens"><table class="sequence-table"><thead><tr><th scope="col">Target</th>']
    for index, t in enumerate(d['timestamps']):
        parts.append(f'<th scope="col" data-frame-cell="{index}"><button type="button" data-frame-select="{index}" aria-controls="{d["track"]}-observation-{index}" aria-pressed="false" disabled>{t:.1f} s</button></th>')
    parts.append('</tr></thead><tbody>')
    for sid, sequence in zip(d['ids'], d['sequences']):
        parts.append(f'<tr><th scope="row">{sid}</th>')
        for index, value in enumerate(sequence):
            if value is None:
                content = '<span class="state inactive">— Inactive</span><small>Excluded</small>'
            elif not value:
                content = '<span class="state missing">∅ Missing</span><small>Active · no match</small>'
            else:
                observed = e(value).replace('JU1CE', 'JU<mark>1</mark>CE')
                content = f'<span class="observed-string">{observed}</span><small>✓ Matched</small>'
            parts.append(f'<td data-frame-cell="{index}">{content}</td>')
        parts.append('</tr>')
    parts += ['</tbody></table></div><div class="timeline-notes">', '<div class="sequence-rule"><b>Inactive ≠ missing</b><p>The first target leaves the active view at 1.0 s, then returns. The second carrier remains active at 1.5 s, but its target has no matched OCR evidence.</p></div>',
              f'<div class="selected-evidence"><span>{d["ids"][0]} · valid temporal pairs</span><strong>0.0 → 0.5 s <i>and</i> 0.5 → 1.5 s</strong><p>The inactive observation is skipped. Candidate IDs are local to each frame; target IDs connect the observations.</p></div></div></div>']
    return ''.join(parts)


def score_visual(d):
    m = d['metrics']
    parts = [f'<div class="score-hero"><span>Illustrative TextVScore</span><strong>{m["textv_score"]:.2f}<small>/ 100</small></strong><p>100 × 2ST / (S + T)</p></div><div class="score-components">']
    for title, key in [('Spatial', 'spatial_fidelity'), ('Temporal', 'temporal_fidelity')]:
        parts.append(f'<div><span>{title}</span><strong>{m[key]:.3f}</strong><div class="bar"><span style="width:{m[key]*100:.4f}%"></span></div></div>')
    parts.append('</div><div class="sequence-scroll" tabindex="0" role="region" aria-label="Per-target scores, scroll horizontally on small screens"><table class="target-scores"><thead><tr><th>Target</th><th>Characters</th><th>Spatial</th><th>Temporal</th></tr></thead><tbody>')
    for sid, metric in zip(d['ids'], d['target_metrics']):
        parts.append(f'<tr><td>{sid}</td><td>{metric["length"]}</td><td>{metric["spatial"]:.3f}</td><td>{metric["temporal"]:.3f}</td></tr>')
    parts.append(f'</tbody></table></div><div class="extra-result"><span>Extra text ratio <small>Separate diagnostic · lower is better</small></span><strong>{m["extra_text_ratio"]:.3f}</strong></div><p class="visual-note">Calculated over all four illustrative observations. P003 remains unassigned on each active frame.</p>')
    return ''.join(parts)


def stage_content(d, step):
    ref = d['track'] == 'ref2v'
    t1, t2 = d['targets']; id1, id2 = d['ids']
    candidates = [{'id': 'P001', 'ocr_text': t1.replace(' JUICE', ''), 'confidence': .98},
                  {'id': 'P002', 'ocr_text': 'JU1CE', 'confidence': .94},
                  {'id': 'P003', 'ocr_text': t1, 'confidence': .99},
                  {'id': 'P004', 'ocr_text': t2, 'confidence': .98}]
    if step == 1:
        purpose = 'Give every intended text a stable identity.'
        description = ('OCR reads the original reference images. Each detected reference region becomes a target tied to its reference ID.' if ref else 'The structured specification binds each target string to a particular carrier. The generation prompt and evaluation targets have distinct roles.')
        inputs = 'Original reference images + generation instruction' if ref else 'Prompt + carrier / slot specification'
        output = 'Reference-grounded target slots' if ref else 'Carrier-grounded target slots'
        data = {'targets': [{'slot_id': sid, 'target_text': target, **({'ref_id': f'R0{i+1}'} if ref else {'carrier': d['carriers'][i]})} for i, (sid, target) in enumerate(zip(d['ids'], d['targets']))]}
        visual = scene_svg(d['track'], 1) + '<div class="target-contracts">' + ''.join(f'<div><code>{sid}</code><span><strong>{e(target)}</strong><small>{e(carrier)}</small></span></div>' for sid, target, carrier in zip(d['ids'], d['targets'], d['carriers'])) + '</div>'
        note = 'Two references are used here to explain routing. This is an illustrative capability example.' if ref else 'Target strings are persistent in this track, even when their carriers move.'
    elif step == 2:
        purpose = 'Observe what is actually rendered.'
        description = 'Sample frames, run OCR, and retain eligible candidates. Each region has an ID, an observed string, confidence, and geometry. The string JU1CE stays exactly as observed.'
        inputs = 'Sampled video frame at 0.5 s'
        output = 'Numbered OCR candidates + marker image'
        data = {'timestamp': .5, 'ocr_candidates': candidates, 'geometry_note': 'Raw observations also store bbox polygons. Compact VLM payloads omit coordinates and use the numbered marker image.'}
        visual = scene_svg(d['track'], 2) + '<div class="candidate-list">' + ''.join(f'<div><code>{c["id"]}</code><span>{e(c["ocr_text"])}</span><small>{c["confidence"]:.2f}</small></div>' for c in candidates) + '</div>'
        note = 'OCR supplies the scored text. A high-confidence string can still be wrong or belong to another target.'
    elif step == 3:
        purpose = 'Identify the visual entity that owns the target.'
        description = ('Route each reference to its corresponding carrier in the generated frame. Here both the R01 carton and R02 can are present. Appearance and identity constrain the next matching step.' if ref else 'Use scene context, position, and visual attachment to find the storefront sign. P003 is inside the window poster, so it cannot satisfy the sign’s target—even with identical text.')
        inputs = 'Reference images + generated frame' if ref else 'Required carriers + numbered marker image'
        output = 'Active reference identities' if ref else 'Carrier presence + candidate ownership'
        data = {'matched_ref_ids': ['R01', 'R02']} if ref else {'carriers': [{'carrier_id': 'C1', 'present': True, 'candidate_ids': ['P001', 'P002']}, {'carrier_id': 'C2', 'present': True, 'candidate_ids': ['P003', 'P004']}]}
        visual = scene_svg(d['track'], 3) + '<div class="grounding-result"><span>✓ ' + ('R01 → carton' if ref else 'C1 → storefront sign') + '</span><span>✓ ' + ('R02 → can' if ref else 'C2 → window poster') + '</span></div>'
        note = 'Multi-reference routing uses the generated frame without OCR tags. A single reference is activated directly.' if ref else 'A carrier can be visible even when no readable candidate belongs to it.'
    elif step == 4:
        purpose = 'Select the intended instance, including its errors.'
        description = f'Combine P001 and P002 in reading order for {id1}. Their layout and carrier establish correspondence. P003 is a textual match on the wrong carrier. The selected JU1CE is not repaired.'
        inputs = 'Targets + reference grounding + marker image + candidates' if ref else 'Unresolved targets + marker image + carrier-constrained candidates'
        output = 'Selected candidate IDs, then verbatim OCR concatenation'
        response = {'matches': [{'slot_id': id1, 'selected_ids': ['P001', 'P002']}, {'slot_id': id2, 'selected_ids': ['P004']}]} if ref else {'matches': [{'i': 0, 'selected_ids': ['P001', 'P002']}]}
        data = {'vlm_response': response, 'assembled_observation': {'slot_id': id1, 'selected_ids': ['P001', 'P002'], 'pred_text': d['wrong']}}
        highlighted = e(d['wrong']).replace('JU1CE', 'JU<mark>1</mark>CE')
        visual = scene_svg(d['track'], 4) + f'<div class="selected-evidence"><span>{id1} ← P001 + P002</span><strong>{highlighted}</strong><p>Matched to the right target. The character error remains.</p></div><details class="why-detail"><summary>Why not P003?</summary><p>Its characters match perfectly, but its visual carrier is {e(d["carriers"][1])}. The target belongs to {e(d["carriers"][0])}. P003 stays unassigned.</p></details>'
        note = 'The VLM returns candidate IDs only. These teaching annotations are not model-generated explanations.' if ref else 'T2 → P004 resolves through the high-similarity fast path. Only unresolved T1 enters this VLM request; i = 0 is its request index.'
    elif step == 5:
        purpose = 'Compare the same target across active observations.'
        description = 'Match each frame independently, then group observations by stable target ID. A temporarily inactive carrier/reference is excluded. A missing match while active stays in the sequence and receives zero credit.'
        inputs = 'Per-frame matches + carrier / reference activity'
        output = 'Target-indexed sequences of active observations'
        data = {'slot_id': id1, 'observations': [{'timestamp': t, 'active': value is not None, 'pred_text': value or ''} for t, value in zip(d['timestamps'], d['sequences'][0])]}
        visual = frame_sequence(d)
        note = 'This uses multi-reference activation. A sole Ref2V reference stays active; missing evidence is not skipped.' if ref else 'Target IDs connect observations. OCR candidate IDs do not act as cross-frame tracking IDs.'
    else:
        purpose = 'Measure correctness and consistency after matching.'
        description = 'Spatial compares each observation with its intended target. Temporal compares adjacent active observations with one another. Persistent misspellings can be temporally stable while remaining spatially wrong.'
        inputs = 'Target strings + complete active observation sequences'
        output = 'Spatial, Temporal, TextVScore + separate diagnostics'
        data = {'metrics': d['metrics'], 'scope': 'All four illustrative frames; not a model benchmark result.'}
        visual = score_visual(d)
        note = 'Each reference has one target here. Scores are averaged equally across R01 and R02. Reading-order preservation is a separate diagnostic, not illustrated by these single-target references.' if ref else 'Video S and T use target-length weights: 16 characters for T1 and 9 for T2. The harmonic mean combines those video-level components.'
    return {'purpose': purpose, 'description': description, 'input': inputs, 'output': output, 'data': data, 'visual': visual, 'note': note}


def build_walkthroughs(root):
    css = (root / 'templates/walkthrough.css').read_text(encoding='utf-8')
    controller = (root / 'templates/motion-controller.js').read_text(encoding='utf-8')
    controller += '\n' + (root / 'templates/frame-sequence.js').read_text(encoding='utf-8')
    audits = {}
    for track in ['t2v', 'ref2v']:
        d = lesson_data(track)
        audits[track] = d
        title = 'T2V · Prompt-grounded correspondence' if track == 't2v' else 'Ref2V · Reference-grounded correspondence'
        parts = [f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{css}</style></head><body>',
                 '<main data-motion-root data-motion-mode="step" data-step-count="6" data-step-current="6" data-frame="static" data-static-frame="complete">',
                 f'<div class="lesson-title"><span>{title}</span><span>Illustrative data</span></div><ol class="step-strip" data-step-tabs aria-label="Evaluation stages">']
        parts += [f'<li class="step-label"><button type="button" class="step-tab" id="step-tab-{i}" data-step-tab="{i}" aria-controls="stage-{i}" disabled><b>{i:02d}</b><span>{name}</span></button></li>' for i, name in enumerate(STEPS, 1)]
        parts += ['</ol><div class="intro-panel"><div class="intro-visual">' + scene_svg(track, 0) + '</div><div class="intro-copy"><span class="overline">A guided example</span><h1>One target.<br>Several possible matches.</h1><p>Follow the evidence from intended text to a final score. At each step, inspect the scene, the decision, and the data it produces.</p><p class="start-hint">Choose any step above to jump in, <b>Next</b> to explore in order, or <b>Play</b> for a quick overview.</p></div></div>']
        for i, name in enumerate(STEPS, 1):
            c = stage_content(d, i)
            sequence_attrs = ' data-frame-sequence data-frame-current="0"' if i == 5 else ''
            timeline_html = timeline(d) if i == 5 else ''
            parts.append(f'<section{sequence_attrs} id="stage-{i}" class="stage-pane stage-{i}" data-motion-item data-step="{i}" aria-label="Step {i}: {e(name)}"><div class="visual-panel"><div class="visual-caption"><span>0{i} / {e(name)}</span><span>{"Target timeline" if i==5 else "Computed example" if i==6 else "Illustrated scene"}</span></div>{c["visual"]}</div><div class="explanation"><span class="overline">Purpose</span><h2>{e(c["purpose"])}</h2><p>{e(c["description"])}</p><dl><dt>Input</dt><dd>{e(c["input"])}</dd><dt>Output</dt><dd>{e(c["output"])}</dd></dl>{json_view(c["data"])}<p class="step-note">{e(c["note"])}</p></div>{timeline_html}</section>')
        parts.append('<div data-motion-controls role="group" aria-label="Walkthrough playback controls"><button type="button" data-motion-action="prev">← Previous</button><button type="button" data-motion-action="play" aria-pressed="false">Play</button><button type="button" data-motion-action="pause" aria-pressed="true">Pause</button><button type="button" data-motion-action="next" class="primary">Next →</button><button type="button" data-motion-action="replay">Replay</button><span data-motion-status-visible aria-hidden="true">Step <span data-motion-step-label>6</span> / 6</span></div><div class="lesson-footer"><span>← / → step · Space play/pause · R replay</span><span>Input → correspondence → measurement</span></div><p class="sr-only" data-motion-status role="status" aria-live="polite" aria-atomic="true"></p><noscript><p class="noscript-note">The complete six-step walkthrough is shown. JavaScript enables playback controls.</p></noscript></main>')
        parts.append('<script data-diagram-controls>' + controller + '</script></body></html>')
        (root / f'assets/diagrams/evaluation-{track}.html').write_text(''.join(parts), encoding='utf-8', newline='\n')
    (root / 'data/walkthrough-audit.json').write_text(json.dumps(audits, indent=2) + '\n', encoding='utf-8', newline='\n')
