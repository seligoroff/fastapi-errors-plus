"""Golden expectations for Errors characterization tests (release 0.9.3 phase 0)."""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from fastapi import status

from fastapi_errors_plus import ErrorProfile, Errors
from fastapi_errors_plus.errors import _HTTP_422

from tests.conftest import SimpleErrorDTO

ErrorsBuilder = Callable[[], Errors]
GoldenMapping = Dict[int, Dict[str, Any]]


def _simple_dto(
    status_code: int = 404,
    message: str = "Not found",
    detail: str = "Not found",
) -> SimpleErrorDTO:
    return SimpleErrorDTO(
        status_code=status_code,
        message=message,
        example_value={"detail": detail},
    )


def build_c01() -> Errors:
    return Errors()


def build_c02() -> Errors:
    return Errors(
        unauthorized_401=True,
        forbidden_403=True,
        validation_error_422=False,
    )


def build_c03() -> Errors:
    return Errors(validation_error_422=False)


def build_c04() -> Errors:
    profile = ErrorProfile(
        unauthorized_401=True,
        validation_error_422=False,
        forbidden_403=True,
    )
    return Errors(profile=profile, forbidden_403=False)


def build_c05() -> Errors:
    return Errors(
        {
            status.HTTP_404_NOT_FOUND: {
                "description": "Not found",
                "content": {
                    "application/json": {
                        "example": {"detail": "Not found"},
                    },
                },
            },
        },
        validation_error_422=False,
    )


def build_c06() -> Errors:
    return Errors(_simple_dto(), validation_error_422=False)


def build_c07() -> Errors:
    return Errors(
        {
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Custom 401",
                "content": {
                    "application/json": {
                        "examples": {
                            "InvalidToken": {
                                "value": {"detail": "Invalid token"},
                            },
                        },
                    },
                },
            },
        },
        unauthorized_401=True,
        validation_error_422=False,
    )


def build_c08() -> Errors:
    return Errors(
        {
            status.HTTP_401_UNAUTHORIZED: {
                "description": "First",
                "headers": {"X-A": {"description": "a"}},
                "links": {"L-A": {"operationId": "a"}},
                "content": {
                    "application/problem+json": {
                        "example": {"detail": "p1"},
                    },
                    "text/plain": {"example": "t1"},
                },
            },
        },
        {
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Second",
                "headers": {"X-B": {"description": "b"}},
                "links": {"L-B": {"operationId": "b"}},
                "content": {
                    "application/problem+json": {
                        "example": {"detail": "p2"},
                    },
                },
            },
        },
        validation_error_422=False,
    )


def build_c09() -> Errors:
    return Errors(
        {
            status.HTTP_401_UNAUTHORIZED: {
                "content": {
                    "application/json": {
                        "examples": {
                            "E": {"value": {"detail": "First"}},
                        },
                    },
                },
            },
        },
        {
            status.HTTP_401_UNAUTHORIZED: {
                "content": {
                    "application/json": {
                        "examples": {
                            "E": {"value": {"detail": "Second"}},
                        },
                    },
                },
            },
        },
        validation_error_422=False,
    )


def build_c10() -> Errors:
    return Errors(
        _simple_dto(
            status_code=status.HTTP_404_NOT_FOUND,
            message="NotFound",
            detail="nothing",
        ),
        {
            status.HTTP_404_NOT_FOUND: {
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/AppError"},
                    },
                },
            },
        },
        validation_error_422=False,
    )


def build_c11() -> Errors:
    return Errors(
        {
            status.HTTP_409_CONFLICT: {
                "description": "Conflict",
                "content": {
                    "application/json": {
                        "example": {"detail": "Conflict"},
                    },
                },
            },
        },
        _simple_dto(),
        unauthorized_401=True,
        forbidden_403=True,
        validation_error_422=False,
    )


def build_c12() -> Errors:
    return Errors(unauthorized_401=True, validation_error_422=False)


EXPECTED_C01: GoldenMapping = {
    _HTTP_422: {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "example": {"detail": "Validation error"},
            },
        },
    },
}

EXPECTED_C02: GoldenMapping = {
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Unauthorized",
        "content": {
            "application/json": {
                "example": {"detail": "Unauthorized"},
            },
        },
    },
    status.HTTP_403_FORBIDDEN: {
        "description": "Forbidden",
        "content": {
            "application/json": {
                "example": {"detail": "Forbidden"},
            },
        },
    },
}

EXPECTED_C03: GoldenMapping = {}

EXPECTED_C04: GoldenMapping = {
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Unauthorized",
        "content": {
            "application/json": {
                "example": {"detail": "Unauthorized"},
            },
        },
    },
}

EXPECTED_C05: GoldenMapping = {
    status.HTTP_404_NOT_FOUND: {
        "description": "Not found",
        "content": {
            "application/json": {
                "example": {"detail": "Not found"},
            },
        },
    },
}

EXPECTED_C06: GoldenMapping = {
    status.HTTP_404_NOT_FOUND: {
        "description": "Not found",
        "content": {
            "application/json": {
                "examples": {
                    "Not found": {
                        "value": {"detail": "Not found"},
                    },
                },
            },
        },
    },
}

EXPECTED_C07: GoldenMapping = {
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Custom 401",
        "content": {
            "application/json": {
                "examples": {
                    "InvalidToken": {
                        "value": {"detail": "Invalid token"},
                    },
                    "StandardUnauthorized": {
                        "value": {"detail": "Unauthorized"},
                    },
                },
            },
        },
    },
}

EXPECTED_C08: GoldenMapping = {
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Second",
        "headers": {
            "X-A": {"description": "a"},
            "X-B": {"description": "b"},
        },
        "links": {
            "L-A": {"operationId": "a"},
            "L-B": {"operationId": "b"},
        },
        "content": {
            "application/problem+json": {
                "example": {"detail": "p2"},
            },
            "text/plain": {"example": "t1"},
        },
    },
}

EXPECTED_C09: GoldenMapping = {
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Unauthorized",
        "content": {
            "application/json": {
                "examples": {
                    "E": {"value": {"detail": "First"}},
                    "E_2": {"value": {"detail": "Second"}},
                },
            },
        },
    },
}

EXPECTED_C10: GoldenMapping = {
    status.HTTP_404_NOT_FOUND: {
        "description": "NotFound",
        "content": {
            "application/json": {
                "examples": {
                    "NotFound": {
                        "value": {"detail": "nothing"},
                    },
                },
                "schema": {"$ref": "#/components/schemas/AppError"},
            },
        },
    },
}

EXPECTED_C11: GoldenMapping = {
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Unauthorized",
        "content": {
            "application/json": {
                "example": {"detail": "Unauthorized"},
            },
        },
    },
    status.HTTP_403_FORBIDDEN: {
        "description": "Forbidden",
        "content": {
            "application/json": {
                "example": {"detail": "Forbidden"},
            },
        },
    },
    status.HTTP_404_NOT_FOUND: {
        "description": "Not found",
        "content": {
            "application/json": {
                "examples": {
                    "Not found": {
                        "value": {"detail": "Not found"},
                    },
                },
            },
        },
    },
    status.HTTP_409_CONFLICT: {
        "description": "Conflict",
        "content": {
            "application/json": {
                "example": {"detail": "Conflict"},
            },
        },
    },
}

EXPECTED_C12: GoldenMapping = {
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Unauthorized",
        "content": {
            "application/json": {
                "example": {"detail": "Unauthorized"},
            },
        },
    },
}


CHARACTERIZATION_CASES: List[tuple[str, ErrorsBuilder, GoldenMapping]] = [
    ("C01", build_c01, EXPECTED_C01),
    ("C02", build_c02, EXPECTED_C02),
    ("C03", build_c03, EXPECTED_C03),
    ("C04", build_c04, EXPECTED_C04),
    ("C05", build_c05, EXPECTED_C05),
    ("C06", build_c06, EXPECTED_C06),
    ("C07", build_c07, EXPECTED_C07),
    ("C08", build_c08, EXPECTED_C08),
    ("C09", build_c09, EXPECTED_C09),
    ("C10", build_c10, EXPECTED_C10),
    ("C11", build_c11, EXPECTED_C11),
    ("C12", build_c12, EXPECTED_C12),
]
