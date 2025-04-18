![画像情報](images/A2A_banner.png)

<p>
    他の言語で表示:
    <a href="README.md">English</a> |
    <a href="README.ko.md">한국어 (Korean)</a> |
    <a href="README.cn.md">中文 (Chinese)</a>
</p>

**_不透明なエージェントアプリケーション間の通信と相互運用性を可能にするオープンプロトコル_**

<!-- 目次 -->

- [Agent2Agent プロトコル A2A](#agent2agent-プロトコル-a2a)
    - [はじめに](#はじめに)
    - [貢献](#貢献)
    - [今後の計画](#今後の計画)
    - [概要](#概要)

<!-- /目次 -->

エンタープライズAI導入における最大の課題の1つは、異なるフレームワークやベンダーで構築されたエージェントを連携させることです。これが、私たちが*Agent2Agent (A2A) プロトコル*を作成した理由です。これは、異なるエコシステムのエージェントが相互に通信できるようにするための協力的な方法です。Googleは、このオープンプロトコルイニシアチブを主導しています。なぜなら、このプロトコルが**フレームワークやベンダーに関係なく、エージェントに共通言語を提供することで、マルチエージェント通信をサポートするために重要**だと信じているからです。

*A2A*により、エージェントは互いの機能を示し、ユーザーとの対話方法（テキスト、フォーム、または双方向のオーディオ/ビデオ）を交渉できます。これらすべてがセキュリティを維持しながら連携して動作します。

### **A2Aの動作を確認**

異なるエージェントフレームワーク間のシームレスな通信をA2Aがどのように可能にするか、[このデモビデオ](https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/A2A_demo_v4.mp4)でご確認ください。

### 概念的な概要

Agent2Agent (A2A) プロトコルは、独立したAIエージェント間の通信を容易にします。主な概念は以下の通りです：

*   **エージェントカード:** エージェントの機能、スキル、エンドポイントURL、認証要件を説明する公開メタデータファイル（通常は`/.well-known/agent.json`に配置）。クライアントはこれを発見(discovery)に使用します。
*   **A2Aサーバー:** A2Aプロトコルメソッド（[JSON仕様](/specification)で定義）を実装するHTTPエンドポイントを公開するエージェントです。リクエストを受信し、タスク実行を管理します。
*   **A2Aクライアント:** A2Aサービスを使用するアプリケーションまたは他のエージェントです。A2AサーバーのURLにリクエスト（例：`tasks/send`）を送信します。
*   **タスク:** 作業の中心単位です。クライアントはメッセージ（`tasks/send`または`tasks/sendSubscribe`）を送信してタスクを開始します。タスクには一意のIDがあり、状態（`submitted`、`working`、`input-required`、`completed`、`failed`、`canceled`）を経て進行します。
*   **メッセージ:** クライアント（`role: "user"`）とエージェント（`role: "agent"`）間の通信ターンを表します。メッセージは`Parts`を含みます。
*   **パート:** `Message`または`Artifact`内の基本コンテンツ単位です。`TextPart`、`FilePart`（インラインバイトまたはURIを含む）、または`DataPart`（構造化JSON、例：フォーム）である可能性があります。
*   **アーティファクト:** タスク中にエージェントが生成した出力（例：生成されたファイル、最終的な構造化データ）を表します。アーティファクトも`Parts`を含みます。
*   **ストリーミング:** 長時間実行タスクの場合、`streaming`機能をサポートするサーバーは`tasks/sendSubscribe`を使用できます。クライアントはServer-Sent Events (SSE)を通じて`TaskStatusUpdateEvent`または`TaskArtifactUpdateEvent`メッセージを受信し、リアルタイムの進行状況を確認できます。
*   **プッシュ通知:** `pushNotifications`をサポートするサーバーは、クライアントが提供したウェブフックURLに`tasks/pushNotification/set`を通じて構成されたタスク更新を事前に送信できます。

**一般的な流れ:**

1.  **発見:** クライアントがサーバーのwell-known URLからエージェントカードを取得します。
2.  **開始:** クライアントが初期ユーザーメッセージと一意のタスクIDを含む`tasks/send`または`tasks/sendSubscribe`リクエストを送信します。
3.  **処理:**
    *   **(ストリーミング):** サーバーがタスクの進行に応じてSSEイベント（ステータス更新、アーティファクト）を送信します。
    *   **(非ストリーミング):** サーバーがタスクを同期的に処理し、レスポンスで最終的な`Task`オブジェクトを返します。
4.  **対話（オプション）:** タスクが`input-required`状態に入ると、クライアントは同じタスクIDを使用して`tasks/send`または`tasks/sendSubscribe`を通じて後続のメッセージを送信します。
5.  **完了:** タスクは最終的に終了状態（`completed`、`failed`、`canceled`）に達します。

### **はじめに**

* 📚 [技術文書](https://google.github.io/A2A/#/documentation)を読んで機能を理解してください
* 📝 プロトコル構造の[JSON仕様](/specification)を確認してください
* 🎬 [サンプル](/samples)を使用してA2Aを実際に確認してください
    * サンプルA2Aクライアント/サーバー ([Python](/samples/python/common), [JS](/samples/js/src))
    * [マルチエージェントWebアプリ](/demo/README.md)
    * CLI ([Python](/samples/python/hosts/cli/README.md), [JS](/samples/js/README.md))
* 🤖 [サンプルエージェント](/samples/python/agents/README.md)を使用して、A2Aをエージェントフレームワークに統合する方法を確認してください
    * [エージェント開発キット (ADK)](/samples/python/agents/google_adk/README.md)
    * [CrewAI](/samples/python/agents/crewai/README.md)
    * [LangGraph](/samples/python/agents/langgraph/README.md)
    * [Genkit](/samples/js/src/agents/README.md)
* 📑 プロトコルの詳細を理解するための主要なトピックを確認してください
    * [A2AとMCP](https://google.github.io/A2A/#/topics/a2a_and_mcp.md)
    * [エージェント発見](https://google.github.io/A2A/#/topics/agent_discovery.md)
    * [エンタープライズ対応](https://google.github.io/A2A/#/topics/enterprise_ready.md)
    * [プッシュ通知](https://google.github.io/A2A/#/topics/push_notifications.md)

### **貢献**

貢献を歓迎します！開始するには[貢献ガイド](CONTRIBUTING.md)を参照してください。\
質問がありますか？[GitHub discussions](https://github.com/google/A2A/discussions/)でコミュニティに参加してください。\
プロトコル改善のフィードバックを提供するには、[GitHub issues](https://github.com/google/A2A/issues)を訪問してください。\
非公開のフィードバックを送信したいですか？[Googleフォーム](https://docs.google.com/forms/d/e/1FAIpQLScS23OMSKnVFmYeqS2dP7dxY3eTyT7lmtGLUa8OJZfP4RTijQ/viewform)を使用してください

### **今後の計画**

今後の計画には、プロトコル自体の改善とサンプルの強化が含まれます：

**プロトコル改善:**

*   **エージェント発見:**
    *   `AgentCard`内に認証スキームとオプションの資格情報を直接含めることを正式化します。
*   **エージェントコラボレーション:**
    *   サポートされていないまたは予期しないスキルを動的に確認するための`QuerySkill()`メソッドを調査します。
*   **タスクライフサイクルとUX:**
    *   タスク*内で*動的UX交渉をサポートします（例：エージェントが会話中にオーディオ/ビデオを追加する場合）。
*   **クライアントメソッドとトランスポート:**
    *   タスク管理を超えてクライアント開始メソッドのサポートを拡張します。
    *   ストリーミングの信頼性とプッシュ通知メカニズムを改善します。

**サンプルとドキュメントの改善:**

*   "Hello World"の例を簡素化します。
*   さまざまなフレームワークとの統合や特定のA2A機能を示す追加の例を含めます。
*   共通のクライアント/サーバーライブラリに関するより包括的なドキュメントを提供します。
*   JSONスキーマから人間が読めるHTMLドキュメントを生成します。

### **概要**

A2Aプロトコルは、Google LLCが運営するオープンソースプロジェクトで、[ライセンス](LICENSE)の下で、コミュニティ全体からの貢献を歓迎しています。 