from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from research_library import database, save_source, search


class SourceLibraryTests(unittest.TestCase):
    def test_refresh_preserves_one_searchable_source(self):
        with TemporaryDirectory() as directory:
            db = database(Path(directory) / 'sources.sqlite')
            save_source(db, 'https://example.com/', 'https://example.com/', 'AI course', 'A free badge course', {})
            result = save_source(db, 'https://example.com/', 'https://example.com/', 'AI course', 'A paid certificate course', {})
            self.assertTrue(result['changed'])
            self.assertEqual(len(search(db, 'certificate')), 1)
            self.assertEqual(search(db, 'badge'), [])
            self.assertEqual(db.execute('SELECT count(*) FROM sources').fetchone()[0], 1)
            db.close()

    def test_search_handles_fts_syntax_as_text(self):
        with TemporaryDirectory() as directory:
            db = database(Path(directory) / 'sources.sqlite')
            self.assertEqual(search(db, '" OR *'), [])
            db.close()


if __name__ == '__main__': unittest.main()
