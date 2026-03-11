-include .env
export

IMAGE        := rundeck-yc-scheduler:local
RUNDECK_URL  := http://localhost:4440
TF_DIR       := examples/configuration/terraform-rundeck-yc-scheduler
TOKEN_FILE   := /tmp/rundeck-yc-token
COOKIE_FILE  := /tmp/rundeck-yc-cookie.txt

.PHONY: build up down restart logs token tf test e2e \
        _check-env _wait-rundeck _get-token

# ---------------------------------------------------------------------------
# Main targets
# ---------------------------------------------------------------------------

## Build the Docker image from local source
build:
	docker build -t $(IMAGE) .

## Build image, start Rundeck, configure via Terraform
up: _check-env build _run _wait-rundeck tf

## Stop and remove the Rundeck container
down:
	docker rm -f rundeck 2>/dev/null || true

## Restart: down + up
restart: down up

## Follow Rundeck container logs
logs:
	docker logs -f rundeck

## Print the stored API token (set during 'make up')
token:
	@cat $(TOKEN_FILE)

## Re-run Terraform against already-running Rundeck (e.g. after config change)
tf: _check-env _get-token
	@SA_KEY_B64=$$(base64 < $$(eval echo $(YC_SA_KEY_FILE))); \
	TYPES=$$(python3 -c " \
	import json, os; \
	types = [t.strip() for t in os.environ['RESOURCE_TYPES'].split(',')]; \
	print(json.dumps({t: {'enabled': True} for t in types})) \
	"); \
	cd $(TF_DIR) && \
	terraform init -input=false -reconfigure -upgrade > /dev/null && \
	TF_VAR_rundeck_url=$(RUNDECK_URL) \
	TF_VAR_rundeck_auth_token=$$(cat $(TOKEN_FILE)) \
	TF_VAR_projects="$$(jq -n \
		--arg folder_id "$(FOLDER_ID)" \
		--arg sa_key "$$SA_KEY_B64" \
		--argjson types "$$TYPES" \
		'[{"name":"dev","folder_id":$$folder_id,"yc_sa_key":$$sa_key,"resource_types":$$types}]')" \
	terraform apply -auto-approve -input=false

## Run unit tests
test:
	uv run pytest

## Run e2e helper against local Rundeck — pass ARGS="<subcommand> ..."
## Examples:
##   make e2e ARGS="wait-node --project dev --resource-id <id>"
##   make e2e ARGS="run-job --project dev --group e2e/compute-instance --name Stop --resource-id <id>"
e2e: _get-token
	RUNDECK_URL=$(RUNDECK_URL) \
	RUNDECK_TOKEN=$$(cat $(TOKEN_FILE)) \
	uv run tests/e2e/rundeck.py $(ARGS)

# ---------------------------------------------------------------------------
# Internal targets
# ---------------------------------------------------------------------------

_check-env:
	@[ -f .env ] || { echo "ERROR: .env not found — copy .env.example and fill in values"; exit 1; }
	@[ -n "$(FOLDER_ID)" ] || { echo "ERROR: FOLDER_ID is not set in .env"; exit 1; }
	@[ -n "$(YC_SA_KEY_FILE)" ] || { echo "ERROR: YC_SA_KEY_FILE is not set in .env"; exit 1; }
	@[ -f $$(eval echo $(YC_SA_KEY_FILE)) ] || { echo "ERROR: SA key file not found: $(YC_SA_KEY_FILE)"; exit 1; }

_run:
	docker rm -f rundeck 2>/dev/null || true
	docker run -d --name rundeck -p 4440:4440 $(IMAGE)

_wait-rundeck:
	@echo "Waiting for Rundeck to start..."
	@for i in $$(seq 1 36); do \
		STATUS=$$(curl -s -o /dev/null -w "%{http_code}" --max-redirs 0 \
			-X POST -c $(COOKIE_FILE) \
			-H "Content-Type: application/x-www-form-urlencoded" \
			-d "j_username=admin&j_password=admin" \
			$(RUNDECK_URL)/j_security_check 2>/dev/null || echo 000); \
		[ "$$STATUS" = "302" ] && echo "Rundeck is ready" && \
			$(MAKE) --no-print-directory _get-token && exit 0; \
		echo "  [$$i/36] status $$STATUS, retrying..."; \
		sleep 5; \
	done; \
	echo "ERROR: Rundeck did not start within 3 minutes"; \
	docker logs rundeck; \
	exit 1

_get-token:
	@TOKEN=$$(curl -sf -b $(COOKIE_FILE) \
		-X POST $(RUNDECK_URL)/api/57/tokens/admin \
		-H "Accept: application/json" \
		-H "Content-Type: application/json" \
		-d '{"roles":"admin"}' 2>/dev/null | jq -r '.token // empty'); \
	if [ -z "$$TOKEN" ]; then \
		STATUS=$$(curl -s -o /dev/null -w "%{http_code}" --max-redirs 0 \
			-X POST -c $(COOKIE_FILE) \
			-H "Content-Type: application/x-www-form-urlencoded" \
			-d "j_username=admin&j_password=admin" \
			$(RUNDECK_URL)/j_security_check 2>/dev/null || echo 000); \
		TOKEN=$$(curl -sf -b $(COOKIE_FILE) \
			-X POST $(RUNDECK_URL)/api/57/tokens/admin \
			-H "Accept: application/json" \
			-H "Content-Type: application/json" \
			-d '{"roles":"admin"}' | jq -r '.token'); \
	fi; \
	echo "$$TOKEN" > $(TOKEN_FILE); \
	echo "Token saved to $(TOKEN_FILE)"
