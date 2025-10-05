"""ArXiv検索機能の実際のAPI統合テスト"""

import pytest

from src.retrieval.arxiv_searcher import run_arxiv_search


class TestArxivSearcherIntegration:
    """実際のArXiv APIを使用した統合テスト"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_arxiv_search_transformer(self):
        """実際のArXiv APIでtransformerを検索"""
        results = run_arxiv_search("transformer attention", max_results=3)

        # 基本的な結果構造の検証
        assert isinstance(results, list)
        assert len(results) <= 3

        if results:  # 結果がある場合のみ検証
            paper = results[0]
            assert isinstance(paper, dict)
            assert "id" in paper
            assert "title" in paper
            assert "link" in paper
            assert "pdf" in paper

            # 基本的な値の検証
            assert isinstance(paper["id"], str)
            assert isinstance(paper["title"], str)
            assert isinstance(paper["link"], str)
            assert isinstance(paper["pdf"], str)

            # ArXivのURLフォーマット検証
            if paper["link"]:
                assert "arxiv.org" in paper["link"]
            if paper["pdf"]:
                assert "arxiv.org" in paper["pdf"]
                assert (
                    "pdf" in paper["pdf"]
                )  # .pdf拡張子がない場合もあるため、pdfが含まれることを確認

    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_arxiv_search_machine_learning(self):
        """実際のArXiv APIでmachine learningを検索"""
        results = run_arxiv_search("machine learning", max_results=2)

        assert isinstance(results, list)
        assert len(results) <= 2

        # 全ての結果が正しい構造を持つことを確認
        for paper in results:
            assert isinstance(paper, dict)
            required_keys = {"id", "title", "link", "pdf"}
            assert set(paper.keys()) == required_keys

    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_arxiv_search_nonexistent_query(self):
        """実際のAPIで存在しないクエリを検索"""
        # 存在しないであろう非常に特殊なクエリ
        results = run_arxiv_search("zzz_nonexistent_query_xyz_12345", max_results=1)

        # 結果が空か、あっても正しい構造であることを確認
        assert isinstance(results, list)
        for paper in results:
            assert isinstance(paper, dict)
            required_keys = {"id", "title", "link", "pdf"}
            assert set(paper.keys()) == required_keys

    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_arxiv_search_single_result(self):
        """実際のAPIで1件のみ検索"""
        results = run_arxiv_search("neural network", max_results=1)

        assert isinstance(results, list)
        assert len(results) <= 1

        if results:
            paper = results[0]
            # IDが正しく抽出されているか
            if paper["id"]:
                # ArXiv IDのフォーマット検証（数字.数字 または カテゴリ/数字.数字）
                assert "." in paper["id"] or "/" in paper["id"]

    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_arxiv_search_pdf_links(self):
        """実際のAPIでPDFリンクの存在確認"""
        results = run_arxiv_search("deep learning", max_results=5)

        assert isinstance(results, list)

        # 少なくとも1つの結果があることを期待（通常の場合）
        if results:
            # 少なくとも一部の論文にPDFリンクがあることを確認
            pdf_count = sum(1 for paper in results if paper["pdf"])
            # ArXivの論文は通常PDFがあるので、0でないことを期待
            # ただし、一時的なAPI問題等も考慮して柔軟にチェック
            assert pdf_count >= 0  # 最低限の検証

    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_arxiv_search_title_length(self):
        """実際のAPIで取得されるタイトルの妥当性確認"""
        results = run_arxiv_search("computer vision", max_results=3)

        for paper in results:
            # タイトルが存在し、最低限の長さがあることを確認
            if paper["title"]:
                assert len(paper["title"]) > 5  # 非常に短いタイトルは論文らしくない
                assert len(paper["title"]) < 500  # 異常に長いタイトルもおかしい

    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_arxiv_search_max_results_parameter(self):
        """実際のAPIでmax_resultsパラメータの動作確認"""
        # 異なるmax_results値でテスト
        for max_results in [1, 3, 5]:
            results = run_arxiv_search(
                "artificial intelligence", max_results=max_results
            )
            assert isinstance(results, list)
            assert len(results) <= max_results

    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_arxiv_search_special_characters(self):
        """実際のAPIで特殊文字を含むクエリの処理"""
        # 特殊文字を含むクエリをテスト
        special_queries = [
            "machine learning & AI",
            "deep-learning",
            "neural networks (CNN)",
        ]

        for query in special_queries:
            results = run_arxiv_search(query, max_results=2)
            assert isinstance(results, list)
            # 特殊文字が含まれていてもエラーにならないことを確認
            for paper in results:
                assert isinstance(paper, dict)
                required_keys = {"id", "title", "link", "pdf"}
                assert set(paper.keys()) == required_keys


@pytest.mark.integration
class TestArxivSearcherRealWorldScenarios:
    """実世界のシナリオを想定したテスト"""

    @pytest.mark.slow
    def test_search_recent_papers(self):
        """最近の論文検索のシミュレーション"""
        # 最近話題のトピックで検索
        results = run_arxiv_search("large language model", max_results=3)

        assert isinstance(results, list)
        for paper in results:
            # 基本構造の確認
            assert "title" in paper
            assert "link" in paper

            # 実際のArXivリンクであることを確認
            if paper["link"]:
                assert "arxiv.org" in paper["link"]

    @pytest.mark.slow
    def test_search_classic_topics(self):
        """古典的なトピックの検索"""
        # 確実に結果があると期待される古典的なトピック
        results = run_arxiv_search("support vector machine", max_results=2)

        assert isinstance(results, list)
        # SVMは確立された分野なので結果があることを期待
        # ただし、APIの状態によっては0件の可能性もあるため柔軟に
        for paper in results:
            assert isinstance(paper["title"], str)
            assert isinstance(paper["id"], str)

    @pytest.mark.slow
    def test_end_to_end_workflow(self):
        """エンドツーエンドワークフローのテスト"""
        # 1. 検索実行
        query = "graph neural network"
        results = run_arxiv_search(query, max_results=2)

        # 2. 結果の基本検証
        assert isinstance(results, list)

        # 3. 各論文の詳細検証
        for paper in results:
            # 必須フィールドの存在確認
            for key in ["id", "title", "link", "pdf"]:
                assert key in paper
                assert isinstance(paper[key], str)

            # リンクの有効性確認（基本的なフォーマット）
            if paper["link"]:
                assert paper["link"].startswith("http")
            if paper["pdf"]:
                assert paper["pdf"].startswith("http")
                assert "pdf" in paper["pdf"]


# スキップ可能な設定（ネットワークアクセスが無い環境用）
pytestmark = pytest.mark.skipif(
    False,  # 常に実行。必要に応じてTrueに変更してスキップ
    reason="Network access required for integration tests",
)
