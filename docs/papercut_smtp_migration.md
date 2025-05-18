# Migrating Local Email Sending to Papercut SMTP (Windows)

This document outlines the steps to migrate your local email sending setup to use [Papercut SMTP](https://github.com/ChangemakerStudios/Papercut-SMTP) for development and testing on Windows.

---

## 1. Download and Run Papercut SMTP

- Go to the [Papercut SMTP Releases page](https://github.com/ChangemakerStudios/Papercut-SMTP/releases).
- Download the latest `PapercutSMTP-x64.zip` (or x86 if needed) for Windows.
- Extract the zip file to a convenient location.
- Run `PapercutSMTP.exe`.
- Papercut will start listening on `localhost:25` by default and open a GUI inbox window.

---

## 2. Configure Your Application to Use Papercut SMTP

- Update your `.env` or configuration to use the following SMTP settings:
  ```env
  SMTP_HOST=localhost
  SMTP_PORT=25
  SMTP_USERNAME=
  SMTP_PASSWORD=
  SENDER_EMAIL=your_test_sender@yourdomain.com
  RECIPIENT_EMAIL=your_test_recipient@yourdomain.com
  ```
- No authentication is required for Papercut SMTP.
- Make sure your application is using these settings for local development.

---

## 3. Test Email Sending

- Run your email sending script or trigger email functionality in your app.
- Sent emails will appear in the Papercut SMTP GUI inbox window.
- You can view, inspect, and debug the full email content (headers, HTML, etc.) in the GUI.

---

## 4. Troubleshooting

- If emails do not appear:
  - Ensure Papercut SMTP is running and listening on the correct port (`25` by default).
  - Make sure your app is configured to use `localhost` and port `25`.
  - Check for firewall or antivirus software blocking local SMTP connections.
- For advanced configuration (e.g., changing the listening port), see the [Papercut SMTP documentation](https://github.com/ChangemakerStudios/Papercut-SMTP#configuration).

---

## 5. Revert for Production

- **Important:** Papercut SMTP is for local development/testing only. Do not use it in production.
- For production, restore your real SMTP or transactional email provider settings.

---

## References
- [Papercut SMTP GitHub](https://github.com/ChangemakerStudios/Papercut-SMTP)
- [Papercut SMTP Releases](https://github.com/ChangemakerStudios/Papercut-SMTP/releases) 