//! Generates the `FILES` table from the vendored `.proto` files under `proto/`.
//! Std-only (no dependencies); driven entirely by the folder contents, so there
//! is no per-file list to maintain.

use std::path::{Path, PathBuf};

fn collect(root: &Path, dir: &Path, out: &mut Vec<(String, PathBuf)>) {
    for entry in std::fs::read_dir(dir).expect("read proto dir") {
        let path = entry.expect("dir entry").path();
        if path.is_dir() {
            collect(root, &path, out);
        } else if path.extension().is_some_and(|e| e == "proto") {
            // Import path = path relative to `proto/`, using `/`.
            let rel = path.strip_prefix(root).expect("under proto root");
            let import = rel
                .components()
                .map(|c| c.as_os_str().to_str().expect("utf-8 path"))
                .collect::<Vec<_>>()
                .join("/");
            out.push((import, path));
        }
    }
}

fn main() {
    let proto_root = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap()).join("proto");
    let out_dir = PathBuf::from(std::env::var("OUT_DIR").unwrap());

    println!("cargo:rerun-if-changed=proto");

    let mut files = Vec::new();
    collect(&proto_root, &proto_root, &mut files);
    files.sort();
    assert!(
        !files.is_empty(),
        "no .proto files found under {proto_root:?}"
    );

    let mut generated = String::from(
        "/// Bundled files as `(import path, source text)` pairs.\npub static FILES: &[(&str, &str)] = &[\n",
    );
    for (import, abs) in &files {
        generated.push_str(&format!(
            "    ({import:?}, include_str!({:?})),\n",
            abs.to_str().expect("utf-8 path")
        ));
    }
    generated.push_str("];\n");
    std::fs::write(out_dir.join("files.rs"), generated).expect("write files.rs");
}
