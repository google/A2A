# Changelog

## [0.2.5](https://github.com/a2aproject/A2A/compare/v0.2.3...v0.2.5) (2025-06-30)


### ⚠ BREAKING CHANGES

* **spec:** Add a required protocol version to the agent card. ([#802](https://github.com/a2aproject/A2A/issues/802))
* update spec & doc topic with non-restartable tasks ([#770](https://github.com/a2aproject/A2A/issues/770))

### Features

* Add support for multiple transport announcement in AgentCard ([#749](https://github.com/a2aproject/A2A/issues/749)) ([b35485e](https://github.com/a2aproject/A2A/commit/b35485e02e796d15232dec01acfab93fc858c3ec))
* **spec:** Add a required protocol version to the agent card. ([#802](https://github.com/a2aproject/A2A/issues/802)) ([90fa642](https://github.com/a2aproject/A2A/commit/90fa64209498948b329a7b2ac6ec38942369157a))
* Support for multiple pushNotification config per task ([#738](https://github.com/a2aproject/A2A/issues/738)) ([f355d3e](https://github.com/a2aproject/A2A/commit/f355d3e922de61ba97873fe2989a8987fc89eec2))


### Bug Fixes

* **spec:** Fix casing of `types.ts` from [#749](https://github.com/a2aproject/A2A/issues/749) ([#759](https://github.com/a2aproject/A2A/issues/759)) ([14424a6](https://github.com/a2aproject/A2A/commit/14424a69d5435f70e86484b3888ef15817b3ce58))
* **spec:** Make `AgentCard.additionalInterfaces` Optional for backwards compatibility ([#760](https://github.com/a2aproject/A2A/issues/760)) ([4a5e970](https://github.com/a2aproject/A2A/commit/4a5e970ec2c4d92439536e01ea649082b177b8b7))
* Typo in delete push notif config ([#782](https://github.com/a2aproject/A2A/issues/782)) ([147a675](https://github.com/a2aproject/A2A/commit/147a675ba0e8c049f4892ada8c1c6753dab57cd3))


### Documentation

* update spec & doc topic with non-restartable tasks ([#770](https://github.com/a2aproject/A2A/issues/770)) ([ebc4157](https://github.com/a2aproject/A2A/commit/ebc4157ca87ae08d1c55e38e522a1a17201f2854))

## [0.2.4](https://github.com/a2aproject/A2A/compare/v0.2.3...v0.2.4) (2025-06-30)


### Features

* feat: Add support for multiple transport announcement in AgentCard ([#749](https://github.com/a2aproject/A2A/issues/749)) ([b35485e](https://github.com/a2aproject/A2A/commit/b35485e02e796d15232dec01acfab93fc858c3ec))

## [0.2.3](https://github.com/a2aproject/A2A/compare/v0.2.2...v0.2.3) (2025-06-12)


### Bug Fixes

* Address some typos in gRPC annotations ([#747](https://github.com/a2aproject/A2A/issues/747)) ([f506881](https://github.com/a2aproject/A2A/commit/f506881c9b8ff0632d7c7107d5c426646ae31592))

## [0.2.2](https://github.com/a2aproject/A2A/compare/v0.2.1...v0.2.2) (2025-06-09)


### ⚠ BREAKING CHANGES

* Resolve spec inconsistencies with JSON-RPC 2.0

### Features

* Add gRPC and REST definitions to A2A protocol specifications ([#695](https://github.com/a2aproject/A2A/issues/695)) ([89bb5b8](https://github.com/a2aproject/A2A/commit/89bb5b82438b74ff7bb0fafbe335db7100a0ac57))
* Add protocol support for extensions ([#716](https://github.com/a2aproject/A2A/issues/716)) ([70f1e2b](https://github.com/a2aproject/A2A/commit/70f1e2b0c68a3631888091ce9460a9f7fbfbdff2))
* **spec:** Add an optional iconUrl field to the AgentCard ([#687](https://github.com/a2aproject/A2A/issues/687)) ([9f3bb51](https://github.com/a2aproject/A2A/commit/9f3bb51257f008bd878d85e00ec5e88357016039))


### Bug Fixes

* Protocol should released as 0.2.2 ([22e7541](https://github.com/a2aproject/A2A/commit/22e7541be082c4f0845ff7fa044992cda05b437e))
* Resolve spec inconsistencies with JSON-RPC 2.0 ([628380e](https://github.com/a2aproject/A2A/commit/628380e7e392bc8f1778ae991d4719bd787c17a9))

## [0.2.1](https://github.com/a2aproject/A2A/compare/v0.2.0...v0.2.1) (2025-05-27)

### Features

* Add a new boolean for supporting authenticated extended cards ([#618](https://github.com/a2aproject/A2A/issues/618)) ([e0a3070](https://github.com/a2aproject/A2A/commit/e0a3070fc289110d43faf2e91b4ffe3c29ef81da))
* Add optional referenceTaskIds for task followups ([#608](https://github.com/a2aproject/A2A/issues/608)) ([5368e77](https://github.com/a2aproject/A2A/commit/5368e7728cb523caf1a9218fda0b1646325f524b))
