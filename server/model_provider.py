"""GCP Vertex AI / Gemini model provider configuration for Strands agents."""

import os

from strands.models.gemini import GeminiModel

# Default model — can be overridden via environment variable.
DEFAULT_MODEL_ID = "gemini-2.5-flash"


def create_model() -> GeminiModel:
    """Create a GeminiModel configured for the current environment.

    On Cloud Run the service account's Application Default Credentials are used
    automatically.  For local development, set GOOGLE_API_KEY or run
    ``gcloud auth application-default login``.
    """
    model_id = os.environ.get("GEMINI_MODEL_ID", DEFAULT_MODEL_ID)

    client_args: dict = {}
    api_key = os.environ.get("GOOGLE_API_KEY")
    if api_key:
        client_args["api_key"] = api_key

    return GeminiModel(
        client_args=client_args or None,
        model_id=model_id,
    )
