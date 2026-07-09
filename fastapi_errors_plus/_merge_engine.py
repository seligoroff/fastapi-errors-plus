"""Merge engine for building OpenAPI error response maps (internal)."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from fastapi_errors_plus._descriptions import apply_dto_description
from fastapi_errors_plus._dto_adapter import (
    collect_dto_examples,
    pick_error_dto_application_json_extra,
    pick_error_dto_model,
)
from fastapi_errors_plus.merge_utils import (
    ensure_examples_dict,
    merge_examples_map,
    merge_openapi_application_json_non_example,
    merge_singular_example,
    standard_flag_example_key,
    unique_key,
)
from fastapi_errors_plus.protocol import ErrorDTO


@dataclass
class MergeState:
    """Mutable merge state for :class:`Errors` construction."""

    responses: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    flag_example_keys: Dict[int, str] = field(default_factory=dict)


def prior_singular_example_key(state: MergeState, status_code: int) -> Optional[str]:
    """Example-map key for a singular ``example`` from a standard flag, if any."""
    return state.flag_example_keys.get(status_code)


def add_standard_error(
    state: MergeState,
    status_code: int,
    description: str,
    example: Dict[str, Any],
) -> None:
    """Add standard error, merging examples on status collision."""
    example_key = standard_flag_example_key(status_code)

    if status_code not in state.responses:
        state.flag_example_keys[status_code] = example_key
        state.responses[status_code] = {
            "description": description,
            "content": {
                "application/json": {
                    "example": example,
                },
            },
        }
    else:
        existing = state.responses[status_code]
        existing_content = existing.setdefault("content", {})
        content = existing_content.setdefault("application/json", {})
        prior_key = prior_singular_example_key(state, status_code)
        examples = ensure_examples_dict(content, prior_singular_key=prior_key)
        resolved_key = unique_key(examples, example_key)
        examples[resolved_key] = {"value": example}


def add_dict_error(state: MergeState, error_dict: Dict[int, Dict[str, Any]]) -> None:
    """Add error from dict in FastAPI responses format (merge on collision)."""
    for status_code, response_data in error_dict.items():
        response_data = copy.deepcopy(response_data)
        if status_code not in state.responses:
            state.responses[status_code] = response_data
        else:
            existing = state.responses[status_code]

            if "description" in response_data:
                existing["description"] = response_data["description"]

            if "model" in response_data:
                existing["model"] = response_data["model"]

            for key in ("headers", "links"):
                if key not in response_data:
                    continue
                incoming_val = response_data[key]
                if key not in existing or not isinstance(existing.get(key), dict):
                    existing[key] = copy.deepcopy(incoming_val)
                elif isinstance(incoming_val, dict):
                    existing[key].update(copy.deepcopy(incoming_val))
                else:
                    existing[key] = copy.deepcopy(incoming_val)

            if "content" in response_data:
                existing_content = existing.setdefault("content", {})
                response_content = response_data["content"]

                for media_type, media_obj in response_content.items():
                    if media_type != "application/json":
                        existing_content[media_type] = copy.deepcopy(media_obj)
                        continue

                    existing_json = existing_content.setdefault("application/json", {})
                    response_json = media_obj

                    merge_openapi_application_json_non_example(
                        existing_json, response_json
                    )

                    if "examples" in response_json:
                        prior_key = prior_singular_example_key(state, status_code)
                        incoming_examples = response_json["examples"]
                        if (
                            prior_key
                            and isinstance(incoming_examples, dict)
                            and prior_key in incoming_examples
                        ):
                            prior_key = "default"
                        merge_examples_map(
                            existing_json,
                            copy.deepcopy(incoming_examples),
                            prior_singular_key=prior_key,
                            unique_key_fn=unique_key,
                        )
                    elif "example" in response_json:
                        merge_singular_example(
                            existing_json,
                            response_json["example"],
                            prior_singular_key=prior_singular_example_key(
                                state, status_code
                            ),
                            unique_key_fn=unique_key,
                        )


def add_error_dto(
    state: MergeState,
    error_dto: ErrorDTO,
    *,
    standard_descriptions: Dict[int, str],
) -> None:
    """Add error from ErrorDTO, merging examples on status collision."""
    status_code = error_dto.status_code
    examples = collect_dto_examples(error_dto)
    dto_extras = pick_error_dto_application_json_extra(error_dto)
    if dto_extras is not None:
        dto_extras = copy.deepcopy(dto_extras)
    dto_model = pick_error_dto_model(error_dto)

    if status_code not in state.responses:
        application_json: Dict[str, Any] = {"examples": examples}
        if dto_extras is not None:
            merge_openapi_application_json_non_example(application_json, dto_extras)
        response_block: Dict[str, Any] = {
            "description": error_dto.message,
            "content": {
                "application/json": application_json,
            },
        }
        if dto_model is not None:
            response_block["model"] = dto_model
        state.responses[status_code] = response_block
    else:
        existing = state.responses[status_code]

        apply_dto_description(existing, error_dto, standard_descriptions)

        if dto_model is not None:
            existing["model"] = dto_model

        existing_content = existing.setdefault("content", {})
        content_json = existing_content.setdefault("application/json", {})
        prior_key = prior_singular_example_key(state, status_code)
        merge_examples_map(
            content_json,
            copy.deepcopy(examples),
            prior_singular_key=prior_key,
            unique_key_fn=unique_key,
        )

        if dto_extras is not None:
            merge_openapi_application_json_non_example(content_json, dto_extras)
