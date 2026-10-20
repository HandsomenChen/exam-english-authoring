#!/usr/bin/env python3
"""Count core English words; apostrophes stay internal, hyphens split."""
import argparse
import json
import re
import unicodedata
from pathlib import Path


def is_latin_letter(char):
    return char.isalpha() and 'LATIN' in unicodedata.name(char, '')


def word_spans(text):
    spans = []
    i = 0
    while i < len(text):
        if not is_latin_letter(text[i]):
            i += 1
            continue
        start = i
        i += 1
        while i < len(text):
            if is_latin_letter(text[i]) or unicodedata.category(text[i]).startswith('M'):
                i += 1
            elif text[i] in "'’" and i + 1 < len(text) and is_latin_letter(text[i + 1]):
                i += 1
            else:
                break
        spans.append((start, i))
    return spans


def count(text):
    return {'core_english_words': len(word_spans(text)),
            'numeric_tokens_separate': len(re.findall(r'\d+(?:[.,]\d+)*', text)),
            'characters': len(text),
            'convention': 'Latin word tokens; internal straight/curly apostrophes retained; hyphens split; numeric tokens separate. No auto-removal of headings/options.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    args = parser.parse_args()
    try:
        text = args.file.read_text(encoding='utf-8')
    except (OSError, UnicodeError) as exc:
        parser.exit(2, f'Cannot read input: {exc}\n')
    print(json.dumps(count(text), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
