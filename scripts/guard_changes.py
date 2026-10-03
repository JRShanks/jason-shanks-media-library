#!/usr/bin/env python3
"""Enforce automatic publication authority: verified additions only, no feature changes."""
import json
import subprocess
from pathlib import Path
from url_identity import normalize_url
ROOT=Path(__file__).resolve().parent.parent

def check(before, after):
    current={item['url']:item for item in after}
    if len(current)!=len(after):raise ValueError('duplicate public URL')
    for item in before:
        if current.get(item['url'])!=item:
            raise ValueError('existing public record changed or removed; separate instruction required')
    known={item['url'] for item in before}
    identities=set()
    for item in after:
        identity=normalize_url(item['url'])
        if identity in identities:raise ValueError('duplicate normalized public URL')
        identities.add(identity)
        if item['url'] not in known and (item.get('verified') is not True or item.get('featured')):
            raise ValueError('new records must be verified and may not introduce featured placement')
    return len(after)-len(before)

if __name__=='__main__':
    before=json.loads(subprocess.check_output(['git','show','HEAD:data/media_links.json'],cwd=ROOT))
    after=json.loads((ROOT/'data/media_links.json').read_text())
    print('Public change guard passed:',check(before,after),'verified addition(s), existing records preserved')
