# Kite Services – Documentation (Single Source of Truth)

One canonical doc per topic. All docs are kept in sync with the codebase.

## Quick links

| Topic | Canonical doc | HTML (easy read) |
|-------|----------------|------------------|
| **API endpoints** | [api/api-reference.md](api/api-reference.md) | [html/](html/index.html) → API Reference |
| **Integration** | [integration/INTEGRATION.md](integration/INTEGRATION.md) | [html/integration.html](html/integration.html) |
| **Request/response models** | [api/data-models.md](api/data-models.md) | [html/api-reference.html](html/api-reference.html) (full; nothing missing) |
| **External APIs used** | [api/apis-used.md](api/apis-used.md) | — |
| **Architecture** | [architecture/architecture.md](architecture/architecture.md) | — |
| **Folder structure** | [architecture/folder-structure.md](architecture/folder-structure.md) | — |
| **Services** | [architecture/services.md](architecture/services.md) | — |
| **Deployment** | [deployment/README.md](deployment/README.md) | — |
| **Development** | [development/README.md](development/README.md) | — |

## HTML docs (easy-to-use)

Open [docs/html/index.html](html/index.html) for a single entry point to:

- Request & response models (copy-paste friendly)
- Integration cURL examples
- Links to Markdown canonical docs

## Base URLs

- **Dev:** `http://localhost:8079`
- **Staging:** `http://localhost:8279`
- **Prod:** `http://YOUR_HOST:8179`
- **Swagger:** `$BASE/docs`

## Structure

| Folder | Purpose |
|--------|---------|
| [api/](api/) | API reference, data models, external APIs used |
| [integration/](integration/) | Single integration guide (INTEGRATION.md) |
| [architecture/](architecture/) | System design, folder layout, services |
| [deployment/](deployment/) | Production, VM deploy, testing |
| [development/](development/) | Config, Kite Connect setup |
| [html/](html/) | Easy-to-read HTML for models and integration |
| [examples/](examples/) | UI integration code examples |

No redundant or duplicate guides. When code or APIs change, the corresponding canonical doc is updated.
