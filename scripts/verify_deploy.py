#!/usr/bin/env python3
"""Verify exact deployed records, generated assets, and Squarespace loader wiring."""
import argparse
import json
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from html.parser import HTMLParser
ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://jason-shanks-media.netlify.app'
SITE = 'https://jasonrshanks.com/media-appearances'

def fetch(url):
    separator = '&' if '?' in url else '?'
    with urlopen(Request(url + separator + 'verify=' + str(time.time_ns()), headers={'User-Agent':'Clive-media-verifier/2'}), timeout=25) as r:
        return r.read()

class Loader(HTMLParser):
    def __init__(self):
        super().__init__(); self.container=False; self.script=False; self.css=False
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if a.get('id')=='jason-media-library': self.container=True
        def resource(value, path):
            p=urlsplit(value or '')
            return p.scheme=='https' and p.netloc=='jason-shanks-media.netlify.app' and p.path==path
        if tag=='script' and resource(a.get('src'), '/embed.js') and resource(a.get('data-jml-data-url'), '/data/media_links.json') and a.get('data-jml-container')=='jason-media-library': self.script=True
        if tag=='link' and resource(a.get('href'), '/embed.css'): self.css=True

def verify(fetcher=fetch, root=ROOT, base=BASE, site=SITE, required=()):
    local=json.loads((root/'public/data/media_links.json').read_text())
    remote=json.loads(fetcher(base+'/data/media_links.json'))
    if remote != local: raise ValueError('deployed JSON differs from expected complete records/order')
    if not set(required) <= {x['url'] for x in remote}: raise ValueError('required URL missing')
    for name in ['index.html','embed.js','embed.css','build-manifest.json']:
        if fetcher(base+'/'+name) != (root/'public'/name).read_bytes(): raise ValueError('deployed asset differs: '+name)
    loader=Loader();loader.feed(fetcher(site).decode())
    if not (loader.container and loader.script and loader.css): raise ValueError('Squarespace loader integration is missing or changed')
    return len(remote)

def main():
    p=argparse.ArgumentParser();p.add_argument('--require-url',action='append',default=[]);p.add_argument('--attempts',type=int,default=1);p.add_argument('--delay',type=float,default=10);a=p.parse_args()
    for attempt in range(max(1,a.attempts)):
        try:
            count=verify(required=a.require_url);print(f'Deployment verified: {count} exact records, all assets, Squarespace integration');return 0
        except Exception as e:
            print(f'Verification attempt {attempt+1}: {type(e).__name__}: {e}')
            if attempt+1<a.attempts:time.sleep(min(30,max(0,a.delay)))
    return 1
if __name__=='__main__':sys.exit(main())
