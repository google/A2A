# Protocol Buffer Definitions

This folder contains the a2a specification in Protocol Buffer (protobuf) format

## Prerequisites

Before you can validate or generate code from these protobuf definitions, you need to install `buf`.

Follow the installation instructions on the official `buf` GitHub repository:
<https://github.com/bufbuild/buf/>

## Validation

To validate your protobuf definitions and ensure they adhere to linting rules and are free of breaking changes (if configured), run the following command from the root of this folder:

```sh
buf build
```

Modify `buf.yaml` to suit your specific requirements.

## Code Generation

`buf.gen.yaml` is configured to generate code for the following languages:

- Go
- Java
- Python
- TypeScript

To generate code for all configured languages, run the following command from the root of this folder:

```sh
buf generate
```

`buf.gen.yaml` uses remote plugins for generation, if you wish to use local plugins change remote to local

```yaml
plugins:
  - local: protoc-gen-java
    out: src/java
  - local: protoc-gen-grpc-java
    out: src/java
```

Alternatively use `protoc` commandline for code generation

```bash
protoc --java_out=./src/java --grpc-java_out=./src/java -I. a2a.proto
```

### Generating for Specific Languages

If you do not need to generate code for all the languages listed above, you can comment out the unwanted language sections in your `buf.gen.yaml` file.

For example, if you only want to generate Java exclude the rest, your `buf.gen.yaml` might look something like this (ensure you adapt this to your actual `buf.gen.yaml` structure):

```yaml
# buf.gen.yaml
version: v2
plugins:
#  - plugin: buf.build/protocolbuffers/go
#    out: src/go
#  - plugin: buf.build/protocolbuffers/python
#    out: src/python
  - plugin: buf.build/protocolbuffers/java
    out: src/java
#  - plugin: buf.build/grpc/typescript
#    out: src/ts
```
