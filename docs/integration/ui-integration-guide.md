# UI Integration Guide (Client / Production)

**Flow:** Get callback URL → User pastes access token (already logged in elsewhere) → Send token to backend.

**Production base URL:** `http://203.57.85.72:8179`

---

## 1. Get callback URL

Use for Kite app setup at [developers.kite.trade](https://developers.kite.trade/) (Redirect URL).

```bash
curl -s http://203.57.85.72:8179/api/token/callback-url
```

Returns the URL to configure. `configured: true` means backend has api_key/api_secret.

---

## 2. Send access token

User already has access token (from Kite or another app). Paste it in your UI and send to backend.

```bash
curl -X PUT http://203.57.85.72:8179/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"access_token": "YOUR_ACCESS_TOKEN"}'
```

Optional: add `"user_id": "AB1234"` in the JSON body.

---

## Flow summary (Production)

| Step | API | cURL |
|------|-----|------|
| Get callback URL | `GET /api/token/callback-url` | `curl -s http://203.57.85.72:8179/api/token/callback-url` |
| Save access token | `PUT /api/auth/token` | `curl -X PUT http://203.57.85.72:8179/api/auth/token -H "Content-Type: application/json" -d '{"access_token":"..."}'` |

No Kite login from here. User obtains token elsewhere and pastes it.
