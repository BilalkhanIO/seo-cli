import unittest
from content_review import prose, VisibleText


class WritingExtractionTests(unittest.TestCase):
    def test_metadata_and_tables_do_not_pollute_prose(self):
        raw = '# Title\n\n**Image query:** private query\n\n| Fee | Amount |\n|---|---|\n| Cost | $10 |\n\nA useful paragraph.'
        text = prose(raw, '.md')
        self.assertNotIn('private query', text)
        self.assertNotIn('$10', text)
        self.assertIn('A useful paragraph.', text)

    def test_html_scripts_and_tables_are_excluded(self):
        p = VisibleText()
        p.feed('<p>Useful text.</p><table><tr><td>Table value</td></tr></table><script>secret()</script><p>More text.</p>')
        text = ''.join(p.parts)
        self.assertNotIn('Table value', text)
        self.assertNotIn('secret', text)
        self.assertIn('More text.', text)


if __name__ == '__main__': unittest.main()
