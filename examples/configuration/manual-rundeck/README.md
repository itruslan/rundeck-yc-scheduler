# Manual Configuration (via Rundeck UI)

Step-by-step guide to configure projects and jobs through the Rundeck web interface.

## Overview

| Step | What | Where in UI |
| --- | --- | --- |
| 1 | Create a project | Projects → Create New Project |
| 2 | Upload SA key to Key Storage | System Menu → Key Storage |
| 3 | Add ACL policy for the plugin | System Menu → Access Control |
| 4 | Configure node source plugin | Project Settings → Edit Nodes |
| 5 | Import jobs | Project → Jobs → Upload Definition |

## Step 1: Create a Project

1. Click **New Project** (or **Projects → Create New Project**)
2. Fill in:
   - **Project Name**: e.g., `production`
   - **Label**: e.g., `Production Environment`
3. Click **Create** (node source will be configured in step 4)

## Step 2: Upload SA Key to Key Storage

The node source plugin and jobs need a Yandex Cloud Service Account key.
If you don't have one yet, [create a service account](https://yandex.cloud/en/docs/iam/operations/sa/create) and [generate an authorized key](https://yandex.cloud/en/docs/iam/operations/authentication/manage-authorized-keys#cli_1):

```bash
yc iam service-account create --name rundeck-scheduler
yc iam key create --service-account-name rundeck-scheduler --output sa-key.json
```

The service account must have permissions to start and stop the resources you want to manage (e.g., `compute.admin`, `mdb.admin`). See [Yandex Cloud roles reference](https://yandex.cloud/en/docs/iam/roles-reference) for details.

1. Encode the key: `base64 -i sa-key.json | tr -d '\n'`
2. Open **System Menu** (gear icon, top right) → **Key Storage**
3. Navigate to `project/<your-project-name>/`
   - Create folders if they don't exist: click **Add or Upload a Key** → select folder
4. Click **Add or Upload a Key**
   - **Key Type**: Password
   - **Name**: `yc-sa-key`
   - **Value**: paste the base64-encoded key
5. Save

The full path should be: `keys/project/<your-project-name>/yc-sa-key`

## Step 3: Add ACL Policy (optional — can be done automatically)

The node source plugin needs permission to read the SA key from Key Storage.
An example policy is in [acl/project-storage.aclpolicy](acl/project-storage.aclpolicy).

You can create the policy manually now, or skip this step — when the node source fails to read the key in step 4, Rundeck will show an "Unauthorized" warning with a ready-made ACL policy and a direct link to **System Settings → Access Control**. Just click the link and save.

**To create manually:**

1. Open **System Menu** → **Access Control**
2. Click **Create ACL Policy**
3. Fill in:
   - **Policy Name**: `<project-name>-storage`
   - **Description**: `Allow project to read SA key from Key Storage`
4. Paste the content from `acl/project-storage.aclpolicy`, replacing `<project-name>` with your actual project name
5. Save

## Step 4: Configure Node Source Plugin

1. Open your project → **Project Settings** → **Edit Nodes**
2. Click **Add a new Node Source**
3. Select **Yandex Cloud Node Source Plugin** from the list
4. Configure:
   - **YC Folder ID**: your Yandex Cloud folder ID (e.g., `b1g0abc123def456`)
   - **SA Key**: select the Key Storage path — `keys/project/<project-name>/yc-sa-key`
5. Click **Save**

After saving, wait a few seconds for the plugin to fetch resources, then go to **Nodes** tab in the project — you should see your YC resources listed.

If you skipped step 3, you will see an "Unauthorized" error instead. Rundeck will suggest the correct ACL policy and provide a direct link to **System Settings → Access Control** — follow it, save the suggested policy, then reload the Nodes page.

## Step 5: Import Jobs

Job definitions are in the [jobs/](jobs/) directory.

### Ready-to-use jobs

| File | Description |
| --- | --- |
| `jobs/stop-all.yaml` | Manual job — stop all resource types at once |
| `jobs/start-all.yaml` | Manual job — start all resource types at once |

Import via UI: **Jobs** → **Upload Definition** → select YAML → **Upload**. The `yc_sa_key` in the plugin step configuration uses `${job.project}` — Rundeck resolves it automatically at runtime.

### Generate per-resource-type jobs from templates

Templates `stop-RESOURCE_TYPE.yaml.tpl` and `start-RESOURCE_TYPE.yaml.tpl` let you generate scheduled jobs for any supported resource type.

**Supported resource types:**

- `compute-instance`
- `managed-postgresql`
- `managed-kubernetes`
- `network-load-balancer`

**Generate jobs for one type:**

```bash
RESOURCE_TYPE=compute-instance
sed "s/RESOURCE_TYPE/$RESOURCE_TYPE/g" jobs/stop-RESOURCE_TYPE.yaml.tpl > "jobs/stop-${RESOURCE_TYPE}.yaml"
sed "s/RESOURCE_TYPE/$RESOURCE_TYPE/g" jobs/start-RESOURCE_TYPE.yaml.tpl > "jobs/start-${RESOURCE_TYPE}.yaml"
```

**Generate jobs for all types at once:**

```bash
for rt in compute-instance managed-postgresql managed-kubernetes network-load-balancer; do
  sed "s/RESOURCE_TYPE/$rt/g" jobs/stop-RESOURCE_TYPE.yaml.tpl > "jobs/stop-${rt}.yaml"
  sed "s/RESOURCE_TYPE/$rt/g" jobs/start-RESOURCE_TYPE.yaml.tpl > "jobs/start-${rt}.yaml"
done
```

Then import the generated YAML files via UI.

### After Import

Jobs are imported without a schedule by default. To enable scheduling:

- Either uncomment the `schedule` block in the YAML file before importing
- Or configure via UI: **Job → Edit → Schedule tab** → set time, days, and time zone

## Repeat for Additional Projects

For each YC folder you want to manage, repeat steps 1-5 with a different project name and folder ID. Each project gets its own SA key in Key Storage and its own set of jobs.
