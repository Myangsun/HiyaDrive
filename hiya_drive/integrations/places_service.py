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
        self,
        cuisine_type: str,
        location: str,
        party_size: int = 2
    ) -> List[Restaurant]:
        """
        Search for restaurants matching criteria.

        Args:
            cuisine_type: Type of cuisine (e.g., "Italian")
            location: Location (e.g., "Boston, MA")
            party_size: Number of people

        Returns:
            List of Restaurant objects
        """
        if not self.api_key:
            logger.warning("Google Places API key not set, returning empty results")
            return []

        try:
            import aiohttp

            query = f"{cuisine_type} restaurants in {location}"
            logger.info(f"Searching Google Places for: {query}")

            # Use Google Places Text Search API
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                "query": query,
                "key": self.api_key,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Google Places API error: {response.status}")
                        return []

                    data = await response.json()

                    if data.get("status") != "OK":
                        logger.warning(f"Google Places API status: {data.get('status')}")
                        return []

                    restaurants = []
                    for result in data.get("results", [])[:5]:  # Top 5 results
                        try:
                            restaurant = Restaurant(
                                name=result.get("name", ""),
                                phone=result.get("formatted_phone_number", ""),
                                address=result.get("formatted_address", ""),
                                rating=result.get("rating", 0.0),
                            )
                            restaurants.append(restaurant)
                        except Exception as e:
                            logger.warning(f"Error parsing restaurant result: {e}")
                            continue

                    logger.info(f"Found {len(restaurants)} restaurants")
                    return restaurants

        except ImportError:
            logger.error("aiohttp not installed. Install: pip install aiohttp")
            return []
        except Exception as e:
            logger.error(f"Error searching restaurants: {e}")
            return []


# Global places service instance
places_service = PlacesService()
