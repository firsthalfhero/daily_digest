# Change Request: Migrate Weather Integration to Google Weather API

## Documentation Update Checklist

- [x] API_INTEGRATION.md — Updated for Google Weather API endpoints, authentication, and data mapping
- [x] ARCHITECTURE.md — Updated to reference Google Weather API throughout, including diagrams and data flow
- [x] WEATHER_MODELS.md — Updated to clarify Google as the primary data source, with field mapping and usage examples
- [x] CHANGE_REQUEST - 1.1 Google Weather API.md — This change request, created and maintained
- [ ] CHANGLOG.md — No references to weather API; no update required
- [ ] CONTIBUTING.md — No references to weather API; no update required
- [ ] FREQUENCY_SCHEDULE.md — No references to weather API; no update required
- [ ] Implementation_plan.md — No references to weather API; no update required
- [ ] MIGRATION_GUIDE.md — No references to weather API; no update required
- [ ] README.md — No references to weather API; no update required
- [ ] SECURITY.md — No references to weather API; no update required
- [ ] STORY_PROGRESS.md — No references to weather API; no update required
- [ ] aws_implementation_plan.md — No references to weather API; no update required
- [ ] epic1.md — No references to weather API; no update required
- [ ] epic2.md — No references to weather API; no update required
- [ ] epic3.md — No references to weather API; no update required
- [ ] epic4.md — No references to weather API; no update required
- [ ] prd.md — No references to weather API; no update required
- [ ] testing-strategy.md — No references to weather API; no update required
- [ ] testing_plan.md — No references to weather API; no update required

> As of this review, only API_INTEGRATION.md, ARCHITECTURE.md, WEATHER_MODELS.md, and this change request required updates for the Google Weather API migration. All other documentation files do not reference the weather API or require changes for this migration.

---

## 1. Background & Rationale

- **Current State:**
  The Daily Digest Assistant currently integrates with the IBM/The Weather Company API for weather data. IBM has announced upcoming changes (including endpoint migration and authentication model changes) that introduce risk and potential future rework.
- **Proposed Change:**
  Migrate the weather integration to the Google Weather API, which offers a modern, stable, and well-documented platform with clear authentication and support.

## 2. Scope of Change

### In Scope
- Replace all IBM Weather API calls with Google Weather API calls.
- Update configuration, authentication, and endpoint usage.
- Refactor the weather API client to support Google's request/response model.
- Update data mapping to internal weather models.
- Update error handling and retry logic to match Google's API.
- Update and expand unit/integration tests with Google API mock responses.
- Update documentation (`API_INTEGRATION.md`, `ARCHITECTURE.md`).
- Ensure all downstream consumers (processors, email generation) continue to function with the new data source.

### Out of Scope
- Changes to calendar integration, email delivery, or unrelated system components.
- UI/UX changes (unless weather data format changes require it).
- Migration of historical weather data.

## 3. Migration Plan

### Step 1: Research & Preparation
- Review Google Weather API documentation and obtain API credentials.
- Identify all codebase locations where weather API integration occurs.

### Step 2: Configuration Updates
- Update `.env` and configuration files:
  - `WEATHER_API_URL=https://weather.googleapis.com/v1`
  - `WEATHER_API_KEY=<google_api_key>`
- Remove or deprecate IBM-specific config.

### Step 3: API Client Refactor
- Refactor or rewrite the weather API client:
  - Change endpoint URLs and HTTP methods (Google uses POST for `/v1/weather:lookup`).
  - Update authentication to use the API key as a URL parameter.
  - Update request body to match Google's required format (lat/lon, units, etc.).
  - Update error handling to match Google's error model.

### Step 4: Data Model Mapping
- Map Google's response fields to internal models (`CurrentWeather`, `ForecastDay`, etc.).
- Update or extend models if Google provides new or differently structured data.

### Step 5: Processor & Business Logic Review
- Review weather data processors to ensure compatibility with new data structure.
- Update logic only if new fields or formats are introduced.

### Step 6: Testing
- Update or create new mock responses for Google's API.
- Update unit and integration tests to use new mocks and validate error handling.
- Perform regression testing to ensure no downstream breakage.

### Step 7: Documentation
- Update `API_INTEGRATION.md` and `ARCHITECTURE.md` to reflect the new provider, endpoints, and data mapping.
- Document any provider-specific quirks or limitations.

### Step 8: Deployment & Rollback
- Deploy changes to a staging environment.
- Validate end-to-end weather data flow and email generation.
- Monitor for errors or data discrepancies.
- Prepare rollback plan (retain IBM client code/config for quick reversion if needed).

## 4. Impact Assessment

- **Development Effort:** 3.5–5.5 days (see previous assessment for breakdown).
- **Testing Impact:** All weather-related tests must be updated; regression testing required.
- **Documentation:** All references to IBM must be updated to Google.
- **Risk:** Low, provided the codebase is well-abstracted and tests are comprehensive.
- **Dependencies:** Google API access/credentials, updated documentation.

## 5. BA Guidance for User Stories

**User Story Example (to be updated by BA):**

> As a user, I want the daily digest to include accurate weather data sourced from the Google Weather API, so that I receive reliable and up-to-date weather information.

**Acceptance Criteria:**
- Weather data is retrieved from the Google Weather API using the correct authentication and endpoint.
- The system maps Google's weather data to internal models and displays it in the daily digest.
- Error handling and retry logic follow Google's documented standards.
- All weather-related features and tests pass with the new integration.
- Documentation is updated to reflect the new provider and integration details.

**Tasks:**
- Update configuration for Google API.
- Refactor weather API client.
- Update data mapping and processors.
- Update and expand tests.
- Update documentation.

## 6. References

- [Google Weather API Documentation](https://developers.google.com/maps/documentation/weather/overview)
- [Current IBM Weather API Documentation](https://docs.weather.com/)
- [Internal API_INTEGRATION.md](../docs/API_INTEGRATION.md)
- [Internal ARCHITECTURE.md](../docs/ARCHITECTURE.md)

**Ready for BA review and user story update.**

---

## Lessons Learnt from Google Weather API Integration

Through hands-on troubleshooting and integration, the following key lessons have been identified to ensure robust and correct use of the Google Weather API:

- **Use the Correct Endpoint and HTTP Method:**
  - For daily forecasts, use a `GET` request to `https://weather.googleapis.com/v1/forecast/days:lookup`.
  - All parameters must be passed as query parameters in the URL, not in the request body.

- **Only Use Supported Query Parameters:**
  - Supported parameters include: `key`, `location.latitude`, `location.longitude`, `days`, `languageCode`, `pageSize`, and `pageToken`.
  - Do **not** include unsupported parameters such as `units` (which will result in a 400 error).

- **Error Handling:**
  - Capture and log the full error response from Google.
  - Surface Google's error messages to the user/developer for clarity.
  - Add troubleshooting guidance for common errors (400, 404, etc.).

- **Testing and Validation:**
  - Test with minimal required parameters first, then add optional parameters one at a time.
  - Ensure tests cover both valid and invalid parameter scenarios, including handling of 400 errors for unsupported parameters.

- **Documentation:**
  - Update internal documentation and code comments to reflect the correct usage of the endpoint and parameters.
  - Add a troubleshooting section for common errors and their solutions.

For a detailed, actionable implementation plan and checklist, see `docs/IMPLEMENTATION_LESSONS_GOOGLE_WEATHER_API.md`.

---

## Implementation Checklist for Google Weather API Migration

### Files to Change
- `src/core/clients/weather_client.py` — Refactor for Google API endpoints, authentication, request/response, error handling.
- `src/core/models/weather.py` — Update field mapping and validation for Google's data structure.
- `src/core/processors/weather.py` — Update logic for new data structure and error handling.
- `src/utils/config.py` — Update config loading for Google API keys/URLs, remove IBM-specific config.
- `src/digest_email/` — Update if weather data structure changes affect email generation.
- `src/utils/exceptions.py` — Update error handling for Google's error model (if needed).

### Tests to Change
- `tests/api/test_weather.py` — Update for Google API endpoints, request/response, and error handling.
- `tests/core/processors/test_weather_processor.py` — Update for new data structure.
- `tests/integration/test_error_handling.py` — Update for Google's error model.
- `tests/scripts/test_get_tasks.py` — Update config and mocks for Google API.
- Any other tests using weather mocks or config.

### Files to Create
- New mock response files for Google Weather API (if using file-based mocks).

### Files to Delete
- Remove/deprecate any IBM-specific config, code, or test data.

---

**Next Steps:**
- Complete all items in this checklist as part of the migration.
- Mark each as complete in this section as work progresses. 