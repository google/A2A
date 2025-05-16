# Protocolo Agent2Agent (A2A)

![Banner de A2A](/docs/assets/a2a-banner.png)
[![Licencia Apache](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
<p>
    <a href="/README.md">English</a> | <a href="/i18n/README_zh.md">简体中文</a> | <a href="/i18n/README_ja.md">日本語</a> | <a href="/i18n/README_es.md">Español</a> | <a href="/i18n/README_de.md">Deutsch</a> | <a href="/i18n/README_fr.md">Français</a>
</p>

**Un protocolo abierto que posibilita la comunicación e interoperabilidad entre aplicaciones agenticas opacas**.

El protocolo Agent2Agent (A2A) aborda un desafío crítico en el panorama de la IA: permitir que agentes de IA generativa, construidos sobre marcos de trabajo diversos por diferentes empresas que operan en servidores separados, se comuniquen y colaboren eficazmente - como agentes, no solo como herramientas. A2A tiene como objetivo proporcionar un lenguaje común para los agentes, fomentando un ecosistema de IA más interconectado, poderoso e innovador.

Con A2A, los agentes pueden:

- Descubrir las capacidades del otro.
- Negociar modalidades de interacción (texto, formularios, medios).
- Colaborar con seguridad en tareas prolongadas.
- Operar sin exponer su estado interno, memoria o herramientas.

## Vea A2A en acción

Mire [este video de demostración](https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/A2A_demo_v4.mp4) para ver cómo A2A permite la comunicación perfecta entre diferentes marcos de agentes.

## ¿Por qué A2A?

A medida que los agentes de IA se vuelven más prevalentes, su capacidad de interoperar es crucial para construir aplicaciones complejas y multifuncionales. A2A tiene como objetivo:

- **Romper silos:** Conectar agentes a través de diferentes ecosistemas.
- **Habilitar colaboraciones complejas:** Permitir que agentes especializados trabajen juntos en tareas que un solo agente no podría manejar por sí solo.
- **Promover estándares abiertos:** Fomentar un enfoque comunitario para la comunicación de agentes, alentando la innovación y la adopción generalizada.
- **Preservar la opacidad:** Permitir que los agentes colaboren sin necesidad de compartir memoria interna, lógica propietaria o implementaciones específicas de herramientas, mejorando la seguridad y protegiendo la propiedad intelectual.

### Características clave

- **Comunicación estandarizada:** JSON-RPC 2.0 sobre HTTP(S).
- **Descubrimiento de agentes:** A través de "Tarjetas de Agente" que detallan capacidades e información de conexión.
- **Interacción flexible:** Admite solicitud/respuesta sincrónica, transmisión (SSE) y notificaciones push asíncronas.
- **Intercambio rico de datos:** Maneja texto, archivos y datos JSON estructurados.
- **Listo para entornos empresariales:** Diseñado pensando en la seguridad, autenticación y observabilidad.

## Empezando

- 📚 **Explore la Documentación:** Visite el [Sitio de Documentación del Protocolo Agent2Agent](https://google.github.io/A2A/) para obtener una visión general completa, la especificación completa del protocolo, tutoriales y guías.
- 📝 **Ver la Especificación:** [Especificación del Protocolo A2A](https://google.github.io/A2A/specification/)
- 🎬 Use nuestras [muestras](/samples) para ver A2A en acción
  - Cliente/Servidor A2A de muestra ([Python](/samples/python/common), [JS](/samples/js/src))
  - [Aplicación Web Multiagente](/demo/README.md)
  - CLI ([Python](/samples/python/hosts/cli/README.md), [JS](/samples/js/README.md))
- 🤖 Use nuestros [agentes de muestra](/samples/python/agents/README.md) para ver cómo integrar A2A en marcos de agentes
  - [Kit de Desarrollo de Agente (ADK)](/samples/python/agents/google_adk/README.md)
  - [CrewAI](/samples/python/agents/crewai/README.md)
  - [Agente de Datos Empresariales (Gemini + Mindsdb)](/samples/python/agents/mindsdb/README.md)
  - [LangGraph](/samples/python/agents/langgraph/README.md)
  - [Genkit](/samples/js/src/agents/README.md)
  - [LlamaIndex](/samples/python/agents/llama_index_file_chat/README.md)
  - [Marvin](/samples/python/agents/marvin/README.md)
  - [Semantic Kernel](/samples/python/agents/semantickernel/README.md)
  - [AG2 + MCP](/samples/python/agents/ag2/README.md)
- 📑 Revise temas clave para comprender los detalles del protocolo
  - [A2A y MCP](https://google.github.io/A2A/topics/a2a-and-mcp/)
  - [Descubrimiento de agentes](https://google.github.io/A2A/topics/agent-discovery/)
  - [Listo para empresas](https://google.github.io/A2A/topics/enterprise-ready/)
  - [Notificaciones push](https://google.github.io/A2A/topics/streaming-and-async/#2-push-notifications-for-disconnected-scenarios)

## Contribución

¡Damos la bienvenida a las contribuciones de la comunidad para mejorar y evolucionar el protocolo A2A!

- **Preguntas y Discusiones:** Únase a nuestras [GitHub Discussions](https://github.com/google/A2A/discussions).
- **Problemas y Comentarios:** Informe problemas o sugiera mejoras a través de [GitHub Issues](https://github.com/google/A2A/issues).
- **Guía de Contribución:** Consulte nuestro [CONTRIBUTING.md](CONTRIBUTING.md) para obtener detalles sobre cómo contribuir.
- **Comentarios Privados:** Utilice este [Google Form](https://goo.gle/a2a-feedback).
- **Programa de Socios:** Los clientes de Google Cloud pueden unirse a nuestro programa de socios mediante este [formulario](https://goo.gle/a2a-partner).

## Próximos pasos

### Mejoras al Protocolo

- **Descubrimiento de agentes:**
  - Formalizar la inclusión de esquemas de autorización y credenciales opcionales directamente dentro de la `AgentCard`.
- **Colaboración entre agentes:**
  - Investigar un método `QuerySkill()` para verificar dinámicamente habilidades no soportadas o inesperadas.
- **Ciclo de vida de las tareas y experiencia del usuario (UX):**
  - Soporte para negociación dinámica de UX _dentro_ de una tarea (por ejemplo, que un agente agregue audio/video durante una conversación).
- **Métodos y transporte del cliente:**
  - Explorar la extensión del soporte a métodos iniciados por el cliente (más allá de la gestión de tareas).
  - Mejoras en la confiabilidad de la transmisión y mecanismos de notificaciones push.

## Acerca del Proyecto

El Protocolo A2A es un proyecto de código abierto iniciado por Google LLC, bajo la [Licencia Apache 2.0](LICENSE), y está abierto a contribuciones de la comunidad.