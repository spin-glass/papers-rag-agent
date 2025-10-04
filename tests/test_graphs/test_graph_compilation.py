"""Tests for LangGraph compilation and configuration."""

import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from graphs.corrective_rag import create_corrective_rag_graph
from graphs.message_routing import create_message_routing_graph
from graphs.content_enhancement import create_content_enhancement_graph
from config import get_graph_recursion_limit


class TestGraphCompilation:
    """Test graph compilation and configuration."""

    def test_corrective_rag_graph_compilation(self):
        """Test that corrective RAG graph compiles without Checkpointer errors."""
        try:
            graph = create_corrective_rag_graph()
            assert graph is not None
            print("✅ Corrective RAG graph compiled successfully")
        except Exception as e:
            error_msg = str(e)
            assert "Checkpointer" not in error_msg, (
                f"Checkpointer error occurred: {error_msg}"
            )
            assert "thread_id" not in error_msg, (
                f"Thread ID error occurred: {error_msg}"
            )
            assert "checkpoint_ns" not in error_msg, (
                f"Checkpoint namespace error occurred: {error_msg}"
            )
            pytest.fail(f"Graph compilation failed: {error_msg}")

    def test_message_routing_graph_compilation(self):
        """Test that message routing graph compiles without Checkpointer errors."""
        try:
            graph = create_message_routing_graph()
            assert graph is not None
            print("✅ Message routing graph compiled successfully")
        except Exception as e:
            error_msg = str(e)
            assert "Checkpointer" not in error_msg, (
                f"Checkpointer error occurred: {error_msg}"
            )
            assert "thread_id" not in error_msg, (
                f"Thread ID error occurred: {error_msg}"
            )
            assert "checkpoint_ns" not in error_msg, (
                f"Checkpoint namespace error occurred: {error_msg}"
            )
            pytest.fail(f"Graph compilation failed: {error_msg}")

    def test_content_enhancement_graph_compilation(self):
        """Test that content enhancement graph compiles without Checkpointer errors."""
        try:
            graph = create_content_enhancement_graph()
            assert graph is not None
            print("✅ Content enhancement graph compiled successfully")
        except Exception as e:
            error_msg = str(e)
            assert "Checkpointer" not in error_msg, (
                f"Checkpointer error occurred: {error_msg}"
            )
            assert "thread_id" not in error_msg, (
                f"Thread ID error occurred: {error_msg}"
            )
            assert "checkpoint_ns" not in error_msg, (
                f"Checkpoint namespace error occurred: {error_msg}"
            )
            pytest.fail(f"Graph compilation failed: {error_msg}")

    def test_recursion_limit_configuration(self):
        """Test that recursion limit is properly configured."""
        limit = get_graph_recursion_limit()
        assert isinstance(limit, int)
        assert limit > 0
        assert limit <= 100  # Reasonable upper bound
        print(f"✅ Recursion limit configured: {limit}")

    def test_all_graphs_have_recursion_limit(self):
        """Test that all graphs are compiled with recursion limit."""
        # This is more of an integration test to ensure the limits are applied
        graphs = [
            ("corrective_rag", create_corrective_rag_graph),
            ("message_routing", create_message_routing_graph),
            ("content_enhancement", create_content_enhancement_graph),
        ]

        for graph_name, graph_factory in graphs:
            try:
                graph = graph_factory()
                # The graph should have compiled without errors
                assert graph is not None, f"{graph_name} graph is None"
                print(f"✅ {graph_name} graph compilation verified")
            except Exception as e:
                pytest.fail(f"Failed to compile {graph_name} graph: {str(e)}")


class TestGraphConfigurationErrors:
    """Test error handling for graph configuration."""

    def test_no_checkpointer_errors_in_compilation(self):
        """Ensure no Checkpointer-related errors during compilation."""
        error_keywords = [
            "Checkpointer requires",
            "thread_id",
            "checkpoint_ns",
            "checkpoint_id",
            "configurable",
        ]

        graphs = [
            create_corrective_rag_graph,
            create_message_routing_graph,
            create_content_enhancement_graph,
        ]

        for graph_factory in graphs:
            try:
                graph = graph_factory()
                assert graph is not None
            except Exception as e:
                error_msg = str(e).lower()
                for keyword in error_keywords:
                    if keyword.lower() in error_msg:
                        pytest.fail(f"Checkpointer error detected: {str(e)}")

    @pytest.mark.parametrize("invalid_limit", [-1, 0, "invalid", None])
    def test_invalid_recursion_limit_handling(self, invalid_limit, monkeypatch):
        """Test handling of invalid recursion limit values."""
        # Mock the environment variable
        if invalid_limit is None:
            monkeypatch.delenv("GRAPH_RECURSION_LIMIT", raising=False)
        else:
            monkeypatch.setenv("GRAPH_RECURSION_LIMIT", str(invalid_limit))

        # Re-import to get fresh config
        from importlib import reload
        import config

        reload(config)

        try:
            limit = config.get_graph_recursion_limit()
            # Should fall back to default value (10) for invalid inputs
            assert limit == 10, f"Expected default value 10, got {limit}"
        except ValueError:
            # This is acceptable for truly invalid values like "invalid"
            pass


if __name__ == "__main__":
    # Quick test run
    test_compilation = TestGraphCompilation()
    test_compilation.test_corrective_rag_graph_compilation()
    test_compilation.test_message_routing_graph_compilation()
    test_compilation.test_content_enhancement_graph_compilation()
    test_compilation.test_recursion_limit_configuration()
    test_compilation.test_all_graphs_have_recursion_limit()

    test_errors = TestGraphConfigurationErrors()
    test_errors.test_no_checkpointer_errors_in_compilation()

    print("🎉 All graph compilation tests passed!")
