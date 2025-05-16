# Agent2Agent (A2A) 协议

![A2A Banner](/docs/assets/a2a-banner.png)
[![Apache License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
<p>
    <a href="/README.md">English</a> | <a href="/i18n/README_zh.md">简体中文</a> | <a href="/i18n/README_ja.md">日本語</a> | <a href="/i18n/README_es.md">Español</a> | <a href="/i18n/README_de.md">Deutsch</a> | <a href="/i18n/README_fr.md">Français</a>
    <!-- Add other languages here like: | <a href="/i18n/README_de.md">Deutsch</a> -->
</p>

**一个开放协议，用于实现不透明代理应用之间的通信与互操作性。**

Agent2Agent（A2A）协议旨在解决当前人工智能领域的一个关键挑战：让构建于不同框架、由不同公司开发并运行在不同服务器上的生成式 AI 代理能够高效地进行通信与协作——作为智能体本身，而不仅仅是工具。A2A 致力于为代理提供一种通用语言，促进更互联、强大和创新的 AI 生态系统。

通过 A2A，代理可以：

- 发现彼此的能力。
- 协商交互方式（文本、表单、媒体）。
- 安全地协作处理长期任务。
- 在不暴露内部状态、内存或工具的前提下运作。

## 观看 A2A 演示

观看 [演示视频](https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/A2A_demo_v4.mp4)，了解 A2A 如何实现不同代理框架之间的无缝通信。

## 为什么选择 A2A？

随着 AI 代理的普及，它们之间的互操作性对于构建复杂、多功能的应用程序至关重要。A2A 的目标是：

- **打破孤岛：** 连接来自不同生态系统的代理。
- **实现复杂协作：** 允许专业化的代理共同完成单一代理无法独立处理的任务。
- **推动开放标准：** 推动社区驱动的代理通信方法，鼓励创新和广泛采用。
- **保持代理不透明：** 使代理能够在不共享内部记忆、专有逻辑或具体工具实现的情况下进行协作，增强安全性并保护知识产权。

### 核心特性

- **标准化通信：** 基于 HTTP(S) 的 JSON-RPC 2.0。
- **代理发现：** 通过“代理卡片”详细描述能力和连接信息。
- **灵活交互：** 支持同步请求/响应、流式传输（SSE）和异步推送通知。
- **丰富的数据交换：** 支持文本、文件和结构化 JSON 数据。
- **企业级就绪：** 设计时充分考虑了安全性、认证机制和可观察性。

## 快速开始

- 📚 **查阅文档：** 访问 [Agent2Agent 协议文档站点](https://google.github.io/A2A/) 获取完整概述、协议规范、教程和指南。
- 📝 **查看协议规范：** [A2A 协议规范](https://google.github.io/A2A/specification/)
- 🎬 使用我们的 [示例](/samples) 查看 A2A 实际运行效果
  - 示例 A2A 客户端/服务端 ([Python](/samples/python/common), [JS](/samples/js/src))
  - [多代理 Web 应用](/demo/README.md)
  - CLI 工具 ([Python](/samples/python/hosts/cli/README.md), [JS](/samples/js/README.md))
- 🤖 使用我们的 [示例代理](/samples/python/agents/README.md) 看如何将 A2A 集成到代理框架中
  - [Agent 开发套件 (ADK)](/samples/python/agents/google_adk/README.md)
  - [CrewAI](/samples/python/agents/crewai/README.md)
  - [企业数据代理 (Gemini + Mindsdb)](/samples/python/agents/mindsdb/README.md)
  - [LangGraph](/samples/python/agents/langgraph/README.md)
  - [Genkit](/samples/js/src/agents/README.md)
  - [LlamaIndex](/samples/python/agents/llama_index_file_chat/README.md)
  - [Marvin](/samples/python/agents/marvin/README.md)
  - [Semantic Kernel](/samples/python/agents/semantickernel/README.md)
  - [AG2 + MCP](/samples/python/agents/ag2/README.md)
- 📑 查阅关键主题以深入了解协议细节
  - [A2A 与 MCP](https://google.github.io/A2A/topics/a2a-and-mcp/)
  - [代理发现](https://google.github.io/A2A/topics/agent-discovery/)
  - [企业级功能](https://google.github.io/A2A/topics/enterprise-ready/)
  - [推送通知](https://google.github.io/A2A/topics/streaming-and-async/#2-push-notifications-for-disconnected-scenarios)

## 贡献

我们欢迎社区贡献以增强和演进 A2A 协议！

- **问题与讨论：** 加入我们的 [GitHub Discussions](https://github.com/google/A2A/discussions)。
- **反馈与建议：** 通过 [GitHub Issues](https://github.com/google/A2A/issues) 报告问题或提出改进建议。
- **贡献指南：** 参见 [CONTRIBUTING.md](CONTRIBUTING.md) 获取贡献详情。
- **私有反馈：** 使用此 [Google 表单](https://goo.gle/a2a-feedback)。
- **合作伙伴计划：** Google Cloud 客户可通过此 [表单](https://goo.gle/a2a-partner) 加入我们的合作伙伴计划。

## 下一步计划

### 协议增强

- **代理发现：**
  - 在 `AgentCard` 中正式包含授权方案和可选凭证。
- **代理协作：**
  - 探索添加 `QuerySkill()` 方法以动态检查未支持或未预期的技能。
- **任务生命周期与用户体验：**
  - 支持在任务中 _动态协商_ 用户体验（如代理在对话中新增音频/视频）。
- **客户端方法与传输方式：**
  - 探索对客户端发起的方法（超出了任务管理范畴）的支持扩展。
  - 提升流式传输可靠性和推送通知机制。

## 关于项目

A2A 协议是一个由 Google LLC 发起的开源项目，遵循 [Apache License 2.0](LICENSE)，并向社区开放贡献。