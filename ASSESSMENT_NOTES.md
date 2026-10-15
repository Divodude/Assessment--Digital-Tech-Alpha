# AlphaRecon – Bank Reconciliation for Capital Calls

**Assessment Notes**
> I completed this assessment without using AI assistance.

## 1. Overview

AlphaRecon is a web application that helps General Partners (GPs) match incoming bank payments with capital call amounts due from Limited Partners (LPs).

## 2. Setup Instructions

### Backend (Django)

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  

   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy the environment file:
   ```bash
   copy .env.example .env
   ```
4. Run migrations and seed demo data:
   ```bash
   python manage.py migrate
   python manage.py seed_demo
   ```
   The seed command creates Northwind Ventures and Bluebird Capital and can be run multiple times safely.
5. Start the backend:
   ```bash
   python manage.py runserver
   ```
   Backend: `http://127.0.0.1:8000/`

### Frontend (Vite)

From the `frontend` directory, run:

```bash
npm install
npm run dev
```

Open `http://localhost:5173/` in your browser.

## 3. Tests

Run the reconciliation test suite, which covers all 8 assessment scenarios:

```bash
python manage.py test reconciliation
```

## 4. Main Data Models

- **Organisation:** Represents a GP tenant. Every related record belongs to an organisation to maintain tenant isolation.
- **InvestorEntity:** Stores LP legal entities, such as Patel Family Trust or Haller Capital LLC.
- **CapitalCall:** Stores the call number, call date, and due date.
- **LineItem:** Tracks each LP's called amount, funded amount, outstanding balance, and funding status.
- **BankTransaction:** Stores imported bank transactions, including the amount (`Decimal`), credit/debit type, bank reference, status, and match reason.
- **Match:** Connects a bank transaction to a capital call line item, with a proposed, approved, or rejected status and an explanation.

## 5. API Endpoints

All endpoints require the `X-Organization: <slug>` header, except `GET /api/organizations/`.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/organizations/` | List organisations for the switcher. |
| GET | `/api/line-items/` | List capital call line items for the active organisation. |
| GET | `/api/transactions/` | List recent bank transactions with match details and reasons. |
| POST | `/api/import/` | Import a bank statement CSV using `multipart/form-data`. |
| POST | `/api/matches/<id>/approve/` | Approve a match, update funding, and reconcile the transaction atomically. Returns 409 if already reconciled or overpaid. |
| POST | `/api/matches/<id>/reject/` | Reject a proposed match. |
| POST | `/api/transactions/<id>/ignore/` | Ignore a transaction. Returns 409 if already reconciled. |

## 6. Key Decisions and Trade-offs

- **Tenant isolation:** Records belonging to other organisations return HTTP 404 instead of 403 to avoid exposing their existence.
- **Duplicate funding prevention:** Match approval uses `transaction.atomic()` and `select_for_update()` to lock relevant records and prevent concurrent approvals from funding the same payment twice. Conflicting requests return HTTP 409.
- **Money precision:** All monetary values use `Decimal(14, 2)` to avoid floating-point errors.
- **CSV imports:** Imports run synchronously, which is suitable for a few thousand rows. For larger files (100,000+ rows), the process could be moved to Celery with Redis for background processing.