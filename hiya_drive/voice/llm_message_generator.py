"""
LLM-based message generator for dynamic voice synthesis.
Uses Claude to generate natural, contextual messages instead of hardcoded strings.
"""

import asyncio
from typing import Optional
import anthropic

from hiya_drive.config.settings import settings
from hiya_drive.utils.logger import logger


class LLMMessageGenerator:
    """Generate dynamic messages using Claude LLM."""

    def __init__(self):
        """Initialize Anthropic client."""
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.llm_model

    async def generate_greeting(self) -> str:
        """Generate a warm greeting message."""
        logger.info("Generating greeting message with LLM")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Generate a brief, warm greeting (1-2 sentences) for HiyaDrive, "
                            "a voice-activated restaurant booking assistant. "
                            "Make it friendly and conversational. Do not use quotes."
                        ),
                    }
                ],
            )

            greeting = message.content[0].text.strip()
            logger.info(f"Generated greeting: {greeting}")
            return greeting

        except Exception as e:
            logger.error(f"Error generating greeting: {e}")
            return "Hello! I'm HiyaDrive. How can I help you today?"

    async def generate_intent_confirmation(
        self,
        party_size: int,
        cuisine_type: str,
        location: str,
        date: str,
        time: str,
    ) -> str:
        """Generate confirmation message for parsed booking intent."""
        logger.info("Generating intent confirmation with LLM")

        try:
            prompt = (
                f"A restaurant booking assistant just parsed a user's request. "
                f"Confirm the details naturally and conversationally (2-3 sentences): "
                f"- Party size: {party_size} people\n"
                f"- Cuisine: {cuisine_type}\n"
                f"- Location: {location}\n"
                f"- Date: {date}\n"
                f"- Time: {time}\n"
                f"Ask if this is correct. Do not use quotes."
            )

            message = self.client.messages.create(
                model=self.model,
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}],
            )

            confirmation = message.content[0].text.strip()
            logger.info(f"Generated intent confirmation: {confirmation}")
            return confirmation

        except Exception as e:
            logger.error(f"Error generating intent confirmation: {e}")
            return (
                f"Perfect! I understand you want to book for {party_size} people "
                f"at a {cuisine_type} restaurant in {location} on {date} at {time}. "
                f"Is that correct?"
            )

    async def generate_calendar_check_message(self, date: str, time: str) -> str:
        """Generate message when checking calendar availability."""
        logger.info("Generating calendar check message with LLM")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Generate a brief message (1 sentence) saying the user is available "
                            f"on {date} at {time}. Be conversational and positive. Do not use quotes."
                        ),
                    }
                ],
            )

            confirmation = message.content[0].text.strip()
            logger.info(f"Generated calendar check message: {confirmation}")
            return confirmation

        except Exception as e:
            logger.error(f"Error generating calendar check message: {e}")
            return f"Great news! You're available on {date} at {time}."

    async def generate_restaurant_found_message(
        self, count: int, cuisine_type: str
    ) -> str:
        """Generate message when restaurants are found."""
        logger.info("Generating restaurant found message with LLM")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Generate a brief, enthusiastic message (1 sentence) announcing "
                            f"that we found {count} {cuisine_type} restaurants. "
                            f"Be conversational. Do not use quotes."
                        ),
                    }
                ],
            )

            announcement = message.content[0].text.strip()
            logger.info(f"Generated restaurant found message: {announcement}")
            return announcement

        except Exception as e:
            logger.error(f"Error generating restaurant found message: {e}")
            return f"Excellent! I found {count} wonderful {cuisine_type} restaurants for you!"

    async def generate_restaurant_option_intro() -> str:
        """Generate intro message for presenting restaurant options."""
        logger.info("Generating restaurant option intro with LLM")

        try:
            message = anthropic.Anthropic(
                api_key=settings.anthropic_api_key
            ).messages.create(
                model=settings.llm_model,
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Generate a brief intro (1 sentence) to present restaurant options. "
                            "Be conversational. Do not use quotes."
                        ),
                    }
                ],
            )

            intro = message.content[0].text.strip()
            logger.info(f"Generated restaurant option intro: {intro}")
            return intro

        except Exception as e:
            logger.error(f"Error generating restaurant option intro: {e}")
            return "Here are the top options for you:"

    async def generate_restaurant_selection_message(
        self, restaurant_name: str, rating: float
    ) -> str:
        """Generate message when selecting a restaurant."""
        logger.info("Generating restaurant selection message with LLM")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Generate a brief message (1 sentence) about booking {restaurant_name} "
                            f"which has a {rating} star rating. Be conversational. Do not use quotes."
                        ),
                    }
                ],
            )

            selection = message.content[0].text.strip()
            logger.info(f"Generated restaurant selection message: {selection}")
            return selection

        except Exception as e:
            logger.error(f"Error generating restaurant selection message: {e}")
            return f"I'm going to book {restaurant_name} for you (rated {rating} stars)."

    async def generate_call_preparation_message(self, restaurant_name: str) -> str:
        """Generate message when preparing to call restaurant."""
        logger.info("Generating call preparation message with LLM")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Generate a brief message (1 sentence) saying we're preparing "
                            f"to call {restaurant_name}. Be conversational. Do not use quotes."
                        ),
                    }
                ],
            )

            preparation = message.content[0].text.strip()
            logger.info(f"Generated call preparation message: {preparation}")
            return preparation

        except Exception as e:
            logger.error(f"Error generating call preparation message: {e}")
            return f"Let me prepare what I'll say to {restaurant_name}."

    async def generate_call_initiation_message(self, restaurant_name: str) -> str:
        """Generate message when initiating call."""
        logger.info("Generating call initiation message with LLM")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Generate a brief message (1 sentence) saying we're now calling {restaurant_name}. "
                            f"Be conversational. Do not use quotes."
                        ),
                    }
                ],
            )

            initiation = message.content[0].text.strip()
            logger.info(f"Generated call initiation message: {initiation}")
            return initiation

        except Exception as e:
            logger.error(f"Error generating call initiation message: {e}")
            return f"Now I'm calling {restaurant_name}..."

    async def generate_booking_confirmation(
        self,
        restaurant_name: str,
        party_size: int,
        date: str,
        time: str,
        confirmation_number: str,
    ) -> str:
        """Generate final booking confirmation message."""
        logger.info("Generating booking confirmation with LLM")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Generate a warm, congratulatory booking confirmation message (2-3 sentences) with: "
                            f"- Restaurant: {restaurant_name}\n"
                            f"- Party size: {party_size} people\n"
                            f"- Date: {date}\n"
                            f"- Time: {time}\n"
                            f"- Confirmation number: {confirmation_number}\n"
                            f"Be conversational and congratulatory. Do not use quotes."
                        ),
                    }
                ],
            )

            confirmation = message.content[0].text.strip()
            logger.info(f"Generated booking confirmation: {confirmation}")
            return confirmation

        except Exception as e:
            logger.error(f"Error generating booking confirmation: {e}")
            return (
                f"Your reservation is confirmed at {restaurant_name} "
                f"for {party_size} people on {date} at {time}. "
                f"Confirmation number is {confirmation_number}."
            )

    async def generate_goodbye(self) -> str:
        """Generate a friendly goodbye message."""
        logger.info("Generating goodbye message with LLM")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Generate a brief, warm goodbye message (1 sentence) from HiyaDrive "
                            "wishing the user a great dining experience. Be friendly. Do not use quotes."
                        ),
                    }
                ],
            )

            goodbye = message.content[0].text.strip()
            logger.info(f"Generated goodbye: {goodbye}")
            return goodbye

        except Exception as e:
            logger.error(f"Error generating goodbye: {e}")
            return "Thanks for using HiyaDrive! Enjoy your meal!"

    async def generate_confirmation_request(self, step_name: str) -> str:
        """Generate a confirmation request for a specific step."""
        logger.info(f"Generating confirmation request for {step_name}")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Generate a brief request (1 sentence) asking the user to confirm "
                            f"the {step_name} step. Be conversational. Do not use quotes."
                        ),
                    }
                ],
            )

            request = message.content[0].text.strip()
            logger.info(f"Generated confirmation request: {request}")
            return request

        except Exception as e:
            logger.error(f"Error generating confirmation request: {e}")
            return f"Does this {step_name} look good to you?"

    async def extract_intent_from_response(
        self,
        user_response: str,
        current_party_size: Optional[int] = None,
        current_cuisine: Optional[str] = None,
        current_location: Optional[str] = None,
        current_date: Optional[str] = None,
        current_time: Optional[str] = None,
    ) -> dict:
        """
        Extract booking intent changes from free-form user response.
        Uses Claude to understand natural corrections like "Actually I want 3 people" or "downtown is better".

        Returns dict with keys: party_size, cuisine_type, location, date, time, is_confirmed (bool)
        """
        logger.info(f"Extracting intent from response: {user_response}")

        try:
            current_state = f"""
Current booking state:
- Party size: {current_party_size}
- Cuisine: {current_cuisine}
- Location: {current_location}
- Date: {current_date}
- Time: {current_time}
"""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Analyze this user response and determine if they're confirming or changing their booking details.

{current_state}

User said: "{user_response}"

Return JSON with:
- is_confirmed: true if user approves (yes, sounds good, let's go, etc.), false if they want changes
- party_size: number if mentioned or correction, else null
- cuisine_type: cuisine if mentioned or correction, else null
- location: location if mentioned or correction, else null
- date: date if mentioned or correction, else null
- time: time if mentioned or correction, else null
- feedback: brief note about what changed (empty string if confirming)

Be strict: only extract clear corrections. "2." alone doesn't change party size.""",
                    }
                ],
            )

            import json
            result_text = message.content[0].text.strip()

            # Try to parse JSON
            try:
                # Find JSON block in response
                start_idx = result_text.find('{')
                end_idx = result_text.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = result_text[start_idx:end_idx]
                    result = json.loads(json_str)
                else:
                    result = json.loads(result_text)
            except json.JSONDecodeError:
                # Fallback: assume confirmation if we can't parse
                logger.warning(f"Could not parse response JSON: {result_text}")
                result = {"is_confirmed": True, "feedback": "Could not parse response"}

            logger.info(f"Extracted intent changes: {result}")
            return result

        except Exception as e:
            logger.error(f"Error extracting intent from response: {e}")
            return {"is_confirmed": True, "feedback": "Error parsing response, proceeding"}

    async def generate_clarification_question(
        self, missing_fields: list, current_details: dict
    ) -> str:
        """
        Generate a natural clarification question for missing booking details.
        E.g., if location is missing, ask "What area would you prefer?"
        """
        logger.info(f"Generating clarification for missing fields: {missing_fields}")

        try:
            fields_str = ", ".join(missing_fields)
            message = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Generate a brief, natural question to ask the user for missing booking details: {fields_str}. "
                            f"Current details: {current_details}. "
                            f"Be conversational and combine questions if possible. Do not use quotes."
                        ),
                    }
                ],
            )

            question = message.content[0].text.strip()
            logger.info(f"Generated clarification: {question}")
            return question

        except Exception as e:
            logger.error(f"Error generating clarification: {e}")
            return f"Can you please tell me the {', '.join(missing_fields)}?"


# Global message generator instance
message_generator = LLMMessageGenerator()
