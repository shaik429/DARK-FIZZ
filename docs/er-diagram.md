# StockSense – Database ER Diagram

Every stock change is a move between two locations. Vendor, Customer and
Adjustment are virtual locations, so receipts, deliveries, transfers and
adjustments all use the same tables. `stock_moves` is the append-only ledger;
`stock_quants` holds on-hand quantity per product per location.

```mermaid
erDiagram
    users ||--o{ password_resets : "requests"
    users ||--o{ operations : "creates"
    users ||--o{ stock_moves : "performs"
    warehouses ||--o{ locations : "contains"
    warehouses ||--o{ reorder_rules : "scopes"
    categories ||--o{ products : "groups"
    uoms ||--o{ products : "measures"
    products ||--o{ reorder_rules : "has"
    products ||--o{ stock_quants : "stocked as"
    products ||--o{ operation_lines : "listed in"
    products ||--o{ stock_moves : "moved in"
    locations ||--o{ stock_quants : "holds"
    locations ||--o{ operations : "source / destination"
    locations ||--o{ stock_moves : "from / to"
    partners ||--o{ operations : "supplier / customer"
    operations ||--o{ operation_lines : "has"
    operations ||--o{ stock_moves : "produces"

    users { int id PK
        string email UK
        string password_hash
        enum role "manager | staff" }
    password_resets { int id PK
        int user_id FK
        string otp_hash
        datetime expires_at
        int attempts }
    warehouses { int id PK
        string name UK
        string code UK }
    locations { int id PK
        int warehouse_id FK "NULL for virtual"
        string name
        enum type "internal | vendor | customer | adjustment" }
    categories { int id PK
        string name UK }
    uoms { int id PK
        string name UK }
    partners { int id PK
        string name
        enum type "supplier | customer" }
    products { int id PK
        string sku UK
        string name
        int category_id FK
        int uom_id FK }
    reorder_rules { int id PK
        int product_id FK
        int warehouse_id FK
        decimal min_qty "0 <= min <= max"
        decimal max_qty }
    stock_quants { int product_id PK, FK
        int location_id PK, FK
        decimal quantity "CHECK >= 0" }
    operations { int id PK
        string reference UK
        enum type "receipt | delivery | internal | adjustment"
        enum status "draft | waiting | ready | done | canceled"
        int source_location_id FK "CHECK <> dest"
        int dest_location_id FK }
    operation_lines { int id PK
        int operation_id FK "UNIQUE with product_id"
        int product_id FK
        decimal quantity "CHECK >= 0" }
    stock_moves { int id PK
        int operation_id FK
        int product_id FK
        int from_location_id FK
        int to_location_id FK
        decimal quantity "CHECK > 0" }
```