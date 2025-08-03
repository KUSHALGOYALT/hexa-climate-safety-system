import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def reverse_geocode(latitude, longitude):
    """
    Reverse geocode coordinates to get address information
    Uses OpenStreetMap Nominatim API (free)
    """
    try:
        url = f"https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json',
            'addressdetails': 1,
            'zoom': 18
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('error'):
            logger.error(f"Reverse geocoding error: {data['error']}")
            return None
            
        address = data.get('address', {})
        
        # Extract address components
        result = {
            'address': data.get('display_name', ''),
            'city': address.get('city') or address.get('town') or address.get('village') or '',
            'state': address.get('state') or '',
            'country': address.get('country') or '',
            'postal_code': address.get('postcode') or '',
            'latitude': latitude,
            'longitude': longitude
        }
        
        return result
        
    except requests.RequestException as e:
        logger.error(f"Reverse geocoding request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Reverse geocoding error: {e}")
        return None

def validate_coordinates(latitude, longitude):
    """
    Validate latitude and longitude coordinates
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
        
        if not (-90 <= lat <= 90):
            return False, "Latitude must be between -90 and 90"
            
        if not (-180 <= lon <= 180):
            return False, "Longitude must be between -180 and 180"
            
        return True, None
        
    except (ValueError, TypeError):
        return False, "Invalid coordinate format"

def geocode_address(address):
    """
    Geocode address to get coordinates
    Uses OpenStreetMap Nominatim API (free)
    """
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            logger.error(f"No results found for address: {address}")
            return None
            
        result = data[0]
        
        # Extract coordinates and address components
        coordinates = {
            'latitude': float(result['lat']),
            'longitude': float(result['lon']),
            'address': result.get('display_name', ''),
            'city': result.get('address', {}).get('city') or result.get('address', {}).get('town') or result.get('address', {}).get('village') or '',
            'state': result.get('address', {}).get('state') or '',
            'country': result.get('address', {}).get('country') or '',
            'postal_code': result.get('address', {}).get('postcode') or ''
        }
        
        return coordinates
        
    except requests.RequestException as e:
        logger.error(f"Geocoding request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return None 