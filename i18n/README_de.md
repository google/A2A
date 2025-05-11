# Agent2Agent (A2A) Protokoll

![A2A Banner](/docs/assets/a2a-banner.png)
[![Apache Lizenz](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
<p>
    <a href="/README.md">English</a> | <a href="/i18n/README_zh.md">简体中文</a> | <a href="/i18n/README_ja.md">日本語</a> | <a href="/i18n/README_es.md">Español</a> | <a href="/i18n/README_de.md">Deutsch</a> | <a href="/i18n/README_fr.md">Français</a>
</p>

**Ein offenes Protokoll zur Ermöglichung von Kommunikation und Interoperabilität zwischen opaken Agentenanwendungen**。

Das Agent2Agent (A2A) Protokoll adressiert eine kritische Herausforderung im KI-Bereich: Generative KI-Agenten, die auf verschiedenen Frameworks basieren, von unterschiedlichen Unternehmen entwickelt werden und auf separaten Servern laufen, effektiv miteinander kommunizieren und zusammenarbeiten zu lassen - als Agenten, nicht nur als Tools。A2A zielt darauf, eine gemeinsame Sprache für Agenten bereitzustellen und so ein stärker vernetztes, leistungsfähigeres und innovativeres KI-Ökosystem zu fördern。

Mit A2A können Agenten:

- Die Fähigkeiten voneinander entdecken。
- Interaktionsmodalitäten (Text, Formulare, Medien) aushandeln。
- Sicher an langfristigen Aufgaben zusammenarbeiten。
- Ohne Offenlegung ihres internen Zustands, ihrer Erinnerungen oder Tools funktionieren。

## A2A in Aktion ansehen

Schauen Sie sich das [Demo-Video](https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/A2A_demo_v4.mp4) an, um zu sehen, wie A2A eine nahtlose Kommunikation zwischen verschiedenen Agenten-Frameworks ermöglicht。

## Warum A2A?

Da KI-Agenten immer verbreiteter werden, ist ihre Fähigkeit zur Interoperabilität entscheidend für den Aufbau komplexer, multifunktionaler Anwendungen。A2A verfolgt folgende Ziele:

- **Silos abbauen:** Agenten über verschiedene Ökosysteme hinweg verbinden。
- **Komplexe Zusammenarbeit ermöglichen:** Spezialisierte Agenten können gemeinsam an Aufgaben arbeiten, die ein einzelner Agent nicht alleine bewältigen könnte。
- **Offene Standards fördern:** Einen communitygesteuerten Ansatz für die Agentenkommunikation fördern, Innovation und breite Akzeptanz anregen。
- **Opazität bewahren:** Agenten können zusammenarbeiten, ohne interne Erinnerungen, proprietäre Logik oder spezifische Tool-Implementierungen teilen zu müssen, was die Sicherheit erhöht und geistiges Eigentum schützt。

### Wichtige Funktionen

- **Standardisierte Kommunikation:** JSON-RPC 2.0 über HTTP(S)。
- **Agentenerkennung:** Über "Agentenkarten", die Fähigkeiten und Verbindungsinformationen enthalten。
- **Flexible Interaktion:** Unterstützt synchrones Request/Response, Streaming (SSE) und asynchrone Push-Benachrichtigungen。
- **Vielfältiger Datenaustausch:** Verarbeitet Text, Dateien und strukturierte JSON-Daten。
- **Unternehmensfähig:** Mit Blick auf Sicherheit, Authentifizierung und Beobachtbarkeit konzipiert。

## Erste Schritte

- 📚 **Dokumentation erkunden:** Besuchen Sie die [Agent2Agent Protokolldokumentationsseite](https://google.github.io/A2A/) für eine vollständige Übersicht, die vollständige Protokollspezifikation, Tutorials und Guides。
- 📝 **Spezifikation ansehen:** [A2A-Protokollspezifikation](https://google.github.io/A2A/specification/)
- 🎬 Nutzen Sie unsere [Beispiele](/samples), um A2A in Aktion zu sehen
  - Beispielhafter A2A-Client/Server ([Python](/samples/python/common), [JS](/samples/js/src))
  - [Multi-Agent Web-Anwendung](/demo/README.md)
  - CLI ([Python](/samples/python/hosts/cli/README.md), [JS](/samples/js/README.md))
- 🤖 Nutzen Sie unsere [Beispielagenten](/samples/python/agents/README.md), um zu sehen, wie man A2A in Agentenframeworks integriert
  - [Agent Development Kit (ADK)](/samples/python/agents/google_adk/README.md)
  - [CrewAI](/samples/python/agents/crewai/README.md)
  - [Enterprise Data Agent (Gemini + Mindsdb)](/samples/python/agents/mindsdb/README.md)
  - [LangGraph](/samples/python/agents/langgraph/README.md)
  - [Genkit](/samples/js/src/agents/README.md)
  - [LlamaIndex](/samples/python/agents/llama_index_file_chat/README.md)
  - [Marvin](/samples/python/agents/marvin/README.md)
  - [Semantic Kernel](/samples/python/agents/semantickernel/README.md)
  - [AG2 + MCP](/samples/python/agents/ag2/README.md)
- 📑 Sehen Sie sich wichtige Themen an, um Einblicke in die Protokolldetails zu erhalten
  - [A2A und MCP](https://google.github.io/A2A/topics/a2a-and-mcp/)
  - [Agentenerkennung](https://google.github.io/A2A/topics/agent-discovery/)
  - [Einsatzbereit für Unternehmen](https://google.github.io/A2A/topics/enterprise-ready/)
  - [Push-Benachrichtigungen](https://google.github.io/A2A/topics/streaming-and-async/#2-push-notifications-for-disconnected-scenarios)

## Mitwirken

Wir freuen uns über Community-Beiträge, um das A2A-Protokoll zu verbessern und weiterzuentwickeln!

- **Fragen & Diskussionen:** Nehmen Sie an unseren [GitHub Discussions](https://github.com/google/A2A/discussions) teil。
- **Probleme & Feedback:** Melden Sie Probleme oder schlagen Sie Verbesserungen über [GitHub Issues](https://github.com/google/A2A/issues) vor。
- **Leitfaden für Beiträge:** Details dazu, wie Sie beitragen können, finden Sie in unserem [CONTRIBUTING.md](CONTRIBUTING.md)。
- **Privates Feedback:** Nutzen Sie dieses [Google Formular](https://goo.gle/a2a-feedback)。
- **Partnerprogramm:** Google Cloud Kunden können über dieses [Formular](https://goo.gle/a2a-partner) unserem Partnerprogramm beitreten。

## Als Nächstes geplante Arbeiten

### Protokollerweiterungen

- **Agentenerkennung:**
  - Die Aufnahme von Autorisierungsschemata und optionalen Zugangsdaten direkt in der `AgentCard` formalisieren。
- **Agentenzusammenarbeit:**
  - Untersuchung einer `QuerySkill()` Methode zum dynamischen Prüfen von nicht unterstützten oder unerwarteten Fähigkeiten。
- **Aufgabenlebenszyklus & UX:**
  - Unterstützung für dynamische UX-Verhandlung _innerhalb_ einer Aufgabe (z.B. Hinzufügen von Audio/Video während eines Gesprächs durch einen Agenten)。
- **Client-Methoden & Transport:**
  - Erforschung der Unterstützung für Client-seitig initiierte Methoden (jenseits des Aufgabenmanagements)。
  - Verbesserungen bei der Zuverlässigkeit von Streaming und Push-Benachrichtigungsmechanismen。

## Über das Projekt

Das A2A-Protokoll ist ein Open-Source-Projekt von Google LLC unter der [Apache License 2.0](LICENSE) und für Beiträge aus der Community geöffnet.