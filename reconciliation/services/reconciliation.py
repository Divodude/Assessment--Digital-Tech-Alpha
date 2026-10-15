import re
from decimal import Decimal
from .. import models


def normalize_reference(ref):
    if not ref:
        return ""
    return re.sub(r"[^A-Z0-9]", "", ref.upper())


def normalize_name(name):
    if not name:
        return ""
    text = re.sub(r"[^A-Z0-9]", " ", name.upper())
    text = " ".join(text.split())
    for suffix in ["LLC", "LP", "LTD", "INC"]:
        if text.endswith(" " + suffix):
            text = text[:-len(suffix)].strip()
            break
    return text


def normalize_description_for_name(desc):
    if not desc:
        return ""
    return " ".join(re.sub(r"[^A-Z0-9]", " ", desc.upper()).split())


def is_name_found_in_description(normalized_name, normalized_desc):
    if not normalized_name or not normalized_desc:
        return False
    pattern = r"\b" + re.escape(normalized_name) + r"\b"
    return bool(re.search(pattern, normalized_desc))


def match_credit_transaction(transaction):

    eligible_line_items = list(
        models.LineItem.objects.filter(
            organisation=transaction.organisation,
            capital_call__call_date__lte=transaction.date
        ).select_related("capital_call", "investor_entity")
    )

    eligible_line_items = [
        item for item in eligible_line_items
        if item.remaining_amount > Decimal("0.00")
    ]

    norm_desc_ref = normalize_reference(transaction.description)
    norm_bank_ref = normalize_reference(transaction.reference)
    norm_desc_name = normalize_description_for_name(transaction.description)

    ref_matched = []
    for item in eligible_line_items:
        norm_item_ref = normalize_reference(item.expected_reference)
        if norm_item_ref and (norm_item_ref in norm_desc_ref or norm_item_ref in norm_bank_ref):
            ref_matched.append(item)

    if ref_matched:
        if len(ref_matched) == 1:
            line_item = ref_matched[0]
            if transaction.amount <= line_item.remaining_amount:
                transaction.status = "suggested"
                if transaction.amount == line_item.remaining_amount:
                    reason = f"Reference {line_item.expected_reference} found; amount equals remaining {line_item.remaining_amount:,.2f}"
                else:
                    reason = f"Reference {line_item.expected_reference} found; partial payment of {transaction.amount:,.2f} against remaining {line_item.remaining_amount:,.2f}"
                transaction.reason = reason
                transaction.save()

                models.Match.objects.create(
                    transaction=transaction,
                    line_item=line_item,
                    status="proposed",
                    reason=reason
                )
            else:
                transaction.status = "needs_review"
                transaction.reason = f"Reference {line_item.expected_reference} found; amount {transaction.amount:,.2f} exceeds remaining {line_item.remaining_amount:,.2f} (overpayment)"
                transaction.save()
        else:
            transaction.status = "needs_review"
            transaction.reason = f"Multiple matching references found: {', '.join(item.expected_reference for item in ref_matched)}"
            transaction.save()

            for item in ref_matched:
                reason = f"Reference {item.expected_reference} found in description/reference"
                models.Match.objects.create(
                    transaction=transaction,
                    line_item=item,
                    status="proposed",
                    reason=reason
                )
        return

    name_matched = []
    for item in eligible_line_items:
        norm_investor = normalize_name(item.investor_entity.name)
        if item.remaining_amount == transaction.amount and is_name_found_in_description(norm_investor, norm_desc_name):
            name_matched.append(item)

    if len(name_matched) == 1:
        line_item = name_matched[0]
        transaction.status = "suggested"
        reason = f"Investor name '{line_item.investor_entity.name}' found; amount equals remaining {line_item.remaining_amount:,.2f}"
        transaction.reason = reason
        transaction.save()

        models.Match.objects.create(
            transaction=transaction,
            line_item=line_item,
            status="proposed",
            reason=reason
        )
    elif len(name_matched) > 1:
        transaction.status = "needs_review"
        transaction.reason = f"Multiple line items match investor name and amount ({len(name_matched)} candidates)"
        transaction.save()

        for item in name_matched:
            reason = f"Investor name '{item.investor_entity.name}' found; amount equals remaining {item.remaining_amount:,.2f}"
            models.Match.objects.create(
                transaction=transaction,
                line_item=item,
                status="proposed",
                reason=reason
            )
    else:
        transaction.status = "needs_review"
        transaction.reason = "No matching reference or investor name with exact remaining amount found"
        transaction.save()
