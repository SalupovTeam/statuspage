# Status Page API Documentation

## Authentication
All endpoints except `/list` require an API key passed in the `x-api-key` header.

## Endpoints

### GET `/list`
Lists all components and their status history.

**Response Example:**
```json
[
  {
    "name": "API Service",
    "website": "https://api.example.com",
    "status_history": ["green", "green", "red", "orange", ...]
  }
]
```

### POST `/add`
Add a new component to monitor.

**Headers:**
- `x-api-key`: Your API key
- `Content-Type: application/json`

**Request Body:**
```json
{
  "name": "API Service",
  "website": "https://api.example.com"
}
```

**Response:**
- Success (201): `{"message": "Component added successfully"}`
- Error (401): `{"error": "Invalid API key"}`
- Error (400): `{"error": "Missing required fields"}`

### POST `/update`
Update component status.

**Headers:**
- `x-api-key`: Your API key
- `Content-Type: application/json`

**Request Body:**
```json
{
  "name": "API Service",
  "status": "working",  // or "outage"
  "date": "2024-12-12"
}
```

**Response:**
- Success (200): `{"message": "Status updated successfully"}`
- Error (401): `{"error": "Invalid API key"}`
- Error (400): `{"error": "Missing required fields"}`
- Error (404): `{"error": "Component not found"}`

## Status Colors
- Green: Working status
- Red: Outage status
- Orange: Mixed status (both working and outage on same day)
- Gray: No updates for that day

## Examples

### Adding a Component
```bash
curl -X POST http://localhost:1487/add \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{"name": "API Service", "website": "https://api.example.com"}'
```

### Updating Status
```bash
curl -X POST http://localhost:1487/update \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{"name": "API Service", "status": "working", "date": "2024-12-12"}'
```

### Listing Components
```bash
curl http://localhost:1487/list
```