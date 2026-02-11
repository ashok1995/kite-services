# Kite Connect URL Formats

<!-- markdownlint-disable MD013 MD040 -->

## "Always login" behavior

If the login page appears every time (even when you're already logged into Kite), this is controlled by **Kite's servers**, not our code. We use the standard URL; there is no parameter to skip login.

Possible reasons it changed:

- **Kite policy** – Zerodha may require explicit login more often for security
- **Browser / cookies** – Opening from a new incognito tab, different browser, or after clearing cookies means no Kite session
- **Same origin** – If the login URL is opened from an embedded iframe or a different site, Kite cookies may not be sent

**Workaround:** Open the login URL in the same browser where you’re already logged into [kite.zerodha.com](https://kite.zerodha.com) (e.g. in a tab where Kite is open).

---

## Login URL (to get request_token)

**Format:**

```
https://kite.zerodha.com/connect/login?v=3&api_key={YOUR_API_KEY}
```

**Example:**

```
https://kite.zerodha.com/connect/login?v=3&api_key=abc123xyz
```

**Usage:** Open in browser. User logs in at Kite. After login, Kite redirects to your **Redirect URL** (configured at developers.kite.trade) with `request_token` in the query.

---

## Callback URL (where Kite redirects – your backend)

**Format:**

```
{BASE_URL}/api/auth/callback?request_token={REQUEST_TOKEN}&status=success
```

**Examples:**

- Dev: `http://127.0.0.1:8079/api/auth/callback?request_token=xxx&status=success`
- Prod: `http://203.57.85.72:8179/api/auth/callback?request_token=xxx&status=success`

**Usage:** Set `{BASE_URL}/api/auth/callback` as **Redirect URL** in your Kite app at [developers.kite.trade](https://developers.kite.trade/). Kite sends the user here after login; `request_token` is in the query.

---

## Flow Summary

| Step | URL / API | What you get |
|------|-----------|--------------|
| 1 | `https://kite.zerodha.com/connect/login?v=3&api_key=XXX` | Open in browser; user logs in |
| 2 | Kite redirects to: `{YOUR_REDIRECT_URL}?request_token=YYY&status=success` | `request_token` in URL |
| 3 | `POST /api/auth/login` with `{"request_token": "YYY"}` | `access_token` |

---

## Optional: redirect_params

You can pass data that Kite echoes back on the redirect:

```
https://kite.zerodha.com/connect/login?v=3&api_key=xxx&redirect_params=some%3DX%26more%3DY
```

Value is URL-encoded query string (e.g. `some=X&more=Y`).
