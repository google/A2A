# Protocole Agent2Agent (A2A)

![Bannière A2A](/docs/assets/a2a-banner.png)
[![Licence Apache](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
<p>
    <a href="/README.md">English</a> | <a href="/i18n/README_zh.md">简体中文</a> | <a href="/i18n/README_ja.md">日本語</a> | <a href="/i18n/README_es.md">Español</a> | <a href="/i18n/README_de.md">Deutsch</a> | <a href="/i18n/README_fr.md">Français</a>
</p>

**Un protocole ouvert permettant la communication et l'interopérabilité entre des applications agençantes opaques**。

Le protocole Agent2Agent (A2A) répond à un défi critique dans le domaine de l'intelligence artificielle : permettre aux agents d'IA générative, construits sur des frameworks divers par différentes entreprises fonctionnant sur des serveurs séparés, de communiquer et collaborer efficacement - en tant qu'agents, pas seulement en tant qu'outils。A2A vise à fournir un langage commun pour les agents, favorisant un écosystème d'IA plus interconnecté, puissant et innovant。

Avec A2A, les agents peuvent :

- Découvrir les capacités les uns des autres。
- Négocier des modalités d'interaction (texte, formulaires, médias)。
- Collaborer en sécurité sur des tâches à long terme。
- Fonctionner sans exposer leur état interne, leurs mémoires ou leurs outils。

## Voir A2A en action

Regardez [cette vidéo de démonstration](https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/A2A_demo_v4.mp4) pour voir comment A2A permet une communication transparente entre différents frameworks d'agents。

## Pourquoi choisir A2A ?

Alors que les agents d'IA deviennent de plus en plus répandus, leur capacité à interopérer est cruciale pour construire des applications complexes et multifonctionnelles。A2A a pour objectif de :

- **Casser les silos :** Connecter les agents à travers différents écosystèmes。
- **Permettre des collaborations complexes :** Autoriser les agents spécialisés à travailler ensemble sur des tâches que seul un agent ne pourrait gérer。
- **Promouvoir les standards ouverts :** Faire émerger une approche communautaire de la communication entre agents, encourageant l'innovation et une large adoption。
- **Préserver l'opacité :** Permettre aux agents de collaborer sans avoir à partager leurs mémoires internes, leur logique propriétaire ou des implémentations spécifiques d'outils, renforçant ainsi la sécurité et protégeant la propriété intellectuelle。

### Fonctionnalités clés

- **Communication standardisée :** JSON-RPC 2.0 sur HTTP(S)。
- **Découverte des agents :** Via des "Fiches agents" détaillant les capacités et les informations de connexion。
- **Interaction flexible :** Prend en charge les requêtes/réponses synchrones, le streaming (SSE) et les notifications push asynchrones。
- **Échange riche de données :** Gère le texte, les fichiers et les données JSON structurées。
- **Adapté aux entreprises :** Conçu avec une attention particulière à la sécurité, à l'authentification et à l'observabilité。

## Premiers pas

- 📚 **Explorer la Documentation :** Visitez le [Site de Documentation du Protocole Agent2Agent](https://google.github.io/A2A/) pour obtenir un aperçu complet, la spécification complète du protocole, des tutoriels et guides。
- 📝 **Consulter la Spécification :** [Spécification du Protocole A2A](https://google.github.io/A2A/specification/)
- 🎬 Utilisez nos [exemples](/samples) pour voir A2A en action
  - Exemple de Client/Serveur A2A ([Python](/samples/python/common), [JS](/samples/js/src))
  - [Application Web Multi-agents](/demo/README.md)
  - CLI ([Python](/samples/python/hosts/cli/README.md), [JS](/samples/js/README.md))
- 🤖 Utilisez nos [agents exemples](/samples/python/agents/README.md) pour découvrir comment intégrer A2A aux frameworks d'agents
  - [Kit de Développement d'Agent (ADK)](/samples/python/agents/google_adk/README.md)
  - [CrewAI](/samples/python/agents/crewai/README.md)
  - [Agent de Données d'Entreprise (Gemini + Mindsdb)](/samples/python/agents/mindsdb/README.md)
  - [LangGraph](/samples/python/agents/langgraph/README.md)
  - [Genkit](/samples/js/src/agents/README.md)
  - [LlamaIndex](/samples/python/agents/llama_index_file_chat/README.md)
  - [Marvin](/samples/python/agents/marvin/README.md)
  - [Semantic Kernel](/samples/python/agents/semantickernel/README.md)
  - [AG2 + MCP](/samples/python/agents/ag2/README.md)
- 📑 Consultez les sujets clés pour comprendre les détails du protocole
  - [A2A et MCP](https://google.github.io/A2A/topics/a2a-and-mcp/)
  - [Découverte des agents](https://google.github.io/A2A/topics/agent-discovery/)
  - [Prêt pour l'entreprise](https://google.github.io/A2A/topics/enterprise-ready/)
  - [Notifications push](https://google.github.io/A2A/topics/streaming-and-async/#2-push-notifications-for-disconnected-scenarios)

## Contributions

Nous accueillons avec enthousiasme les contributions de la communauté pour améliorer et faire évoluer le protocole A2A !

- **Questions & Discussions :** Rejoignez nos [GitHub Discussions](https://github.com/google/A2A/discussions).
- **Problèmes & Suggestions :** Signalez des problèmes ou faites des suggestions d'amélioration via [GitHub Issues](https://github.com/google/A2A/issues).
- **Guide de contribution :** Consultez notre [CONTRIBUTING.md](CONTRIBUTING.md) pour obtenir les détails sur la façon de contribuer.
- **Feedback privé :** Utilisez ce [Google Form](https://goo.gle/a2a-feedback).
- **Programme Partenaire :** Les clients Google Cloud peuvent rejoindre notre programme partenaire via ce [formulaire](https://goo.gle/a2a-partner).

## Prochaines étapes

### Améliorations du protocole

- **Découverte des agents :**
  - Formaliser l'inclusion des schémas d'autorisation et identifiants optionnels directement au sein de la `AgentCard`.
- **Collaboration entre agents :**
  - Explorer une méthode `QuerySkill()` pour vérifier dynamiquement les compétences non supportées ou inattendues.
- **Cycle de vie des tâches & UX :**
  - Support pour la négociation dynamique de l'expérience utilisateur (_UX_) _au sein même d'une tâche (par exemple, ajout audio/video par un agent en cours de conversation).
- **Méthodes & Transport côté client :**
  - Explorer l'extension du support aux méthodes initiées par le client (au-delà de la gestion des tâches).
  - Améliorations apportées à la fiabilité du streaming et des mécanismes de notification push.

## À propos du projet

Le protocole A2A est un projet open-source lancé par Google LLC sous la [Licence Apache 2.0](LICENSE), et il est ouvert aux contributions de la communauté.