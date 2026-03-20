"""Shared Gemini model configuration for all Strands agents.

Set GOOGLE_API_KEY for local dev, or use Vertex AI on GCP (ADC auto-detected).
"""

from strands.models.gemini import GeminiModel

from server.config import get_settings


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
    s = get_settings()

    if s.google_api_key:
        return GeminiModel(
            client_args={"api_key": s.google_api_key},
            model_id=s.gemini_model_id,
        )

    return GeminiModel(
        client_args={
            "vertexai": True,
            "project": s.google_cloud_project,
            "location": s.google_cloud_location,
        },
        model_id=s.gemini_model_id,
    )
