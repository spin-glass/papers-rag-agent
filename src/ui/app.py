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
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{API_BASE}/arxiv/search", json=payload)
        r.raise_for_status()
        return r.json().get("items", [])


async def call_digest(cat: str = "cs.LG", days: int = 1, limit: int = 10) -> list[dict]:
    params = {"cat": cat, "days": days, "limit": limit}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(f"{API_BASE}/digest", params=params)
        r.raise_for_status()
        return r.json()


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

        lines = [f"### デイリーダイジェスト（{cat}, 過去{days}日・最大{limit}件）"]
        for it in items:
            title = (it.get("title") or "").strip() or "（無題）"
            url = it.get("url") or it.get("link") or ""
            pdf = it.get("pdf") or ""
            summary = it.get("summary_short") or it.get("summary") or ""
            bullet = f"- {title}"
            if url:
                bullet = f"- [{title}]({url})"
            if pdf:
                bullet += f"（[PDF]({pdf})）"
            lines.append(bullet)
            if summary:
                s = summary.strip()
                if len(s) > 280:
                    s = s[:280] + "..."
                lines.append(f"  \n  {s}")
        await cl.Message(content="\n".join(lines)).send()
    except httpx.HTTPStatusError as he:
        await cl.Message(
            content=f"❌ /digest エラー {he.response.status_code}: {he.response.text}"
        ).send()
    except Exception as e:
        await cl.Message(
            content=f"❌ デイリーダイジェスト取得に失敗しました: `{e}`"
        ).send()


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

            lines = ["### デイリーダイジェスト"]
            for it in items:
                title = (it.get("title") or "").strip() or "（無題）"
                url = it.get("url") or it.get("link") or ""
                pdf = it.get("pdf") or ""
                summary = it.get("summary_short") or it.get("summary") or ""
                bullet = f"- **{title}**"
                if url:
                    bullet = f"- **[{title}]({url})**"
                if pdf:
                    bullet += f" （[PDF]({pdf})）"
                lines.append(bullet)
                if summary:
                    s = summary.strip()
                    if len(s) > 280:
                        s = s[:280] + "..."
                    lines.append(f"  \n  {s}")
            await cl.Message(content="\n".join(lines)).send()
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
