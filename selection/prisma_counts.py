"""Recompute the PRISMA 2020 flow numbers (identification to full-text inclusion) from the project files.

Run from search_redo_2026/. Full-text exclusion reasons use the first failed condition of the model(s) that excluded
the record; where both models excluded with different first failed conditions, the Opus condition is used.
"""
import csv, glob, collections
import pandas as pd
from pathlib import Path
csv.field_size_limit(10**9)
R = Path('.'); V2 = R/'02_exports'/'v2'; FT = R/'07_fulltext'
loaded = {'arXiv': len(pd.read_csv(V2/'arxiv_v2.csv', encoding='utf-8-sig')),
  'IEEE': sum(1 for f in glob.glob(str(V2/'ieee_v2'/'*.csv')) for _ in csv.DictReader(open(f, encoding='utf-8-sig', newline=''))),
  'ACM': len(pd.read_csv(V2/'acm_v2'/'acm_v2_records.csv', encoding='utf-8-sig')),
  'Venue': len(pd.read_csv(R/'03_manual'/'venue_v2_candidates.csv', encoding='utf-8-sig'))}
date_removed = {'arXiv': 0, 'IEEE': 200, 'ACM': 15, 'Venue': 0}
merged = len(pd.read_csv(V2/'v2_merged_records.csv', encoding='utf-8-sig'))
print('loaded', loaded, sum(loaded.values()), 'date removed', sum(date_removed.values()), 'after date', sum(loaded.values())-sum(date_removed.values()), 'merged', merged)
dl = pd.read_csv(FT/'fulltext_download_list.csv', encoding='utf-8-sig', dtype=str)
wd = pd.read_csv(FT/'excluded_withdrawn.csv'); fd = pd.read_csv(FT/'fulltext_duplicates.csv')
ve = pd.read_csv(FT/'venue_eligibility.csv', encoding='utf-8-sig', dtype=str)
print('sought', len(dl), 'withdrawn', len(wd), 'ftdup', len(fd), 've rows', len(ve), ve.venue_category.value_counts().to_dict())
print('unreadable', open(FT/'text_unreadable.csv',encoding='utf-8-sig').read()[:200])
m = pd.read_csv(FT/'ft_merged.csv', encoding='utf-8-sig', dtype=str).fillna('')
adj = pd.read_csv(FT/'returned/ft_adjudication_author1_20261026.csv', encoding='utf-8-sig', dtype=str).set_index('record_id')
print('assessed', len(m), 'S0371 in', 'S0371' in set(m.record_id), set(ve[ve.c5_eligible=='True'].record_id)-set(m.record_id))
import re as _re
src = (FT/'apply_ft_adjudication.py').read_text(encoding='utf-8')
scope = set(_re.findall(r"'(S\d{4})': '", src[src.index('C3_EXCLUDED = {'):src.index('}', src.index('C3_EXCLUDED = {'))]))
dups = set(_re.findall(r"'(S\d{4})': 'S\d{4}'", src))
included = set(pd.read_csv(FT/'ft_included.csv', encoding='utf-8-sig', dtype=str).record_id)
core = pd.read_csv(FT/'c4b_core_merged.csv', encoding='utf-8-sig', dtype=str)
core_adj = pd.read_csv(FT/'returned/c4b_core_adjudication_author1_20261026.csv', encoding='utf-8-sig', dtype=str)
core_ex = set(core[core.status == 'both not satisfied'].record_id) | set(core_adj[core_adj.author1_decision == 'not_satisfied'].record_id)
adj = adj[adj.index.isin(m.record_id)]
reasons = collections.Counter()
for _, r in m.iterrows():
    rid, o, g = r.record_id, r.opus_decision, r.gpt_decision
    if rid in included: continue
    if rid in dups: reasons['duplicate'] += 1; continue
    if rid in scope: reasons['C3 (scope ruling)'] += 1; continue
    if rid in core_ex: reasons['C4b (harness not core contribution)'] += 1; continue
    if o == 'exclude' and g == 'exclude': reasons[r.opus_first_failed] += 1; continue
    reasons[r.opus_first_failed if o == 'exclude' else r.gpt_first_failed] += 1
print('ft excl reasons', dict(reasons), sum(reasons.values()), '| included', len(included))
both_ex = m[(m.opus_decision=='exclude')&(m.gpt_decision=='exclude')]
print('both-ex reason differs', (both_ex.opus_first_failed != both_ex.gpt_first_failed).sum())
