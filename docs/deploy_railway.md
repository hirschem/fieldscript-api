# Deploying to Railway (Docker)

⚠️ Railway must be configured to use the repository Dockerfile.

## Required Configuration

- Set **Build Type** to **Docker** (not Python / Railpack)
- Set **Dockerfile Path** to:
  ```
  /Dockerfile
  ```
- The container binds to `0.0.0.0:$PORT` (default in Dockerfile)
- **No start command is required**; Railway uses the Dockerfile's CMD

## Common Deployment Errors

**Error:** `No start command was found.`

This means Railway is using the default Python (Railpack) builder, which does not detect FastAPI apps automatically.

**Solution:**
- Set the build type to Docker
- Set the Dockerfile path to `/Dockerfile`

This will resolve the error and deploy your app using the Dockerfile.
