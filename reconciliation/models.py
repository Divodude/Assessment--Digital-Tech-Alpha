from datetime import date
from decimal import Decimal
import uuid
from django.db import models


class Organisation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class InvestorEntity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    Organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="investor_entities"
    )

    @property
    def organisation(self):
        return self.Organisation

    @organisation.setter
    def organisation(self, val):
        self.Organisation = val

    def __str__(self):
        return self.name


class CapitalCall(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="capital_calls"
    )
    number = models.IntegerField()
    call_date = models.DateField()
    due_date = models.DateField()

    def __str__(self):
        return f"{self.organisation.name} Call #{self.number}"


class LineItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="line_items"
    )
    capital_call = models.ForeignKey(
        CapitalCall,
        on_delete=models.CASCADE,
        related_name="line_items"
    )
    investor_entity = models.ForeignKey(
        InvestorEntity,
        on_delete=models.CASCADE,
        related_name="line_items"
    )
    expected_reference = models.CharField(max_length=100)
    amount_called = models.DecimalField(max_digits=12, decimal_places=2)
    amount_funded = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )
    status = models.CharField(max_length=50, default="open")

    @property
    def remaining_amount(self):
        return self.amount_called - self.amount_funded

    def __str__(self):
        return f"{self.expected_reference} ({self.investor_entity.name}): {self.amount_funded}/{self.amount_called}"


class BankTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=50)
    reference = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    description = models.TextField()
    reason = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organisation", "reference"],
                name="unique_org_bank_ref"
            )
        ]

    def __str__(self):
        return f"{self.date} {self.reference} {self.amount} ({self.status})"


class Match(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(
        BankTransaction,
        on_delete=models.CASCADE,
        related_name="matches"
    )
    line_item = models.ForeignKey(
        LineItem,
        on_delete=models.CASCADE,
        related_name="matches"
    )
    status = models.CharField(max_length=50, default="proposed")
    reason = models.TextField()

    def __str__(self):
        return f"Match {self.transaction.reference} -> {self.line_item.expected_reference} ({self.status})"
