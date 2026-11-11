import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from tempfile import TemporaryDirectory
from argparse import Namespace
from contextlib import redirect_stdout
import io
import json
from article_improver import repair_links, canonical, related_posts, validate_candidate, fingerprint, apply_plan


class ArticleRepairTests(unittest.TestCase):
    def test_replacement_only_changes_the_matched_href(self):
        raw='<p>Read <a class="x" href="https://example.com/dead?a=1&amp;b=2">this guide</a>.</p>'
        result,changes=repair_links(raw,'https://example.com/post',{'https://example.com/dead?a=1&b=2':{'action':'replace','to':'https://example.com/live'}})
        self.assertIn('class="x" href="https://example.com/live">this guide</a>',result)
        self.assertEqual(len(changes),1)

    def test_unlink_retains_reader_text_and_formatting(self):
        result,_=repair_links('<a href="https://example.com/dead"><strong>Scholarship</strong></a>','',{'https://example.com/dead':{'action':'unlink'}})
        self.assertEqual(result,'<strong>Scholarship</strong>')

    def test_unreviewed_links_are_unchanged(self):
        raw='<a href="https://example.com">A</a>'
        self.assertEqual(repair_links(raw,'',{})[0],raw)

    def test_mobile_variant_normalization_preserves_other_parameters(self):
        self.assertEqual(canonical('https://example.com/a?m=1&x=2'),'https://example.com/a?x=2')

    def test_related_posts_do_not_cross_blogs(self):
        p={'id':'1','title':'AI prompting course','blog':{'id':'a'}}
        options=[{'id':'2','title':'AI prompting basics','blog':{'id':'b'}}]
        self.assertEqual(related_posts(p,options),[])

    def test_invalid_schema_is_blocked(self):
        with self.assertRaises(ValueError): validate_candidate('<p>Text</p><script type="application/ld+json">{bad}</script>')

    def exercise_apply(self,status='LIVE',conflict=False):
        with TemporaryDirectory() as folder:
            root=Path(folder); (root/'reports').mkdir()
            before='<p>Original article.</p>'; after='<p>Reviewed article.</p>'
            candidate=root/'candidate.html'; candidate.write_text(after)
            post={'id':'1','blog':{'id':'blog'},'title':'Existing title','url':'https://example.com/a',
                  'content':'<p>Other editor changed it</p>' if conflict else before,'status':status,'published':'2026-01-01'}
            record={'id':'1','blog_id':'blog','title':post['title'],'url':post['url'], 'before_sha256':fingerprint(before),
                    'after_sha256':fingerprint(after),'candidate':str(candidate),'changes':[{'kind':'test'}],'validation_errors':[]}
            packet=root/'plan.json'; packet.write_text(json.dumps({'folder':str(root),'posts':[record]}))
            api=MagicMock(); api.posts.return_value.get.return_value.execute.side_effect=[post,{**post,'content':after}]
            with patch('article_improver.BASE',root),patch('article_improver.service',return_value=api),redirect_stdout(io.StringIO()):
                blocked=apply_plan(Namespace(plan=packet,post=None))
            return blocked,api.posts.return_value.patch.call_args,api.posts.return_value.patch.call_count

    def test_apply_is_content_only_and_verified(self):
        blocked,call,count=self.exercise_apply()
        self.assertFalse(blocked)
        self.assertEqual(count,1)
        self.assertEqual(call.kwargs['body'],{'content':'<p>Reviewed article.</p>'})
        self.assertNotIn('publish',call.kwargs)

    def test_draft_is_not_automatically_published(self):
        blocked,_,count=self.exercise_apply(status='DRAFT')
        self.assertTrue(blocked); self.assertEqual(count,0)

    def test_concurrent_editor_changes_are_not_overwritten(self):
        blocked,_,count=self.exercise_apply(conflict=True)
        self.assertTrue(blocked); self.assertEqual(count,0)


if __name__=='__main__': unittest.main()
