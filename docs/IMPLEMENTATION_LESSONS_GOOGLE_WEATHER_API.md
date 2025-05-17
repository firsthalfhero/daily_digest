# Implementation Plan: Lessons Learnt from Google Weather API Integration

This document outlines the actionable steps required to ensure all lessons from the Google Weather API integration troubleshooting are reflected in the codebase and development process.

---

## 1. API Client Update
- Refactor the weather client to use the correct endpoint and HTTP method:
  - Use `GET` requests to `https://weather.googleapis.com/v1/forecast/days:lookup` for daily forecasts.
  - Pass all parameters as query parameters (not in the request body).
  - Do **not** include unsupported parameters (e.g., `units`).
- **File(s):** `src/core/clients/weather_client.py`

## 2. Configuration
- Ensure only supported parameters are configurable (API key, days, languageCode, etc.).
- Remove any references to unsupported parameters (e.g., `units`) from config files and code.
- **File(s):** `src/utils/config.py`, `.env`, `.env.template`

## 3. Error Handling
- Update error handling to capture and log the full error response from Google.
- Surface Google's error messages to the user/developer for clarity.
- Add troubleshooting guidance for common errors (400, 404, etc.).
- **File(s):** `src/core/clients/weather_client.py`, `src/utils/exceptions.py`

## 4. Documentation
- Update internal documentation and code comments to reflect the correct usage of the endpoint and parameters.
- Add a troubleshooting section for common errors and their solutions.
- **File(s):** `docs/API_INTEGRATION.md`, `docs/CHANGE_REQUEST - 1.1 Google Weather API.md`, `docs/WEATHER_MODELS.md`

## 5. Testing
- Update or add tests to ensure:
  - Only supported parameters are sent in requests.
  - The client correctly handles 400 errors for unsupported parameters.
  - The client works with both minimal and full parameter sets.
- **File(s):** `tests/api/test_weather.py`, `tests/core/processors/test_weather_processor.py`, `tests/integration/test_error_handling.py`

---

## Checklist for Implementation
- [ ] Refactor weather client to use correct endpoint and GET method
- [ ] Remove unsupported parameters from all code and config
- [ ] Update error handling to log and surface Google API errors
- [ ] Update documentation to reflect correct usage and troubleshooting
- [ ] Update/add tests for parameter validation and error handling
- [ ] Review and validate all changes in staging

---

**Note:**
- Reference the [Google Weather API documentation](https://developers.google.com/maps/documentation/weather/daily-forecast) for the latest supported parameters and usage.
- Update this checklist as each step is completed. 