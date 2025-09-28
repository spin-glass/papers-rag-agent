#!/usr/bin/env python3
"""Generate Mermaid diagrams for LangGraph workflows."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from graphs.message_routing import create_message_routing_graph
from graphs.corrective_rag import create_corrective_rag_graph
from graphs.content_enhancement import create_content_enhancement_graph


def generate_all_mermaid_graphs():
    """Generate Mermaid diagrams for all LangGraph workflows."""
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / "docs" / "graphs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    graphs = {
        "message_routing": {
            "graph": create_message_routing_graph(),
            "title": "Message Routing Workflow",
            "description": "Main workflow for routing user messages to appropriate processors"
        },
        "corrective_rag": {
            "graph": create_corrective_rag_graph(),
            "title": "Corrective RAG Workflow", 
            "description": "RAG workflow with HyDE-based query correction for improved retrieval"
        },
        "content_enhancement": {
            "graph": create_content_enhancement_graph(),
            "title": "Content Enhancement Workflow",
            "description": "Post-processing workflow to generate Cornell notes and quiz questions"
        }
    }
    
    print("🎨 Generating Mermaid diagrams for LangGraph workflows...")
    
    for name, config in graphs.items():
        try:
            print(f"  📊 Generating {config['title']}...")
            
            # Generate Mermaid diagram
            mermaid_code = config["graph"].get_graph().draw_mermaid()
            
            # Save to file
            mermaid_file = output_dir / f"{name}.mmd"
            with open(mermaid_file, "w", encoding="utf-8") as f:
                f.write(f"---\ntitle: {config['title']}\n---\n")
                f.write(mermaid_code)
            
            print(f"    ✅ Saved: {mermaid_file}")
            
            # Also create a markdown file with the diagram
            md_file = output_dir / f"{name}.md"
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(f"# {config['title']}\n\n")
                f.write(f"{config['description']}\n\n")
                f.write("```mermaid\n")
                f.write(mermaid_code)
                f.write("\n```\n")
            
            print(f"    ✅ Saved: {md_file}")
            
        except Exception as e:
            print(f"    ❌ Failed to generate {name}: {e}")
    
    # Create an index file
    index_file = output_dir / "README.md"
    with open(index_file, "w", encoding="utf-8") as f:
        f.write("# LangGraph Workflow Diagrams\n\n")
        f.write("This directory contains Mermaid diagrams for all LangGraph workflows in the Papers RAG Agent.\n\n")
        
        for name, config in graphs.items():
            f.write(f"## {config['title']}\n\n")
            f.write(f"{config['description']}\n\n")
            f.write(f"- [Mermaid file]({name}.mmd)\n")
            f.write(f"- [Markdown with diagram]({name}.md)\n\n")
    
    print(f"📚 Created index: {index_file}")
    print("✅ All Mermaid diagrams generated successfully!")
    
    return output_dir


if __name__ == "__main__":
    try:
        output_dir = generate_all_mermaid_graphs()
        print(f"\n🎯 Output directory: {output_dir}")
        print("💡 You can now use these Mermaid diagrams in your README or documentation.")
        
    except Exception as e:
        print(f"❌ Error generating Mermaid graphs: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
