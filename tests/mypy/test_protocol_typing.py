"""Mypy: ErrorDTO protocol assignments."""

from fastapi_errors_plus.protocol import ErrorDTO


class _ModernDTO:
    status_code = 404
    message = "Not found"

    def to_examples(self) -> dict:
        return {"n": {"value": {"detail": "x"}}}


def _accept_error_dto(_: ErrorDTO) -> None:
    pass


_accept_error_dto(_ModernDTO())
