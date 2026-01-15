from __future__ import annotations

import pytest
import requests
import responses

from package_comparison_tool.api import ALT_RDB_API_BASE, fetch_branch_binary_packages
from package_comparison_tool.exceptions import AltApiError, BranchNotFoundError


def _sample_payload() -> dict[str, object]:
    return {
        "packages": [
            {
                "name": "pkg",
                "epoch": 0,
                "version": "1",
                "release": "1",
                "arch": "x86_64",
                "buildtime": 0,
                "disttag": "",
            }
        ]
    }


@responses.activate
def test_fetch_branch_binary_packages_raises_on_404() -> None:
    branch = "missing"
    url = f"{ALT_RDB_API_BASE}/branch_binary_packages/{branch}"
    responses.add(responses.GET, url, status=404)

    with pytest.raises(BranchNotFoundError), requests.Session() as sess:
        fetch_branch_binary_packages(branch, session=sess, retries=1)


@responses.activate
def test_fetch_branch_binary_packages_invalid_json() -> None:
    branch = "sisyphus"
    url = f"{ALT_RDB_API_BASE}/branch_binary_packages/{branch}"
    responses.add(responses.GET, url, body="not-json", status=200)

    with pytest.raises(AltApiError):
        fetch_branch_binary_packages(branch, retries=1)


def test_fetch_branch_binary_packages_retries_timeout(monkeypatch) -> None:
    calls: list[int] = []

    class TimeoutSession(requests.Session):
        def get(self, *args, **kwargs):
            calls.append(1)
            raise requests.Timeout("boom")

    monkeypatch.setattr("package_comparison_tool.api.time.sleep", lambda _delay: None)

    with TimeoutSession() as sess, pytest.raises(AltApiError):
        fetch_branch_binary_packages("sisyphus", session=sess, retries=3, retry_backoff=0)

    assert len(calls) == 3  # retries respected


@responses.activate
def test_user_agent_respected_with_custom_session() -> None:
    branch = "sisyphus"
    url = f"{ALT_RDB_API_BASE}/branch_binary_packages/{branch}"
    responses.add(responses.GET, url, json=_sample_payload(), status=200)

    with requests.Session() as sess:
        sess.headers.update({"User-Agent": "session-UA"})
        fetch_branch_binary_packages(branch, session=sess, user_agent="custom-UA", retries=1)

    sent_headers = responses.calls[0].request.headers
    assert sent_headers["User-Agent"] == "custom-UA"


@responses.activate
def test_explicit_headers_override_user_agent_and_merge_session_headers() -> None:
    branch = "sisyphus"
    url = f"{ALT_RDB_API_BASE}/branch_binary_packages/{branch}"
    responses.add(responses.GET, url, json=_sample_payload(), status=200)

    with requests.Session() as sess:
        sess.headers.update({"User-Agent": "session-UA", "X-From-Session": "yes"})
        fetch_branch_binary_packages(
            branch,
            session=sess,
            user_agent="custom-UA",
            headers={"User-Agent": "explicit-UA", "X-Test": "1"},
            retries=1,
        )

    sent_headers = responses.calls[0].request.headers
    assert sent_headers["User-Agent"] == "explicit-UA"  # explicit headers win
    assert sent_headers["X-Test"] == "1"
    assert sent_headers["X-From-Session"] == "yes"
