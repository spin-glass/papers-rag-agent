"""ArXiv検索機能のPyTestテスト"""

import pytest
from unittest.mock import patch, Mock
from src.retrieval.arxiv_searcher import run_arxiv_search


class TestArxivSearcherPytest:
    """PyTestを使用したArXiv検索機能のテストクラス"""

    @patch("src.retrieval.arxiv_searcher.feedparser.parse")
    def test_successful_search(self, mock_parse, mock_arxiv_response):
        """正常な検索結果のテスト"""
        # モックレスポンスの作成
        mock_entries = []
        for paper in mock_arxiv_response:
            mock_entry = Mock()
            mock_entry.id = f"http://arxiv.org/abs/{paper['id']}v1"
            mock_entry.title = paper["title"]
            mock_entry.link = paper["link"]
            mock_entry.links = [
                Mock(type="text/html", href=paper["link"]),
                Mock(type="application/pdf", href=paper["pdf"]),
            ]
            mock_entries.append(mock_entry)

        mock_feed = Mock()
        mock_feed.entries = mock_entries
        mock_parse.return_value = mock_feed

        # テスト実行
        result = run_arxiv_search("transformer", max_results=2)

        # 結果の検証
        assert len(result) == 2
        assert result[0]["title"] == "Attention Is All You Need"
        assert (
            result[1]["title"]
            == "BERT: Pre-training of Deep Bidirectional Transformers"
        )

    @patch("src.retrieval.arxiv_searcher.feedparser.parse")
    def test_empty_search_results(self, mock_parse, empty_arxiv_response):
        """空の検索結果のテスト"""
        mock_feed = Mock()
        mock_feed.entries = []
        mock_parse.return_value = mock_feed

        result = run_arxiv_search("nonexistent query")

        assert len(result) == 0
        assert result == []

    @pytest.mark.parametrize(
        "arxiv_id,expected_core_id",
        [
            ("http://arxiv.org/abs/2301.00001v1", "2301.00001"),
            ("http://arxiv.org/abs/2301.00001v2", "2301.00001"),
            ("http://arxiv.org/abs/2301.00001", "2301.00001"),
            (
                "http://arxiv.org/abs/cs.AI/0601001v1",
                "0601001",
            ),  # 実装では最後の部分のみ抽出
            ("", ""),
        ],
    )
    @patch("src.retrieval.arxiv_searcher.feedparser.parse")
    def test_id_extraction(self, mock_parse, arxiv_id, expected_core_id):
        """ArXiv ID抽出のパラメータ化テスト"""
        mock_entry = Mock()
        mock_entry.id = arxiv_id
        mock_entry.title = "Test Paper"
        mock_entry.link = (
            f"http://arxiv.org/abs/{expected_core_id}" if expected_core_id else ""
        )
        mock_entry.links = []

        mock_feed = Mock()
        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed

        result = run_arxiv_search("test")
        assert result[0]["id"] == expected_core_id

    @pytest.mark.parametrize("max_results", [1, 5, 10, 20])
    @patch("src.retrieval.arxiv_searcher.feedparser.parse")
    def test_max_results_parameter(self, mock_parse, max_results):
        """max_resultsパラメータのテスト"""
        mock_feed = Mock()
        mock_feed.entries = []
        mock_parse.return_value = mock_feed

        run_arxiv_search("test", max_results=max_results)

        # URLに正しいmax_resultsが含まれているかを確認
        args, kwargs = mock_parse.call_args
        assert f"max_results={max_results}" in args[0]

    @patch("src.retrieval.arxiv_searcher.feedparser.parse")
    def test_pdf_link_priority(self, mock_parse):
        """複数のPDFリンクがある場合の優先順位テスト"""
        mock_entry = Mock()
        mock_entry.id = "http://arxiv.org/abs/2301.00001v1"
        mock_entry.title = "Test Paper"
        mock_entry.link = "http://arxiv.org/abs/2301.00001"
        mock_entry.links = [
            Mock(type="text/html", href="http://arxiv.org/abs/2301.00001"),
            Mock(type="application/pdf", href="http://arxiv.org/pdf/first.pdf"),
            Mock(type="application/pdf", href="http://arxiv.org/pdf/second.pdf"),
        ]

        mock_feed = Mock()
        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed

        result = run_arxiv_search("test")

        # 最初のPDFリンクが使用されることを確認
        assert result[0]["pdf"] == "http://arxiv.org/pdf/first.pdf"

    @patch("src.retrieval.arxiv_searcher.feedparser.parse")
    def test_missing_attributes_handling(self, mock_parse):
        """属性が欠落している場合の処理テスト"""
        # 一部の属性が存在しないentryをシミュレート
        mock_entry = Mock()
        # getattr のデフォルト値をテスト
        del mock_entry.id
        del mock_entry.title
        del mock_entry.link
        del mock_entry.links

        mock_feed = Mock()
        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed

        result = run_arxiv_search("test")

        assert len(result) == 1
        assert result[0]["id"] == ""
        assert result[0]["title"] == ""
        assert result[0]["link"] == ""
        assert result[0]["pdf"] == ""

    @patch("src.retrieval.arxiv_searcher.urllib.parse.quote")
    @patch("src.retrieval.arxiv_searcher.feedparser.parse")
    def test_query_encoding(self, mock_parse, mock_quote):
        """クエリのURL エンコーディングテスト"""
        mock_feed = Mock()
        mock_feed.entries = []
        mock_parse.return_value = mock_feed
        mock_quote.return_value = "encoded_query"

        run_arxiv_search("test query with spaces")

        # urllib.parse.quote が正しく呼ばれたことを確認（新しいクエリ形式）
        mock_quote.assert_called_once_with(
            "ti:test query with spaces OR abs:test query with spaces"
        )

    @patch("src.retrieval.arxiv_searcher.feedparser.parse")
    def test_url_construction_components(self, mock_parse):
        """URL構築の各コンポーネントテスト"""
        mock_feed = Mock()
        mock_feed.entries = []
        mock_parse.return_value = mock_feed

        run_arxiv_search("machine learning", max_results=10)

        args, kwargs = mock_parse.call_args
        url = args[0]

        # URL の各部分が含まれていることを確認（新しい実装）
        assert "https://export.arxiv.org/api/query" in url
        assert "search_query=" in url
        assert "sortBy=relevance" in url  # relevanceに変更
        assert "sortOrder=descending" in url
        assert "max_results=10" in url

    @pytest.mark.integration
    @patch("src.retrieval.arxiv_searcher.feedparser.parse")
    def test_end_to_end_workflow(self, mock_parse):
        """エンドツーエンドのワークフローテスト"""
        # 実際のAPIレスポンスに近いモックデータ
        mock_entry = Mock()
        mock_entry.id = "http://arxiv.org/abs/1706.03762v5"
        mock_entry.title = "Attention Is All You Need"
        mock_entry.link = "http://arxiv.org/abs/1706.03762"
        mock_entry.links = [
            Mock(type="text/html", href="http://arxiv.org/abs/1706.03762"),
            Mock(type="application/pdf", href="http://arxiv.org/pdf/1706.03762v5.pdf"),
        ]

        mock_feed = Mock()
        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed

        # 検索実行
        result = run_arxiv_search("attention mechanism transformer", max_results=1)

        # 結果の完全性を確認
        assert len(result) == 1
        paper = result[0]
        assert paper["id"] == "1706.03762"
        assert paper["title"] == "Attention Is All You Need"
        assert paper["link"] == "http://arxiv.org/abs/1706.03762"
        assert paper["pdf"] == "http://arxiv.org/pdf/1706.03762v5.pdf"

        # 全ての必要なキーが存在することを確認
        expected_keys = {"id", "title", "link", "pdf"}
        assert set(paper.keys()) == expected_keys
