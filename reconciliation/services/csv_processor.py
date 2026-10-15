import csv
from decimal import Decimal, InvalidOperation
from datetime import datetime
from .. import models
from .reconciliation import match_credit_transaction


def import_bank_statement(file_obj, organisation):
    if hasattr(file_obj, "read"):
        content = file_obj.read()
        if isinstance(content, bytes):
            decoded_file = content.decode("utf-8-sig")
        else:
            decoded_file = content
    elif isinstance(file_obj, str):
        decoded_file = file_obj
    else:
        raise ValueError("Invalid file input")

    lines = [line for line in decoded_file.splitlines() if line.strip()]
    if not lines:
        raise ValueError("CSV file is empty")

    reader = csv.reader(lines)
    try:
        raw_headers = next(reader)
    except StopIteration:
        raise ValueError("CSV file has no header row")

    headers = [h.strip() for h in raw_headers]
    required_columns = {"date", "description", "amount", "type", "reference"}
    missing_columns = required_columns - set(headers)
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing_columns))}")

    imported = 0
    duplicates = 0
    errors = []
    seen_references = set()

    for line_number, row_values in enumerate(reader, start=2):
        if not row_values or all(not v.strip() for v in row_values):
            continue

        if len(row_values) != len(headers):
            errors.append({
                "line": line_number,
                "message": f"Expected {len(headers)} columns, found {len(row_values)}"
            })
            continue

        row = {headers[i]: row_values[i].strip() for i in range(len(headers))}

        try:
            raw_date = row.get("date", "")
            raw_desc = row.get("description", "")
            raw_amount = row.get("amount", "")
            raw_type = row.get("type", "").lower()
            raw_ref = row.get("reference", "")

            if not raw_date:
                raise ValueError("date is required")
            if not raw_desc:
                raise ValueError("description is required")
            if not raw_amount:
                raise ValueError("amount is required")
            if not raw_type:
                raise ValueError("type is required")
            if not raw_ref:
                raise ValueError("reference is required")

            try:
                parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid calendar date '{raw_date}' (format must be YYYY-MM-DD)")

            if raw_type not in ["credit", "debit"]:
                raise ValueError("type must be 'credit' or 'debit'")

            try:
                clean_amount = raw_amount.replace(",", "")
                amount = Decimal(clean_amount)
            except InvalidOperation:
                raise ValueError(f"Invalid amount format: '{raw_amount}'")

            if amount == Decimal("0.00") or amount == Decimal("0"):
                raise ValueError("amount cannot be zero")

            if raw_type == "credit" and amount <= Decimal("0"):
                raise ValueError(f"credit amount must be positive, got {amount}")
            if raw_type == "debit" and amount >= Decimal("0"):
                raise ValueError(f"debit amount must be negative, got {amount}")

            if raw_ref in seen_references:
                duplicates += 1
                continue
            seen_references.add(raw_ref)

            if models.BankTransaction.objects.filter(organisation=organisation, reference=raw_ref).exists():
                duplicates += 1
                continue

            if raw_type == "debit":
                models.BankTransaction.objects.create(
                    organisation=organisation,
                    date=parsed_date,
                    amount=amount,
                    type="debit",
                    reference=raw_ref,
                    status="ignored",
                    description=raw_desc,
                    reason="Debit transaction ignored"
                )
                imported += 1
            else:
                txn = models.BankTransaction.objects.create(
                    organisation=organisation,
                    date=parsed_date,
                    amount=amount,
                    type="credit",
                    reference=raw_ref,
                    status="suggested",
                    description=raw_desc
                )
                match_credit_transaction(txn)
                imported += 1

        except Exception as e:
            errors.append({
                "line": line_number,
                "message": str(e)
            })

    return {
        "imported": imported,
        "duplicates": duplicates,
        "errors": errors,
    }