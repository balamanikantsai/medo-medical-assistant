# Google Cloud API Setup Guide — Medo Medical Assistant

This document walks you through obtaining **every Google Cloud credential JSON** the Medo project requires. By the end you will have three files placed inside `backend/credentials/`:

| File | Used By | Google API |
|------|---------|------------|
| `translate.json` | Translation service | Cloud Translation API |
| `speech-credentials.json` | Speech-to-Text & Text-to-Speech | Cloud Speech-to-Text API, Cloud Text-to-Speech API |
| `tempCredentials.json` | Calendar event creation | Google Calendar API |

A fourth file, `token.json`, is **auto-generated** the first time the Calendar OAuth flow runs — you do not create it manually.

---

## Prerequisites

| Requirement | Why |
|-------------|-----|
| A Google account | To access Google Cloud Console |
| A Google Cloud project | All APIs and credentials live under one project |
| Billing enabled on the project | Some APIs (Translate, Speech) require billing even on the free tier |

> **Tip:** You can use a single project for all three APIs. The guide below assumes one project named *"medo-assistant"*, but any name works.

---

## Step 1 — Create a Google Cloud Project

1. Go to **[Google Cloud Console](https://console.cloud.google.com/)**.
2. Click the project selector dropdown at the top-left → **New Project**.
3. Enter a name (e.g. `medo-assistant`), choose your organization (or "No organization"), then click **Create**.
4. Make sure the new project is selected in the top-left dropdown.

---

## Step 2 — Enable the Required APIs

From the **[API Library](https://console.cloud.google.com/apis/library)** page (or use the search bar), enable each of the following APIs one by one:

| API to Enable | Search Term |
|---------------|-------------|
| **Cloud Translation API** | `Cloud Translation` |
| **Cloud Speech-to-Text API** | `Cloud Speech-to-Text` |
| **Cloud Text-to-Speech API** | `Cloud Text-to-Speech` |
| **Google Calendar API** | `Google Calendar` |

For each one:
1. Click on the API card.
2. Click **Enable**.
3. Wait for the confirmation banner.

---

## Step 3 — Create a Service Account (for Translate + Speech)

Service accounts are used for **server-to-server** APIs (Translate, Speech-to-Text, Text-to-Speech). They don't require user consent.

1. Go to **[IAM & Admin → Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)**.
2. Click **+ Create Service Account**.
3. Fill in:
   - **Name:** `medo-backend`
   - **Description:** `Backend service account for Translate and Speech APIs`
4. Click **Create and Continue**.
5. Under **Grant this service account access to project**, add these roles:
   - `Cloud Translation API User`
   - `Cloud Speech Client`  
   *(You can also use the broader `Editor` role during development, but limit it in production.)*
6. Click **Continue** → **Done**.

### 3a — Download the key for **Translation** → `translate.json`

1. In the Service Accounts list, click the **medo-backend** row.
2. Go to the **Keys** tab → **Add Key** → **Create new key**.
3. Choose **JSON** → **Create**.
4. A `.json` file downloads automatically.
5. **Rename** it to `translate.json`.
6. Move it to `backend/credentials/translate.json`.

### 3b — Download the key for **Speech** → `speech-credentials.json`

You have two options:

- **Option A (same service account):** Download a *second* key from the same `medo-backend` service account (Keys tab → Add Key → Create new key → JSON). Rename it to `speech-credentials.json`.
- **Option B (separate service account):** Repeat Step 3 to create a new service account named `medo-speech`, grant it `Cloud Speech Client` role, then download its JSON key and rename it to `speech-credentials.json`.

> **Either option works.** Using one service account is simpler; using two gives finer permission control.

6. Move the file to `backend/credentials/speech-credentials.json`.

---

## Step 4 — Create OAuth 2.0 Credentials (for Google Calendar) → `tempCredentials.json`

The Calendar API requires **user consent** (OAuth 2.0), not a service account, because it accesses a real user's calendar.

### 4a — Configure the OAuth Consent Screen

1. Go to **[APIs & Services → OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)**.
2. Choose **External** (unless you have a Google Workspace org and want Internal).
3. Click **Create**.
4. Fill in the required fields:
   - **App name:** `Medo Medical Assistant`
   - **User support email:** your email
   - **Developer contact email:** your email
5. Click **Save and Continue**.
6. On the **Scopes** page, click **Add or Remove Scopes** and add:
   ```
   https://www.googleapis.com/auth/calendar
   ```
7. Click **Update** → **Save and Continue**.
8. On the **Test Users** page, click **+ Add Users** and add your own Gmail address (the one whose calendar will receive medication reminders).
9. Click **Save and Continue** → **Back to Dashboard**.

### 4b — Create the OAuth Client ID

1. Go to **[APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials)**.
2. Click **+ Create Credentials** → **OAuth client ID**.
3. Set:
   - **Application type:** `Desktop app`
   - **Name:** `Medo Calendar Client`
4. Click **Create**.
5. In the dialog that appears, click **Download JSON**.
6. **Rename** the downloaded file to `tempCredentials.json`.
7. Move it to `backend/credentials/tempCredentials.json`.

### 4c — Generate the Token (first-time authorization)

The first time Medo's calendar service runs, it needs to open a browser so you can grant access. Do this **once** from a terminal:

```bash
cd backend
python -c "from services.calendar import create_calendar_event; print('token.json created')"
```

Or simply start the backend and upload a test prescription. The OAuth flow will:

1. Open your default browser.
2. Ask you to sign in with the Google account you added as a test user.
3. Ask you to grant Medo access to your calendar.
4. Save the resulting token to `backend/credentials/token.json`.

After this, `token.json` refreshes automatically — you won't be prompted again unless the token is revoked or deleted.

---

## Step 5 — Verify Your Credentials Folder

Your `backend/credentials/` directory should now contain:

```
backend/
  credentials/
    translate.json            ← Service-account key for Cloud Translation
    speech-credentials.json   ← Service-account key for Speech-to-Text & TTS
    tempCredentials.json      ← OAuth 2.0 client secret for Google Calendar
    token.json                ← Auto-generated after first Calendar auth
```

Make sure all four paths match what is in `backend/config.py` (the defaults already point to the paths above).

---

## Step 6 — Map Credentials to Config

In `backend/config.py`, the relevant settings are:

```python
GOOGLE_TRANSLATE_CREDENTIALS = "credentials/translate.json"
GOOGLE_SPEECH_CREDENTIALS    = "credentials/speech-credentials.json"
GOOGLE_CALENDAR_CREDENTIALS  = "credentials/tempCredentials.json"
GOOGLE_CALENDAR_TOKEN        = "credentials/token.json"
```

You can override any of these via environment variables in your `.env` file if you store the files elsewhere.

---

## Quick Reference — Service Account vs. OAuth 2.0

| Credential Type | JSON File | When to Use |
|-----------------|-----------|-------------|
| **Service Account Key** | `translate.json`, `speech-credentials.json` | Server-side APIs that don't access user-owned resources |
| **OAuth 2.0 Client Secret** | `tempCredentials.json` | APIs that touch a real user's data (e.g., their Google Calendar) |
| **OAuth 2.0 Token** | `token.json` (auto) | Stores the user's authorization so they don't have to approve every time |

---

## Troubleshooting

### "API has not been enabled" error
→ Go to the API Library and make sure the specific API is enabled for your project.

### "Request had insufficient authentication scopes"
→ Delete `credentials/token.json` and re-run the Calendar auth flow so the new scope is included.

### "File not found: credentials/translate.json"
→ Verify the JSON is in the correct path relative to where you run `python app.py`. The default expects you to run from inside `backend/`.

### "Permission denied" or "IAM policy" error
→ Check that your service account has the required roles in **IAM & Admin → IAM**.

### "This app isn't verified" warning during Calendar OAuth
→ This is normal for development. Click **Advanced** → **Go to Medo Medical Assistant (unsafe)** to proceed. For production, submit your app for Google verification.

### OAuth consent screen shows "Access blocked: app not verified"
→ Make sure you added your email under **Test Users** in the OAuth consent screen configuration.

---

## Security Best Practices

1. **Never commit credential JSONs to Git.** Add `credentials/` to your `.gitignore`.
2. **Rotate keys periodically.** Delete old keys from the Service Accounts → Keys tab.
3. **Use least-privilege roles.** Avoid `Owner` or `Editor` roles in production.
4. **Store secrets in a vault** (e.g., Google Secret Manager, Azure Key Vault) for production deployments.
5. **Set restrictive file permissions:** `chmod 600 credentials/*.json` on Linux/Mac.

---

*Document generated for the Medo Medical Assistant project.*
