# Safety Management System - Complete Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Flow Chart](#architecture-flow-chart)
3. [API Documentation](#api-documentation)
4. [User Flow Charts](#user-flow-charts)
5. [System Design](#system-design)
6. [Database Schema](#database-schema)
7. [Security & Authentication](#security--authentication)

---

## System Overview

The Safety Management System is a comprehensive web application designed for solar power plants to manage safety incidents, employee information, and site operations. The system consists of:

- **Frontend**: React.js application with Tailwind CSS
- **Backend**: Django REST API with PostgreSQL
- **Features**: QR code generation, incident reporting, employee management, site management

---

## Architecture Flow Chart

```mermaid
graph TB
    subgraph "Frontend (React)"i w
        A[User Interface] --> B[React Components]
        B --> C[API Service Layer]
        C --> D[State Management]
    end
    
    subgraph "Backend (Django)"
        E[Django REST API] --> F[ViewSets]
        F --> G[Serializers]
        G --> H[Models]
        H --> I[PostgreSQL Database]
    end
    
    subgraph "External Services"
        J[QR Code Generation]
        K[Email Notifications]
        L[File Storage]
    end
    
    C --> E
    F --> J
    F --> K
    F --> L
    
    subgraph "User Types"
        M[Admin Users]
        N[Site Managers]
        O[Employees]
        P[Public Users]
    end
    
    A --> M
    A --> N
    A --> O
    A --> P
```

---

## API Documentation

### Base URL
```
http://localhost:8000/api/v1/
```

### Authentication
Currently, the system uses session-based authentication. No API keys are required for basic operations.

### Core API Endpoints

#### 1. Companies API
| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | `/companies/` | List all companies | `page`, `search` |
| POST | `/companies/` | Create new company | Company data |
| GET | `/companies/{id}/` | Get specific company | `id` |
| PATCH | `/companies/{id}/` | Update company | `id`, Company data |
| DELETE | `/companies/{id}/` | Delete company | `id` |

#### 2. Sites API
| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | `/sites/` | List all sites | `page`, `search`, `company` |
| POST | `/sites/` | Create new site | Site data |
| GET | `/sites/{id}/` | Get specific site | `id` |
| PATCH | `/sites/{id}/` | Update site | `id`, Site data |
| DELETE | `/sites/{id}/` | Delete site | `id` |
| GET | `/sites/{id}/qr/` | Generate QR code | `id` |
| GET | `/sites/{id}/qr-url/` | Generate URL QR code | `id` |
| GET | `/sites/available-companies/` | Get companies for site creation | None |
| GET | `/sites/dashboard-stats/` | Get site statistics | None |

#### 3. Incidents API
| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | `/incidents/` | List all incidents | `page`, `status`, `site` |
| POST | `/incidents/` | Create incident | Incident data |
| POST | `/incidents/anonymous/` | Create anonymous incident | Incident data |
| GET | `/incidents/{id}/` | Get specific incident | `id` |
| PATCH | `/incidents/{id}/` | Update incident | `id`, Incident data |
| PATCH | `/incidents/{id}/status/` | Update incident status | `id`, `status` |
| POST | `/incidents/{id}/assign/` | Assign incident | `id`, `assigned_to` |
| GET | `/incidents/dashboard-stats/` | Get incident statistics | None |
| GET | `/incidents/trending/` | Get trending analysis | None |
| GET | `/incidents/export/` | Export incident data | `format`, `date_range` |

#### 4. Employees API
| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | `/employees/` | List all employees | `page`, `search`, `site` |
| POST | `/employees/` | Create new employee | Employee data |
| GET | `/employees/{id}/` | Get specific employee | `id` |
| PATCH | `/employees/{id}/` | Update employee | `id`, Employee data |
| DELETE | `/employees/{id}/` | Delete employee | `id` |
| POST | `/employees/{id}/assign-site/` | Assign to site | `id`, `site_id` |

#### 5. Emergency Contacts API
| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | `/emergency-contacts/` | List emergency contacts | `page`, `site` |
| POST | `/emergency-contacts/` | Create contact | Contact data |
| GET | `/emergency-contacts/{id}/` | Get specific contact | `id` |
| PATCH | `/emergency-contacts/{id}/` | Update contact | `id`, Contact data |
| DELETE | `/emergency-contacts/{id}/` | Delete contact | `id` |

#### 6. Public Access API
| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | `/public/{company_code}/{site_code}/` | Public site access | `company_code`, `site_code` |
| GET | `/validate/{company_code}/{site_code}/` | Validate site QR | `company_code`, `site_code` |

### Request/Response Examples

#### Create Site Request
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

#### Create Incident Request
```json
{
    "site": 1,
    "incident_type": "UNSAFE_ACT",
    "severity": "MEDIUM",
    "description": "Employee not wearing safety helmet",
    "location": "Solar Panel Area A",
    "reported_by": "John Doe",
    "contact_number": "+91-9876543210",
    "anonymous": false
}
```

---

## User Flow Charts

### 1. Incident Reporting Flow
```mermaid
flowchart TD
    A[User Scans QR Code] --> B[Public Site Access Page]
    B --> C{Choose Report Type}
    C -->|Unsafe Act| D[Unsafe Act Form]
    C -->|Unsafe Condition| E[Unsafe Condition Form]
    C -->|Near Miss| F[Near Miss Form]
    C -->|Emergency| G[Emergency Contact Page]
    
    D --> H[Fill Incident Details]
    E --> H
    F --> H
    
    H --> I{Anonymous Report?}
    I -->|Yes| J[Submit Anonymous Report]
    I -->|No| K[Fill Personal Details]
    K --> L[Submit Named Report]
    
    J --> M[Success Page]
    L --> M
    M --> N[Email Notification Sent]
```

### 2. Admin Dashboard Flow
```mermaid
flowchart TD
    A[Admin Login] --> B[Admin Dashboard]
    B --> C{Choose Action}
    
    C -->|Manage Sites| D[Site Management]
    C -->|Manage Employees| E[Employee Management]
    C -->|View Incidents| F[Incident Reports]
    C -->|Generate QR Codes| G[QR Generator]
    C -->|Manage Companies| H[Company Management]
    
    D --> I[Create/Edit Sites]
    E --> J[Create/Edit Employees]
    F --> K[View/Update Incidents]
    G --> L[Generate QR Codes]
    H --> M[Create/Edit Companies]
    
    I --> N[Update Database]
    J --> N
    K --> N
    L --> O[Download/Print QR]
    M --> N
```

### 3. QR Code Generation Flow
```mermaid
flowchart TD
    A[Select Site] --> B[Generate QR Code]
    B --> C[API Call to Backend]
    C --> D[Create QR Data]
    D --> E[Generate QR Image]
    E --> F[Return Base64 Image]
    F --> G[Display QR Code]
    G --> H{Choose Action}
    H -->|Download| I[Download PNG]
    H -->|Print| J[Open Print Window]
    H -->|Copy Data| K[Copy to Clipboard]
```

---

## System Design

### 1. Technology Stack

#### Frontend
- **Framework**: React.js 18+
- **Styling**: Tailwind CSS
- **State Management**: React Hooks (useState, useEffect)
- **HTTP Client**: Axios
- **Routing**: React Router
- **Build Tool**: Create React App

#### Backend
- **Framework**: Django 4.2.7
- **API**: Django REST Framework
- **Database**: PostgreSQL
- **Authentication**: Django Session Authentication
- **CORS**: django-cors-headers
- **Filtering**: django-filter

#### Database
- **Primary Database**: PostgreSQL
- **ORM**: Django ORM
- **Migrations**: Django Migrations

### 2. Database Schema

#### Core Models

**Company Model**
```python
- id (Primary Key)
- name (CharField)
- company_code (CharField, unique)
- address (TextField)
- phone (CharField)
- email (EmailField)
- created_at (DateTimeField)
- updated_at (DateTimeField)
```

**Site Model**
```python
- id (Primary Key)
- company (ForeignKey to Company)
- name (CharField)
- site_code (CharField, unique)
- description (TextField)
- address (TextField)
- city (CharField)
- state (CharField)
- country (CharField)
- postal_code (CharField)
- latitude (DecimalField)
- longitude (DecimalField)
- phone (CharField)
- email (EmailField)
- plant_type (CharField, choices)
- capacity (CharField)
- operational_status (CharField, choices)
- is_active (BooleanField)
- created_at (DateTimeField)
- updated_at (DateTimeField)
```

**Employee Model**
```python
- id (Primary Key)
- company (ForeignKey to Company)
- site (ForeignKey to Site, null=True)
- name (CharField)
- employee_id (CharField, unique)
- position (CharField)
- phone (CharField)
- email (EmailField)
- is_active (BooleanField)
- created_at (DateTimeField)
- updated_at (DateTimeField)
```

**Incident Model**
```python
- id (Primary Key)
- site (ForeignKey to Site)
- incident_type (CharField, choices)
- severity (CharField, choices)
- description (TextField)
- location (CharField)
- reported_by (CharField)
- contact_number (CharField)
- anonymous (BooleanField)
- status (CharField, choices)
- assigned_to (ForeignKey to Employee, null=True)
- created_at (DateTimeField)
- updated_at (DateTimeField)
```

### 3. Security Design

#### Authentication & Authorization
- **Session-based authentication** for admin users
- **Public access** for incident reporting (no authentication required)
- **CSRF protection** enabled
- **CORS configuration** for frontend-backend communication

#### Data Protection
- **Input validation** on all API endpoints
- **SQL injection protection** via Django ORM
- **XSS protection** via Django's built-in security
- **File upload restrictions** for QR code images

#### API Security
- **Rate limiting** (can be implemented)
- **Request validation** via serializers
- **Error handling** without exposing sensitive information

### 4. Scalability Considerations

#### Horizontal Scaling
- **Stateless API design** allows multiple backend instances
- **Database connection pooling** for better performance
- **CDN integration** for static files (QR codes, images)

#### Performance Optimization
- **Database indexing** on frequently queried fields
- **API pagination** for large datasets
- **Caching strategy** for frequently accessed data
- **QR code caching** to avoid regeneration

#### Monitoring & Logging
- **Django logging** for error tracking
- **API request/response logging** for debugging
- **Performance monitoring** for response times

### 5. Deployment Architecture

```mermaid
graph TB
    subgraph "Production Environment"
        A[Load Balancer] --> B[Web Server 1]
        A --> C[Web Server 2]
        B --> D[Database Cluster]
        C --> D
        B --> E[Redis Cache]
        C --> E
        B --> F[File Storage]
        C --> F
    end
    
    subgraph "Development Environment"
        G[Local Development] --> H[Single Server]
        H --> I[Local Database]
    end
```

---

## Configuration & Environment Variables

### Frontend Environment Variables
```bash
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_ENVIRONMENT=development
```

### Backend Environment Variables
```bash
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/safety_db
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

---

## API Response Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful GET, PUT, PATCH requests |
| 201 | Created | Successful POST requests |
| 400 | Bad Request | Validation errors, missing fields |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Permission denied |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server-side errors |

---

## Error Handling

### Frontend Error Handling
```javascript
// API error handling
export const handleApiError = (error, defaultMessage = 'An error occurred') => {
    if (error.response?.data?.message) {
        return error.response.data.message;
    }
    if (error.response?.data?.detail) {
        return error.response.data.detail;
    }
    if (error.message) {
        return error.message;
    }
    return defaultMessage;
};
```

### Backend Error Handling
```python
# Django REST Framework error handling
from rest_framework import status
from rest_framework.response import Response

def handle_validation_error(serializer):
    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )
```

---

## Testing Strategy

### Frontend Testing
- **Unit Tests**: React component testing with Jest
- **Integration Tests**: API integration testing
- **E2E Tests**: User flow testing with Cypress

### Backend Testing
- **Unit Tests**: Django model and view testing
- **API Tests**: Endpoint testing with Django REST Framework
- **Integration Tests**: Database and external service testing

---

This documentation provides a comprehensive overview of the Safety Management System, including all API endpoints, user flows, system architecture, and deployment considerations. 