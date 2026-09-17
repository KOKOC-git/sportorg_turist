import gzip
from io import StringIO

from sportorg.modules.backup.json import _read_json_bytes_with_fallback


def test_read_gzip_json(tmp_path):
    file_name = tmp_path / 'event.json'
    expected = b'{"title":"Tourism"}'
    file_name.write_bytes(gzip.compress(expected))

    with file_name.open() as file:
        assert _read_json_bytes_with_fallback(file) == expected


def test_read_json_from_memory():
    assert _read_json_bytes_with_fallback(StringIO('{"title":"Tourism"}')) == (
        b'{"title":"Tourism"}'
    )
