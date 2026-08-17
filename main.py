import json
import hashlib

from database import (
    create_database,
    save_order,
    has_been_processed,
    save_reconciliation_history
)
from reconciliation import compare_orders

def create_input_hash(item):
    data = (
        item["order_id"]
        + item["action"]
        + str(item["live_order"])
        + str(item["warehouse_order"])
    )

    return hashlib.sha256(
        data.encode()
    ).hexdigest()

    
def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_current_orders(events):
    orders = {}

    for event in events:
        order_id = event["order_id"]

        # Store the latest event as the current state of this order.
        orders[order_id] = {
            "order_id": order_id,
            "status": event["status"],
            "amount": event["amount"],
            "last_event_id": event["event_id"],
            "last_event_type": event["event_type"],
            "last_updated": event["timestamp"]
        }

    return orders


def save_reconciled_orders(comparison):
    for item in comparison:

        order_id = item["order_id"]
        action = item["action"]
        reason = item["reason"]

        # Create a fingerprint so the same reconciliation is not applied twice.
        input_hash = create_input_hash(item)

        if has_been_processed(input_hash):
            print(
                f"{order_id} | Skipped (already reconciled)"
            )
            continue

        if action == "ACCEPT_LIVE":
            live_order = item["live_order"]

            order = {
                "order_id": live_order["order_id"],
                "status": live_order["status"],
                "amount": live_order["amount"],
                "source": "LIVE",
                "last_updated": live_order["last_updated"]
            }

            save_order(order)

        elif action == "ACCEPT_SNAPSHOT":
            warehouse_order = item["warehouse_order"]

            order = {
                "order_id": warehouse_order["order_id"],
                "status": warehouse_order["status"],
                "amount": warehouse_order["amount"],
                "source": "SNAPSHOT",
                "last_updated": warehouse_order["snapshot_time"]
            }

            save_order(order)

        save_reconciliation_history(
            order_id,
            action,
            reason,
            input_hash
        )

        print(
            f"{order_id} | Applied {action}"
        )

def main():
    live_events = read_json("data/live_events.json")
    warehouse_orders = read_json("data/warehouse_snapshot.json")

    current_orders = get_current_orders(live_events)

    comparison = compare_orders(
        current_orders,
        warehouse_orders
    )

    create_database()

    save_reconciled_orders(comparison)

    print("\nCurrent live orders")
    print("-------------------")

    for order in current_orders.values():
        print(
            f'{order["order_id"]} | '
            f'{order["status"]} | '
            f'£{order["amount"]} | '
            f'{order["last_updated"]}'
        )

    print("\nWarehouse snapshot")
    print("------------------")

    for order in warehouse_orders:
        print(
            f'{order["order_id"]} | '
            f'{order["status"]} | '
            f'£{order["amount"]} | '
            f'{order["snapshot_time"]}'
        )

    print("\nComparison")
    print("----------")

    for item in comparison:
        print(
            f'{item["order_id"]} | '
            f'{item["status"]} | '
            f'{item["action"]}'
        )

        print(
            f'   Reason: {item["reason"]}'
        )


if __name__ == "__main__":
    main()