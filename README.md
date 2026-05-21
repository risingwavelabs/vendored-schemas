# vendored-schemas

Rust crates that provide common protobuf schema files beyond the well-known types.

Each crate ships only the `.proto` source as a single `&[(import_path, content)]` slice.
It does NOT ship generated Rust types or compiled descriptors.

| Crate | Import prefix | Vendored from (Apache-2.0) |
| --- | --- | --- |
| [`proto-src-google-type`](proto-src-google-type) | `google/type/` | [googleapis/googleapis], © Google LLC |
| [`proto-src-confluent`](proto-src-confluent) | `confluent/` | [confluentinc/schema-registry], © Confluent, Inc. |

## Usage

```toml
[dependencies]
proto-src-google-type = "0.1"
```

```rust
// Each crate exposes its files as (import path, source) pairs.
for (import_path, source) in proto_src_google_type::FILES {
    // hand them to your compiler — e.g. a protox FileResolver that returns
    // File::from_source(import_path, source), or a prost-reflect pool, or buf.
}
```

## Maintenance & provenance

The `.proto` files are vendored **verbatim** from upstream (sources above). The
exact path and pinned commit for each is in [`vendor.toml`](vendor.toml) — the
single source of truth. To refresh a bundle:
bump its `rev` there, run

```sh
./scripts/sync.py
```

(a shallow, blobless, sparse fetch of just the needed paths), review the diff,
and cut a release. Each `rev` must be a commit that actually edits its `src`
folder — `sync.py` rejects an arbitrary commit that doesn't touch the vendored
path. CI re-runs `sync.py` and fails on any diff, so the vendored files can
never drift from the pinned commits.

> The scripts in `scripts/` are AI-generated and NOT reviewed. Use at your own
> risk.

## License

Apache-2.0 (see [`LICENSE`](LICENSE)). The vendored files are themselves
Apache-2.0; their copyright holders are listed in the table above.

[googleapis/googleapis]: https://github.com/googleapis/googleapis
[confluentinc/schema-registry]: https://github.com/confluentinc/schema-registry
