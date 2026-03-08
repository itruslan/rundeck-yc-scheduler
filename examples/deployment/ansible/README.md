# Ansible Deployment

Ansible role for deploying Rundeck YC Scheduler as a Docker container.

By default uses H2 embedded database (no external dependencies). Can be configured to use PostgreSQL or other databases via environment variables.

## What the Role Does

1. Creates the deploy directory on the target host
2. Runs the `rundeck-yc-scheduler` container with configurable environment
3. Templates `tokens.properties` and `admin.aclpolicy`
4. Optionally removes the container and volumes for a clean deploy

## Prerequisites

**Target host:**

- Docker Engine 20.10+

**Control node (where you run Ansible):**

- Ansible 2.17+
- `community.docker` collection (declared in role `meta/main.yml`):

```bash
ansible-galaxy collection install community.docker
```

## Usage

### 1. Add the role to your playbook

```yaml
# deploy.yml
- hosts: rundeck
  roles:
    - role: rundeck_yc_scheduler
      vars:
        rundeck_yc_scheduler_admin_token: "{{ vault_admin_token }}"
```

### 2. Build the image on the target host

```bash
docker build -t rundeck-yc-scheduler:5.19.0 /path/to/rundeck-yc-scheduler/
```

### 3. Run the playbook

```bash
ansible-playbook deploy.yml
```

## Role Variables

| Variable | Default | Description |
| --- | --- | --- |
| `rundeck_yc_scheduler_image` | `rundeck-yc-scheduler:5.19.0` | Docker image name |
| `rundeck_yc_scheduler_deploy_path` | `/opt/rundeck` | Directory for config files |
| `rundeck_yc_scheduler_port` | `4440` | Host port mapping |
| `rundeck_yc_scheduler_url` | `http://<host>:4440` | External URL |
| `rundeck_yc_scheduler_admin_token` | — | API token (**required**, use vault). The token has no expiration by default (`RUNDECK_API_TOKENS_DURATION_MAX=0`). Generate with: `uuidgen \| tr '[:upper:]' '[:lower:]'` |
| `rundeck_yc_scheduler_env` | `{}` | Extra environment variables for the container |
| `rundeck_yc_scheduler_clean` | `false` | Set `true` to remove container and volumes |
| `rundeck_yc_scheduler_health_retries` | `24` | Health check retry count |
| `rundeck_yc_scheduler_health_delay` | `5` | Seconds between retries |

### Using PostgreSQL

By default Rundeck uses H2 embedded database. To use PostgreSQL, set `rundeck_yc_scheduler_env`.
Variables from `rundeck_yc_scheduler_env` are merged with the base env (`RUNDECK_GRAILS_URL`, `RUNDECK_API_TOKENS_DURATION_MAX=0`, etc.):

```yaml
rundeck_yc_scheduler_env:
  RUNDECK_DATABASE_DRIVER: org.postgresql.Driver
  RUNDECK_DATABASE_URL: "jdbc:postgresql://db-host:5432/rundeck"
  RUNDECK_DATABASE_USERNAME: rundeck
  RUNDECK_DATABASE_PASSWORD: "{{ vault_db_password }}"
  RUNDECK_STORAGE_PROVIDER: db
  RUNDECK_PROJECT_STORAGE_TYPE: db
```

## Clean Deploy

```bash
ansible-playbook deploy.yml -e rundeck_yc_scheduler_clean=true
```
