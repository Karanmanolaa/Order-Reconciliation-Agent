from datetime import datetime


def decide_action(status, live_order=None, warehouse_order=None):
    if status == "MATCH":
        return {
            "action": "NO_ACTION",
            "reason": "Live and warehouse already agree, nothing to reconcile."
        }

    if status == "LIVE_ONLY":
        return {
            "action": "ACCEPT_LIVE",
            "reason": "No warehouse record yet because most likely this order came in after the last snapshot. Using live data."
        }

    if status == "SNAPSHOT_ONLY":
        return {
            "action": "ACCEPT_SNAPSHOT",
            "reason": "Order is in the warehouse but never appeared in the event stream, which suggests a missed event rather than a timing gap. Accepting the snapshot, flagging for review."
        }

    if status == "CONFLICT":
        live_time = datetime.fromisoformat(live_order["last_updated"])
        snapshot_time = datetime.fromisoformat(
            warehouse_order["snapshot_time"]
        )
        # For conflicts, use timestamps to determine which source has the latest state.
        if live_time > snapshot_time:
            return {
                "action": "ACCEPT_LIVE",
                "reason": "Live was updated after this snapshot was taken, so the warehouse just hasn't caught up yet. Using live data."
            }

        else:
            return {
                "action": "ACCEPT_SNAPSHOT",
                "reason": "Live hasn't changed since before the snapshot, yet they disagree , the warehouse reflects a change the stream never emitted. Accepting the snapshot, flagging for review."
            }


def compare_orders(live_orders, warehouse_orders):
    warehouse_lookup = {}

    for order in warehouse_orders:
        warehouse_lookup[order["order_id"]] = order

    results = []

    all_order_ids = set(live_orders) | set(warehouse_lookup)

    for order_id in sorted(all_order_ids):
        live_order = live_orders.get(order_id)
        warehouse_order = warehouse_lookup.get(order_id)

        if live_order is None:
            status = "SNAPSHOT_ONLY"

        elif warehouse_order is None:
            status = "LIVE_ONLY"

        elif (
            live_order["status"] == warehouse_order["status"]
            and live_order["amount"] == warehouse_order["amount"]
        ):
            status = "MATCH"

        else:
            status = "CONFLICT"

        decision = decide_action(
            status,
            live_order,
            warehouse_order
        )

        results.append({
            "order_id": order_id,
            "status": status,
            "action": decision["action"],
            "reason": decision["reason"],
            "live_order": live_order,
            "warehouse_order": warehouse_order
        })

    return results