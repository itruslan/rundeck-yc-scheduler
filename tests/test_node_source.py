"""Tests for node_source.py."""

import json
from unittest.mock import MagicMock

import node_source


def _make_resource(name="my-resource", id="res-id", status=2, labels=None, description=""):
    r = MagicMock()
    r.name = name
    r.id = id
    r.status = status
    r.labels = labels or {}
    r.description = description
    return r


class TestStatus:
    def test_known_code(self):
        assert node_source._status({2: "RUNNING"}, 2) == "RUNNING"

    def test_unknown_code_returns_string(self):
        assert node_source._status({}, 99) == "99"


class TestPaginate:
    def test_single_page(self):
        response = MagicMock()
        response.instances = [MagicMock(), MagicMock()]
        response.next_page_token = ""
        list_fn = MagicMock(return_value=response)

        result = node_source._paginate(list_fn, MagicMock(), "instances", "folder-id")

        assert len(result) == 2
        list_fn.assert_called_once()

    def test_multiple_pages(self):
        page1 = MagicMock()
        page1.items = [MagicMock()]
        page1.next_page_token = "token-1"

        page2 = MagicMock()
        page2.items = [MagicMock(), MagicMock()]
        page2.next_page_token = ""

        list_fn = MagicMock(side_effect=[page1, page2])

        result = node_source._paginate(list_fn, MagicMock(), "items", "folder-id")

        assert len(result) == 3
        assert list_fn.call_count == 2


class TestToNode:
    def test_basic_fields(self):
        resource = _make_resource(name="my-vm", id="vm-id", status=2)
        node = node_source._to_node(resource, "compute-instance", 2, {2: "RUNNING"}, "folder-1")

        assert node["nodename"] == "my-vm"
        assert node["resource_id"] == "vm-id"
        assert node["resource_type"] == "compute-instance"
        assert node["status"] == "RUNNING"
        assert node["folder_id"] == "folder-1"
        assert node["hostname"] == "localhost"

    def test_labels_added(self):
        resource = _make_resource(labels={"env": "prod", "team": "sre"})
        node = node_source._to_node(resource, "compute-instance", 2, {}, "folder-1")

        assert node["labels:env"] == "prod"
        assert node["labels:team"] == "sre"
        assert "label:env:prod" in node["tags"]

    def test_extra_fields(self):
        resource = _make_resource()
        node = node_source._to_node(
            resource, "compute-instance", 2, {}, "folder-1", zone="ru-central1-a"
        )
        assert node["zone"] == "ru-central1-a"


class TestInstanceToNode:
    def test_output(self):
        instance = _make_resource(name="web-server", id="inst-1", status=2)
        instance.zone_id = "ru-central1-a"

        node = node_source.instance_to_node(instance, "folder-1")

        assert node["resource_type"] == "compute-instance"
        assert node["zone"] == "ru-central1-a"


class TestPgClusterToNode:
    def test_output(self):
        cluster = _make_resource(name="pg-prod", id="pg-1", status=2)
        node = node_source.pg_cluster_to_node(cluster, "folder-1")

        assert node["resource_type"] == "managed-postgresql"


class TestK8sClusterToNode:
    def test_output(self):
        cluster = _make_resource(name="k8s-prod", id="k8s-1", status=2)
        node = node_source.k8s_cluster_to_node(cluster, "folder-1")

        assert node["resource_type"] == "managed-kubernetes"


class TestNlbToNode:
    def test_output(self):
        balancer = _make_resource(name="nlb-prod", id="nlb-1", status=3)
        node = node_source.nlb_to_node(balancer, "folder-1")

        assert node["resource_type"] == "network-load-balancer"


class TestAlbToNode:
    def test_output(self):
        balancer = _make_resource(name="alb-prod", id="alb-1", status=3)
        node = node_source.alb_to_node(balancer, "folder-1")

        assert node["resource_type"] == "application-load-balancer"
        assert node["status"] == "ACTIVE"


class TestRedisClusterToNode:
    def test_output(self):
        cluster = _make_resource(name="redis-prod", id="redis-1", status=2)
        node = node_source.redis_cluster_to_node(cluster, "folder-1")

        assert node["resource_type"] == "managed-redis"
        assert node["status"] == "RUNNING"


class TestMysqlClusterToNode:
    def test_output(self):
        cluster = _make_resource(name="mysql-prod", id="mysql-1", status=2)
        node = node_source.mysql_cluster_to_node(cluster, "folder-1")

        assert node["resource_type"] == "managed-mysql"
        assert node["status"] == "RUNNING"


class TestK8sNodeFilter:
    """K8S worker nodes (auto-named) must be excluded from the node list."""

    def test_k8s_node_pattern_matches(self):
        assert node_source.K8S_NODE_PATTERN.match("abcdefghij1234567890-ab12")

    def test_k8s_node_pattern_no_match(self):
        assert not node_source.K8S_NODE_PATTERN.match("my-regular-vm")

    def test_main_filters_k8s_nodes(self, monkeypatch, mocker, capsys):
        monkeypatch.setenv("RD_CONFIG_FOLDER_ID", "folder-1")
        monkeypatch.setenv("RD_CONFIG_YC_SA_KEY", "dGVzdA==")  # "test" in base64

        k8s_worker = _make_resource(name="abcdefghij1234567890-ab12")
        k8s_worker.zone_id = "ru-central1-a"
        regular_vm = _make_resource(name="web-server")
        regular_vm.zone_id = "ru-central1-a"

        mocker.patch("node_source.load_sdk_from_storage", return_value=MagicMock())
        mocker.patch("node_source.list_compute_instances", return_value=[k8s_worker, regular_vm])
        mocker.patch("node_source.list_pg_clusters", return_value=[])
        mocker.patch("node_source.list_k8s_clusters", return_value=[])
        mocker.patch("node_source.list_nlb", return_value=[])
        mocker.patch("node_source.list_kafka_clusters", return_value=[])
        mocker.patch("node_source.list_alb", return_value=[])
        mocker.patch("node_source.list_redis_clusters", return_value=[])
        mocker.patch("node_source.list_mysql_clusters", return_value=[])

        node_source.main()

        output = json.loads(capsys.readouterr().out)
        assert "web-server" in output
        assert "abcdefghij1234567890-ab12" not in output
