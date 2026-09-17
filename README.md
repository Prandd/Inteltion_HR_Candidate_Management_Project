# Inteltion HR Candidate Management --- 7-Day MVP

A web-based system that uploads a CV, extracts structured candidate data
via an LLM, and displays it on an HR dashboard with inline editing and
candidate pipeline management.

This README is the single setup guide for all team members. Follow it to
run the full stack locally and understand the current system workflow.

------------------------------------------------------------------------

# 1. Project Structure

    Inteltion_HR_Candidate_Management_Project/

    ├── frontend/
    │   ├── dashboard/        # HR Dashboard, login, candidate list/detail views
    │   ├── upload-edit/      # Upload flow + edit forms
    │   └── components/       # Shared frontend components
    │
    ├── backend/              # FastAPI app, DB, file handling, candidate APIs
    ├── llm-service/          # CV extraction engine (LLM + parsing)
    ├── shared-contracts/     # Shared schema and API contracts
    ├── docker-compose.yml
    ├── .env.example
    └── README.md

------------------------------------------------------------------------

# 2. Authentication

The system requires authentication before accessing the HR dashboard.

## Current Implementation

-   Frontend MVP authentication
-   Login page
-   Logout through user profile dropdown
-   Authentication state stored using localStorage

Flow:

    Login
      |
      v
    Authentication Check
      |
      v
    Dashboard

Logout:

    Profile Dropdown
            |
            v
    Remove Authentication State
            |
            v
    Redirect to Login

------------------------------------------------------------------------

# 3. Dashboard Features

## Candidate Search

Users can search candidates by:

-   Candidate name
-   Email
-   Skills

## Candidate Filtering

Available filters:

-   Minimum experience years
-   Position

## Candidate Sorting

Candidates can be sorted by:

-   Latest Import
-   Oldest Import
-   Name A-Z
-   Name Z-A

Sorting process:

    Candidates
        |
        v
    Search / Filter
        |
        v
    Sorting
        |
        v
    Dashboard Board / Table

------------------------------------------------------------------------

# 4. Candidate Upload Flow

The CV upload process consists of multiple stages:

    Upload CV

        |
        v

    Uploading resume

        |
        v

    Extracting CV information

        |
        v

    AI analyzing candidate profile

        |
        v

    Saving candidate profile

        |
        v

    Completed

The progress bar represents the complete CV processing pipeline, not
only file transfer progress.

------------------------------------------------------------------------

# 5. Candidate Detail Management

Candidate detail page supports:

-   View extracted candidate information
-   View skills and experience
-   Update candidate status
-   Download resume
-   Delete candidate

------------------------------------------------------------------------

# 6. AI Extraction Confidence

The candidate score shown in the system represents:

    extraction_confidence

Meaning:

-   Confidence level of LLM CV information extraction

Example:

    0.85 = 85% extraction confidence

Important:

This value is NOT a candidate-job matching score.

It does not represent candidate suitability for a position.

------------------------------------------------------------------------

# 7. Candidate Delete API

## Delete Candidate

Method:

    DELETE /candidates/{candidate_id}

Purpose:

Remove a candidate record from the system.

------------------------------------------------------------------------

# 8. Running the Full Stack

## Docker Compose

Start all services:

``` bash
docker compose up --build
```

Services:

-   PostgreSQL
-   Backend FastAPI
-   Dashboard frontend
-   Upload/Edit frontend

Stop:

``` bash
docker compose down
```

Reset database:

``` bash
docker compose down -v
```

------------------------------------------------------------------------

# 9. Local Development

## Dashboard Frontend

``` bash
cd frontend/dashboard

npm install

npm run dev
```

Runs on:

    http://localhost:5173

## Backend

``` bash
cd backend

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

Backend:

    http://localhost:8000

API Docs:

    http://localhost:8000/docs

## LLM Service

``` bash
cd llm-service

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

python run_test_harness.py
```

------------------------------------------------------------------------

# 10. Environment Variables

Required Azure OpenAI variables:

    CV_SCORING_PROVIDER
    AZURE_OPENAI_ENDPOINT
    AZURE_OPENAI_API_KEY
    AZURE_OPENAI_DEPLOYMENT

Azure Storage:

    AZURE_STORAGE_CONNECTION_STRING_FILE

Backend:

    DATABASE_URL
    CORS_ORIGINS

Frontend:

    VITE_API_BASE_URL
    VITE_USE_MOCK_DATA

Never commit:

    .env
    *.env
    azure-storage-connection-string.txt
    API keys
    connection strings

------------------------------------------------------------------------

# 11. Shared Contracts

The shared contract contains:

-   Candidate schema
-   API contract
-   Mock candidate data

Any changes to shared contracts must be communicated to all team members
before editing.

------------------------------------------------------------------------

# 12. Development Notes

Current dashboard data flow:

    Candidate API

          |

          v

    Search / Filter

          |

          v

    Sorting

          |

          v

    Board / Table Display

When modifying candidate schema, API responses, or shared contracts,
notify other team members to avoid integration issues.

------------------------------------------------------------------------

# 13. Troubleshooting

## Frontend cannot reach backend

Check:

-   Backend running
-   CORS_ORIGINS configuration
-   VITE_API_BASE_URL

## Azure OpenAI Error

Check:

-   AZURE_OPENAI_ENDPOINT
-   AZURE_OPENAI_API_KEY
-   AZURE_OPENAI_DEPLOYMENT

## Upload Error

Check:

-   Azure Storage connection string
-   Backend environment variables

------------------------------------------------------------------------

# 14. Team Conventions

-   Use feature branches:

```{=html}
<!-- -->
```
    feature/<lane>-<description>

-   Do not commit secrets.
-   Changes to shared-contracts require team notification.
-   Keep commits focused on your assigned module.
