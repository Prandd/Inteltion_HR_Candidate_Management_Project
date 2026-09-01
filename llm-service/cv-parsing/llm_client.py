"""
llm_client.py — Azure OpenAI call wrapper.

Reads config from environment variables exactly as documented in the
project README (Section 4.3):
    CV_SCORING_PROVIDER
    AZURE_OPENAI_ENDPOINT
    AZURE_OPENAI_API_KEY
    AZURE_OPENAI_DEPLOYMENT

Uses JSON mode (response_format={"type": "json_object"}) — per Section 2.3
of the sprint plan, this alone eliminates most malformed-JSON failures
before the repair layer even has to run.

IMPORTANT — which OpenAI client class this uses, and why:
Azure now issues two different endpoint shapes for OpenAI/Foundry
resources:
    (a) Legacy: https://<resource>.openai.azure.com/
        -> paired with the `AzureOpenAI` client + an explicit
           `api_version` (the SDK appends /openai/deployments/{name}/...
           itself).
    (b) Current (GA): https://<resource>.openai.azure.com/openai/v1/
        (or the Foundry-project form
        https://<resource>.services.ai.azure.com/openai/v1)
        -> this is an *implicitly versioned*, OpenAI-compatible route.
           Per Microsoft's docs, this shape is used with the plain
           `OpenAI` client (`base_url=<endpoint>`, no `api_version`),
           NOT `AzureOpenAI`. Pointing `AzureOpenAI` at a `/openai/v1`
           endpoint double-appends the deployments path and returns a
           404 "Resource not found" — that's the failure this module
           previously hit.
This module detects shape (b) by checking for "/openai/v1" in the
configured endpoint and picks the matching client automatically, so the
same code works for either style of endpoint without a team-wide config
migration.
"""
from __future__ import annotations

import os
import time
from typing import List, Optional

# Only used for the legacy (a) endpoint shape. Bump deliberately if the
# team decides to move to a newer preview version.
LEGACY_AZURE_OPENAI_API_VERSION = "2024-08-01-preview"


class LLMConfigError(EnvironmentError):
    """Raised when required Azure OpenAI environment variables are missing."""


class LLMCallError(RuntimeError):
    """Raised when the LLM call fails after all retries."""


def _get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise LLMConfigError(
            f"Missing required environment variable '{name}'. "
            f"See README.md Section 4 for setup."
        )
    return value


def _build_client():
    """Lazily constructs the right OpenAI client for the configured
    endpoint shape, so this module can be imported (e.g., for
    unit-testing other functions) even in environments where the
    `openai` package isn't installed yet."""
    provider = os.environ.get("CV_SCORING_PROVIDER", "azure_openai")
    if provider != "azure_openai":
        raise LLMConfigError(
            f"CV_SCORING_PROVIDER='{provider}' is not supported by this "
            f"module yet — only 'azure_openai' is implemented."
        )

    endpoint = _get_required_env("AZURE_OPENAI_ENDPOINT").rstrip("/")
    api_key = _get_required_env("AZURE_OPENAI_API_KEY")
    deployment = _get_required_env("AZURE_OPENAI_DEPLOYMENT")

    if "/openai/v1" in endpoint:
        # Current GA endpoint shape — implicit versioning, plain OpenAI client.
        try:
            from openai import OpenAI
        except ImportError as e:
            raise RuntimeError(
                "The 'openai' package is not installed. Run: pip install openai"
            ) from e
        client = OpenAI(base_url=endpoint, api_key=api_key)
    else:
        # Legacy endpoint shape — AzureOpenAI client, explicit api_version.
        try:
            from openai import AzureOpenAI
        except ImportError as e:
            raise RuntimeError(
                "The 'openai' package is not installed. Run: pip install openai"
            ) from e
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=LEGACY_AZURE_OPENAI_API_VERSION,
        )

    return client, deployment


def call_llm_json(
    messages: List[dict],
    *,
    max_retries: int = 1,
    temperature: int = 1,
    max_completion_tokens: int = 2000,
    retry_backoff_seconds: float = 1.5,
) -> str:
    """Calls Azure OpenAI's chat completions endpoint in JSON mode.

    Args:
        messages: full chat message list (system/user/assistant turns).
        max_retries: number of retries AFTER the first attempt (so
            max_retries=1 means "try once, retry once on failure" —
            matches the sprint plan's "retry once" repair strategy).
        temperature: kept low for consistent structured output.
        max_completion_tokens: generous enough for a full candidate profile; raise
            if you see truncated JSON on long CVs with many roles.
        retry_backoff_seconds: base backoff between retries.

    Returns:
        The raw JSON string returned by the model (not yet parsed).

    Raises:
        LLMConfigError: missing/invalid environment configuration.
        LLMCallError: the call failed on every attempt.
    """
    client, deployment = _build_client()

    last_error: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=deployment,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=temperature,
                max_completion_tokens=max_completion_tokens,
            )
            content = response.choices[0].message.content
            if not content or not content.strip():
                raise LLMCallError("Model returned an empty response body.")
            return content
        except Exception as e:  # noqa: BLE001 - intentionally broad; we retry then wrap
            last_error = e
            if attempt < max_retries:
                time.sleep(retry_backoff_seconds * (attempt + 1))

    error_str = str(last_error)
    hint = ""
    if "404" in error_str:
        hint = (
            " HINT: A 404 from Azure OpenAI usually means the endpoint/deployment/"
            "api-version combination doesn't resolve to a real resource — check that "
            "AZURE_OPENAI_DEPLOYMENT is the exact deployment name (not the model name) "
            "from Azure AI Foundry, and that AZURE_OPENAI_ENDPOINT has no typos. "
            "Run check_azure_config.py to diagnose."
        )
    elif "401" in error_str or "403" in error_str:
        hint = " HINT: This looks like an authentication error — verify AZURE_OPENAI_API_KEY."

    raise LLMCallError(
        f"LLM call failed after {max_retries + 1} attempt(s): {last_error}.{hint}"
    ) from last_error
