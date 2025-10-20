import json
import os
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI
from prompt import build_judge_prompt, build_story_prompt

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

In the next two hours, I’d focus on hardening and validating the flow:
1. Wrap the OpenAI calls with retries, timeouts, structured logging, and a graceful fallback if every attempt fails.
2. Add a couple of fast unit tests that mock the judge/story prompts to lock down the JSON contract.
3. Expose a lightweight config layer so model, temperature, and max rounds come from env vars.
"""
load_dotenv()


def call_model(prompt: str, max_tokens=3000, temperature=0.0) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing OPENAI_API_KEY. Please set it in your environment or .env file."
        )
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message.content  # type: ignore


def generate_story(
    user_request: str, revision_feedback: Optional[str] = None
) -> str:
    """Call the storyteller prompt."""
    story_prompt = build_story_prompt(user_request, revision_feedback)
    return call_model(story_prompt, max_tokens=450, temperature=0.6)


def judge_story(user_request: str, story: str) -> Tuple[Dict[str, Any], str]:
    """Ask the judge for detailed feedback."""
    judge_prompt = build_judge_prompt(user_request, story)
    raw_feedback = call_model(judge_prompt, max_tokens=600, temperature=0.0)
    try:
        parsed_feedback = json.loads(raw_feedback)
    except json.JSONDecodeError:
        parsed_feedback = {
            "approved": False,
            "feedback": ["Judge response was not valid JSON."],
            "raw_response": raw_feedback,
        }
        return parsed_feedback, raw_feedback

    feedback_field = parsed_feedback.get("feedback")
    if isinstance(feedback_field, list):
        parsed_feedback["feedback"] = [
            item.strip() for item in feedback_field if isinstance(item, str) and item.strip()
        ]
    elif isinstance(feedback_field, str) and feedback_field.strip():
        parsed_feedback["feedback"] = [feedback_field.strip()]
    else:
        parsed_feedback["feedback"] = []

    if "raw_response" not in parsed_feedback:
        parsed_feedback["raw_response"] = raw_feedback

    return parsed_feedback, raw_feedback


def prepare_revision_notes(judge_result: Dict[str, Any], raw_judge: str) -> str:
    """Blend judge feedback and raw report for the storyteller."""
    notes: List[str] = []
    feedback = judge_result.get("feedback")

    if isinstance(feedback, list):
        notes = [item.strip() for item in feedback if isinstance(item, str) and item.strip()]
    elif isinstance(feedback, str) and feedback.strip():
        notes = [feedback.strip()]

    parts: List[str] = []
    if notes:
        bullet_points = "\n".join(f"- {note}" for note in notes)
        parts.append("Action items from Luna:\n" + bullet_points)

    parts.append("Full judge report JSON:\n" + raw_judge.strip())
    return "\n\n".join(parts).strip()


def storytelling_session(
    user_request: str, max_rounds: int = 3
) -> Tuple[str, bool, Dict[str, Any], str, int]:
    """Iteratively generate and refine a story until approved or retries exhausted."""
    revision_notes: Optional[str] = None
    last_story = ""
    last_judge: Dict[str, Any] = {}
    last_raw = ""
    attempt = 0

    for attempt in range(1, max_rounds + 1):
        last_story = generate_story(user_request, revision_notes)
        last_judge, last_raw = judge_story(user_request, last_story)
        approved_flag = last_judge.get("approved")

        if isinstance(approved_flag, bool) and approved_flag:
            return last_story, True, last_judge, last_raw, attempt

        revision_notes = prepare_revision_notes(last_judge, last_raw)

    return last_story, False, last_judge, last_raw, attempt


def main():
    user_input = input("What kind of story do you want to hear? ")
    if not user_input.strip():
        print("Please share a short prompt for the bedtime story.")
        return

    story, approved_flag, judge_result, raw_judge, rounds_taken = storytelling_session(
        user_input, max_rounds=3
    )

    print("\nHere is your bedtime story:\n")
    print(story)

    if rounds_taken > 1:
        print(f"\n(Story refined with {rounds_taken} rounds.)")

    if not approved_flag:
        print("\nLuna still sees room for improvement after the final round.")
        feedback_notes = judge_result.get("feedback", [])
        if isinstance(feedback_notes, list) and feedback_notes:
            print("Latest suggestions:")
            for note in feedback_notes:
                print(f"- {note}")
        print("\nJudge report:")
        print(raw_judge.strip())


if __name__ == "__main__":
    main()
