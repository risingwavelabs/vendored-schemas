#[test]
fn all_bundled_protos_compile() {
    let files = proto_src_google_type::FILES;
    assert_eq!(files.len(), 17);

    let fds = testkit::compile(files).expect("google/type protos compile");

    let names = testkit::file_names(&fds);
    for (path, _) in files {
        assert!(names.contains(path), "not compiled: {path}");
    }
    assert!(
        testkit::has_message(&fds, "Date"),
        "google.type.Date not found"
    );
}
