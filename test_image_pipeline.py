import unittest
from unittest.mock import patch
import pexels_helper
from upload_drafts import markdown_to_html, build_content
from seo_pipeline_check import ArticleExtractor


class PipelineTests(unittest.TestCase):
    def test_table_and_metadata(self):
        raw = '# Title\n\n**Secondary keywords:** private metadata\n\n| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n| 5 | 6 |\n| 7 | 8 |\n\nAfter table'
        content = markdown_to_html(raw)
        self.assertNotIn('private metadata', content)
        self.assertNotIn('<h1>', content)
        self.assertEqual(content.count('<table>'), 1)
        self.assertLess(content.index('</table>'), content.index('After table'))

    def test_image_required(self):
        with self.assertRaises(ValueError):
            build_content('# Article')

    def test_hero_escaping_and_attribution(self):
        photo = dict(src={'large':'https://images.pexels.com/x.jpg'}, width=600, height=400,
                     alt='A "desk"', photographer='A & B', photographer_url='https://www.pexels.com/@a',
                     url='https://www.pexels.com/photo/1')
        with patch.object(pexels_helper, 'search', return_value=[photo]):
            content, _ = pexels_helper.img_block('desk', hero=True)
        self.assertIn('fetchpriority="high"', content)
        self.assertIn('&quot;desk&quot;', content)
        self.assertIn('width="1200" height="800"', content)
        self.assertIn('href="https://www.pexels.com/photo/1"', content)

    def test_article_excludes_chrome(self):
        extractor = ArticleExtractor()
        extractor.feed('<nav>Sidebar</nav><div class="post-body"><p>Article<img src="x" /></p></div><footer>Footer</footer>')
        result = ''.join(extractor.parts)
        self.assertIn('Article', result)
        self.assertNotIn('Sidebar', result)
        self.assertNotIn('Footer', result)


if __name__ == '__main__':
    unittest.main()
