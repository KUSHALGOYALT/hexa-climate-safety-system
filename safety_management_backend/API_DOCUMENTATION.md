# Safety Management Backend API Documentation

## Base URL
`http://127.0.0.1:8000/api/v1/`

## Sites API

### Get Available Companies
**GET** `/sites/available-companies/`

Returns list of available companies for site creation.

**Response:**
```json
{
    "companies": [
        {
            "id": 1,
            "name": "Sample Power Company",
            "company_code": "SPC001"
        }
    ]
}
```

### Create New Site
**POST** `/sites/`

**Required Fields:**
- `company` (integer) - Company ID
- `name` (string) - Site name
- `site_code` (string) - Unique site code (alphanumeric only)
- `address` (string) - Full address
- `city` (string) - City name
- `state` (string) - State name
- `postal_code` (string) - Postal code
- `latitude` (decimal) - Latitude coordinate (-90 to 90)
- `longitude` (decimal) - Longitude coordinate (-180 to 180)
- `phone` (string) - Phone number
- `email` (string) - Valid email address

**Optional Fields:**
- `description` (string) - Site description
- `plant_type` (string) - Type of power plant (SOLAR, WIND, THERMAL, etc.)
- `capacity` (string) - Plant capacity (e.g., "50 MWp")
- `operational_status` (string) - Default: "OPERATIONAL"

**Example Request:**
```json
{
    "company": 1,
    "name": "Solar Plant 1",
    "site_code": "SPL001",
    "description": "Main solar power plant",
    "address": "Solar Farm Road",
    "city": "Mumbai",
    "state": "Maharashtra",
    "postal_code": "400001",
    "latitude": 19.0760,
    "longitude": 72.8777,
    "phone": "+91-22-12345678",
    "email": "solar@spl001.com",
    "plant_type": "SOLAR",
    "capacity": "50 MWp"
}
```

**Example Response:**
```json
{
    "id": 1,
    "company_name": "Sample Power Company",
    "company_code": "SPC001",
    "name": "Solar Plant 1",
    "site_code": "SPL001",
    "description": "Main solar power plant",
    "address": "Solar Farm Road",
    "city": "Mumbai",
    "state": "Maharashtra",
    "country": "India",
    "country_code": "IND",
    "postal_code": "400001",
    "latitude": "19.0760000",
    "longitude": "72.8777000",
    "phone": "+91-22-12345678",
    "email": "solar@spl001.com",
    "plant_type": "SOLAR",
    "capacity": "50 MWp",
    "operational_status": "OPERATIONAL",
    "is_active": true
}
```

### Get All Sites
**GET** `/sites/`

Returns paginated list of all sites.

### Get Specific Site
**GET** `/sites/{id}/`

Returns detailed information about a specific site.

### Update Site
**PUT** `/sites/{id}/` or **PATCH** `/sites/{id}/`

Update site information.

### Delete Site
**DELETE** `/sites/{id}/`

Soft delete (sets is_active to false).

## Error Handling

### Validation Errors
When required fields are missing or invalid, the API returns a 400 Bad Request with detailed error messages:

```json
{
    "company": ["This field is required."],
    "name": ["This field is required."],
    "site_code": ["This field is required."],
    "address": ["This field is required."],
    "city": ["This field is required."],
    "state": ["This field is required."],
    "postal_code": ["This field is required."],
    "latitude": ["This field is required."],
    "longitude": ["This field is required."],
    "phone": ["This field is required."],
    "email": ["This field is required."]
}
```

### Common Error Scenarios
1. **Missing Company**: Ensure company ID exists and is active
2. **Invalid Coordinates**: Latitude must be -90 to 90, Longitude must be -180 to 180
3. **Duplicate Site Code**: Site code must be unique within the same company
4. **Invalid Email**: Email must be in valid format
5. **Invalid Site Code**: Site code must contain only alphanumeric characters

## Frontend Integration Steps

1. **Get Available Companies**: Call `/sites/available-companies/` to populate company dropdown
2. **Validate Form**: Ensure all required fields are filled
3. **Submit Site Data**: POST to `/sites/` with complete site information
4. **Handle Errors**: Display validation errors to user
5. **Success**: Redirect or show success message

## Plant Types Available
- SOLAR - Solar Power Plant
- WIND - Wind Power Plant
- THERMAL - Thermal Power Plant
- HYDRO - Hydro Power Plant
- NUCLEAR - Nuclear Power Plant
- BIOMASS - Biomass Power Plant
- GEOTHERMAL - Geothermal Power Plant
- HYBRID - Hybrid Power Plant
- OTHER - Other

## Operational Status Options
- OPERATIONAL - Operational
- MAINTENANCE - Under Maintenance
- SHUTDOWN - Shutdown
- COMMISSIONING - Under Commissioning
- DECOMMISSIONED - Decommissioned 