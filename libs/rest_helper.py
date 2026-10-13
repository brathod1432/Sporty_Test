"""Simple REST helper for API testing.

Built on `requests` + `libs.logger`. Five small functions, one response
object, one error class. Nothing fancy.

Example:
    from libs.rest_helper import send_get, send_request

    res = send_get("https://example.com/api/matches",
                   headers={"x-user-id": "me"})
    print(res.status_code, res.body)

    res = send_request("post", "https://example.com/api/place-bet",
                       headers={"x-user-id": "me"},
                       json={"matchId": "m1", "selection": "HOME", "stake": 10},
                       raiseError=False)
    print(res.json_dump())
"""
from __future__ import annotations
__author__ = "Brijesh Rathod [bgrathod00@gmail.com]"

import json as json_lib
import time
from dataclasses import dataclass
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from libs.logger import get_logger

logger = get_logger("RestHelper")

# Common constants — tweak once, applies everywhere.
DEFAULT_TIMEOUT: float = 30.0
DEFAULT_AUTH_SCHEME: str = "Bearer"
SUPPORTED_METHODS: tuple[str, ...] = ("GET", "POST", "PUT", "PATCH", "DELETE")
BODY_METHODS: tuple[str, ...] = ("POST", "PUT", "PATCH")


class RestRequestError(Exception):
    """Raised when a request fails and raiseError=True.

    Attributes:
        response: Parsed response if the server answered, else None.
        status_code: HTTP status (0 = never reached the server).
    """

    def __init__(self, message: str, response: RestResponse | None = None, status_code: int = 0) -> None:
        super().__init__(message)
        self.response = response
        self.status_code = status_code


@dataclass
class RestResponse:
    """Plain response object — status code plus full body."""

    method: str
    url: str
    status_code: int
    reason: str
    headers: dict[str, str]
    body: Any
    raw_text: str
    elapsed_ms: float
    ok: bool

    def to_dict(self) -> dict[str, Any]:
        """Response as a plain dict (easy to pick fields from)."""
        return {
            "method": self.method,
            "url": self.url,
            "status_code": self.status_code,
            "reason": self.reason,
            "headers": self.headers,
            "body": self.body,
            "raw_text": self.raw_text,
            "elapsed_ms": self.elapsed_ms,
            "ok": self.ok,
        }

    def json_dump(self, indent: int = 2) -> str:
        """Whole response as a JSON string (easy to log or save)."""
        return json_lib.dumps(self.to_dict(), indent=indent, default=str)


def _request(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json: Any | None = None,
    data: Any | None = None,
    username: str | None = None,
    password: str | None = None,
    token: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    verify: bool = True,
    raiseError: bool = True,
) -> RestResponse:
    """Single internal function every helper below uses."""
    name = method.upper()
    final_headers = dict(headers) if headers else {}
    auth: HTTPBasicAuth | None = None

    # Explicit header wins, then token, then username/password.
    if "Authorization" not in final_headers and "authorization" not in final_headers:
        if token:
            final_headers["Authorization"] = f"{DEFAULT_AUTH_SCHEME} {token}"
        elif username and password:
            auth = HTTPBasicAuth(username, password)

    logger.info(f"{name} {url}")
    start = time.perf_counter()
    try:
        raw = requests.request(
            name, url,
            headers=final_headers, params=params, json=json, data=data,
            auth=auth, timeout=timeout, verify=verify,
        )
    except requests.RequestException as exc:
        spent = (time.perf_counter() - start) * 1000
        logger.warning(f"{name} {url} -> FAILED ({type(exc).__name__})")
        if raiseError:
            raise RestRequestError(f"{name} {url} failed: {exc}", status_code=0) from exc
        return RestResponse(name, url, 0, type(exc).__name__, {}, str(exc), str(exc), spent, False)

    spent = (time.perf_counter() - start) * 1000
    try:
        body: Any = raw.json()
    except ValueError:
        body = raw.text
    res = RestResponse(
        method=name, url=raw.url, status_code=raw.status_code,
        reason=raw.reason or "", headers=dict(raw.headers),
        body=body, raw_text=raw.text, elapsed_ms=spent, ok=raw.ok,
    )
    logger.info(f"{name} {url} -> {res.status_code} ({spent:.0f}ms)")
    if not res.ok and raiseError:
        raise RestRequestError(f"{name} {url} -> HTTP {res.status_code}", response=res, status_code=res.status_code)
    return res


def send_get(
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    username: str | None = None,
    password: str | None = None,
    token: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    verify: bool = True,
    raiseError: bool = True,
) -> RestResponse:
    """Send a GET request."""
    return _request("GET", url, headers=headers, params=params, username=username,
                    password=password, token=token, timeout=timeout, verify=verify, raiseError=raiseError)


def send_post(
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json: Any | None = None,
    data: Any | None = None,
    username: str | None = None,
    password: str | None = None,
    token: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    verify: bool = True,
    raiseError: bool = True,
) -> RestResponse:
    """Send a POST request (json= dict for JSON body, data= for form body)."""
    return _request("POST", url, headers=headers, params=params, json=json, data=data,
                    username=username, password=password, token=token,
                    timeout=timeout, verify=verify, raiseError=raiseError)


def send_patch(
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json: Any | None = None,
    data: Any | None = None,
    username: str | None = None,
    password: str | None = None,
    token: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    verify: bool = True,
    raiseError: bool = True,
) -> RestResponse:
    """Send a PATCH request. Same args as send_post."""
    return _request("PATCH", url, headers=headers, params=params, json=json, data=data,
                    username=username, password=password, token=token,
                    timeout=timeout, verify=verify, raiseError=raiseError)


def send_delete(
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    username: str | None = None,
    password: str | None = None,
    token: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    verify: bool = True,
    raiseError: bool = True,
) -> RestResponse:
    """Send a DELETE request. Same args as send_get."""
    return _request("DELETE", url, headers=headers, params=params, username=username,
                    password=password, token=token, timeout=timeout, verify=verify, raiseError=raiseError)


def send_put(
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json: Any | None = None,
    data: Any | None = None,
    username: str | None = None,
    password: str | None = None,
    token: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    verify: bool = True,
    raiseError: bool = True,
) -> RestResponse:
    """Send a PUT request. Same args as send_post."""
    return _request("PUT", url, headers=headers, params=params, json=json, data=data,
                    username=username, password=password, token=token,
                    timeout=timeout, verify=verify, raiseError=raiseError)


def send_request(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json: Any | None = None,
    data: Any | None = None,
    username: str | None = None,
    password: str | None = None,
    token: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    verify: bool = True,
    raiseError: bool = True,
) -> RestResponse:
    """Send any HTTP request by naming the method instead of calling send_get/send_post.

    Dispatcher for the five supported verbs. Every argument is spelled out here, so
    this is the single place to read for the full contract - no need to open each
    send_* helper to learn what a parameter does.

    Args:
        method: HTTP verb, case-insensitive - "GET", "POST", "PUT", "PATCH", "DELETE".
        url: Full URL including scheme, host and path, e.g. "https://host/api/balance".
        headers: Request headers as a dict. An explicit "Authorization" key here wins
            over the token/username arguments below.
        params: Query-string parameters, e.g. {"user-id": "abc"}. Ignored for methods
            that carry a body.
        json: Object serialised as a JSON request body. Mutually exclusive with `data`.
            Only sent for POST/PUT/PATCH - ignored on GET and DELETE, which have no body.
        data: Raw body - a dict (form-encoded) or a string. Use for malformed-body tests.
            Only sent for POST/PUT/PATCH - ignored on GET and DELETE, which have no body.
        username: HTTP Basic username. Used only when `password` is also given and no
            explicit Authorization header and no `token` are supplied.
        password: HTTP Basic password. Pairs with `username`.
        token: Bearer token. Sent as "Authorization: Bearer <token>" (scheme from
            DEFAULT_AUTH_SCHEME). Takes precedence over username/password.
        timeout: Seconds to wait before giving up. Defaults to DEFAULT_TIMEOUT (30.0).
        verify: Verify the server's TLS certificate. Set False only against self-signed
            local servers.
        raiseError: When True (default) a non-2xx response or a transport failure raises
            RestRequestError. When False the RestResponse is returned either way, with
            status_code 0 for a transport failure - use this to assert on error codes.

    Returns:
        A RestResponse carrying the status code, parsed body (JSON when possible, else
        raw text), headers and elapsed time.

    Raises:
        ValueError: when `method` is not one of SUPPORTED_METHODS.
        RestRequestError: on a transport failure or non-2xx status when raiseError=True.

    Example:
        res = send_request("get", "https://host/api/balance",
                           headers={"x-user-id": "me"}, raiseError=False)
        assert res.status_code == 200

        res = send_request("post", "https://host/api/place-bet",
                           headers={"x-user-id": "me"},
                           json={"matchId": "m1", "selection": "HOME", "stake": 10},
                           raiseError=False)
    """
    name = method.upper()
    helpers: dict[str, Any] = {
        "GET": send_get, "POST": send_post, "PUT": send_put,
        "PATCH": send_patch, "DELETE": send_delete,
    }
    if name not in helpers:
        msg = f"Unknown method '{method}'. Use one of: {', '.join(SUPPORTED_METHODS)}"
        logger.error(msg)
        raise ValueError(msg)

    # GET and DELETE carry no body, so their helpers have no json/data parameter.
    # Only forward a body to the verbs that accept one.
    if name in BODY_METHODS:
        return helpers[name](url, headers=headers, params=params, json=json, data=data,
                             username=username, password=password, token=token,
                             timeout=timeout, verify=verify, raiseError=raiseError)
    return helpers[name](url, headers=headers, params=params,
                         username=username, password=password, token=token,
                         timeout=timeout, verify=verify, raiseError=raiseError)


__all__ = [
    "BODY_METHODS",
    "DEFAULT_TIMEOUT",
    "DEFAULT_AUTH_SCHEME",
    "SUPPORTED_METHODS",
    "RestResponse",
    "RestRequestError",
    "send_get",
    "send_post",
    "send_put",
    "send_patch",
    "send_delete",
    "send_request",
]
