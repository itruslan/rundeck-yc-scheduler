#!/usr/bin/env python3
"""
Rundeck Dynamic Node Source — Yandex Cloud resources.

Execution context:
  Runs INSIDE the Rundeck container as part of the yc-node-source script plugin.
  Invoked by Rundeck as a ResourceModelSource (not a job step).

Environment (set by Rundeck from plugin.yaml config):
  RD_CONFIG_FOLDER_ID  — Yandex Cloud folder ID to list resources from.
  RD_CONFIG_YC_SA_KEY  — base64-encoded service account JSON key,
                         injected automatically by Rundeck from Key Storage
                         via valueConversion: STORAGE_PATH_AUTOMATIC_READ.
"""

import json
import os
import re
import sys
from typing import Any, Callable

import yandexcloud
from yandex.cloud.compute.v1 import instance_service_pb2, instance_service_pb2_grpc
from yandex.cloud.k8s.v1 import cluster_service_pb2 as k8s_cluster_service_pb2
from yandex.cloud.k8s.v1 import cluster_service_pb2_grpc as k8s_cluster_service_pb2_grpc
from yandex.cloud.loadbalancer.v1 import (
    network_load_balancer_service_pb2,
    network_load_balancer_service_pb2_grpc,
)
from yandex.cloud.mdb.postgresql.v1 import cluster_service_pb2, cluster_service_pb2_grpc
from yc_common import load_sdk_from_storage

# YC automatically names Kubernetes worker nodes as: 20 chars + dash + 4 chars.
K8S_NODE_PATTERN = re.compile(r"^[a-z0-9]{20}-[a-z0-9]{4}$")

# ---------------------------------------------------------------------------
# Status code → string mappings (for node attributes)
# ---------------------------------------------------------------------------

_COMPUTE_STATUSES = {
    0: "UNSPECIFIED",
    1: "PROVISIONING",
    2: "RUNNING",
    3: "STOPPING",
    4: "STOPPED",
    5: "STARTING",
    6: "RESTARTING",
    7: "UPDATING",
    8: "ERROR",
    9: "CRASHED",
    10: "DELETING",
}

_PG_STATUSES = {
    0: "STATUS_UNKNOWN",
    1: "CREATING",
    2: "RUNNING",
    3: "ERROR",
    4: "UPDATING",
    5: "STOPPING",
    6: "STOPPED",
    7: "STARTING",
}

_K8S_STATUSES = {
    0: "STATUS_UNSPECIFIED",
    1: "PROVISIONING",
    2: "RUNNING",
    3: "RECONCILING",
    4: "STOPPING",
    5: "STOPPED",
    6: "DELETING",
    7: "STARTING",
    8: "ERROR",
}

_NLB_STATUSES = {
    0: "STATUS_UNSPECIFIED",
    1: "CREATING",
    2: "STARTING",
    3: "ACTIVE",
    4: "STOPPING",
    5: "STOPPED",
    6: "DELETING",
    7: "INACTIVE",
}


def _status(mapping: dict[int, str], code: int) -> str:
    return mapping.get(code, str(code))


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def _paginate(list_fn: Callable, request_cls: Any, response_field: str, folder_id: str) -> list:
    """Fetch all pages from a YC list API."""
    items: list = []
    page_token = ""
    while True:
        response = list_fn(request_cls(folder_id=folder_id, page_token=page_token))
        items.extend(getattr(response, response_field))
        if not response.next_page_token:
            break
        page_token = response.next_page_token
    return items


def _to_node(
    resource: Any,
    resource_type: str,
    status_code: int,
    status_map: dict[int, str],
    folder_id: str,
    **extra: str,
) -> dict:
    """Convert a YC resource to Rundeck node format."""
    node: dict = {
        "nodename": resource.name,
        "hostname": "localhost",
        "username": "rundeck",
        "node-executor": "local",
        "file-copier": "local",
        "resource_id": resource.id,
        "resource_type": resource_type,
        "folder_id": folder_id,
        "stop_order": "1",
        "status": _status(status_map, status_code),
        "tags": resource_type,
        "description": resource.description or "",
        **extra,
    }
    for k, v in resource.labels.items():
        node[f"labels:{k}"] = v
        node["tags"] += f",label:{k}:{v}"
    return node


# ---------------------------------------------------------------------------
# Resource-specific list + convert functions
# ---------------------------------------------------------------------------


def list_compute_instances(sdk: yandexcloud.SDK, folder_id: str) -> list:
    svc = sdk.client(instance_service_pb2_grpc.InstanceServiceStub)
    return _paginate(svc.List, instance_service_pb2.ListInstancesRequest, "instances", folder_id)


def instance_to_node(instance: Any, folder_id: str) -> dict:
    """Convert a YC compute instance to Rundeck node format."""
    return _to_node(
        instance,
        "compute-instance",
        instance.status,
        _COMPUTE_STATUSES,
        folder_id,
        zone=instance.zone_id,
    )


def list_pg_clusters(sdk: yandexcloud.SDK, folder_id: str) -> list:
    svc = sdk.client(cluster_service_pb2_grpc.ClusterServiceStub)
    return _paginate(svc.List, cluster_service_pb2.ListClustersRequest, "clusters", folder_id)


def pg_cluster_to_node(cluster: Any, folder_id: str) -> dict:
    """Convert a YC managed-postgresql cluster to Rundeck node format."""
    return _to_node(cluster, "managed-postgresql", cluster.status, _PG_STATUSES, folder_id)


def list_k8s_clusters(sdk: yandexcloud.SDK, folder_id: str) -> list:
    svc = sdk.client(k8s_cluster_service_pb2_grpc.ClusterServiceStub)
    return _paginate(svc.List, k8s_cluster_service_pb2.ListClustersRequest, "clusters", folder_id)


def k8s_cluster_to_node(cluster: Any, folder_id: str) -> dict:
    """Convert a YC managed-kubernetes cluster to Rundeck node format."""
    return _to_node(cluster, "managed-kubernetes", cluster.status, _K8S_STATUSES, folder_id)


def list_nlb(sdk: yandexcloud.SDK, folder_id: str) -> list:
    svc = sdk.client(network_load_balancer_service_pb2_grpc.NetworkLoadBalancerServiceStub)
    return _paginate(
        svc.List,
        network_load_balancer_service_pb2.ListNetworkLoadBalancersRequest,
        "network_load_balancers",
        folder_id,
    )


def nlb_to_node(balancer: Any, folder_id: str) -> dict:
    """Convert a YC network load balancer to Rundeck node format."""
    return _to_node(balancer, "network-load-balancer", balancer.status, _NLB_STATUSES, folder_id)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    folder_id = os.environ.get("RD_CONFIG_FOLDER_ID")
    if not folder_id:
        print("ERROR: RD_CONFIG_FOLDER_ID is not set", file=sys.stderr)
        sys.exit(1)

    sdk = load_sdk_from_storage()
    nodes: dict = {}

    # Compute instances are the primary resource type — fail hard if unavailable.
    # Other resource types log a warning and continue so that partial results
    # are still returned to Rundeck (graceful degradation).
    try:
        instances = list_compute_instances(sdk, folder_id)
    except Exception as e:
        print(f"ERROR: failed to list compute instances: {e}", file=sys.stderr)
        sys.exit(1)

    for instance in instances:
        if K8S_NODE_PATTERN.match(instance.name):
            continue
        nodes[instance.name] = instance_to_node(instance, folder_id)

    try:
        for cluster in list_pg_clusters(sdk, folder_id):
            nodes[cluster.name] = pg_cluster_to_node(cluster, folder_id)
    except Exception as e:
        print(f"WARNING: failed to list managed-postgresql clusters: {e}", file=sys.stderr)

    try:
        for cluster in list_k8s_clusters(sdk, folder_id):
            nodes[cluster.name] = k8s_cluster_to_node(cluster, folder_id)
    except Exception as e:
        print(f"WARNING: failed to list managed-kubernetes clusters: {e}", file=sys.stderr)

    try:
        for balancer in list_nlb(sdk, folder_id):
            nodes[balancer.name] = nlb_to_node(balancer, folder_id)
    except Exception as e:
        print(f"WARNING: failed to list network load balancers: {e}", file=sys.stderr)

    print(json.dumps(nodes, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
