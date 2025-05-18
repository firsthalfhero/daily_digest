# Migrating Email Sending to Mailersend

This document outlines the steps required to migrate the email sending logic in this project to use [Mailersend](https://www.mailersend.com/) as the email delivery provider.

---

## 1. Install the Mailersend Python SDK

- **Add the Mailersend SDK to your project dependencies.**
- Update `requirements.txt` and/or `requirements-dev.txt`:
  ```
  mailersend
  ```
- Install it in your environment:
  ```sh
  pip install mailersend
  ```

---

## 2. Configure the API Key

- **Ensure your `.env` file contains the Mailersend API key:**
  ```
  MAILERSEND_API_KEY=your_actual_api_key_here
  ```
- Make sure your code loads this value (using `os.environ` or `python-dotenv`).
- **API Key Security:**
  - Never hardcode the API key in your codebase.
  - Ensure `.env` is included in `.gitignore` and not committed to version control.

---

## 3. Implement a Mailersend Email Sender Class

- **Create a new class (e.g., `MailersendEmailSender`) in your codebase.**
- Place it in `src/digest_email/sender.py` or a new file as appropriate.
- The class should:
  - Initialize the Mailersend client with the API key.
  - Implement a `send_templated_email` or similar method matching your current interface.
  - Accept parameters for sender, recipients, subject, HTML, and text content.
  - Use the Mailersend SDK to send emails.
  - **Configuration Validation:**
    - Check that the API key is present and raise a clear error if not.
  - **Error Handling & Logging:**
    - Implement robust error handling and log failed sends with error details.
    - Optionally, implement retry logic for transient errors.
    - Example:
      ```python
      try:
          mailer.send(...)
      except Exception as e:
          logger.error(f"Failed to send email: {e}")
      ```

---

## 4. Update Usage in Your Codebase

- **Replace usage of the old `EmailSender` with your new `MailersendEmailSender`.**
- Update `scripts/manual_send_digest.py` and any other places where `EmailSender` is used.
- Ensure the new sender is instantiated and called with the correct parameters.
- **Deprecation Notice:**
  - If the old `EmailSender` class is widely used, mark it as deprecated in code before removal to help with transition.

---

## 5. Template Handling (If Needed)

- **If you use templates, render them before sending.**
- Mailersend's SDK example sends raw HTML/text. Render your template to HTML/text before passing to the Mailersend sender.
- If you use Mailersend's template system, use their API for template-based sending.
- **Template Variables:**
  - If your emails use dynamic variables, clarify how these are rendered and passed to Mailersend (especially if using Mailersend's template system).

---

## 6. Testing

- **Test the new implementation.**
- Run your script(s) to ensure emails are sent via Mailersend.
- Check for errors and verify delivery.
- **Unit and Integration Tests:**
  - Add or modify unit tests for the new sender class.
  - Use mocking (e.g., `unittest.mock` or `pytest-mock`) to avoid sending real emails during tests.
  - Consider integration tests that mock Mailersend or use a sandbox environment.

---

## 7. Documentation and Cleanup

- **Document the new setup and remove old, unused email-sending code.**
- Update README, developer onboarding docs, and any architecture diagrams that reference the old email system.
- Remove or refactor legacy email sender classes.

---

## 8. Rate Limiting and Quotas

- **Review Mailersend's rate limits and quotas** to avoid unexpected issues in production. Refer to Mailersend documentation for current limits.

---

### Summary Table

| Step | Task | File(s) | Notes |
|------|------|---------|-------|
| 1 | Install SDK | requirements.txt | `pip install mailersend` |
| 2 | Configure API Key | .env | Use `MAILERSEND_API_KEY` |
| 3 | Implement Sender | src/digest_email/sender.py | New class for Mailersend, error handling, config validation |
| 4 | Update Usage | scripts/manual_send_digest.py, others | Replace `EmailSender`, deprecate old class |
| 5 | Template Handling | src/digest_email/templates/ | Render before sending, handle variables |
| 6 | Testing | scripts/, tests/ | Unit/integration tests, use mocking |
| 7 | Documentation | README, onboarding docs | Remove old code, update docs |
| 8 | Rate Limiting | N/A | Review Mailersend quotas |

---

For further details, refer to the [Mailersend Python SDK documentation](https://github.com/mailersend/mailersend-python). 