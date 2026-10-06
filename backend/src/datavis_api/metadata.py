"""Client for collection-specific labels owned by specify-metadata-service."""

from __future__ import annotations

from urllib.parse import quote

import requests


class MetadataError(RuntimeError):
    """Raised when a saved-query field cannot be localized."""


class MetadataClient:
    def __init__(self, base_url: str, token: str, collection_id: int):
        self.base_url = base_url.rstrip("/")
        self.collection_id = collection_id
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {token}"

    def _get(self, path: str, **parameters):
        response = self.session.get(
            f"{self.base_url}{path}", params=parameters, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def column_label(self, string_id: str) -> str:
        resolved = self._get(
            f"/collections/{self.collection_id}/resolve", string_id=string_id
        )
        components = resolved.get("components")
        if not isinstance(components, list) or not components:
            raise MetadataError(f"metadata returned no components for {string_id!r}")

        current_table = components[0].get("name")
        if not current_table:
            raise MetadataError(f"metadata returned no root table for {string_id!r}")
        labels = []
        rank_seen = False
        for component in components[1:]:
            resource = component.get("resource")
            name = component.get("name")
            if not resource or not name:
                raise MetadataError(
                    f"metadata returned an invalid component for {string_id!r}"
                )
            if resource == "relationship":
                relationship = self._get(
                    f"/collections/{self.collection_id}/tables/"
                    f"{quote(current_table, safe='')}/relationships/"
                    f"{quote(name, safe='')}"
                )
                labels.append(str(relationship.get("label") or name))
                target = relationship.get("target") or {}
                current_table = target.get("name")
                if not current_table:
                    raise MetadataError(
                        f"metadata did not resolve relationship {name!r} "
                        f"for {string_id!r}"
                    )
            elif resource == "rank":
                ranks = self._get(
                    f"/collections/{self.collection_id}/trees/"
                    f"{quote(current_table, safe='')}/ranks"
                ).get("items", [])
                rank = next(
                    (
                        item
                        for item in ranks
                        if str(item.get("name", "")).casefold() == name.casefold()
                    ),
                    None,
                )
                if rank is None:
                    raise MetadataError(
                        f"metadata did not resolve rank {name!r} for {string_id!r}"
                    )
                labels.append(str(rank.get("label") or name))
                rank_seen = True
            elif resource == "field":
                if rank_seen:
                    continue
                field = self._get(
                    f"/collections/{self.collection_id}/tables/"
                    f"{quote(current_table, safe='')}/fields/{quote(name, safe='')}"
                )
                labels.append(str(field.get("label") or name))
            else:
                raise MetadataError(
                    f"metadata returned unsupported component {resource!r} "
                    f"for {string_id!r}"
                )
        if not labels:
            raise MetadataError(f"metadata returned no display label for {string_id!r}")
        return " › ".join(labels)
