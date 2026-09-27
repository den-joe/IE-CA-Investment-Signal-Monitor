import os

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field

load_dotenv()

TIER_TAXONOMY = """
1. Direct statement of intent - the company's own press release, earnings
   call, or investor material states expansion into the EU or Ireland
   specifically.
2. Regulatory/structural indicator - EU subsidiary registration, CE marking
   application, trade mission delegation membership.
3. Behavioural proxy - hiring activity for EU/Dublin/European roles on the
   company's own careers page. This is inference, not confirmation.
4. Sector/policy tailwind - general EU-Canada dialogue or CETA developments.
   Context only, never a company-specific signal on its own.
0. Not a signal - the text does not fit any of the four tiers above (e.g.
   generic financial news, unrelated product/software descriptions, or
   any other content with no EU/Ireland expansion relevance).
"""


class TierClassification(BaseModel):
    tier: int = Field(ge=0, le=4)
    justification: str


def classify_tier(signal_text: str) -> TierClassification:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in .env")

    model = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=api_key,
    ).with_structured_output(TierClassification)

    prompt = (
        "Classify the following signal text into exactly one of these "
        f"tiers (use 0 if none genuinely apply):\n{TIER_TAXONOMY}\n"
        f"Signal text: {signal_text!r}\n\n"
        "Return the tier number and a one-line justification. Do not force "
        "a tier of 1-4 onto text that has no real EU/Ireland expansion "
        "relevance - use tier 0 in that case."
    )

    return model.invoke(prompt)
