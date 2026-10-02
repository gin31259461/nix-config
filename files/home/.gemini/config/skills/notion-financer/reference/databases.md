# Financer Databases

Live schema was fetched from Notion on 2026-07-02. Re-fetch before writes if a property is missing, a write fails, or the user appears to have changed the workspace.

## Data Sources

| Area | Database ID | Data source |
| --- | --- | --- |
| Transactions DB | `374e5198-eb31-808f-a025-c7a2ae9235be` | `collection://374e5198-eb31-80db-829c-000bc278fc83` |
| Accounts DB | `374e5198-eb31-8008-a35f-e52a814187f2` | `collection://374e5198-eb31-8050-a7fa-000bf463ec46` |
| Categories DB | `374e5198-eb31-809e-b556-dd8d190294c4` | `collection://374e5198-eb31-80c8-a554-000ba26b86da` |
| Fixed Expenses DB | `374e5198-eb31-8092-b7d9-d301b0d9ca5f` | `collection://374e5198-eb31-80ed-8947-000b9e7a9884` |
| Monthly Report DB | `e7945e71-b228-4e1f-9a0e-ac1c1ebfe593` | `collection://aa21aa5c-c752-43df-9f62-fa7b9d8c9259` |

## Transactions DB

Writable fields:

- `Item Name` title
- `Type` select: `Income`, `Expense`
- `Amount` number, New Taiwan dollar format
- `date:Date:start`, `date:Date:end`, `date:Date:is_datetime`
- `Category` relation to Categories DB, JSON array of page URLs
- `Account` relation to Accounts DB, JSON array of page URLs

Read-only formulas:

- `Expense_Amount`
- `Income_Amount`
- `Flow_Amount`

Example query:

```sql
SELECT url, "Item Name", "Type", "Amount", "date:Date:start", "Category", "Account"
FROM "collection://374e5198-eb31-80db-829c-000bc278fc83"
WHERE "date:Date:start" >= ? AND "date:Date:start" < ?
ORDER BY "date:Date:start" DESC
```

## Accounts DB

Writable fields:

- `Account Name` title
- `Initial Balance` number, New Taiwan dollar format
- `Transactions` relation to Transactions DB, normally populated by reciprocal transaction relations

Read-only computed fields:

- `Net Flow` rollup
- `Current Balance` formula

Known account observed on 2026-07-02:

- `現金` at `https://app.notion.com/374e5198eb31807d9964c2ad6b711928`

## Categories DB

Writable fields:

- `Category Name` title
- `Monthly Budget` number, New Taiwan dollar format
- `Transactions` relation to Transactions DB, normally populated by reciprocal transaction relations
- `Fixed Expenses DB` relation to Fixed Expenses DB, normally populated by reciprocal fixed-expense relations

Read-only computed field:

- `Total Spent` rollup

Known categories observed on 2026-07-02:

- `交通費` at `https://app.notion.com/374e5198eb318102825ce2b04232f01d`
- `娛樂` at `https://app.notion.com/374e5198eb31803c8d44c137d826f381`
- `稅務` at `https://app.notion.com/374e5198eb3180e59437fa7bf53603e2`
- `訂閱服務` at `https://app.notion.com/374e5198eb318081b07de1422820cc91`
- `貸款` at `https://app.notion.com/374e5198eb318041a50ee3abde8fe593`
- `醫療` at `https://app.notion.com/374e5198eb31806c9041eda518aedc77`
- `電信費` at `https://app.notion.com/374e5198eb31803bb29ddc1c65d82f87`
- `餐飲` at `https://app.notion.com/374e5198eb318133a2acd5d4784d2883`

## Fixed Expenses DB

Writable fields:

- `Item Name` title
- `Amount` number, New Taiwan dollar format
- `Billing Cycle` select: `Monthly`, `Annually`
- `date:Start Date:start`, `date:Start Date:end`, `date:Start Date:is_datetime`
- `Total Months` number
- `Category` relation to Categories DB, JSON array of page URLs

Read-only computed field:

- `Monthly Amortization` formula

Use `Total Months` only for finite amortized expenses. For ordinary recurring monthly or annual bills, leave it empty unless the user specifies an end period.

## Monthly Report DB

Writable fields:

- `Month` title, use `YYYY-MM`
- `date:Period Start:start`, `date:Period Start:end`, `date:Period Start:is_datetime`
- `Notes` text
- `Transactions` relation to Transactions DB, JSON array of page URLs
- `Fixed Expenses` relation to Fixed Expenses DB, JSON array of page URLs

Read-only computed fields:

- `Total Income` rollup
- `Variable Spending` rollup
- `Fixed Burden` rollup
- `Total Spending` formula
- `Net` formula

## SQL Patterns

Resolve an account:

```sql
SELECT url, "Account Name", "Initial Balance"
FROM "collection://374e5198-eb31-8050-a7fa-000bf463ec46"
WHERE lower("Account Name") = lower(?)
LIMIT 5
```

Resolve a category:

```sql
SELECT url, "Category Name", "Monthly Budget"
FROM "collection://374e5198-eb31-80c8-a554-000ba26b86da"
WHERE lower("Category Name") = lower(?)
LIMIT 5
```

Filter transactions by related page URL:

```sql
SELECT url, "Item Name", "Type", "Amount", "date:Date:start"
FROM "collection://374e5198-eb31-80db-829c-000bc278fc83"
WHERE "Account" LIKE ?
ORDER BY "date:Date:start" DESC
```

Pass `%https://app.notion.com/page_id_without_dashes%` as the relation-match parameter.
