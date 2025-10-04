"""ArXiv検索機能のテスト"""

import unittest
from unittest.mock import Mock, patch

from retrieval.arxiv_searcher import run_arxiv_search  # noqa: E402


class TestArxivSearcher(unittest.TestCase):
    """ArXiv検索機能のテストクラス"""

    @patch("retrieval.arxiv_searcher.feedparser.parse")
    def test_run_arxiv_search_successful(self, mock_parse):
        """正常な検索結果のテスト"""
        # モックレスポンスの作成
        mock_entry1 = Mock()
        mock_entry1.id = "http://arxiv.org/abs/2301.00001v1"
        mock_entry1.title = "Test Paper 1"
        mock_entry1.link = "http://arxiv.org/abs/2301.00001"
        mock_entry1.links = [
            Mock(type="text/html", href="http://arxiv.org/abs/2301.00001"),
            Mock(type="application/pdf", href="http://arxiv.org/pdf/2301.00001.pdf"),
        ]

        mock_entry2 = Mock()
        mock_entry2.id = "http://arxiv.org/abs/2301.00002v2"
        mock_entry2.title = "Test Paper 2"
        mock_entry2.link = "http://arxiv.org/abs/2301.00002"
        mock_entry2.links = [
            Mock(type="text/html", href="http://arxiv.org/abs/2301.00002")
        ]

        mock_feed = Mock()
        mock_feed.entries = [mock_entry1, mock_entry2]
        mock_parse.return_value = mock_feed

        # テスト実行
        result = run_arxiv_search("machine learning", max_results=2)

        # 結果の検証
        self.assertEqual(len(result), 2)

        # 1番目の論文
        self.assertEqual(result[0]["id"], "2301.00001")
        self.assertEqual(result[0]["title"], "Test Paper 1")
        self.assertEqual(result[0]["link"], "http://arxiv.org/abs/2301.00001")
        self.assertEqual(result[0]["pdf"], "http://arxiv.org/pdf/2301.00001.pdf")

        # 2番目の論文（PDFなし）
        self.assertEqual(result[1]["id"], "2301.00002")
        self.assertEqual(result[1]["title"], "Test Paper 2")
        self.assertEqual(result[1]["link"], "http://arxiv.org/abs/2301.00002")
        self.assertEqual(result[1]["pdf"], "")

    @patch("retrieval.arxiv_searcher.feedparser.parse")
    def test_run_arxiv_search_empty_results(self, mock_parse):
        """空の検索結果のテスト"""
        mock_feed = Mock()
        mock_feed.entries = []
        mock_parse.return_value = mock_feed

        result = run_arxiv_search("nonexistent query")

        self.assertEqual(len(result), 0)
        self.assertEqual(result, [])

    @patch("retrieval.arxiv_searcher.feedparser.parse")
    def test_run_arxiv_search_missing_attributes(self, mock_parse):
        """属性が欠落している場合のテスト"""
        mock_entry = Mock()
        # 一部の属性が存在しない場合をシミュレート
        mock_entry.id = ""
        mock_entry.title = ""
        mock_entry.link = ""
        mock_entry.links = []

        mock_feed = Mock()
        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed

        result = run_arxiv_search("test query")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "")
        self.assertEqual(result[0]["title"], "")
        self.assertEqual(result[0]["link"], "")
        self.assertEqual(result[0]["pdf"], "")

    @patch("retrieval.arxiv_searcher.feedparser.parse")
    def test_run_arxiv_search_no_entries_attribute(self, mock_parse):
        """feedに entries 属性がない場合のテスト"""
        mock_feed = Mock()
        # entries 属性を削除
        del mock_feed.entries
        mock_parse.return_value = mock_feed

        result = run_arxiv_search("test query")

        self.assertEqual(len(result), 0)
        self.assertEqual(result, [])

    @patch("retrieval.arxiv_searcher.feedparser.parse")
    def test_run_arxiv_search_url_construction(self, mock_parse):
        """URL構築の確認"""
        mock_feed = Mock()
        mock_feed.entries = []
        mock_parse.return_value = mock_feed

        run_arxiv_search("machine learning", max_results=10)

        # URLが正しく構築されたかを確認（新しいクエリ形式）
        # "machine learning" は特別な処理を受ける
        expected_url_pattern = (
            "https://export.arxiv.org/api/query?"
            "search_query=cat%3Acs.LG%20OR%20cat%3Astat.ML"
            "&sortBy=relevance&sortOrder=descending&max_results=10"
        )
        mock_parse.assert_called_once_with(expected_url_pattern)

    @patch("retrieval.arxiv_searcher.feedparser.parse")
    def test_run_arxiv_search_id_extraction(self, mock_parse):
        """ArXiv ID抽出の詳細テスト"""
        test_cases = [
            ("http://arxiv.org/abs/2301.00001v1", "2301.00001"),
            ("http://arxiv.org/abs/2301.00001v2", "2301.00001"),
            ("http://arxiv.org/abs/2301.00001", "2301.00001"),
            (
                "http://arxiv.org/abs/cs.AI/0601001v1",
                "0601001",
            ),  # 実装では最後の部分のみ抽出
            ("", ""),
        ]

        for i, (arxiv_id, expected_core_id) in enumerate(test_cases):
            with self.subTest(i=i):
                mock_entry = Mock()
                mock_entry.id = arxiv_id
                mock_entry.title = f"Test Paper {i}"
                mock_entry.link = (
                    f"http://arxiv.org/abs/{expected_core_id}"
                    if expected_core_id
                    else ""
                )
                mock_entry.links = []

                mock_feed = Mock()
                mock_feed.entries = [mock_entry]
                mock_parse.return_value = mock_feed

                result = run_arxiv_search("test")
                self.assertEqual(result[0]["id"], expected_core_id)

    @patch("retrieval.arxiv_searcher.feedparser.parse")
    def test_run_arxiv_search_pdf_link_extraction(self, mock_parse):
        """PDF リンク抽出のテスト"""
        # PDFリンクが複数ある場合、最初のものを使用することを確認
        mock_entry = Mock()
        mock_entry.id = "http://arxiv.org/abs/2301.00001v1"
        mock_entry.title = "Test Paper"
        mock_entry.link = "http://arxiv.org/abs/2301.00001"
        mock_entry.links = [
            Mock(type="text/html", href="http://arxiv.org/abs/2301.00001"),
            Mock(type="application/pdf", href="http://arxiv.org/pdf/2301.00001.pdf"),
            Mock(type="application/pdf", href="http://example.com/duplicate.pdf"),
        ]

        mock_feed = Mock()
        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed

        result = run_arxiv_search("test")

        # 最初のPDFリンクが使用されることを確認
        self.assertEqual(result[0]["pdf"], "http://arxiv.org/pdf/2301.00001.pdf")

    def test_run_arxiv_search_default_parameters(self):
        """デフォルトパラメータのテスト"""
        with patch("retrieval.arxiv_searcher.feedparser.parse") as mock_parse:
            mock_feed = Mock()
            mock_feed.entries = []
            mock_parse.return_value = mock_feed

            run_arxiv_search("test")

            # デフォルトのmax_results=5が使用されることを確認
            args, kwargs = mock_parse.call_args
            self.assertIn("max_results=5", args[0])


if __name__ == "__main__":
    unittest.main()
