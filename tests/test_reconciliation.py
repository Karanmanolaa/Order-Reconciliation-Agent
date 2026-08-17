import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

from reconciliation import compare_orders


def test_live_only_order():
    live_orders = {
        "ORD001": {
            "order_id": "ORD001",
            "status": "PROCESSING",
            "amount": 100,
            "last_updated": "2026-08-15T10:00:00"
        }
    }

    warehouse_orders = []

    result = compare_orders(
        live_orders,
        warehouse_orders
    )

    assert result[0]["status"] == "LIVE_ONLY"
    assert result[0]["action"] == "ACCEPT_LIVE"


def test_snapshot_only_order():
    live_orders = {}

    warehouse_orders = [
        {
            "order_id": "ORD002",
            "status": "PROCESSING",
            "amount": 200,
            "snapshot_time": "2026-08-15T12:00:00"
        }
    ]

    result = compare_orders(
        live_orders,
        warehouse_orders
    )

    assert result[0]["status"] == "SNAPSHOT_ONLY"
    assert result[0]["action"] == "ACCEPT_SNAPSHOT"


def test_conflict_uses_newer_live_update():

    live_orders = {
        "ORD003": {
            "order_id": "ORD003",
            "status": "SHIPPED",
            "amount": 100,
            "last_updated": "2026-08-15T15:00:00"
        }
    }

    warehouse_orders = [
        {
            "order_id": "ORD003",
            "status": "PROCESSING",
            "amount": 100,
            "snapshot_time": "2026-08-15T12:00:00"
        }
    ]

    result = compare_orders(
        live_orders,
        warehouse_orders
    )

    assert result[0]["status"] == "CONFLICT"
    assert result[0]["action"] == "ACCEPT_LIVE"


def test_conflict_uses_snapshot_when_snapshot_is_newer():

    live_orders = {
        "ORD005": {
            "order_id": "ORD005",
            "status": "PROCESSING",
            "amount": 300,
            "last_updated": "2026-08-15T12:00:00"
        }
    }

    warehouse_orders = [
        {
            "order_id": "ORD005",
            "status": "CANCELLED",
            "amount": 300,
            "snapshot_time": "2026-08-15T15:00:00" 
        }
    ]

    result = compare_orders(
        live_orders,
        warehouse_orders
    )

    assert result[0]["status"] == "CONFLICT"
    assert result[0]["action"] == "ACCEPT_SNAPSHOT"