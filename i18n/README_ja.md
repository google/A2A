# Agent2Agent (A2A) プロトコル

![A2A バナー](/docs/assets/a2a-banner.png)
[![Apache License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
<p>
    <a href="/README.md">English</a> | <a href="/i18n/README_zh.md">简体中文</a> | <a href="/i18n/README_ja.md">日本語</a> | <a href="/i18n/README_es.md">Español</a> | <a href="/i18n/README_de.md">Deutsch</a> | <a href="/i18n/README_fr.md">Français</a>
</p>

**不透明なエージェント型アプリケーション間の通信および相互運用性を実現するオープンプロトコル**。

Agent2Agent (A2A) プロトコルは、AI分野における重要な課題に取り組みます。異なるフレームワーク上で構築され、異なる企業によって開発され、別々のサーバーで動作するジェネレーティブAIエージェントが効果的に通信・協働できるようにすること - ただのツールとしてではなく、エージェントとしての協働を目指します。A2Aは、エージェントのための共通言語を提供し、より相互接続された強力で革新的なAIエコシステムを促進することを目指しています。

A2Aにより、エージェントは以下のことが可能になります：

- 互いの能力を発見する。
- インタラクションモダリティ（テキスト、フォーム、メディア）を交渉する。
- 長時間にわたるタスクを安全に共同で処理する。
- 自身の内部状態、メモリ、ツールを公開せずに動作する。

## A2Aの実行例

[デモ動画](https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/A2A_demo_v4.mp4)を見て、異なるエージェントフレームワーク間でのシームレスな通信をどのように実現するかをご覧ください。

## A2Aを選ぶ理由

AIエージェントがますます普及する中で、それらの相互運用性は複雑で多機能なアプリケーション構築において不可欠です。A2Aは以下の目標を持っています：

- **孤島の解消：** 異なるエコシステムに存在するエージェントをつなぎます。
- **複雑な協働の実現：** 専門化されたエージェントが協力して、単一のエージェントでは対処できないタスクを遂行できるようにします。
- **オープン標準の推進：** コミュニティ主導のエージェント通信方式を育て、革新と広範な採用を促進します。
- **非可視性の保持：** エージェントが内部メモリや独自のロジック、特定のツール実装を共有することなく協働できるようにし、セキュリティを強化しつつ知的財産を保護します。

### 主な特徴

- **標準化された通信：** HTTP(S) 上でのJSON-RPC 2.0。
- **エージェント発見：** 機能と接続情報を詳細に記載した「エージェントカード」を通じて。
- **柔軟なインタラクション：** 同期リクエスト/レスポンス、ストリーミング（SSE）、非同期プッシュ通知をサポート。
- **豊かなデータ交換：** テキスト、ファイル、構造化されたJSONデータを扱います。
- **エンタープライズ対応：** セキュリティ、認証、可観測性を念頭に設計されています。

## はじめに

- 📚 **ドキュメンテーションの閲覧：** [Agent2Agent プロトコルドキュメンテーションサイト](https://google.github.io/A2A/)で完全な概要、プロトコル仕様、チュートリアルおよびガイドを参照してください。
- 📝 **仕様の閲覧：** [A2Aプロトコル仕様](https://google.github.io/A2A/specification/)
- 🎬 当社の [サンプル](/samples) を使用して A2A の実行例をご覧ください
  - サンプル A2A クライアント/サーバー ([Python](/samples/python/common), [JS](/samples/js/src))
  - [マルチエージェント Web アプリケーション](/demo/README.md)
  - CLI ([Python](/samples/python/hosts/cli/README.md), [JS](/samples/js/README.md))
- 🤖 当社の [サンプルエージェント](/samples/python/agents/README.md) を使用して、エージェントフレームワークに A2A を統合する方法をご覧ください
  - [エージェント開発キット (ADK)](/samples/python/agents/google_adk/README.md)
  - [CrewAI](/samples/python/agents/crewai/README.md)
  - [エンタープライズデータエージェント (Gemini + Mindsdb)](/samples/python/agents/mindsdb/README.md)
  - [LangGraph](/samples/python/agents/langgraph/README.md)
  - [Genkit](/samples/js/src/agents/README.md)
  - [LlamaIndex](/samples/python/agents/llama_index_file_chat/README.md)
  - [Marvin](/samples/python/agents/marvin/README.md)
  - [Semantic Kernel](/samples/python/agents/semantickernel/README.md)
  - [AG2 + MCP](/samples/python/agents/ag2/README.md)
- 📑 プロトコルの詳細を理解するために主要なトピックを確認してください
  - [A2A と MCP](https://google.github.io/A2A/topics/a2a-and-mcp/)
  - [エージェント発見](https://google.github.io/A2A/topics/agent-discovery/)
  - [エンタープライズ対応](https://google.github.io/A2A/topics/enterprise-ready/)
  - [プッシュ通知](https://google.github.io/A2A/topics/streaming-and-async/#2-push-notifications-for-disconnected-scenarios)

## 貢献

私たちはコミュニティからの貢献を歓迎し、A2Aプロトコルを強化・進化させたいと考えています！

- **質問・ディスカッション：** 私たちの [GitHub Discussions](https://github.com/google/A2A/discussions) に参加してください。
- **問題報告・フィードバック：** [GitHub Issues](https://github.com/google/A2A/issues) を通じて問題報告や改善提案を行ってください。
- **貢献ガイド：** 貢献方法の詳細については [CONTRIBUTING.md](CONTRIBUTING.md) をご参照ください。
- **プライベートフィードバック：** この [Google フォーム](https://goo.gle/a2a-feedback) をご利用ください。
- **パートナープログラム：** Google Cloud 顧客の方はこの [フォーム](https://goo.gle/a2a-partner) からパートナープログラムにご参加いただけます。

## 次のステップ

### プロトコルの拡張

- **エージェント発見：**
  - `AgentCard` 内で承認スキームとオプションの資格情報を正式に含めること。
- **エージェント協働：**
  - サポートされていないまたは予期しないスキルを動的にチェックする `QuerySkill()` メソッドの調査。
- **タスクリフサイクル・ユーザーインターフェース：**
  - タスク内でダイナミックなUX交渉をサポート（例：会話中にエージェントが音声/動画を追加）。
- **クライアントメソッドとトランスポート：**
  - タスク管理を超えたクライアント発信メソッドのサポート拡張。
  - ストリーミング信頼性とプッシュ通知メカニズムの向上。

## 本プロジェクトについて

A2Aプロトコルは Google LLC が立ち上げたオープンソースプロジェクトであり、[Apache License 2.0](LICENSE) の下で提供され、コミュニティからの貢献を受け付けています。