from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from argparse import Namespace
from contextlib import redirect_stdout
import io
import json
from seo_workbench import connect, findings, issue, reconcile, run_job


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.db = connect(Path(self.temp.name) / 'history.sqlite')
        for run in ('one','two','three','four'):
            self.db.execute("INSERT INTO runs(id) VALUES(?)", (run,))
        self.db.commit()

    def tearDown(self):
        self.db.close(); self.temp.cleanup()

    def test_new_persistent_resolved_reopened(self):
        item = issue('a','url','broken','404',100)
        self.assertEqual(reconcile(self.db,'one',[item],{'a'})['new'],1)
        self.assertEqual(reconcile(self.db,'two',[item],{'a'})['persistent'],1)
        self.assertEqual(reconcile(self.db,'three',[],{'a'})['resolved'],1)
        self.assertEqual(reconcile(self.db,'four',[item],{'a'})['reopened'],1)

    def test_missing_measurement_never_resolves_issue(self):
        item = issue('crawl','url','broken','404',100)
        reconcile(self.db,'one',[item],{'crawl'})
        self.assertEqual(reconcile(self.db,'two',[],set())['resolved'],0)
        self.assertEqual(self.db.execute('SELECT state FROM issues').fetchone()[0],'open')

    def test_changes_on_one_page_do_not_resolve_another_page(self):
        a = issue('page-a','a','broken','404',100)
        b = issue('page-b','b','broken','404',100)
        reconcile(self.db,'one',[a,b],{'page-a','page-b'})
        reconcile(self.db,'two',[],{'page-a'})
        self.assertEqual(self.db.execute('SELECT state FROM issues WHERE id=?',(b['id'],)).fetchone()[0],'open')

    def test_blocked_responses_are_review_not_broken(self):
        items,coverage = findings('links',{'error_map':{'pillar_free_ai_courses_2026.html':[{'url':'https://example.com','status':{'code':403,'text':'Forbidden'}}]}})
        self.assertEqual(items[0]['kind'],'verify-response')
        self.assertEqual(coverage,set())

    def test_crawl_network_errors_cannot_resolve_prior_findings(self):
        _,coverage = findings('growth',{'sites':{'site':{'audit':[{'url':'https://example.com', 'issues':['unverified response None: https://other.com']} ]}}})
        self.assertNotIn('audit:site:https://example.com',coverage)

    def test_unavailable_vale_cannot_resolve_writing_findings(self):
        _,coverage = findings('writing',{'files':[{'file':'draft.md','vale_error':'Tool unavailable'}]})
        self.assertNotIn('writing:draft.md',coverage)

    def test_unrelated_blocked_target_does_not_hide_a_verified_repair(self):
        scope='audit:site:https://example.com'
        old=issue(scope,'https://example.com','broken-link','broken link: https://old.example',100)
        reconcile(self.db,'one',[old],{scope})
        items,coverage=findings('growth',{'sites':{'site':{'audit':[{'url':'https://example.com','page_status':200,'body_observed':True,'issues':['unverified response 403: https://other.example']}]}}})
        reconcile(self.db,'two',items,coverage)
        self.assertEqual(self.db.execute('SELECT state FROM issues WHERE id=?',(old['id'],)).fetchone()[0],'resolved')

    def test_same_blocked_target_keeps_prior_broken_finding_open(self):
        scope='audit:site:https://example.com'
        old=issue(scope,'https://example.com','broken-link','broken link: https://old.example',100)
        reconcile(self.db,'one',[old],{scope})
        items,coverage=findings('growth',{'sites':{'site':{'audit':[{'url':'https://example.com','page_status':200,'body_observed':True,'issues':['unverified response 403: https://old.example']}]}}})
        reconcile(self.db,'two',items,coverage)
        self.assertEqual(self.db.execute('SELECT state FROM issues WHERE id=?',(old['id'],)).fetchone()[0],'open')

    def test_blocked_image_is_a_verification_task(self):
        items,_=findings('growth',{'sites':{'site':{'audit':[{'url':'https://example.com','issues':['unverified response 429: https://example.com/image.jpg']}]}}})
        self.assertEqual(items[0]['kind'],'verify-response')

    def test_failed_refresh_does_not_import_stale_report(self):
        root = Path(self.temp.name)
        (root / 'reports').mkdir()
        (root / 'bad.py').write_text('')
        (root / 'reports/content_review_latest.json').write_text(json.dumps({'files':[
            {'file':'old.md', 'long_sentences_over_30_words':['stale finding']}
        ]}))
        args = Namespace(dry_run=False,refresh=True,database=root / 'runner.sqlite')
        stage = [('writing',['bad.py'],'content_review_latest.json',(0,),1)]
        result = Namespace(returncode=9,stdout='',stderr='simulated failure')
        with patch('seo_workbench.BASE',root), patch('seo_workbench.STAGES',stage), patch('seo_workbench.subprocess.run',return_value=result), redirect_stdout(io.StringIO()):
            run_job(args)
        db = connect(args.database)
        self.assertEqual(db.execute('SELECT status FROM stages').fetchone()[0],'failed')
        self.assertEqual(db.execute('SELECT count(*) FROM issues').fetchone()[0],0)
        self.assertEqual(db.execute('SELECT status FROM runs').fetchone()[0],'partial')
        db.close()


if __name__ == '__main__': unittest.main()
