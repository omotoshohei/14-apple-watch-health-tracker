from pathlib import Path

from health_report.html import convert_html_images_to_data_uris


def test_convert_html_images_to_data_uris(tmp_path: Path) -> None:
    # Create a dummy image file
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    img_file = assets_dir / "test.png"
    img_file.write_bytes(b"dummy image data")

    # HTML content referencing the image
    html_content = """
    <html>
        <body>
            <img src="assets/test.png" />
            <img src="assets/nonexistent.png" />
        </body>
    </html>
    """

    converted = convert_html_images_to_data_uris(html_content, tmp_path)

    # The existing image should be converted to data URI
    assert "data:image/png;base64,ZHVtbXkgaW1hZ2UgZGF0YQ==" in converted
    # The nonexistent image should remain as is
    assert 'src="assets/nonexistent.png"' in converted
