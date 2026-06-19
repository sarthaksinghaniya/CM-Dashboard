from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class GeoTagger:
    """
    Extracts geographic location from text or validates provided lat/lon.
    Uses simple heuristic mapping for the zero-shot prototype.
    """
    
    def __init__(self):
        # Mock geographic mapping for NYC areas (Lat, Lon)
        self.mock_mapping = {
            "5th avenue": (40.7750, -73.9654),
            "downtown": (40.7128, -74.0060),
            "brooklyn": (40.6782, -73.9442),
            "queens": (40.7282, -73.7949),
            "bronx": (40.8448, -73.8648),
            "staten island": (40.5795, -74.1502),
            "central park": (40.7812, -73.9665)
        }
        
    def extract_location(self, text: str, lat: Optional[float] = None, lon: Optional[float] = None, area_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns a standardized location block.
        If lat/lon are provided, it trusts them.
        Otherwise, it infers them from text.
        """
        if lat is not None and lon is not None:
            return {
                "lat": float(lat),
                "lon": float(lon),
                "area_name": area_name or "Unknown Area (Manual GPS)"
            }
            
        text_lower = text.lower()
        for area, coords in self.mock_mapping.items():
            if area in text_lower:
                logger.info(f"GeoTagger: Matched location '{area}' from text.")
                return {
                    "lat": coords[0],
                    "lon": coords[1],
                    "area_name": area.title()
                }
                
        # Default fallback if no location is found
        logger.info("GeoTagger: No location found, defaulting to generic region.")
        return {
            "lat": 40.7128,
            "lon": -74.0060,
            "area_name": "Generic Downtown"
        }
