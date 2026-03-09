#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""Rundeck API helper for e2e tests.

Environment variables:
  RUNDECK_URL    Rundeck base URL (default: http://localhost:4440)
  RUNDECK_TOKEN  Rundeck API token

Commands:
  wait-node  --project P --resource-id ID [--timeout 120]
  run-job    --project P --group G --name N --resource-id ID [--timeout 300]
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import requests

_API = "/api/14"


def _session() -> requests.Session:
    url = os.environ.get("RUNDECK_URL", "http://localhost:4440").rstrip("/")
    token = os.environ["RUNDECK_TOKEN"]
    s = requests.Session()
    s.headers.update(
        {
            "X-Rundeck-Auth-Token": token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    )
    s._base_url = url  # type: ignore[attr-defined]
    return s


def _url(s: requests.Session, path: str) -> str:
    return f"{s._base_url}{_API}{path}"  # type: ignore[attr-defined]


def cmd_wait_node(args: argparse.Namespace) -> None:
    """Poll Rundeck node source until the resource appears."""
    s = _session()
    deadline = time.monotonic() + args.timeout
    attempt = 0

    while time.monotonic() < deadline:
        attempt += 1

        try:
            s.post(_url(s, f"/project/{args.project}/resources/refresh"), timeout=10)
        except requests.RequestException:
            pass

        time.sleep(5)

        try:
            resp = s.get(
                _url(s, f"/project/{args.project}/resources"),
                params={"format": "json"},
                timeout=10,
            )
            if resp.ok:
                for node_name, attrs in resp.json().items():
                    if attrs.get("resource_id") == args.resource_id:
                        print(f"[{attempt}] Node found: {node_name}")
                        return
        except requests.RequestException as exc:
            print(f"[{attempt}] Request error: {exc}")

        remaining = max(0, int(deadline - time.monotonic()))
        print(f"[{attempt}] Node not found, {remaining}s remaining...")
        time.sleep(10)

    print(
        f"ERROR: Node {args.resource_id} did not appear within {args.timeout}s",
        file=sys.stderr,
    )
    sys.exit(1)


def cmd_run_job(args: argparse.Namespace) -> None:
    """Find a job by group+name, run it filtered to a specific resource, wait for completion."""
    s = _session()

    resp = s.get(
        _url(s, f"/project/{args.project}/jobs"),
        params={"groupPath": args.group, "jobExactFilter": args.name},
        timeout=10,
    )
    resp.raise_for_status()
    jobs = resp.json()
    if not jobs:
        print(
            f"ERROR: Job '{args.group}/{args.name}' not found in project {args.project}",
            file=sys.stderr,
        )
        sys.exit(1)
    job_id = jobs[0]["id"]
    print(f"Job found: {job_id}")

    resp = s.post(
        _url(s, f"/job/{job_id}/run"),
        json={"filter": f"resource_id: {args.resource_id}"},
        timeout=10,
    )
    resp.raise_for_status()
    exec_id = resp.json()["id"]
    print(f"Execution started: {exec_id}")

    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        resp = s.get(_url(s, f"/execution/{exec_id}"), timeout=10)
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status")
        print(f"  status: {status}")
        if status == "succeeded":
            print("Job succeeded")
            return
        if status in ("failed", "aborted"):
            print(f"ERROR: Job {status}", file=sys.stderr)
            sys.exit(1)
        time.sleep(10)

    print(f"ERROR: Execution {exec_id} timed out after {args.timeout}s", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_wait = sub.add_parser("wait-node", help="Wait for a node to appear in Rundeck node source")
    p_wait.add_argument("--project", required=True)
    p_wait.add_argument("--resource-id", required=True)
    p_wait.add_argument("--timeout", type=int, default=120)
    p_wait.set_defaults(func=cmd_wait_node)

    p_job = sub.add_parser("run-job", help="Run a Rundeck job and wait for completion")
    p_job.add_argument("--project", required=True)
    p_job.add_argument("--group", required=True)
    p_job.add_argument("--name", required=True)
    p_job.add_argument("--resource-id", required=True)
    p_job.add_argument("--timeout", type=int, default=300)
    p_job.set_defaults(func=cmd_run_job)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
