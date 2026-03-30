"""HTTP client for Hevy API v1."""

from __future__ import annotations

import os
from typing import Any

import httpx

from models import ExerciseTemplate, PostRoutinesRequestBody, RoutineCreated

DEFAULT_BASE_URL = "https://api.hevyapp.com/v1"
DEFAULT_TIMEOUT = 60.0
MAX_PAGE_SIZE = 100


class HevyAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None, body: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class HevyClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        key = api_key or os.environ.get("HEVY_API_KEY")
        if not key:
            raise ValueError("Missing API key: set HEVY_API_KEY or pass api_key=")
        self._client = httpx.Client(
            base_url=base_url.rstrip("/") + "/",
            timeout=timeout,
            headers={"api-key": key},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HevyClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.is_success:
            return
        body: Any
        try:
            body = response.json()
        except Exception:
            body = response.text
        raise HevyAPIError(
            f"Hevy API error {response.status_code}: {body!r}",
            status_code=response.status_code,
            body=body,
        )

    def fetch_all_exercise_templates(self) -> list[ExerciseTemplate]:
        """GET /exercise_templates with pagination (page, pageSize max 100)."""
        all_templates: list[ExerciseTemplate] = []
        page = 1
        while True:
            response = self._client.get(
                "exercise_templates",
                params={"page": page, "pageSize": MAX_PAGE_SIZE},
            )
            self._raise_for_status(response)
            data = response.json()
            batch = data.get("exercise_templates") or []
            for item in batch:
                all_templates.append(ExerciseTemplate.model_validate(item))
            page_count = int(data.get("page_count") or 1)
            if page >= page_count or not batch:
                break
            page += 1
        return all_templates

    def create_routine(self, body: PostRoutinesRequestBody) -> RoutineCreated:
        """POST /routines — returns 201 with Routine."""
        response = self._client.post(
            "routines",
            json=body.model_dump(mode="json", exclude_none=True),
        )
        self._raise_for_status(response)
        data = response.json()
        return RoutineCreated.model_validate(data)
