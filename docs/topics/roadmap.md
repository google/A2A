# A2A protocol roadmap

Last updated: Jul 16, 2025

### Near-term initiatives

- Release 0.3 version of the protocol which we intend to keep supported and without breaking changes for a significant amount of time with backward compatibility of the SDKs starting at version 0.3. As part of this release there are a few known breaking changes including:
    - Update the `/.well-known/agent.json` path for hosting Agent Cards to `/.well-known/agent-card.json` based on feedback from IANA.
    - Refactor class fields to be more Pythonic and adopt snake case. [PR 199](https://github.com/a2aproject/a2a-python/pull/199)
- Solidify the support for [A2A extensions](https://a2aproject.github.io/A2A/latest/) with SDK support (starting with the Python SDK) and publishing sample extensions.  
- Introduce support for signed Agent Cards [Discussion 199](https://github.com/a2aproject/A2A/discussions/199#discussioncomment-13770576) to allow verifying the integrity of Agent Card content. 
- Enhance the client side support in SDK (starting with Python) to expose ready-to-use A2A clients, streamlined auth handling and improved handling of tasks.

To review recent protocol changes see [Release Notes](https://github.com/a2aproject/A2A/releases).

### Longer term (3-6 month period) roadmap

#### Governance 

The protocol has been [donated](https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents) to the Linux Foundation. The TSC is working on implementing a governance structure that prioritizes community-led development with standardized processes for contributing to the specification, SDKs and tooling. As part of the effort there will be dedicated working groups created for specific areas of the protocol. 

#### Agent Registry 

Agent Registry enables the discovery of agents and is a critical component of a multi-agent system. There is an active and ongoing discussion in the community around the latest [Discussion 741](https://github.com/a2aproject/A2A/discussions/741).

#### Validation

As the A2A ecosystem matures, it becomes critical for the A2A community to have tools to validate their agents. The community has launched two efforts to help with validation which the group will continue to enhance in the coming months. Learn more about [A2A Inspector](https://github.com/a2aproject/a2a-inspector) and the [A2A Protocol Technology Compatibility Kit](https://github.com/a2aproject/a2a-tck) (TCK).

#### SDKs

A2A Project currently hosts SDKs in four languages (Python, JS, Java, .NET) and contributors are adding more including Go (in progress). 

#### Community best practices

As companies and individuals deploy A2A systems at an increasing pace, we are looking to accelerate the learning of the community by collecting and sharing the best practices and success stories that A2A enabled.
