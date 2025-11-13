"""
Google Places API integration for restaurant search.
"""

from typing import List
from hiya_drive.models.state import Restaurant
from hiya_drive.config.settings import settings
from hiya_drive.utils.logger import logger


class PlacesService:
    """Integrates with Google Places API."""

    def __init__(self):
        """Initialize Google Places client."""
        self.api_key = settings.google_places_api_key
        self.client = None
        self._init_places()

    def _init_places(self):
        """Initialize Google Places client."""
        try:
            if not self.api_key:
                logger.warning("GOOGLE_PLACES_API_KEY not set")
                return

            logger.info("Google Places API initialized (uses HTTP requests)")

        except Exception as e:
            logger.warning(f"Failed to initialize Google Places: {e}")

    async def search_restaurants(
        self, cuisine_type: str, location: str, party_size: int = 2
    ) -> List[Restaurant]:
        """
        Search for restaurants matching criteria using Google Places API.

        Args:
            cuisine_type: Type of cuisine (e.g., "Italian")
            location: Location (e.g., "Boston, MA")
            party_size: Number of people

        Returns:
            List of Restaurant objects

        Raises:
            ValueError: If API key is not set
            Exception: If Google Places API call fails
        """
        if not self.api_key:
            raise ValueError(
                "GOOGLE_PLACES_API_KEY must be set in .env\n"
                "See setup instructions in README.md for enabling Google Places API"
            )

        try:
            import aiohttp

            query = f"{cuisine_type} restaurants in {location}"
            logger.info(f"Searching Google Places for: {query}")

            # Use Google Places Text Search API (Legacy)
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                "query": query,
                "key": self.api_key,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        raise Exception(
                            f"Google Places API HTTP error: {response.status}"
                        )

                    data = await response.json()

                    if data.get("status") != "OK":
                        error_msg = data.get(
                            "error_message", data.get("status"))
                        raise Exception(
                            f"Google Places API error: {error_msg}\n"
                            "Make sure the Places API is enabled in Google Cloud Console: "
                            "https://console.cloud.google.com/apis/library/places-backend.googleapis.com"
                        )

                    restaurants = []
                    for result in data.get("results", [])[:5]:  # Top 5 results
                        try:
                            # Extract phone number - may require additional Place Details API call
                            phone = result.get("formatted_phone_number", "")

                            # If phone not in text search result, try to get from place_id
                            if not phone and result.get("place_id"):
                                phone = await self._get_phone_from_place_details(
                                    result.get("place_id")
                                )

                            restaurant = Restaurant(
                                name=result.get("name", ""),
                                phone=phone,
                                address=result.get("formatted_address", ""),
                                rating=result.get("rating", 0.0),
                            )

                            if not restaurant.phone:
                                logger.warning(
                                    f"Restaurant '{restaurant.name}' has no phone number. "
                                    "Consider enabling the Place Details API for phone numbers."
                                )

                            restaurants.append(restaurant)
                        except Exception as e:
                            logger.warning(
                                f"Error parsing restaurant result: {e}")
                            continue

                    if not restaurants:
                        raise Exception(
                            f"No restaurants found for '{query}' in Google Places API"
                        )

                    logger.info(f"Found {len(restaurants)} restaurants")
                    return restaurants

        except ImportError:
            raise Exception(
                "aiohttp not installed. Install with: pip install aiohttp"
            )


# Global places service instance
places_service = PlacesService()
