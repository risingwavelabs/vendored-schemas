# proto-src-google-type

Vendored `google/type/*.proto` sources, exposed as a single
`&[(import_path, content)]` slice with zero dependencies. **Schema resources,
not generated Rust types.**

These are the googleapis common types (`Date`, `Money`, `LatLng`, `Decimal`, …)
that Confluent Schema Registry treats as ambient — a protobuf compiler won't
resolve `import "google/type/date.proto"` on its own; this crate gives you the
sources to feed it.

```toml
[dependencies]
proto-src-google-type = "0.1"
```

```rust
for (import_path, source) in proto_src_google_type::FILES {
    // e.g. a protox FileResolver returning File::from_source(import_path, source),
    // a prost-reflect DescriptorPool, buf, …
}
```

Apache-2.0. The vendored `google/type/*.proto` files are © Google LLC;
Google does not maintain or endorse this crate.
