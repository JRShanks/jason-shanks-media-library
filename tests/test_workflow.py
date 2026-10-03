import unittest
import tempfile
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from url_identity import normalize_url
from run_control import transition
from verify_deploy import verify, BASE, SITE
from scraper import merge_candidates
from guard_changes import check
class WorkflowTests(unittest.TestCase):
    def test_url_identity_preserves_case(self):
        self.assertNotEqual(normalize_url('https://youtube.com/watch?v=AbC'),normalize_url('https://youtube.com/watch?v=abc'))
        self.assertNotEqual(normalize_url('https://example.com/Case'),normalize_url('https://example.com/case'))
        self.assertEqual(normalize_url('HTTPS://EXAMPLE.COM/Case?i=AbC&utm_source=test#fragment'),'https://example.com/Case?i=AbC')
    def test_repeat_candidate_discovery(self):
        item={'title':'Public test','url':'https://example.com/Case?utm_source=a','verified':False}
        candidates,n=merge_candidates([],[],[item]);self.assertEqual(n,1)
        self.assertEqual(merge_candidates([],candidates,[item])[1],0)
    def test_lease_and_duplicate_run(self):
        state={};r=transition(state,'begin','weekly','2026-W40',None,1)
        with self.assertRaises(ValueError):transition(state,'begin','monthly','2026-10',None,2)
        with self.assertRaises(ValueError):transition(state,'complete','weekly','2026-W40','wrong',2)
        transition(state,'complete','weekly','2026-W40',r['token'],3)
        self.assertEqual(transition(state,'begin','weekly','2026-W40',None,4)['status'],'already-completed')
        r=transition(state,'begin','monthly','2026-10',None,5)
        transition(state,'fail','monthly','2026-10',r['token'],6)
        self.assertEqual(transition(state,'begin','monthly','2026-10',None,7)['status'],'acquired')
    def test_publication_authority(self):
        before=[{'url':'https://example.com/Old','verified':True,'featured':True}]
        new={'url':'https://example.com/New','verified':True}
        self.assertEqual(check(before,before+[new]),1)
        for after in [[],[dict(before[0],featured=False)],before+[dict(new,featured=True)],before+[dict(new,verified=False)]]:
            with self.assertRaises(ValueError):check(before,after)

    def test_exact_verification_rejects_stale_fields_extras_and_assets(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'public/data').mkdir(parents=True)
            records=[{'url':'https://example.com/item','title':'Correct','featured':True}]
            raw=json.dumps(records).encode();(root/'public/data/media_links.json').write_bytes(raw)
            responses={BASE+'/data/media_links.json':raw,SITE:b'<div id="jason-media-library"></div><link href="https://jason-shanks-media.netlify.app/embed.css"><script src="https://jason-shanks-media.netlify.app/embed.js" data-jml-container="jason-media-library" data-jml-data-url="https://jason-shanks-media.netlify.app/data/media_links.json"></script>'}
            for name in ['index.html','embed.js','embed.css','build-manifest.json']:
                (root/'public'/name).write_bytes(b'expected');responses[BASE+'/'+name]=b'expected'
            self.assertEqual(verify(responses.__getitem__,root),1)
            for wrong in [[dict(records[0],title='Stale')],records+[{'url':'https://extra'}],[]]:
                responses[BASE+'/data/media_links.json']=json.dumps(wrong).encode()
                with self.assertRaises(ValueError):verify(responses.__getitem__,root)
            responses[BASE+'/data/media_links.json']=raw;responses[BASE+'/embed.js']=b'stale'
            with self.assertRaises(ValueError):verify(responses.__getitem__,root)
            responses[BASE+'/embed.js']=b'expected';responses[SITE]=b'<div>missing loader</div>'
            with self.assertRaises(ValueError):verify(responses.__getitem__,root)
if __name__=='__main__':unittest.main()
