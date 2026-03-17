"""Shared Gemini model configuration for all Strands agents."""

import os

from strands.models.gemini import GeminiModel

MODEL_ID = os.environ.get("GEMINI_MODEL_ID", "gemini-2.5-flash")


def create_model() -> GeminiModel:
    """Create a GeminiModel configured for the current environment.

    On GCP Cloud Run the service-account identity provides Application Default
    Credentials automatically, so we only need to enable the Vertex AI backend
    and point at the right project/region.

    For local development you can either:
      - set GOOGLE_API_KEY to use the Google AI Studio API directly, or
      - run ``gcloud auth application-default login`` so that ADC is available
        and set GOOGLE_CLOUD_PROJECT + GOOGLE_CLOUD_LOCATION.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if api_key:
        return GeminiModel(
            client_args={"api_key": api_key},
            model_id=MODEL_ID,
        )

    return GeminiModel(
        client_args={
            "vertexai": True,
            "project": os.environ.get("GOOGLE_CLOUD_PROJECT"),
            "location": os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
        },
        model_id=MODEL_ID,
    )
