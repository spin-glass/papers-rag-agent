"""共通テスト設定ファイル"""

import pytest

@pytest.fixture(scope="session")
def setup_test_environment():
    """テスト環境のセットアップ"""
    # テスト用の環境変数や設定を行う
    import os

    os.environ["TESTING"] = "1"
    yield
    # クリーンアップ処理
    os.environ.pop("TESTING", None)


@pytest.fixture
def mock_arxiv_response():
    """ArXiv APIレスポンスのモックデータ"""
    return [
        {
            "id": "2301.00001",
            "title": "Attention Is All You Need",
            "link": "http://arxiv.org/abs/2301.00001",
            "pdf": "http://arxiv.org/pdf/2301.00001.pdf",
        },
        {
            "id": "2301.00002",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "link": "http://arxiv.org/abs/2301.00002",
            "pdf": "http://arxiv.org/pdf/2301.00002.pdf",
        },
    ]


@pytest.fixture
def empty_arxiv_response():
    """空のArXiv APIレスポンス"""
    return []
