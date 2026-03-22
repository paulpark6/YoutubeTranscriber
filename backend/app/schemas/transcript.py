from pydantic import BaseModel, Field


class TranscriptRequest(BaseModel):
    """Request body for the POST /api/transcript endpoint."""

    urls: list[str] = Field(
        ...,
        min_length=1,
        description="One or more YouTube URLs or 11-character video IDs.",
    )
    include_timestamps: bool = Field(
        default=True,
        description="When True, each transcript line is prefixed with [MM:SS].",
    )
    language: str = Field(
        default="en",
        description="BCP-47 language code for the requested transcript (e.g. 'en', 'es').",
    )
    filename: str | None = Field(
        default=None,
        description=(
            "Custom base filename (without extension) for the downloaded file. "
            "Only honoured when a single URL is provided."
        ),
    )
