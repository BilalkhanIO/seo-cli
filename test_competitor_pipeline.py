import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from datetime import datetime, timezone
import article_competitor_audit as audit
from seo_workbench import findings

class ComparisonTests(unittest.TestCase):
    def test_only_live_unique_canonical_articles_survive(self):
        base={'status':'LIVE','title':'Page','content':'<p>Original article</p>','updated':'2026-01-01'}
        posts=[{**base,'url':'https://example.com/a'},
               {**base,'url':'https://example.com/a?m=1','updated':'2026-02-01'},
               {**base,'url':'https://example.com/draft','status':'DRAFT'},
               {**base,'url':'https://example.com/unknown','status':None}]
        live, excluded=audit.published_posts(posts)
        self.assertEqual(len(live),1)
        self.assertEqual(live[0]['updated'],'2026-02-01')
        self.assertEqual(excluded['DRAFT'],1)
        self.assertEqual(excluded['duplicate_url'],1)

    def test_article_scope_excludes_navigation_and_script(self):
        result=audit.measure('<nav>navigation words ignored</nav><div class="post-body"><h2>Useful heading</h2><p>Useful article words</p><script>ignored javascript</script></div>',fragment=True)
        self.assertEqual(result['words'],5)
        self.assertEqual(result['headings'],[{'level':'h2','text':'Useful heading'}])

    def test_no_article_container_remains_unknown_when_extractor_unavailable(self):
        with patch.dict('sys.modules',{'trafilatura':None}):
            result=audit.measure('<body><nav>Menus</nav><div>chrome only</div></body>')
        self.assertEqual(result['status'],'extraction_unavailable')
        self.assertIsNone(result['words'])

    def packet(self):
        return {'source':'verified_import','engine':'google','country':'us','language':'en',
                'device':'desktop','observed_at':datetime.now(timezone.utc).isoformat(),
                'result_type':'organic_ranked','query_reviewed':True}

    def test_single_measured_competitor_never_completes_top_ten(self):
        rows=[{'status':'measured','position':1}]
        self.assertEqual(audit.comparison_status(self.packet(),rows),'comparison_partial')

    def test_completion_requires_all_ten_ranks_context_and_success(self):
        rows=[{'status':'measured','position':i} for i in range(1,11)]
        self.assertEqual(audit.comparison_status(self.packet(),rows),'comparison_complete')
        for key,value in [('country',None),('query_reviewed',False),('result_type','candidate_pages'),('observed_at','2099-01-01T00:00:00Z')]:
            self.assertEqual(audit.comparison_status({**self.packet(),key:value},rows),'comparison_partial')
        rows[-1]['position']=9
        self.assertEqual(audit.comparison_status(self.packet(),rows),'comparison_partial')
        rows[-1]={'status':'fetch_unavailable','position':10}
        self.assertEqual(audit.comparison_status(self.packet(),rows),'comparison_partial')

    def test_repeated_heading_on_one_page_does_not_make_recurring_topic(self):
        heading={'level':'h2','text':'Certificate verification'}
        mine={'_tokens':['course']}
        self.assertFalse(audit.topic_candidates(mine,[{'headings':[heading,heading]}]))
        topics=audit.topic_candidates(mine,[{'headings':[heading]},{'headings':[heading]}])
        self.assertEqual(topics[0]['competitor_pages'],2)
        self.assertFalse(audit.topic_candidates({'_tokens':['certificate','verification']},[{'headings':[heading]},{'headings':[heading]}]))

    def test_duplicate_mobile_urls_do_not_inflate_sample(self):
        post={'url':'https://mine.example/page','title':'My page','content':'<h2>Helpful page</h2><p>Text</p>'}
        packet={'results':[{'url':'https://other.example/page','position':1}, {'url':'https://other.example/page?m=1','position':2}]}
        result=audit.compare(post,packet)
        self.assertEqual(len(result['competitors']),1)
        self.assertEqual(result['status'],'comparison_unavailable')

    def test_serp_provider_is_bounded_and_secret_is_not_cached(self):
        from io import BytesIO
        with TemporaryDirectory() as temp, patch.object(audit,'CACHE',Path(temp)), patch.dict('os.environ',{'SERPAPI_API_KEY':'private-test-key'}):
            response={'organic_results':[{'link':'https://example.com/a','position':1}], 'search_metadata':{'id':'id1'}}
            with patch.object(audit,'urlopen',return_value=BytesIO(json.dumps(response).encode())) as network:
                first=audit.discover('query','us','en','desktop')
                second=audit.discover('query','us','en','desktop')
            self.assertEqual(network.call_count,1)
            self.assertTrue(second['cached'])
            self.assertNotIn('private-test-key',next(Path(temp).glob('*.json')).read_text())
            self.assertEqual(first['results'][0]['position'],1)

    def test_fetch_uses_public_address_guard_before_opening(self):
        with patch.object(audit,'public_url',side_effect=ValueError('private')), patch.object(audit,'build_opener') as opener:
            result=audit.fetch('http://127.0.0.1/')
        self.assertEqual(result['status'],'fetch_unavailable')
        opener.assert_not_called()

    def test_runner_queues_pending_but_only_resolves_complete_coverage(self):
        data={'articles':[{'url':'https://example.com/a','status':'comparison_partial'}]}
        items, scopes=findings('competitors',data)
        self.assertEqual(items[0]['kind'],'competitor-research')
        self.assertLess(items[0]['priority'],95)
        self.assertIn('competitors:https://example.com/a',scopes)
        data['articles'][0]['status']='comparison_complete'
        self.assertEqual(findings('competitors',data)[0],[])

class LinkCoverageTests(unittest.TestCase):
    def test_successful_inventory_link_report_covers_each_published_url(self):
        data={"error_map":{},"input_sources":{"/snapshot/a.html":"https://example.com/a", "/snapshot/b.html":"https://example.com/b"},"timeouts":0}
        items,coverage=findings('links',data)
        self.assertEqual(items,[])
        self.assertEqual(coverage,{'lychee:https://example.com/a','lychee:https://example.com/b'})

    def test_link_errors_route_to_article_instead_of_snapshot_file(self):
        data={"error_map":{"/snapshot/a.html":[{"url":"https://other.example/gone","status":{"code":404,"text":"Not found"}}]},
              "input_sources":{"/snapshot/a.html":"https://example.com/a"}}
        items,coverage=findings('links',data)
        self.assertEqual(items[0]['url'],'https://example.com/a')
        self.assertEqual(items[0]['kind'],'broken-link')

    def test_manifest_measurement_keeps_blocked_target_but_observes_other_articles(self):
        data={"exit_code":2,"error_map":{"/snapshot/b.html":[{"url":"https://other.example/blocked","status":{"code":403,"text":"Forbidden"}}]},
            "input_sources":{"/snapshot/a.html":"https://example.com/a","/snapshot/b.html":"https://example.com/b"}}
        items,coverage=findings('links',data)
        self.assertIn('lychee:https://example.com/a',coverage)
        self.assertEqual(items[0]['kind'],'verify-response')
        self.assertIn('https://other.example/blocked',items[0]['detail'])

    def test_failed_link_execution_does_not_claim_manifest_coverage(self):
        data={"exit_code":1,"timeouts":1,"error_map":{},"input_sources":{"/snapshot/a.html":"https://example.com/a"}}
        self.assertNotIn('lychee:https://example.com/a',findings('links',data)[1])

    def test_pending_comparisons_keep_cached_job_partial(self):
        from argparse import Namespace
        from contextlib import redirect_stdout
        from io import StringIO
        import sqlite3
        import seo_workbench as runner
        with TemporaryDirectory() as temp:
            root=Path(temp); (root/'reports').mkdir()
            (root/'article_competitor_audit.py').write_text('')
            (root/'reports/article_competitor_latest.json').write_text(json.dumps({'articles':[{'url':'https://example.com/a','status':'pending_search_results'}]}))
            stages=[('competitors',['article_competitor_audit.py'],'article_competitor_latest.json',(0,),1)]
            with patch.object(runner,'BASE',root),patch.object(runner,'STAGES',stages),redirect_stdout(StringIO()):
                runner.run_job(Namespace(dry_run=False,refresh=False,database=root/'state.sqlite'))
            with sqlite3.connect(root/'state.sqlite') as db:
                self.assertEqual(db.execute('select status from runs').fetchone()[0],'partial')
                self.assertEqual(db.execute('select kind from issues').fetchone()[0],'competitor-research')

class IndexingTests(unittest.TestCase):
    def test_article_publishers_have_no_indexing_api_endpoint(self):
        root=Path(__file__).resolve().parent
        for name in ('index_flow.py','seo_optimize.py','st_optimize.py'):
            self.assertNotIn('indexing.googleapis.com', (root/name).read_text())

class DashboardTests(unittest.TestCase):
    def test_workbench_endpoint_exposes_coverage_and_goals_without_api_calls(self):
        path=Path(__file__).parent/'dashboard/app.py'
        spec=importlib.util.spec_from_file_location('audit_dashboard',path)
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with TemporaryDirectory() as temp:
            root=Path(temp); (root/'reports').mkdir(); (root/'research').mkdir()
            (root/'reports/article_competitor_latest.json').write_text(json.dumps({'articles':[{'url':'https://studenttimepk.blogspot.com/a','status':'pending_search_results'},{'url':'https://learners-link.blogspot.com/a','status':'comparison_complete'}]}))
            with patch.object(module,'BASE',temp):
                data=module.app.test_client().get('/api/workbench?site=studenttimepk').get_json()
            self.assertEqual(data['competitors']['published_articles'],1)
            self.assertEqual(data['competitors']['coverage'],{'pending_search_results':1})
            self.assertIsNotNone(data['queue']['error'])
            with patch.object(module,'BASE',temp):
                unavailable=module.app.test_client().get('/api/overview?site=studenttimepk').get_json()
            self.assertIsNone(unavailable['signal']['impressions'])
            self.assertIsNone(unavailable['signal']['stage'])
            self.assertIsNotNone(unavailable['error'])

if __name__=='__main__': unittest.main()
