---
name: notion-financer
description: Manage the user's Financer Notion workspace: log income and expenses, add accounts, add categories and budgets, maintain fixed expenses, query balances and spending, reconcile transactions, and create monthly finance reports. Use when the user asks about personal finance records, transactions, accounts, categories, recurring bills, budgets, monthly summaries, or Financer data in Notion.
---

# Notion Financer

Use the Notion MCP tools to operate the user's `Financer` Notion workspace. Read `reference/databases.md` before doing any finance write, monthly report, schema-sensitive query, or relation mapping.

## Operating Rules

- Fetch the relevant database before writes when schema freshness matters; use the reference file as the starting map, not as a substitute for live validation.
- Store transaction `Amount` values as positive numbers. Use `Type` to distinguish `Income` from `Expense`.
- Treat currency values as New Taiwan dollars unless the user specifies otherwise.
- Resolve relative dates against the user's current date and timezone from the conversation environment.
- Do not write formula, rollup, created-time, or read-only properties.
- Ask before bulk edits, deletions, category merges, account migrations, or historical transaction rewrites.

## Entity Resolution

Resolve accounts and categories before creating transaction or fixed-expense relations:

1. Query `Accounts DB` or `Categories DB` by exact title first.
2. If no exact match exists, try a case-insensitive or substring query for likely aliases.
3. If the user omitted account, default to `現金` when it exists.
4. If the user named an account or category that does not exist, ask before creating it unless the request explicitly says to add/create that account or category.
5. Use relation values as JSON arrays of Notion page URLs for relation properties such as `Account` and `Category`.

## Log Transactions

For expenses and income, create a page in `Transactions DB`.

Required properties:

- `Item Name`: concise item/source name.
- `Type`: `Expense` or `Income`.
- `Amount`: positive number.
- `date:Date:start`: `YYYY-MM-DD` unless a datetime is explicitly needed.
- `date:Date:is_datetime`: `0` for date-only values.

Optional properties:

- `Account`: JSON array of matched account page URLs.
- `Category`: JSON array of matched category page URLs.

Use today's date only when the user says today or gives no date. Preserve user-provided notes in page content only when useful; otherwise keep transaction rows compact.

## Add Accounts And Categories

Create account pages in `Accounts DB` with:

- `Account Name`
- `Initial Balance` as a number, defaulting to `0` only when the user did not provide a starting balance.

Create category pages in `Categories DB` with:

- `Category Name`
- `Monthly Budget` when provided.

## Add Fixed Expenses

Create recurring or amortized expenses in `Fixed Expenses DB` with:

- `Item Name`
- `Amount`
- `Billing Cycle`: `Monthly` or `Annually`
- `date:Start Date:start`
- `date:Start Date:is_datetime`: `0`
- `Category`: JSON array of matched category page URLs when known
- `Total Months` when the expense has a finite amortization period

Do not also create a transaction unless the user asks to record a payment.

## Query And Report

For spending or income questions, query `Transactions DB` with an inclusive start date and exclusive end date for the period. Derive totals from `Type` and positive `Amount` values:

- Expenses: `Type = 'Expense'`
- Income: `Type = 'Income'`
- Net flow: income minus expense

For account balances, query the account's initial balance and all related transactions, then compute:

```text
current balance = initial balance + related income - related expense
```

For category spending, resolve the category page URL and filter transaction `Category` relation JSON for that URL.

For monthly reports, create a page in `Monthly Report DB` with:

- `Month`: `YYYY-MM`
- `date:Period Start:start`: first day of the month
- `date:Period Start:is_datetime`: `0`
- `Transactions`: JSON array of transaction page URLs for the month
- `Fixed Expenses`: JSON array of active fixed-expense page URLs when the report should include fixed burden
- `Notes`: concise generated summary when useful

Fetch or query the created report after creation if the user needs computed rollups such as `Total Income`, `Variable Spending`, `Fixed Burden`, `Total Spending`, or `Net`.
