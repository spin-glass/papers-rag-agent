import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch

from api.core.rag_index import (
    RagIndexHolder,
    load_or_build_index,
    a_load_or_build_index,
    _build_index_from_queries,
)
from retrieval.inmemory import InMemoryIndex


class TestRagIndexHolder:
    """RagIndexHolderの基本動作テスト"""

    def test_initial_state(self):
        """初期状態のテスト"""
        holder = RagIndexHolder()
        assert holder.get() is None
        assert not holder.is_ready()
        assert holder.size() == 0

    def test_set_and_get(self):
        """set/getの基本動作テスト"""
        holder = RagIndexHolder()
        mock_index = Mock(spec=InMemoryIndex)
        mock_index.papers_with_embeddings = [1, 2, 3]

        holder.set(mock_index)
        assert holder.get() is mock_index
        assert holder.is_ready()
        assert holder.size() == 3

    def test_set_none_raises_error(self):
        """Noneをsetしようとした場合のエラーテスト"""
        holder = RagIndexHolder()
        with pytest.raises(ValueError, match="idx must not be None"):
            holder.set(None)

    def test_concurrent_access(self):
        """並列アクセステスト"""
        holder = RagIndexHolder()
        mock_index = Mock(spec=InMemoryIndex)
        mock_index.papers_with_embeddings = [1, 2, 3, 4, 5]

        def set_index():
            holder.set(mock_index)
            return holder.get()

        def get_index():
            return holder.get()

        # 並列でset/getを実行
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            # 5回set
            for _ in range(5):
                futures.append(executor.submit(set_index))
            # 5回get
            for _ in range(5):
                futures.append(executor.submit(get_index))

            results = []
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    results.append(result)

        # すべての結果が同じmock_indexであることを確認
        assert all(result is mock_index for result in results)
        assert holder.is_ready()
        assert holder.size() == 5


class TestLoadOrBuildIndex:
    """load_or_build_indexのテスト"""

    @patch("api.core.rag_index.load_precomputed_cache")
    @patch("api.core.rag_index.cache_exists")
    def test_cache_hit(self, mock_cache_exists, mock_load_cache):
        """キャッシュヒットのテスト"""
        # キャッシュが存在し、ロードが成功する場合
        mock_cache_exists.return_value = True
        mock_index = Mock(spec=InMemoryIndex)
        mock_index.papers_with_embeddings = [1, 2, 3]
        mock_load_cache.return_value = mock_index

        result = load_or_build_index()

        assert result is mock_index
        mock_cache_exists.assert_called_once()
        mock_load_cache.assert_called_once()

    @patch("api.core.rag_index.load_precomputed_cache")
    @patch("api.core.rag_index.cache_exists")
    def test_cache_miss_success(self, mock_cache_exists, mock_load_cache):
        """キャッシュミス→検索成功のテスト"""
        # キャッシュが存在しない場合
        mock_cache_exists.return_value = False
        mock_load_cache.return_value = None

        # モックPaperオブジェクトを作成
        mock_paper1 = Mock()
        mock_paper1.id = "paper1"
        mock_paper2 = Mock()
        mock_paper2.id = "paper2"
        mock_paper3 = Mock()
        mock_paper3.id = "paper1"  # 重複ID

        with patch("api.core.rag_index.search_arxiv_papers") as mock_search:
            mock_search.return_value = [mock_paper1, mock_paper2, mock_paper3]

            with patch("api.core.rag_index.InMemoryIndex") as mock_index_class:
                mock_index = Mock(spec=InMemoryIndex)
                mock_index.papers_with_embeddings = [1, 2]  # 重複排除後
                mock_index_class.return_value = mock_index

                result = load_or_build_index()

                assert result is mock_index
                mock_index.build.assert_called_once()
                # 重複排除が正しく動作することを確認
                called_papers = mock_index.build.call_args[0][0]
                assert len(called_papers) == 2  # 重複が排除されている

    @patch("api.core.rag_index.load_precomputed_cache")
    @patch("api.core.rag_index.cache_exists")
    def test_all_failure(self, mock_cache_exists, mock_load_cache):
        """全失敗のテスト"""
        # キャッシュが存在しない
        mock_cache_exists.return_value = False
        mock_load_cache.return_value = None

        # 検索も失敗
        with patch("api.core.rag_index.search_arxiv_papers") as mock_search:
            mock_search.side_effect = Exception("Search failed")

            with patch("api.core.rag_index.InMemoryIndex") as mock_index_class:
                mock_empty_index = Mock(spec=InMemoryIndex)
                mock_empty_index.papers_with_embeddings = []
                mock_index_class.return_value = mock_empty_index

                result = load_or_build_index()

                assert result is mock_empty_index
                mock_empty_index.build.assert_called_once_with([])

    @patch("api.core.rag_index.load_precomputed_cache")
    @patch("api.core.rag_index.cache_exists")
    def test_cache_load_failure(self, mock_cache_exists, mock_load_cache):
        """キャッシュロード失敗のテスト"""
        # キャッシュは存在するが、ロードに失敗
        mock_cache_exists.return_value = True
        mock_load_cache.side_effect = Exception("Cache load failed")

        # モックPaperオブジェクトを作成
        mock_paper = Mock()
        mock_paper.id = "paper1"

        with patch("api.core.rag_index.search_arxiv_papers") as mock_search:
            mock_search.return_value = [mock_paper]

            with patch("api.core.rag_index.InMemoryIndex") as mock_index_class:
                mock_index = Mock(spec=InMemoryIndex)
                mock_index.papers_with_embeddings = [1]
                mock_index_class.return_value = mock_index

                result = load_or_build_index()

                assert result is mock_index
                mock_index.build.assert_called_once()


class TestAsyncLoadOrBuildIndex:
    """a_load_or_build_indexのテスト"""

    @patch("api.core.rag_index.load_precomputed_cache")
    @patch("api.core.rag_index.cache_exists")
    @pytest.mark.asyncio
    async def test_async_cache_hit(self, mock_cache_exists, mock_load_cache):
        """非同期キャッシュヒットのテスト"""
        mock_cache_exists.return_value = True
        mock_index = Mock(spec=InMemoryIndex)
        mock_index.papers_with_embeddings = [1, 2, 3]
        mock_load_cache.return_value = mock_index

        result = await a_load_or_build_index()

        assert result is mock_index

    @patch("api.core.rag_index.load_precomputed_cache")
    @patch("api.core.rag_index.cache_exists")
    @pytest.mark.asyncio
    async def test_async_cache_miss(self, mock_cache_exists, mock_load_cache):
        """非同期キャッシュミスのテスト"""
        mock_cache_exists.return_value = False
        mock_load_cache.return_value = None

        mock_paper = Mock()
        mock_paper.id = "paper1"

        with patch("api.core.rag_index.search_arxiv_papers") as mock_search:
            mock_search.return_value = [mock_paper]

            with patch("api.core.rag_index.InMemoryIndex") as mock_index_class:
                mock_index = Mock(spec=InMemoryIndex)
                mock_index.papers_with_embeddings = [1]
                mock_index_class.return_value = mock_index

                result = await a_load_or_build_index()

                assert result is mock_index


class TestBuildIndexFromQueries:
    """_build_index_from_queriesのテスト"""

    def test_build_with_unique_papers(self):
        """ユニークなペーパーでのビルドテスト"""
        mock_paper1 = Mock()
        mock_paper1.id = "paper1"
        mock_paper2 = Mock()
        mock_paper2.id = "paper2"

        with patch("api.core.rag_index.search_arxiv_papers") as mock_search:
            mock_search.return_value = [mock_paper1, mock_paper2]

            with patch("api.core.rag_index.InMemoryIndex") as mock_index_class:
                mock_index = Mock(spec=InMemoryIndex)
                mock_index.papers_with_embeddings = [1, 2]
                mock_index_class.return_value = mock_index

                result = _build_index_from_queries(["query1", "query2"], 5)

                assert result is mock_index
                mock_index.build.assert_called_once()
                called_papers = mock_index.build.call_args[0][0]
                assert len(called_papers) == 2

    def test_build_with_duplicate_papers(self):
        """重複ペーパーでのビルドテスト"""
        mock_paper1 = Mock()
        mock_paper1.id = "paper1"
        mock_paper2 = Mock()
        mock_paper2.id = "paper2"
        mock_paper3 = Mock()
        mock_paper3.id = "paper1"  # 重複

        with patch("api.core.rag_index.search_arxiv_papers") as mock_search:
            mock_search.return_value = [mock_paper1, mock_paper2, mock_paper3]

            with patch("api.core.rag_index.InMemoryIndex") as mock_index_class:
                mock_index = Mock(spec=InMemoryIndex)
                mock_index.papers_with_embeddings = [1, 2]
                mock_index_class.return_value = mock_index

                result = _build_index_from_queries(["query1"], 5)

                assert result is mock_index
                called_papers = mock_index.build.call_args[0][0]
                assert len(called_papers) == 2  # 重複が排除されている

    def test_build_with_no_papers(self):
        """ペーパーが取得できない場合のテスト"""
        with patch("api.core.rag_index.search_arxiv_papers") as mock_search:
            mock_search.return_value = []

            result = _build_index_from_queries(["query1"], 5)

            assert result is None

    def test_build_with_search_failure(self):
        """検索が失敗する場合のテスト"""
        with patch("api.core.rag_index.search_arxiv_papers") as mock_search:
            mock_search.side_effect = Exception("Search failed")

            result = _build_index_from_queries(["query1"], 5)

            assert result is None

    def test_build_with_mixed_results(self):
        """一部のクエリが成功、一部が失敗する場合のテスト"""
        mock_paper1 = Mock()
        mock_paper1.id = "paper1"

        def mock_search_side_effect(query, max_results):
            if query == "success_query":
                return [mock_paper1]
            else:
                raise Exception("Search failed")

        with patch("api.core.rag_index.search_arxiv_papers") as mock_search:
            mock_search.side_effect = mock_search_side_effect

            with patch("api.core.rag_index.InMemoryIndex") as mock_index_class:
                mock_index = Mock(spec=InMemoryIndex)
                mock_index.papers_with_embeddings = [1]
                mock_index_class.return_value = mock_index

                result = _build_index_from_queries(["success_query", "fail_query"], 5)

                assert result is mock_index
                called_papers = mock_index.build.call_args[0][0]
                assert len(called_papers) == 1
