"""Unit tests for merge_utils helpers."""

import warnings

import pytest

from fastapi_errors_plus.merge_utils import (
    ensure_examples_dict,
    merge_examples_map,
    unique_key,
)


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


@pytest.mark.unit
class TestEnsureExamplesDict:
    def test_non_dict_examples_emits_warning_and_resets(self) -> None:
        media = {"examples": ["not", "a", "dict"]}
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = ensure_examples_dict(media)
        assert result == {}
        assert media["examples"] == {}
        assert len(caught) == 1
        assert issubclass(caught[0].category, UserWarning)


@pytest.mark.unit
class TestMergeExamplesMap:
    def test_identical_value_is_idempotent(self) -> None:
        media: dict = {
            "examples": {
                "Conflict": {"value": {"code": "RULE", "detail": "exists"}},
            },
        }
        incoming = {
            "Conflict": {"value": {"code": "RULE", "detail": "exists"}},
        }
        merge_examples_map(media, incoming, unique_key_fn=unique_key)
        assert list(media["examples"].keys()) == ["Conflict"]

    def test_different_value_allocates_unique_key(self) -> None:
        media: dict = {
            "examples": {
                "Conflict": {"value": {"detail": "first"}},
            },
        }
        incoming = {
            "Conflict": {"value": {"detail": "second"}},
        }
        merge_examples_map(media, incoming, unique_key_fn=unique_key)
        assert set(media["examples"].keys()) == {"Conflict", "Conflict_2"}
