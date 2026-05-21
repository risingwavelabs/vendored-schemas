//! Test helpers shared by the vendored-schema crates. Not published — pulled in
//! as a path dev-dependency, so it never reaches consumers.

use std::collections::HashSet;

use prost_types::FileDescriptorSet;
use protox::file::{ChainFileResolver, File, FileResolver, GoogleFileResolver};

/// Serves a crate's `FILES` to protox; `google/protobuf/*` well-known types
/// come from `GoogleFileResolver`.
struct Bundled(&'static [(&'static str, &'static str)]);

impl FileResolver for Bundled {
    fn open_file(&self, name: &str) -> Result<File, protox::Error> {
        match self.0.iter().find(|(p, _)| *p == name) {
            Some((path, source)) => File::from_source(path, source),
            None => Err(protox::Error::file_not_found(name)),
        }
    }
}

/// Compile every file in `files` with protox, returning the descriptor set
/// (or the protox error if anything fails to compile).
pub fn compile(
    files: &'static [(&'static str, &'static str)],
) -> Result<FileDescriptorSet, protox::Error> {
    let mut resolver = ChainFileResolver::new();
    resolver.add(Bundled(files));
    resolver.add(GoogleFileResolver::new());

    let paths: Vec<&str> = files.iter().map(|(p, _)| *p).collect();
    let mut compiler = protox::Compiler::with_file_resolver(resolver);
    compiler.include_imports(true);
    compiler.open_files(paths)?;
    Ok(compiler.file_descriptor_set())
}

/// The file names present in a descriptor set.
pub fn file_names(fds: &FileDescriptorSet) -> HashSet<&str> {
    fds.file.iter().map(|f| f.name()).collect()
}

/// Whether any file defines a top-level message with the given name.
pub fn has_message(fds: &FileDescriptorSet, name: &str) -> bool {
    fds.file
        .iter()
        .any(|f| f.message_type.iter().any(|m| m.name() == name))
}
