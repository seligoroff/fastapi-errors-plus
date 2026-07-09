"""Unit tests for merge_utils helpers."""

import pytest

from fastapi_errors_plus.merge_utils import unique_key


@pytest.mark.unit
class TestUniqueKey:
    def test_first_collision_appends_2(self) -> None:
        assert unique_key({"default": {}}, "default") == "default_2"

    def test_multiple_collisions_increment_suffix(self) -> None:
        examples = {
            "CustomExample": {"value": {"detail": "First"}},
            "CustomExample_2": {"value": {"detail": "Second"}},
        }
        assert unique_key(examples, "CustomExample") == "CustomExample_3"

        examples["CustomExample_3"] = {"value": {"detail": "Third"}}
        assert unique_key(examples, "CustomExample") == "CustomExample_4"
