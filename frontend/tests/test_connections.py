from types import SimpleNamespace

from datavis.connections import DatasetClient


class StreamingResponse:
    def __init__(self):
        self.iterated = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size):
        assert chunk_size == 1024 * 1024
        self.iterated = True
        yield b"name,count\n"
        yield b"Oak,2\n"


def test_dataframe_streams_csv_to_a_temporary_file(monkeypatch):
    client = DatasetClient(
        SimpleNamespace(backend_url="http://backend", backend_token="token")
    )
    response = StreamingResponse()

    def get(url, **kwargs):
        assert url == "http://backend/v1/datasets/plants.csv"
        assert kwargs == {"timeout": 190, "stream": True}
        return response

    monkeypatch.setattr(client.session, "get", get)

    frame = client.dataframe("plants")

    assert response.iterated
    assert frame.to_dict(orient="records") == [{"name": "Oak", "count": 2}]
