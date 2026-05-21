#[test]
fn all_bundled_protos_compile() {
    let files = proto_src_confluent::FILES;
    assert_eq!(files.len(), 2);

    let fds = testkit::compile(files).expect("confluent protos compile");

    let names = testkit::file_names(&fds);
    for (path, _) in files {
        assert!(names.contains(path), "not compiled: {path}");
    }
    assert!(
        testkit::has_message(&fds, "Decimal"),
        "confluent.type.Decimal not found"
    );
}
