from pathlib import Path

text = Path('components/claude_processor.py').read_text(encoding='utf-8').splitlines()
for idx, line in enumerate(text, 1):
    if 'name="max_total_pages"' in line:
        print('max', idx)
    if 'name="pages_per_topic"' in line:
        print('per', idx)
    if 'def _max_total_pages' in line:
        print('defmax', idx)
    if 'def _pages_per_topic' in line:
        print('deftopic', idx)
    if 'def process_pages' in line:
        print('process', idx)
