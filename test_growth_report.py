import unittest
from unittest.mock import patch, MagicMock
import io
import json
from growth_report import prioritize, md, public_inventory, inspect_sample


class GrowthReportTests(unittest.TestCase):
    def test_indexing_sample_preserves_google_exclusion_and_bounds_requests(self):
        api=MagicMock()
        api.urlInspection.return_value.index.return_value.inspect.return_value.execute.return_value={
            'inspectionResult':{'indexStatusResult':{'verdict':'NEUTRAL','coverageState':'Crawled - currently not indexed','lastCrawlTime':'2026-11-01T00:00:00Z'}}}
        rows=inspect_sample(api,'https://example.com/',['https://example.com/','https://example.com/','https://example.com/a','https://example.com/b','https://example.com/c'])
        self.assertEqual(len(rows),3)
        self.assertEqual(api.urlInspection.return_value.index.return_value.inspect.call_count,3)
        self.assertEqual(rows[0]['coverageState'],'Crawled - currently not indexed')

    def test_indexing_api_failure_is_not_reported_as_indexed_or_zero(self):
        api=MagicMock()
        api.urlInspection.return_value.index.return_value.inspect.return_value.execute.side_effect=RuntimeError('quota')
        row=inspect_sample(api,'https://example.com/',['https://example.com/'])[0]
        self.assertEqual(row['error'],'RuntimeError')
        self.assertNotIn('verdict',row)

    def test_public_inventory_paginates_without_credentials(self):
        first={'feed':{'openSearch$totalResults':{'$t':'2'},'entry':[{'title':{'$t':'First'},'content':{'$t':'<p>A</p>'},'link':[{'rel':'alternate','href':'https://example.com/a'}]}]}}
        second={'feed':{'openSearch$totalResults':{'$t':'2'},'entry':[{'title':{'$t':'Second'},'link':[{'rel':'alternate','href':'https://example.com/b'}]}]}}
        responses=[]
        for data in (first,second):
            response=MagicMock(); response.__enter__.return_value=io.StringIO(json.dumps(data)); responses.append(response)
        with patch('growth_report.urllib.request.urlopen',side_effect=responses) as fetch:
            posts=public_inventory('https://example.com/')
        self.assertEqual([p['url'] for p in posts],['https://example.com/a','https://example.com/b'])
        self.assertIn('start-index=2',fetch.call_args_list[1].args[0].full_url)

    def test_incomplete_public_inventory_is_rejected(self):
        response=MagicMock(); response.__enter__.return_value=io.StringIO(json.dumps({'feed':{'openSearch$totalResults':{'$t':'1'}}}))
        with patch('growth_report.urllib.request.urlopen',return_value=response),self.assertRaises(ValueError):
            public_inventory('https://example.com/')

    def test_priorities_keep_page_identity(self):
        rows = [{"keys": ["https://example.com/a"], "impressions": 10, "clicks": 0, "position": 12},
                {"keys": ["https://example.com/b"], "impressions": 10, "clicks": 1, "position": 65}]
        result = prioritize(rows, [])
        self.assertEqual(result[0]["url"], "https://example.com/a")
        self.assertIn("Near page one", result[0]["action"])

    def test_decline_is_a_priority_signal(self):
        rows = [{"keys": ["a"], "impressions": 1, "clicks": 0, "position": 60}]
        previous = [{"keys": ["a"], "impressions": 100}]
        self.assertEqual(prioritize(rows, previous)[0]["score"], 100)

    def test_markdown_table_escape(self):
        self.assertEqual(md("a|b\nc"), "a/b c")

    def test_mobile_pages_combine_with_weighted_position(self):
        rows = [{"keys":["https://example.com/a"],"impressions":10,"clicks":0,"position":10},
                {"keys":["https://example.com/a?m=1"],"impressions":30,"clicks":2,"position":30}]
        result=prioritize(rows,[])
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["impressions"],40)
        self.assertEqual(result[0]["position"],25)


if __name__ == "__main__": unittest.main()
