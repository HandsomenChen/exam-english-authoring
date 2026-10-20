#!/usr/bin/env python3
"""Audit one structured unit. Structural success is not semantic approval."""
import argparse
import json
from pathlib import Path
from count_words import count, word_spans

MODES = {'cloze', 'reading_a', 'matching', 'sorting', 'headings', 'insertion',
         'translation_e1', 'translation_e2'}


def audit(unit):
    errors, warnings = [], []
    report = {'structural_ok': False, 'errors': errors, 'warnings': warnings,
              'scope': 'Structure, counts, exact spans, restoration and answer mappings only; no semantic, source, translation or visual certification.'}
    def require(ok, message):
        if not ok:
            errors.append(message)
        return ok
    if not require(isinstance(unit, dict), 'Unit must be an object.'):
        return report
    mode = unit.get('mode')
    if not require(isinstance(mode, str) and mode in MODES, 'Unknown mode.'):
        return report
    report['mode'] = mode
    require(isinstance(unit.get('unit_id'), str) and bool(unit['unit_id'].strip()), 'unit_id must be nonempty.')
    require(isinstance(unit.get('source_id'), str) and bool(unit['source_id'].strip()), 'source_id must be nonempty (not a source verification).')
    paras = unit.get('paragraphs')
    if not require(isinstance(paras, list) and bool(paras), 'paragraphs must be a nonempty list.'):
        return report
    if not require(all(isinstance(p, dict) and isinstance(p.get('id'), str) and p['id'] and isinstance(p.get('text'), str) and p['text'].strip() for p in paras), 'Every paragraph needs nonempty id and text.'):
        return report
    ids = [p['id'] for p in paras]
    require(len(set(ids)) == len(ids), 'Duplicate paragraph IDs.')
    body = '\n\n'.join(p['text'] for p in paras)
    report['body_count'] = count(body)
    report['paragraph_counts'] = {p['id']: count(p['text']) for p in paras}
    if 'adapted_text' in unit:
        require(unit['adapted_text'] == body, 'adapted_text differs from canonical paragraph join.')
    if not all(isinstance(p.get('zh'), str) and p['zh'].strip() for p in paras):
        warnings.append('Not all paragraphs contain Chinese; bilingual delivery completeness is pending.')

    def sequence(value, name, expected):
        if not require(isinstance(value, list) and all(isinstance(x, dict) for x in value), f'{name} must be a list of objects.'):
            return []
        nums = [x.get('number') for x in value]
        require(nums == list(expected), f'{name} numbers must be {list(expected)} in order.')
        return value

    def options(item):
        opts = item.get('options')
        if not require(isinstance(opts, dict) and set(opts) == set('ABCD') and all(isinstance(v, str) and v.strip() for v in opts.values()), 'Each MCQ needs four nonempty options A-D.'):
            return None
        require(len({v.strip().casefold() for v in opts.values()}) == 4, 'Duplicate option text.')
        correct = item.get('correct')
        if not require(isinstance(correct, str) and correct in opts, 'Correct answer label must be A-D.'):
            return None
        return opts[correct]

    def ranges(items, expected_text):
        valid = []
        for item, wanted in zip(items, expected_text):
            a, b = item.get('start'), item.get('end')
            if not require(type(a) is int and type(b) is int and 0 <= a < b <= len(body), f'Invalid character span at {item.get("number")}.'):
                continue
            actual = body[a:b]
            require(isinstance(wanted, str) and actual == wanted, f'Span text mismatch at {item.get("number")}.')
            valid.append((a, b, item))
        ordered = sorted(valid, key=lambda x: x[0])
        require([v[2].get('number') for v in ordered] == [v[2].get('number') for v in valid], 'Spans must follow text order.')
        for prev, cur in zip(ordered, ordered[1:]):
            require(prev[1] <= cur[0], 'Overlapping spans.')
        return ordered

    def blanked(ordered):
        text = body
        for a, b, item in reversed(ordered):
            text = text[:a] + '{{' + str(item['number']) + '}}' + text[b:]
        return text

    if mode == 'cloze':
        gaps = sequence(unit.get('gaps'), 'gaps', range(1, 21))
        expected = []
        for gap in gaps:
            correct = options(gap)
            require(gap.get('answer') == correct and isinstance(correct, str), 'Cloze answer must equal correct option text.')
            expected.append(gap.get('answer'))
        ordered = ranges(gaps, expected)
        report['printed_text'] = blanked(ordered)
        report['printed_count'] = count(replace_markers(report['printed_text']))
        report['answer_span_counts'] = [count(body[a:b])['core_english_words'] for a,b,_ in ordered]
        distances = [len(word_spans(body[a[1]:b[0]])) for a,b in zip(ordered,ordered[1:])]
        report['adjacent_printed_word_gaps'] = distances
        if any(d < 3 for d in distances):
            warnings.append('At least one adjacent gap has fewer than 3 printed English words. Review local cues; 3 is a review trigger, not an official minimum.')
    elif mode == 'reading_a':
        start = unit.get('question_start', 21)
        if not require(type(start) is int and start in (21,26,31,36), 'question_start must be 21,26,31 or36.'):
            start = 21
        items = sequence(unit.get('items'), 'items', range(start,start+5))
        for item in items:
            require(isinstance(item.get('stem'),str) and bool(item['stem'].strip()), 'Each reading item needs a stem.')
            options(item)
    elif mode == 'translation_e1':
        spans = sequence(unit.get('spans'), 'spans', range(46,51))
        ordered = ranges(spans, [x.get('text') for x in spans])
        report['underlined_counts'] = [count(body[a:b]) for a,b,_ in ordered]
        report['underlined_total_words'] = sum(x['core_english_words'] for x in report['underlined_counts'])
        for span in spans:
            require(isinstance(span.get('reference_translation'),str) and bool(span['reference_translation'].strip()), 'Each span needs a reference translation.')
    elif mode == 'translation_e2':
        require(unit.get('number') == 46, 'English II whole-text translation number must be46.')
        require(not unit.get('spans'), 'English II must not contain English I underlined spans.')
        require(isinstance(unit.get('reference_translation'),str) and bool(unit['reference_translation'].strip()), 'Whole-text reference translation is required.')
    else:
        candidates = unit.get('candidates')
        if not require(isinstance(candidates,list) and all(isinstance(c,dict) for c in candidates), 'candidates must be a list of objects.'):
            return report
        labels = [c.get('label') for c in candidates]
        labels_ok = all(isinstance(v,str) and len(v)==1 and 'A' <= v <= 'Z' for v in labels)
        require(labels_ok and len(set(labels))==len(labels), 'Candidate labels must be unique uppercase letters.')
        if not labels_ok:
            return report
        answers = sequence(unit.get('answers'), 'answers', range(41,46))
        picks = [a.get('label') for a in answers]
        for label in picks:
            require(isinstance(label,str) and label in labels, 'Answer refers to missing candidate.')
        reuse = unit.get('allow_reuse',False)
        require(type(reuse) is bool, 'allow_reuse must be boolean.')
        require(not reuse or mode=='matching', 'Reuse supported only for explicit matching instructions.')
        if not reuse and all(isinstance(v,str) for v in picks):
            require(len(set(picks))==len(picks), 'Repeated answer candidate when reuse is not allowed.')
        if mode == 'sorting':
            paragraph_ids = [c.get('paragraph_id') for c in candidates]
            if not require(all(isinstance(v,str) and v in ids for v in paragraph_ids), 'Sorting candidates must map to existing paragraph IDs.'):
                return report
            require(len(paragraph_ids)==len(ids) and len(set(paragraph_ids))==len(ids), 'Each paragraph must appear in exactly one sorting candidate.')
            order = unit.get('answer_order')
            if not require(isinstance(order,list) and all(isinstance(v,str) for v in order) and len(order)==len(labels) and set(order)==set(labels), 'answer_order must include every candidate exactly once.'):
                return report
            mapped = {c['label']:c.get('paragraph_id') for c in candidates}
            require([mapped[v] for v in order]==ids, 'Restored sorting order differs from canonical paragraph order.')
            fixed = unit.get('fixed_positions',[])
            if not require(isinstance(fixed,list) and all(isinstance(f,dict) for f in fixed), 'fixed_positions must be a list of objects.'):
                fixed=[]
            positions=[]
            for obj in answers+fixed:
                pos,label=obj.get('position'),obj.get('label')
                if require(type(pos) is int and 1<=pos<=len(order),'Sorting positions out of range.'):
                    positions.append(pos)
                    require(order[pos-1]==label,'Fixed position or answer conflicts with answer_order.')
            require(sorted(positions)==list(range(1,len(order)+1)), 'Fixed and answer positions must cover all positions once.')
            report['restored_text'] = body
        else:
            require(labels == list('ABCDEFG'), 'Matching/headings/insertion use seven candidates A-G in this contract.')
            for c in candidates:
                require(isinstance(c.get('text'),str) and bool(c['text'].strip()), 'Each candidate needs nonempty text.')
            if mode in ('matching','headings'):
                targets=sequence(unit.get('targets'),'targets',range(41,46))
                for target in targets:
                    require(isinstance(target.get('description'),str) and bool(target['description'].strip()), 'Each target needs a person/object or section description.')
            if mode=='insertion':
                gaps=sequence(unit.get('gaps'),'gaps',range(41,46))
                lookup={c['label']:c.get('text') for c in candidates}
                by_number={a.get('number'):a.get('label') for a in answers if type(a.get('number')) is int}
                ordered=ranges(gaps,[lookup.get(by_number.get(g.get('number'))) for g in gaps])
                report['printed_text']=blanked(ordered)
                visible=count(replace_markers(report['printed_text']))
                report['printed_count']=visible
                report['correct_fragment_words']=sum(count(body[a:b])['core_english_words'] for a,b,_ in ordered)
                report['all_candidate_words']=sum(count(c.get('text',''))['core_english_words'] for c in candidates if isinstance(c.get('text'),str))
                report['total_reading_load_words']=visible['core_english_words']+report['all_candidate_words']
    report['structural_ok'] = not errors
    return report


def replace_markers(text):
    import re
    return re.sub(r'\{\{\d+\}\}', '', text)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    try:
        unit=json.loads(args.file.read_text(encoding='utf-8'))
    except (OSError,UnicodeError,json.JSONDecodeError) as exc:
        parser.exit(2,f'Cannot read JSON input: {exc}\n')
    report=audit(unit)
    text=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        args.output.write_text(text,encoding='utf-8')
    else:
        print(text,end='')
    parser.exit(0 if report['structural_ok'] else 1)


if __name__=='__main__':
    main()
