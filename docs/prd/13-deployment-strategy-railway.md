# 13. Deployment Strategy --- Railway

-   Railway hosts **single FastAPI service** (UI + API).\
-   Env vars: `MODE`, `HAPI_BASE_URLS`, `OPENAI_API_KEY`,
    `REQUEST_TIMEOUT_S`, `RETRY_MAX`, `BACKOFF_BASE_MS`.\
-   Failover logic implemented for `/validate`.\
-   DEMO mode points to public HAPI endpoints.\
-   Regression mode points to local HAPI in Docker.

------------------------------------------------------------------------
