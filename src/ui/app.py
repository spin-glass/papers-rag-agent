# src/ui/app.py
from __future__ import annotations
import os
import json
import asyncio
import httpx
import chainlit as cl

API_BASE = os.getenv("PAPERS_API_BASE", "http://localhost:9000")


# -------- helpers --------
async def get_health() -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{API_BASE}/health")
        r.raise_for_status()
        return r.json()


async def call_arxiv_search(query: str, max_results: int = 10) -> list[dict]:
    payload = {"query": query, "max_results": max_results}
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(f"{API_BASE}/arxiv/search", json=payload)
        r.raise_for_status()
        return r.json().get("items", [])


async def call_digest(cat: str = "cs.LG", days: int = 1, limit: int = 10) -> list[dict]:
    params = {"cat": cat, "days": days, "limit": limit}
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(f"{API_BASE}/digest", params=params)
        r.raise_for_status()
        return r.json()


async def call_digest_details(paper_id: str) -> dict:
    """論文の詳細情報を取得"""
    try:
        async with httpx.AsyncClient(timeout=360.0) as client:
            r = await client.get(f"{API_BASE}/digest/{paper_id}/details")
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        print(f"❌ API Error: {error_msg}")
        raise Exception(f"API Error: {error_msg}")
    except httpx.TimeoutException:
        error_msg = "Request timeout (360s)"
        print(f"❌ Timeout: {error_msg}")
        raise Exception(f"Timeout: {error_msg}")
    except Exception as e:
        error_msg = f"Request failed: {str(e)}"
        print(f"❌ Request failed: {error_msg}")
        raise Exception(error_msg)


async def call_fulltext(
    paper_id: str, fmt: str = "plain", max_bytes: int = 100000
) -> str:
    """論文の全文を取得"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(
            f"{API_BASE}/digest/{paper_id}/fulltext",
            params={"format": fmt, "max_bytes": max_bytes},
        )
        response.raise_for_status()
        return response.text


async def sse_rag_stream(query: str):
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST", f"{API_BASE}/rag/stream", json={"query": query}
            ) as resp:
                resp.raise_for_status()
                try:
                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            obj = json.loads(data)
                        except Exception:
                            obj = {}

                        # ステータスメッセージの処理
                        if obj.get("type") == "status":
                            yield {
                                "type": "status",
                                "text": obj.get("text", ""),
                                "done": False,
                            }
                        # コンテンツの処理
                        elif obj.get("type") == "content":
                            yield {
                                "type": "content",
                                "text": obj.get("text", ""),
                                "done": obj.get("done", False),
                            }
                        # エラーの処理
                        elif obj.get("type") == "error":
                            yield {
                                "type": "error",
                                "text": obj.get("text", ""),
                                "done": True,
                            }
                        # 従来のフォーマットとの互換性
                        else:
                            text = (
                                obj.get("delta")
                                or obj.get("text")
                                or obj.get("content")
                                or ""
                            )
                            if text:
                                yield {"type": "content", "text": text, "done": False}
                except asyncio.CancelledError:
                    # キャンセルされた場合は適切に処理
                    raise
                except Exception as e:
                    # ストリーミング中のエラーを適切に処理
                    yield {
                        "type": "error",
                        "text": f"ストリーミングエラー: {str(e)}",
                        "done": True,
                    }
    except asyncio.CancelledError:
        # キャンセルされた場合は再発生
        raise
    except Exception as e:
        # その他のエラーを適切に処理
        yield {"type": "error", "text": f"接続エラー: {str(e)}", "done": True}


# -------- chainlit hooks --------
@cl.on_chat_start
async def on_chat_start():
    try:
        h = await get_health()
        await cl.Message(
            content=(
                "## Papers RAG Agent (Baseline + Corrective RAG)\n\n"
                "こんにちは！論文に関する質問をしてください。\n"
                "Baseline RAGを実行し、Support値が閾値を超えない場合にHyDEを使った補正検索を実行します。\n\n"
                "**使い方:**\n"
                "- 通常の質問: RAGによる回答\n"
                "- `arxiv: <query>`: 論文検索\n\n"
                "**テスト用クエリ例:**\n"
                "- 「最近のTransformerに関する論文を探しています」\n"
                "- 「Attention機構について教えてください」\n"
                "- 「BERT と GPT の違いは何ですか？」\n\n"
                f"**システム状態:**\n"
                f"- RAG Ready: {h.get('rag_ready')}\n"
                f"- Index Size: {h.get('size', 0)}件の論文\n\n"
                "何について知りたいですか？"
            )
        ).send()
        await cl.Message(
            content="ワンクリックで日次ダイジェストを取得できます。",
            actions=[
                cl.Action(
                    name="daily_digest",
                    payload={"cat": "cs.LG", "days": 2, "limit": 10},
                    label="📰 デイリーダイジェスト（cs.LG, 直近2日）",
                )
            ],
        ).send()
    except Exception as e:
        await cl.Message(
            content=(
                "## ⚠️ API接続エラー\n\n"
                f"FastAPIサーバーに接続できません: `{e}`\n\n"
                f"**確認事項:**\n"
                f"- `PAPERS_API_BASE={API_BASE}` が正しいか\n"
                f"- FastAPIサーバーが起動しているか\n\n"
                "**利用可能な機能:**\n"
                "- `arxiv: <query>`: 論文検索（API Key不要）\n\n"
                "管理者にお問い合わせください。"
            )
        ).send()


@cl.action_callback("daily_digest")
async def on_daily_digest(action: cl.Action):
    try:
        cfg = {}
        try:
            if isinstance(action.payload, dict):
                cfg = action.payload
            elif isinstance(action.payload, str):
                cfg = json.loads(action.payload)
        except Exception:
            cfg = {}
        cat = cfg.get("cat", "cs.LG")
        days = int(cfg.get("days", 2))
        limit = int(cfg.get("limit", 10))

        items = await call_digest(cat=cat, days=days, limit=limit)
        if not items:
            await cl.Message(
                content="該当するダイジェスト項目がありませんでした。"
            ).send()
            return

        # ヘッダーメッセージを送信
        await cl.Message(
            content=f"# 📰 デイリーダイジェスト\n\n**カテゴリ:** {cat} | **期間:** 過去{days}日 | **件数:** {limit}件"
        ).send()

        # 各論文を個別のメッセージとして表示（ボタンを近くに配置）
        for i, it in enumerate(items, 1):
            title = (it.get("title") or "").strip() or "（無題）"
            url = it.get("url") or it.get("link") or ""
            pdf = it.get("pdf") or ""
            summary = it.get("summary_short") or it.get("summary") or ""
            paper_id = it.get("id", "")

            # 論文情報を構築
            paper_content = f"## {i}. {title}\n"

            # リンク情報
            links = []
            if url:
                links.append(f"[arXiv]({url})")
            if pdf:
                links.append(f"[PDF]({pdf})")
            if links:
                paper_content += f"🔗 {' | '.join(links)}\n"

            # 要約
            if summary:
                s = summary.strip()
                if len(s) > 200:
                    s = s[:200] + "..."
                paper_content += f"📝 {s}"

            # 詳細表示ボタンを準備
            actions = []
            if paper_id:
                actions.append(
                    cl.Action(
                        name="show_digest_details",
                        payload={"paper_id": paper_id, "paper_title": title},
                        label="📖 詳細を見る",
                    )
                )

            # 各論文を個別のメッセージとして送信
            await cl.Message(content=paper_content, actions=actions).send()
    except httpx.HTTPStatusError as he:
        await cl.Message(
            content=f"❌ /digest エラー {he.response.status_code}: {he.response.text}"
        ).send()
    except Exception as e:
        await cl.Message(
            content=f"❌ デイリーダイジェスト取得に失敗しました: `{e}`"
        ).send()


@cl.action_callback("show_digest_details")
async def on_show_digest_details(action: cl.Action):
    """論文の詳細情報を表示"""
    try:
        paper_id = action.payload.get("paper_id")
        paper_title = action.payload.get("paper_title", "論文")

        if not paper_id:
            await cl.Message(content="❌ 論文IDが指定されていません").send()
            return

        # ローディング表示
        loading_msg = await cl.Message(
            content=f"📖 {paper_title} の詳細情報を取得中..."
        ).send()

        try:
            details = await call_digest_details(paper_id)

            # 論文の章立てに基づく構造化された詳細情報を構築
            content_parts = [f"# 📄 {details['title']}"]

            # 論文メタデータ
            content_parts.append("## 📋 論文情報")

            if details.get("authors"):
                authors_str = ", ".join(details["authors"][:3])  # 最初の3名のみ表示
                if len(details["authors"]) > 3:
                    authors_str += f" 他{len(details['authors']) - 3}名"
                content_parts.append(f"**👥 著者:** {authors_str}")

            if details.get("categories"):
                content_parts.append(
                    f"**🏷️ カテゴリ:** {', '.join(details['categories'])}"
                )

            # リンク情報
            links = []
            if details.get("url"):
                links.append(f"[arXiv]({details['url']})")
            if details.get("pdf"):
                links.append(f"[PDF]({details['pdf']})")
            if links:
                content_parts.append(f"**🔗 リンク:** {' | '.join(links)}")

            # 論文の概要
            if details.get("full_summary"):
                content_parts.append("\n## 📝 論文概要")
                content_parts.append(f"{details['full_summary']}")

            # 論文構造の表示
            if details.get("paper_structure"):
                structure = details["paper_structure"]
                content_parts.append("\n## 📖 論文構造")

                # 章立ての表示
                if structure.get("sections"):
                    content_parts.append("**📋 章立て:**")
                    for i, section in enumerate(structure["sections"], 1):
                        content_parts.append(f"{i}. {section}")

                # 分析品質の表示
                quality = structure.get("content_quality", "unknown")
                completeness = structure.get("analysis_completeness", "unknown")

                if quality == "high" and completeness == "complete":
                    content_parts.append(
                        "\n✅ **分析品質:** 高品質な詳細分析が完了しています"
                    )
                elif quality == "low" or completeness == "incomplete":
                    content_parts.append(
                        "\n⚠️ **分析品質:** 分析が不完全です。より詳細な情報を取得中..."
                    )

                # RAG結果に基づく詳細分析
                if (
                    details.get("cornell_note")
                    or details.get("quiz_items")
                    or details.get("citations")
                ):
                    content_parts.append("\n## 🔬 研究詳細")

                    # Cornell Note（研究ノート）から実際の内容を抽出
                    if details.get("cornell_note"):
                        cornell = details["cornell_note"]
                        content_parts.append("\n### 📚 研究ノート")
                        content_parts.append(
                            f"**💡 キーポイント:** {cornell.get('cue', '')}"
                        )
                        content_parts.append(
                            f"**📝 詳細分析:**\n{cornell.get('notes', '')}"
                        )
                        content_parts.append(
                            f"**📋 研究要約:** {cornell.get('summary', '')}"
                        )

                    # 関連研究
                    if details.get("citations"):
                        content_parts.append("\n### 📚 関連研究")
                        for i, cite in enumerate(details["citations"], 1):
                            content_parts.append(
                                f"{i}. [{cite.get('title', '')}]({cite.get('url', '')})"
                            )

                    # 理解度チェック
                    if details.get("quiz_items"):
                        content_parts.append("\n### 🧠 理解度チェック")
                        for i, quiz in enumerate(details["quiz_items"], 1):
                            content_parts.append(
                                f"\n**問題 {i}:** {quiz.get('question', '')}"
                            )
                            for option in quiz.get("options", []):
                                marker = (
                                    "✅ "
                                    if option.get("id") == quiz.get("correct_answer")
                                    else "⚪ "
                                )
                                content_parts.append(
                                    f"  {marker}{option.get('id', '').upper()}: {option.get('text', '')}"
                                )
                            content_parts.append("")
            else:
                # 論文構造が取得できない場合
                content_parts.append("\n## 📖 論文内容")
                content_parts.append(
                    "⚠️ 論文構造の分析中です。RAG処理により詳細な研究内容を取得しています..."
                )

                # 基本的なRAG結果がある場合は表示
                if (
                    details.get("cornell_note")
                    or details.get("quiz_items")
                    or details.get("citations")
                ):
                    content_parts.append("\n## 🔬 研究詳細")

                    if details.get("cornell_note"):
                        cornell = details["cornell_note"]
                        content_parts.append("\n### 📚 研究ノート")
                        content_parts.append(
                            f"**💡 キーポイント:** {cornell.get('cue', '')}"
                        )
                        content_parts.append(
                            f"**📝 詳細分析:**\n{cornell.get('notes', '')}"
                        )
                        content_parts.append(
                            f"**📋 研究要約:** {cornell.get('summary', '')}"
                        )

                    if details.get("citations"):
                        content_parts.append("\n### 📚 関連研究")
                        for i, cite in enumerate(details["citations"], 1):
                            content_parts.append(
                                f"{i}. [{cite.get('title', '')}]({cite.get('url', '')})"
                            )

                    if details.get("quiz_items"):
                        content_parts.append("\n### 🧠 理解度チェック")
                        for i, quiz in enumerate(details["quiz_items"], 1):
                            content_parts.append(
                                f"\n**問題 {i}:** {quiz.get('question', '')}"
                            )
                            for option in quiz.get("options", []):
                                marker = (
                                    "✅ "
                                    if option.get("id") == quiz.get("correct_answer")
                                    else "⚪ "
                                )
                                content_parts.append(
                                    f"  {marker}{option.get('id', '').upper()}: {option.get('text', '')}"
                                )
                            content_parts.append("")

            # 研究の意義
            content_parts.append("\n## 🎯 研究の意義")
            if details.get("categories"):
                categories = details["categories"]
                if "cs.LG" in categories:
                    content_parts.append("- **機械学習分野**での新たなアプローチを提案")
                if "cs.AI" in categories:
                    content_parts.append("- **人工知能**の発展に寄与する重要な知見")
                if "cs.RO" in categories:
                    content_parts.append("- **ロボティクス**分野での実用的な応用可能性")
                if "cs.CV" in categories:
                    content_parts.append(
                        "- **コンピュータビジョン**における革新的な手法"
                    )
                if "cs.CL" in categories:
                    content_parts.append("- **自然言語処理**における新たな手法")
                if "cs.RO" in categories:
                    content_parts.append("- **ロボティクス**分野での実用的な応用可能性")

            if details.get("sections"):
                content_parts.append("\n## 📑 検出されたセクション")
                toc = details.get("toc_flat", [])
                if toc:
                    for heading in toc[:10]:
                        content_parts.append(f"- {heading}")
                    if len(toc) > 10:
                        content_parts.append(f"... (他 {len(toc) - 10} セクション)")

                if details.get("has_full_text"):
                    content_parts.append(
                        f"\n**コンテンツサイズ**: {details.get('content_length', 0):,} bytes"
                    )

            # ローディングメッセージを更新
            loading_msg.content = "\n".join(content_parts)

            actions = []
            if details.get("has_full_text"):
                actions.append(
                    cl.Action(
                        name="show_fulltext",
                        payload={"paper_id": paper_id},
                        label="📄 全文を表示",
                    )
                )

            if actions:
                loading_msg.actions = actions

            await loading_msg.update()

        except httpx.HTTPStatusError as he:
            error_content = (
                f"❌ 詳細取得エラー {he.response.status_code}: {he.response.text}"
            )
            print(f"❌ HTTP Error: {error_content}")
            loading_msg.content = error_content
            await loading_msg.update()
        except Exception as e:
            error_content = f"❌ 詳細取得失敗: {str(e)}"
            print(f"❌ General Error: {error_content}")
            loading_msg.content = error_content
            await loading_msg.update()

    except Exception as e:
        await cl.Message(content=f"❌ 詳細表示エラー: `{e}`").send()


@cl.action_callback("show_fulltext")
async def on_show_fulltext(action: cl.Action):
    """全文表示のコールバック"""
    try:
        paper_id = action.payload.get("paper_id")

        if not paper_id:
            await cl.Message(content="❌ 論文IDが指定されていません").send()
            return

        loading_msg = await cl.Message(content="📄 全文を取得中...").send()

        try:
            fulltext = await call_fulltext(paper_id, fmt="plain", max_bytes=100000)

            if len(fulltext) >= 100000:
                warning = "\n\n⚠️ **注意**: コンテンツは100,000バイトに制限されています。完全な内容を見るにはPDFをダウンロードしてください。\n\n"
            else:
                warning = ""

            content = f"""### 📄 全文コンテンツ

{warning}```
{fulltext}
```
"""
            await loading_msg.update(content=content)

        except Exception as e:
            error_msg = f"❌ 全文取得エラー: {str(e)}"
            await loading_msg.update(content=error_msg)

    except Exception as e:
        await cl.Message(content=f"❌ エラー: {str(e)}").send()


@cl.on_message
async def on_message(msg: cl.Message):
    text = (msg.content or "").strip()
    if text.lower().startswith("digest"):
        try:
            parts = text.split()
            cat = "cs.LG"
            days = 2
            limit = 10
            for token in parts[1:]:
                t = token.strip()
                if t.lower().startswith("cs."):
                    cat = t
                elif t.lower().startswith("days="):
                    days = int(t.split("=", 1)[1])
                elif t.lower().startswith("limit="):
                    limit = int(t.split("=", 1)[1])

            items = await call_digest(cat=cat, days=days, limit=limit)
            if not items:
                await cl.Message(
                    content="該当するダイジェスト項目がありませんでした。"
                ).send()
                return

            # ヘッダーメッセージを送信
            await cl.Message(content="# 📰 デイリーダイジェスト").send()

            # 各論文を個別のメッセージとして表示（ボタンを近くに配置）
            for i, it in enumerate(items, 1):
                title = (it.get("title") or "").strip() or "（無題）"
                url = it.get("url") or it.get("link") or ""
                pdf = it.get("pdf") or ""
                summary = it.get("summary_short") or it.get("summary") or ""
                paper_id = it.get("id", "")

                # 論文情報を構築
                paper_content = f"## {i}. {title}\n"

                # リンク情報
                links = []
                if url:
                    links.append(f"[arXiv]({url})")
                if pdf:
                    links.append(f"[PDF]({pdf})")
                if links:
                    paper_content += f"🔗 {' | '.join(links)}\n"

                # 要約
                if summary:
                    s = summary.strip()
                    if len(s) > 200:
                        s = s[:200] + "..."
                    paper_content += f"📝 {s}"

                # 詳細表示ボタンを準備
                actions = []
                if paper_id:
                    actions.append(
                        cl.Action(
                            name="show_digest_details",
                            payload={"paper_id": paper_id, "paper_title": title},
                            label="📖 詳細を見る",
                        )
                    )

                # 各論文を個別のメッセージとして送信
                await cl.Message(content=paper_content, actions=actions).send()
        except httpx.HTTPStatusError as he:
            await cl.Message(
                content=f"❌ /digest {he.response.status_code}: {he.response.text}"
            ).send()
        except Exception as e:
            await cl.Message(content=f"❌ /digest 失敗: `{e}`").send()
        return

    # arxiv: クエリ
    if text.lower().startswith("arxiv:"):
        query = text.split(":", 1)[1].strip()
        try:
            items = await call_arxiv_search(query, max_results=10)
            if not items:
                await cl.Message(content="該当結果がありませんでした。").send()
                return
            lines = []
            for it in items:
                title = it.get("title", "").strip() or "（無題）"
                url = it.get("url") or ""
                summary = it.get("summary") or ""
                if url:
                    lines.append(f"- **[{title}]({url})**")
                else:
                    lines.append(f"- **{title}**")
                if summary:
                    # 長すぎると鬱陶しいので軽く抑制
                    s = summary.strip()
                    if len(s) > 280:
                        s = s[:280] + "..."
                    lines.append(f"  \n  {s}")
            await cl.Message(content="### arXiv 検索結果\n" + "\n".join(lines)).send()
        except httpx.HTTPStatusError as he:
            await cl.Message(
                content=f"❌ /arxiv/search {he.response.status_code}: {he.response.text}"
            ).send()
        except Exception as e:
            await cl.Message(content=f"❌ /arxiv/search 失敗: `{e}`").send()
        return

    # それ以外は /rag/stream をSSEで受信しながら表示
    # 最初に readiness を軽く確認
    try:
        h = await get_health()
        if not h.get("rag_ready"):
            await cl.Message(
                content="⏳ RAG index 準備中です。しばらくしてからお試しください。"
            ).send()
            return
    except Exception:
        # health失敗時も一応本番を叩いてみる
        pass

    # 処理開始のステップ表示
    async with cl.Step(name="RAG処理開始", type="run") as step:
        step.output = "🔍 質問を処理中です..."

    out = cl.Message(content="")
    await out.send()

    try:
        async for chunk in sse_rag_stream(text):
            if chunk.get("type") == "status":
                # ステータスメッセージをステップとして表示
                async with cl.Step(name="処理状況", type="tool") as status_step:
                    status_step.output = chunk.get("text", "")
            elif chunk.get("type") == "content":
                # コンテンツをストリーミング表示
                text = chunk.get("text", "")
                if text:
                    await out.stream_token(text)
            elif chunk.get("type") == "error":
                # エラーメッセージを表示
                await out.update(content=f"❌ エラー: {chunk.get('text', '')}")
                return

        await out.update()

        # 処理完了のステップ表示
        async with cl.Step(name="RAG処理完了", type="run") as step:
            step.output = "✅ 回答生成が完了しました"

    except asyncio.CancelledError:
        # キャンセルされた場合は適切に処理
        await out.update(content="⏹️ 処理がキャンセルされました")
    except httpx.HTTPStatusError as he:
        if he.response.status_code == 503:
            await out.update(content="⚠️ RAG index が未準備です。（503）")
        else:
            await out.update(
                content=f"❌ /rag/stream {he.response.status_code}: {he.response.text}"
            )
    except Exception as e:
        await out.update(content=f"❌ /rag/stream 失敗: `{e}`")
