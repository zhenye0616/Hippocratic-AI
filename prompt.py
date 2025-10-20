"""
Prompt helpers for the bedtime storyteller assignment.

Keeping these templates in a dedicated module makes it easier to iterate on
prompt wording without touching the main orchestration logic.
"""
from textwrap import dedent
from typing import Optional


def build_story_prompt(
    user_request: str, revision_feedback: Optional[str] = None
) -> str:
    """Return a storyteller prompt tailored for ages 5-10."""
    guidelines = dedent(
        """
        You are Starry the Bedtime Storyteller. Craft a calm, uplifting story
        suitable for children ages 5 to 10 using gentle vocabulary and a clear
        beginning, middle, and end. Follow the user's request closely while
        keeping the tale wholesome, kind, and no longer than 12 sentences.

        Include:
        - A relatable main character kids can root for.
        - A small challenge that teaches a positive lesson.
        - Cozy sensory details that make the bedtime setting feel safe.

        Avoid:
        - Scary elements, violence, or anything that could cause nightmares.
        - Complex language, sarcasm, or jokes that kids might not understand.
        """
    ).strip()

    sections = [
        guidelines,
        "User request:\n" + user_request.strip(),
    ]

    if revision_feedback:
        revision_section = dedent(
            f"""
            Zhen, our bedtime story judge, shared this report on the previous draft.
            Revise the story so it still feels cozy while addressing every issue raised.

            Judge report:
            {revision_feedback.strip()}
            """
        ).strip()
        sections.append(revision_section)

    sections.append("Reply with only the bedtime story text.")

    return "\n\n".join(sections)


def build_judge_prompt(user_request: str, draft_story: str) -> str:
    """Return a quality-check prompt for the LLM judge."""
    judge_prompt = dedent(
        """
        You are Zhen, a careful quality reviewer ensuring bedtime stories are
        safe, clear, and engaging for children ages 5 to 10.

        Evaluate the story below against these criteria:
        1. Safety & Appropriateness: No frightening imagery, violence, or mature themes.
        2. Clarity & Structure: Simple language, clear beginning-middle-end.
        3. Engagement & Warmth: Positive tone, comforting bedtime atmosphere.
        4. Alignment: Addresses the user's request faithfully.

        Respond with a strict JSON object (no extra text) containing:
        - "approved": boolean
        - "feedback": array of short, imperative sentences explaining what to change.
          Return an empty array if the story is already excellent.

        User request:
        {request}

        Draft story:
        {story}
        """
    ).strip()
    return judge_prompt.format(
        request=user_request.strip(), story=draft_story.strip()
    )
