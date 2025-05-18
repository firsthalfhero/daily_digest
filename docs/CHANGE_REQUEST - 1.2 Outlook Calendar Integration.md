# CHANGE_REQUEST - 1.2 Outlook Calendar Integration (Microsoft Graph API)

## 1. Summary

**Title:** Migrate Calendar Integration from Motion API to Outlook (Microsoft Graph API)  
**Date:** [Insert Date]  
**Owner:** [Insert Owner/Requester]  
**Status:** Proposed

---

## 2. Background & Rationale

The Daily Digest Assistant currently integrates with the Motion API to retrieve calendar data. To better align with user needs and leverage Microsoft 365 capabilities, we are migrating the calendar integration to Outlook using the Microsoft Graph API. This change will also ensure compatibility with enterprise environments and provide a more robust authentication and authorization model.

---

## 3. Scope

- Replace all Motion API calendar integration with Microsoft Graph API (Outlook) integration.
- Support both AWS Lambda (production) and local development on Windows 11.
- Update documentation, error handling, and monitoring to reflect the new integration.

---

## 4. Technical Details

### 4.1 Libraries & Tools

- **Authentication:**  
  - Use Microsoft Authentication Library (MSAL) for Python (`msal`)
  - Optionally, use Azure Identity (`azure-identity`) for simplified credential management
- **API Access:**  
  - Use Microsoft Graph SDK for Python (`msgraph-sdk`)


### 4.2 Authentication Flows

- **AWS Lambda (Production):**  
  - Use Client Credentials Flow (daemon app, no user interaction)
  - Store Azure AD credentials (client ID, secret, tenant ID) in AWS Secrets Manager
- **Local Development (Windows 11):**  
  - Use Device Code Flow (interactive browser login)
  - Store credentials in a `.env` file (excluded from version control)
  - MSAL will cache tokens locally for convenience

### 4.3 Configuration Management

- For local development, all Azure AD credentials (e.g., client ID, tenant ID, client secret) must be stored in a `.env` file at the project root. 
- The `.env` file must never be committed to version control (ensure `.env` is in `.gitignore`).
- The `.env.template` file must be updated to include all required variables for Microsoft Graph API authentication (see sample below).
- The application must use `python-dotenv` (or equivalent) to load these variables when running locally.
- For production (AWS Lambda), credentials must continue to be managed via AWS Secrets Manager.

#### Sample `.env.template` Section

```
# Azure AD Credentials for Microsoft Graph API (local development only)
AZURE_CLIENT_ID=
AZURE_TENANT_ID=
AZURE_CLIENT_SECRET=
# Add any other required variables here
```

### 4.4 Data Model & API Changes

- Replace Motion API endpoints and data models with Microsoft Graph API equivalents.
- Map Microsoft Graph event schema to the existing digest format.
- Update error handling for new error codes and rate limits.

### 4.5 Testing & Validation

- Update unit and integration tests to mock Microsoft Graph API responses.
- Validate end-to-end flow both locally and in AWS.

---

## 5. Impact Assessment

| Area                | Change/Impact                                                                 |
|---------------------|-------------------------------------------------------------------------------|
| Auth                | Migrate to OAuth 2.0 (MSAL), Azure AD app registration, token management      |
| API Client          | Use msal + msgraph-sdk, new endpoints, new data models                        |
| Data Model          | Map Microsoft Graph event schema to digest format                             |
| Security            | Store Azure credentials in AWS Secrets Manager and local `.env`               |
| Error Handling      | Update for Graph API errors, rate limits, token expiry                        |
| Monitoring          | Add metrics for Graph API calls and token refreshes                           |
| Testing             | Update mocks and integration tests                                            |
| Documentation       | Update for Microsoft Graph API, OAuth 2.0 flows, and local dev setup          |

---

## 6. Developer Action Items

1. **Register an Azure AD application** for both production and local development.
2. **Update codebase** to:
   - Remove Motion API integration
   - Add MSAL authentication and Microsoft Graph SDK usage
   - Implement environment-based configuration and authentication flow selection
   - Use `python-dotenv` to load environment variables from `.env` during local development
3. **Update secrets management:**
   - Store Azure credentials in AWS Secrets Manager (production)
   - Store credentials in `.env` for local development (never commit `.env`)
   - Update `.env.template` with all required variables
4. **Update and expand tests** for new integration.
5. **Update documentation** for setup, authentication, and troubleshooting.
6. **Test the integration** on Windows 11 and AWS Lambda.

---

## 7. Rollout Plan

- Develop and test the new integration in a feature branch.
- Validate locally on Windows 11 and in a staging AWS environment.
- Update documentation and communicate changes to all developers.
- Deploy to production after successful validation.

---

## 8. Risks & Mitigations

- **OAuth 2.0 Complexity:**  
  Mitigate with clear documentation and use of MSAL/azure-identity libraries.
- **Token Expiry/Refresh Issues:**  
  Use MSAL's built-in token caching and refresh logic.
- **Data Model Differences:**  
  Carefully map and test event data transformation.
- **Local/Cloud Parity:**  
  Ensure both environments are tested and documented.

---

## 9. References

- [Microsoft Graph API Documentation](https://docs.microsoft.com/en-us/graph/)
- [MSAL for Python](https://github.com/AzureAD/microsoft-authentication-library-for-python)
- [Microsoft Graph SDK for Python](https://github.com/microsoftgraph/msgraph-sdk-python)
- [Azure Identity for Python](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/identity/azure-identity)

---

## 10. Files Impacted

The following files and modules will require updates as part of the migration from Motion API to Microsoft Graph API (Outlook) for calendar integration:

### API Client
- `src/api/motion.py` (to be removed/replaced)
- `src/api/__init__.py` (update exports)
- (New) `src/api/outlook.py` or similar (implement Microsoft Graph client)

### Data Models
- `src/core/models/calendar.py` (update event models, add mapping for Graph API schema)

### Processors
- `src/core/processors/calendar.py` (update event processing logic for new schema)

### Email Content
- `src/digest_email/content_assembler.py` (update to handle new event format)

### Utilities & Config
- `src/utils/config.py` (remove Motion config, add Outlook/Graph config)
- `src/utils/exceptions.py` (remove Motion-specific exceptions, add new ones as needed)

### Scripts
- `scripts/get_tasks.py` (update to use new API client/config)
- `scripts/manual_send_digest.py` (update to fetch/process events from Outlook)
- `scripts/simple_motion_test.py` (remove or replace with Outlook/Graph test)

### Examples
- `examples/error_handling_example.py` (update to demonstrate new error handling)

### Environment & Templates
- `.env.template` (update with new Azure AD variables, remove Motion variables)

> **Note:** Additional files may be impacted depending on how calendar data is consumed elsewhere in the codebase. All references to Motion API, its config, and its data models must be removed or replaced.

---

**Please review and provide feedback or approval to proceed.** 