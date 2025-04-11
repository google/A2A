![图片信息](images/A2A_banner.png)

<p>
    其他语言版本:
    <a href="README.md">English</a> |
    <a href="README.ko.md">한국어 (Korean)</a> |
    <a href="README.ja.md">日本語 (Japanese)</a>
</p>

**_一个开放协议，使不透明的代理应用程序之间能够进行通信和互操作_**

<!-- 目录 -->

- [Agent2Agent 协议 A2A](#agent2agent-协议-a2a)
    - [入门指南](#入门指南)
    - [贡献](#贡献)
    - [未来计划](#未来计划)
    - [关于](#关于)

<!-- /目录 -->

企业AI采用的最大挑战之一是让基于不同框架和供应商构建的代理能够协同工作。这就是我们创建*Agent2Agent (A2A) 协议*的原因，这是一种协作方式，帮助不同生态系统中的代理相互通信。Google正在推动这个开放协议倡议，因为我们相信这个协议**对于支持多代理通信至关重要，因为它为您的代理提供了一种共同语言，无论它们基于什么框架或供应商构建**。

通过*A2A*，代理可以展示彼此的能力，并协商它们与用户的交互方式（通过文本、表单或双向音频/视频）——所有这些都在安全协作的情况下进行。

### **查看 A2A 的实际应用**

观看[此演示视频](https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/A2A_demo_v4.mp4)，了解A2A如何实现不同代理框架之间的无缝通信。

### 概念概述

Agent2Agent (A2A) 协议促进了独立AI代理之间的通信。以下是核心概念：

*   **代理卡片：** 描述代理功能、技能、端点URL和认证要求的公共元数据文件（通常位于`/.well-known/agent.json`）。客户端使用此文件进行发现。
*   **A2A 服务器：** 暴露实现A2A协议方法（在[JSON规范](/specification)中定义）的HTTP端点的代理。它接收请求并管理任务执行。
*   **A2A 客户端：** 使用A2A服务的应用程序或另一个代理。它向A2A服务器的URL发送请求（如`tasks/send`）。
*   **任务：** 工作的中心单元。客户端通过发送消息（`tasks/send`或`tasks/sendSubscribe`）启动任务。任务具有唯一ID，并通过状态（`submitted`、`working`、`input-required`、`completed`、`failed`、`canceled`）进行。
*   **消息：** 表示客户端（`role: "user"`）和代理（`role: "agent"`）之间的通信轮次。消息包含`Parts`。
*   **部分：** `Message`或`Artifact`中的基本内容单元。可以是`TextPart`、`FilePart`（包含内联字节或URI）或`DataPart`（用于结构化JSON，例如表单）。
*   **工件：** 表示代理在任务期间生成的输出（例如生成的文件、最终结构化数据）。工件也包含`Parts`。
*   **流式传输：** 对于长时间运行的任务，支持`streaming`功能的服务器可以使用`tasks/sendSubscribe`。客户端通过Server-Sent Events (SSE)接收`TaskStatusUpdateEvent`或`TaskArtifactUpdateEvent`消息，提供实时进度。
*   **推送通知：** 支持`pushNotifications`的服务器可以主动将任务更新发送到客户端提供的webhook URL，通过`tasks/pushNotification/set`配置。

**典型流程：**

1.  **发现：** 客户端从服务器的well-known URL获取代理卡片。
2.  **启动：** 客户端发送包含初始用户消息和唯一任务ID的`tasks/send`或`tasks/sendSubscribe`请求。
3.  **处理：**
    *   **（流式传输）：** 服务器随着任务进展发送SSE事件（状态更新、工件）。
    *   **（非流式传输）：** 服务器同步处理任务并在响应中返回最终的`Task`对象。
4.  **交互（可选）：** 如果任务进入`input-required`状态，客户端使用相同的任务ID通过`tasks/send`或`tasks/sendSubscribe`发送后续消息。
5.  **完成：** 任务最终达到终止状态（`completed`、`failed`、`canceled`）。

### **入门指南**

* 📚 阅读[技术文档](https://google.github.io/A2A/#/documentation)以了解功能
* 📝 查看协议的[JSON规范](/specification)
* 🎬 使用我们的[示例](/samples)查看A2A的实际应用
    * 示例A2A客户端/服务器 ([Python](/samples/python/common), [JS](/samples/js/src))
    * [多代理Web应用](/demo/README.md)
    * CLI ([Python](/samples/python/hosts/cli/README.md), [JS](/samples/js/README.md))
* 🤖 使用我们的[示例代理](/samples/python/agents/README.md)了解如何将A2A集成到代理框架中
    * [代理开发工具包 (ADK)](/samples/python/agents/google_adk/README.md)
    * [CrewAI](/samples/python/agents/crewai/README.md)
    * [LangGraph](/samples/python/agents/langgraph/README.md)
    * [Genkit](/samples/js/src/agents/README.md)
* 📑 查看关键主题以了解协议详情
    * [A2A和MCP](https://google.github.io/A2A/#/topics/a2a_and_mcp.md)
    * [代理发现](https://google.github.io/A2A/#/topics/agent_discovery.md)
    * [企业就绪](https://google.github.io/A2A/#/topics/enterprise_ready.md)
    * [推送通知](https://google.github.io/A2A/#/topics/push_notifications.md)

### **贡献**

欢迎贡献！请参阅我们的[贡献指南](CONTRIBUTING.md)开始。\
有问题吗？加入[GitHub讨论](https://github.com/google/A2A/discussions/)中的社区。\
提供协议改进反馈，请访问[GitHub问题](https://github.com/google/A2A/issues)。\
想发送私人反馈？使用此[Google表单](https://docs.google.com/forms/d/e/1FAIpQLScS23OMSKnVFmYeqS2dP7dxY3eTyT7lmtGLUa8OJZfP4RTijQ/viewform)

### **未来计划**

未来计划包括协议本身的改进和示例的增强：

**协议增强：**

*   **代理发现：**
    *   在`AgentCard`中正式包含授权方案和可选凭据。
*   **代理协作：**
    *   研究`QuerySkill()`方法，用于动态检查不支持或未预期的技能。
*   **任务生命周期和UX：**
    *   支持任务*内*的动态UX协商（例如，代理在对话中添加音频/视频）。
*   **客户端方法和传输：**
    *   探索扩展对客户端发起方法的支持（超越任务管理）。
    *   改进流式传输可靠性和推送通知机制。

**示例和文档增强：**

*   简化"Hello World"示例。
*   包含与不同框架集成或展示特定A2A功能的额外示例。
*   为通用客户端/服务器库提供更全面的文档。
*   从JSON模式生成人类可读的HTML文档。

### **关于**

A2A协议是由Google LLC运营的开源项目，在[许可证](LICENSE)下，欢迎整个社区的贡献。 