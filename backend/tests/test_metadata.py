from datavis_api.metadata import MetadataClient


class Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_localizes_relationship_path_and_field(monkeypatch):
    client = MetadataClient("http://metadata", "token", 32768)
    responses = iter(
        [
            {
                "components": [
                    {"resource": "table", "name": "collectionobject"},
                    {"resource": "relationship", "name": "collectingEvent"},
                    {"resource": "field", "name": "endDate"},
                ]
            },
            {
                "label": "Collecting Information",
                "target": {"name": "collectingevent"},
            },
            {"label": "End Date"},
        ]
    )
    monkeypatch.setattr(client.session, "get", lambda *args, **kwargs: Response(next(responses)))

    assert (
        client.column_label("1,10.collectingevent.endDate")
        == "Collecting Information › End Date"
    )


def test_uses_tree_rank_label_instead_of_full_name(monkeypatch):
    client = MetadataClient("http://metadata", "token", 32768)
    responses = iter(
        [
            {
                "components": [
                    {"resource": "table", "name": "collectionobject"},
                    {"resource": "relationship", "name": "geography"},
                    {"resource": "rank", "name": "Country"},
                    {"resource": "field", "name": "fullName"},
                ]
            },
            {"label": "Geography", "target": {"name": "geography"}},
            {"items": [{"name": "Country", "label": "Country"}]},
        ]
    )
    monkeypatch.setattr(client.session, "get", lambda *args, **kwargs: Response(next(responses)))

    assert client.column_label("country-field") == "Geography › Country"
