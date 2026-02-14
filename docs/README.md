# Kite Services – Documentation

**⭐ START HERE FOR INTEGRATION:**

- **[Kite Service Integration Guide](integration/KITE-SERVICE-INTEGRATION-GUIDE.md)**
  — Complete guide
- [Authentication Guide](integration/auth-curl-commands.md) -
  How to authenticate with Kite Connect
- [Production Integration Guide](integration/prod-integration-guide.md) -
  Tested cURL examples for prod (health, auth, quotes, historical, trading)

---

## Structure

| Folder | Purpose |
|--------|---------|
| **[integration/](integration/)** | Integration guides – primary for API consumers |
| **[api/](api/)** | API reference, external APIs, data models |
| **[architecture/](architecture/)** | System design, folder layout, services |
| **[deployment/](deployment/)** | Production deployment, testing workflow |
| **[development/](development/)** | Config, Kite Connect setup |
| **[examples/](examples/)** | UI integration examples |

---

## Base URLs

- **Dev:** `http://localhost:8079`
- **Staging (local):** `http://localhost:8279` — test before prod
- **Prod:** `http://YOUR_HOST:8179`
- **Swagger:** `/docs`
