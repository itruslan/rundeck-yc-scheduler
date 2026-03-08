# Docker Deployment

Run Rundeck YC Scheduler as a single container with embedded H2 database (no external dependencies).

## Quick Start

```bash
# Build the image (from the repo root)
docker build -t rundeck-yc-scheduler:5.19.0 .

# Run
docker run -d \
  --name rundeck \
  -p 4440:4440 \
  -e RUNDECK_GRAILS_URL=http://localhost:4440 \
  -e RUNDECK_SERVER_ADDRESS=0.0.0.0 \
  -e RUNDECK_FEATURE_REPOSITORY_ENABLED=false \
  -e RUNDECK_API_TOKENS_DURATION_MAX=0 \
  -v rundeck_data:/home/rundeck/server/data \
  rundeck-yc-scheduler:5.19.0

# Open Rundeck
open http://localhost:4440
```

Default login / password: `admin` / `admin`

## Environment Variables

| Variable | Required | Description |
| --- | --- | --- |
| `RUNDECK_GRAILS_URL` | yes | External URL (used for redirects) |
| `RUNDECK_SERVER_ADDRESS` | yes | Bind address (`0.0.0.0` for Docker) |
| `RUNDECK_API_TOKENS_DURATION_MAX` | no | Token max lifetime in seconds (`0` = no expiration) |
| `RUNDECK_FEATURE_REPOSITORY_ENABLED` | no | Disable plugin repository (`false`) |

### Using PostgreSQL

To use an external database instead of H2, add database variables:

```bash
docker run -d \
  --name rundeck \
  -p 4440:4440 \
  -e RUNDECK_GRAILS_URL=http://localhost:4440 \
  -e RUNDECK_SERVER_ADDRESS=0.0.0.0 \
  -e RUNDECK_DATABASE_DRIVER=org.postgresql.Driver \
  -e RUNDECK_DATABASE_URL=jdbc:postgresql://db-host:5432/rundeck \
  -e RUNDECK_DATABASE_USERNAME=rundeck \
  -e RUNDECK_DATABASE_PASSWORD=changeme \
  -e RUNDECK_STORAGE_PROVIDER=db \
  -e RUNDECK_PROJECT_STORAGE_TYPE=db \
  -e RUNDECK_FEATURE_REPOSITORY_ENABLED=false \
  -e RUNDECK_API_TOKENS_DURATION_MAX=0 \
  -v rundeck_data:/home/rundeck/server/data \
  rundeck-yc-scheduler:5.19.0
```

## Operations

```bash
# View logs
docker logs -f rundeck

# Restart
docker restart rundeck

# Stop
docker stop rundeck

# Full reset (removes all data)
docker rm -fv rundeck && docker volume rm rundeck_data
```

## Verifying the Plugin

```bash
curl -s -H "Accept: application/json" \
  -H "X-Rundeck-Auth-Token: <your-token>" \
  http://localhost:4440/api/41/plugin/list | \
  jq '.[] | select(.name | startswith("yc-"))'
```

You should see three entries: `yc-node-source`, `yc-start`, and `yc-stop`.

## What's Next

Once Rundeck is running, configure projects and jobs:

- [Terraform module](../../configuration/terraform-rundeck-yc-scheduler/) — recommended for IaC
- [Manual setup via UI](../../configuration/manual-rundeck/) — step-by-step guide
