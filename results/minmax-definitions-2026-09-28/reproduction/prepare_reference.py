#!/usr/bin/env python3
"""Remove only the two added grammar exclusions, retaining all comparison tests."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
a=p.parse_args()
f=a.source/'parser/tau.tgf'
s=f.read_text()
old='capture | (ref & ~bf_min & ~bf_max) | wff | bf'
if s.count(old)!=2:
    p.error('expected exactly two added grammar exclusions; source unchanged')
f.write_text(s.replace(old,'capture | ref | wff | bf'))
