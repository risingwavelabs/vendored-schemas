# proto-src-confluent

Vendored `confluent/*.proto` sources, exposed as a single
`&[(import_path, content)]` slice with zero dependencies. **Schema resources,
not generated Rust types.**

These are the Confluent-specific schemas (`confluent/meta.proto`,
`confluent/type/decimal.proto`) that Confluent Schema Registry treats as ambient
("known") dependencies — a protobuf compiler won't resolve
`import "confluent/type/decimal.proto"` on its own; this crate gives you the
sources to feed it. (Tracks the latest released `kafka-protobuf-types`;
`confluent/type/variant.proto` exists only on unreleased main and is not
bundled yet.)

```toml
[dependencies]
proto-src-confluent = "0.1"
```

```rust
for (import_path, source) in proto_src_confluent::FILES {
    // e.g. a protox FileResolver returning File::from_source(import_path, source),
    // a prost-reflect DescriptorPool, buf, …
}
```

Apache-2.0. The vendored `confluent/*.proto` files are © Confluent, Inc.;
Confluent does not maintain or endorse this crate.
