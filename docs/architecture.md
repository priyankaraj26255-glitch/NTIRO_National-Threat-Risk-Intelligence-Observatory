# NTIRO System Architecture

## 1. Purpose
NTIRO (National Threat & Risk Intelligence Observatory) is planned as a public-data intelligence and decision-support platform. It will analyze evidence-based indicators to help users understand threat and risk patterns.

## 2. Architecture Layers

### Public Data Sources
Collect suitable public datasets and official reports. Document each source's origin, date, and limitations.

### Data Ingestion and Validation
Import data, validate its structure, handle missing values, flag invalid records, and preserve data provenance.

### PostgreSQL Database
Store validated datasets and structured indicators. Design the schema around actual source data and use cases.

### Analytics and Threat Indicators
Calculate transparent indicators using documented definitions, weights, and assumptions. Clearly communicate uncertainty.

### FastAPI Backend
Expose approved data and analytics through HTTP endpoints. The current application has root and health endpoints.

### Dashboard and Reports
Provide visual summaries, trends, appropriate maps, and reports that communicate sources, dates, and limitations.

## 3. Planned Data Flow
Public sources -> ingestion and validation -> PostgreSQL -> analytics -> FastAPI -> dashboard and reports.

## 4. Current Implementation
- FastAPI application created.
- Root and health endpoints implemented.
- Automated endpoint tests created.
- Database, analytics, and dashboard components remain planned.

## 5. Design Principles
- Traceable data sources.
- Transparent calculations.
- Privacy-conscious data handling.
- Reproducible analysis.
- Clear communication of uncertainty and limitations.
