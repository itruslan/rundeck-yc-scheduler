"""
Shared helpers for Yandex Cloud Rundeck plugin scripts.

Execution context:
  This module is imported by scripts that run INSIDE the Rundeck container
  as part of the yc-scheduler ScriptPlugin:
    - node_source.py    (yc-node-source — ResourceModelSource)
    - start.py          (yc-start — WorkflowNodeStep)
    - stop.py           (yc-stop  — WorkflowNodeStep)

  All scripts receive the SA key via RD_CONFIG_YC_SA_KEY, injected
  automatically by Rundeck from Key Storage.
"""

import base64
import binascii
import json
import os
import sys
import time

import yandexcloud

# ---------------------------------------------------------------------------
# Resource status codes
# ---------------------------------------------------------------------------

# Compute instance (Instance.Status)
COMPUTE_RUNNING = 2
COMPUTE_STOPPING = 3
COMPUTE_STOPPED = 4
COMPUTE_STARTING = 5

# Managed PostgreSQL cluster (Cluster.Status)
PG_RUNNING = 2
PG_STOPPING = 5
PG_STOPPED = 6
PG_STARTING = 7

# Managed Kubernetes cluster (Cluster.Status)
K8S_RUNNING = 2
K8S_STOPPING = 4
K8S_STOPPED = 5
K8S_STARTING = 7

# Network Load Balancer (NetworkLoadBalancer.Status)
NLB_ACTIVE = 3
NLB_STOPPING = 4
NLB_STOPPED = 5
NLB_STARTING = 2

# Managed Kafka cluster (Cluster.Status)
KAFKA_RUNNING = 2
KAFKA_STOPPING = 5
KAFKA_STOPPED = 6
KAFKA_STARTING = 7


def load_sdk_from_storage() -> yandexcloud.SDK:
    """Load Yandex Cloud SDK from RD_CONFIG_YC_SA_KEY env var.

    Used by node_source.py running as a Rundeck script plugin.
    Rundeck automatically reads the key from Key Storage and injects it
    via RD_CONFIG_YC_SA_KEY when valueConversion: STORAGE_PATH_AUTOMATIC_READ
    is configured in plugin.yaml.

    Returns:
        Configured yandexcloud.SDK instance.

    Raises:
        SystemExit: If RD_CONFIG_YC_SA_KEY is not set.
    """
    key_b64 = os.environ.get("RD_CONFIG_YC_SA_KEY")
    if not key_b64:
        print("ERROR: RD_CONFIG_YC_SA_KEY is not set", file=sys.stderr)
        sys.exit(1)

    return _sdk_from_key_b64(key_b64)


def _sdk_from_key_b64(key_b64: str) -> yandexcloud.SDK:
    """Decode a base64 SA key and return a configured SDK instance."""
    try:
        sa_key = json.loads(base64.b64decode(key_b64))
    except (binascii.Error, json.JSONDecodeError) as exc:
        print(f"ERROR: failed to decode SA key: {exc}", file=sys.stderr)
        sys.exit(1)
    return yandexcloud.SDK(service_account_key=sa_key)


def wait_for_operation(sdk: yandexcloud.SDK, operation_id: str, timeout: int = 300) -> None:
    """Poll operation until done or timeout.

    Args:
        sdk: Yandex Cloud SDK instance.
        operation_id: ID of the operation to wait for.
        timeout: Maximum wait time in seconds.

    Raises:
        RuntimeError: If the operation fails or times out.
    """
    from yandex.cloud.operation import operation_service_pb2, operation_service_pb2_grpc

    op_svc = sdk.client(operation_service_pb2_grpc.OperationServiceStub)
    deadline = time.time() + timeout

    while time.time() < deadline:
        op = op_svc.Get(operation_service_pb2.GetOperationRequest(operation_id=operation_id))
        if op.done:
            if op.HasField("error"):
                raise RuntimeError(f"operation failed: {op.error.message}")
            return
        print(f"  waiting... (operation {operation_id})")
        time.sleep(5)

    raise RuntimeError(f"operation timed out after {timeout}s")
