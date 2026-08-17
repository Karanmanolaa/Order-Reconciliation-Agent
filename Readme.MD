# Order Reconciliation Agent

## Overview

This project implements an order reconciliation system that compares two different sources of order data:

- A live event stream containing order changes (create, update, cancel)
- A warehouse snapshot containing the current stored state

The purpose of the system is to identify differences between these sources, decide which state should be accepted, store the final reconciled state, and ensure the same reconciliation is not applied more than once.

---

## Problem

In real systems, the same business data is usually stored across multiple services.

For example, an order may appear in:

- A live operational system receiving events immediately
- A warehouse database updated periodically

Because these systems do not update at exactly the same time, differences can occur.

Examples:

- An order exists in the live system but is missing from the warehouse snapshot.
- The warehouse contains an order that never appeared in the event stream.
- Both systems contain the order but disagree on the current status.
- The same reconciliation job runs multiple times.

This project focuses on building a simple and explainable process for resolving these situations.

---

# How the system works

The reconciliation flow is:

```
Live Events
     |
     v
Build Current Order State
     |
     v
Compare with Warehouse Snapshot
     |
     v
Apply Reconciliation Rules
     |
     v
Save Final State and Reconciliation History
```

---

# Reconciliation Strategy

The system first classifies each order into one of four categories.

## 1. MATCH

The live system and warehouse snapshot contain the same order information.

Example:

```
Live:
ORD001 - PROCESSING

Warehouse:
ORD001 - PROCESSING
```

Action:

```
NO_ACTION
```

No update is required.

---

## 2. LIVE_ONLY

The order exists in the live event stream but not in the warehouse snapshot.

Example:

```
Live:
ORD003 - PROCESSING

Warehouse:
Not found
```

Decision:

```
ACCEPT_LIVE
```

The live state is accepted because the order was most likely created after the previous warehouse snapshot.

---

## 3. SNAPSHOT_ONLY

The order exists in the warehouse snapshot but no matching live event exists.

Example:

```
Warehouse:
ORD004 - PROCESSING

Live:
Not found
```

Decision:

```
ACCEPT_SNAPSHOT
```

The snapshot is accepted to avoid losing existing data.

This case is treated as suspicious because it may indicate a missing event in the live pipeline.

---

## 4. CONFLICT

Both sources contain the order but have different states.

Example:

```
Live:
ORD001 - SHIPPED
Updated: 15:00


Warehouse:
ORD001 - PROCESSING
Snapshot: 12:00
```

For conflicts, the system compares timestamps.

Rules:

- If the live update happened after the warehouse snapshot, the live state is accepted.
- If the warehouse contains a newer state, the snapshot is accepted and the case is flagged for review.

This avoids blindly trusting one source and keeps the decision explainable.

---

# Idempotency

A reconciliation process should be safe to run multiple times.

To handle this, every reconciliation creates an input fingerprint based on:

- Order ID
- Selected action
- Live order state
- Warehouse order state

Before applying a reconciliation, the system checks whether that fingerprint has already been processed.

Example:

First run:

```
ORD001 → ACCEPT_LIVE
Saved
```

Second run:

```
ORD001 → Skipped (already reconciled)
```

This prevents duplicate corrections and keeps the reconciliation history consistent.

---

# Database

SQLite is used as the persistent ledger.

## Orders table

Stores the final accepted order state.

Fields:

```
order_id
status
amount
source
last_updated
```

## Reconciliation history table

Stores every reconciliation decision.

Fields:

```
order_id
action
reason
input_hash
processed_time
```

This provides an audit trail showing why a particular state was selected.

---

# Project Structure

```
lec_order_reconciliation/

|-- data/
|-- |_ live_events.json
│   |_ warehouse_snapshot.json
│
├── tests/
│   ├── test_reconciliation.py
│   └── test_idempotency.py
│
├── main.py
├── reconciliation.py
├── database.py
├── check_database.py
├── requirements.txt
└── README.md
```

---

# Running the Project

## Create virtual environment

```bash
python3 -m venv venv
```

Activate:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the reconciliation agent:

```bash
python3 main.py
```

Example output:

```
ORD001 | CONFLICT | ACCEPT_LIVE
ORD002 | CONFLICT | ACCEPT_LIVE
ORD003 | LIVE_ONLY | ACCEPT_LIVE
ORD004 | SNAPSHOT_ONLY | ACCEPT_SNAPSHOT
```

---

# Running Tests

The project includes tests for:

- Live-only orders
- Snapshot-only orders
- Conflict resolution using timestamps
- Idempotent reconciliation processing

Run:

```bash
pytest
```

Expected output:

```
5 passed
```

---

# Design Decisions

## Why timestamp-based conflict resolution?

Neither source can always be considered correct.

A live system may contain updates that have not reached the warehouse yet.

A warehouse snapshot may contain information that was missed by the event stream.

Using timestamps provides a simple rule that is easy to understand and explain.

---

## Why SQLite?

For a production system, a larger database would likely be used.

SQLite was chosen because it provides:

- Persistent storage
- Transactions
- Simple local setup

while still demonstrating the core behaviour of a reconciliation ledger.

---

# Possible Improvements

If this was extended into a production system, the next improvements would be:

- Replace JSON files with a real event stream
- Add a message queue such as Kafka
- Create a manual review workflow for flagged conflicts
- Add monitoring and reconciliation metrics
- Add retry handling for failed processing

---

# Summary

This project demonstrates a complete reconciliation workflow:

- Detecting differences between data sources
- Applying explainable resolution rules
- Maintaining a persistent ledger
- Recording reconciliation history
- Preventing duplicate processing through idempotency
