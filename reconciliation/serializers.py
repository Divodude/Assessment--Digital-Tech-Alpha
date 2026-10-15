from . import models
from rest_framework import serializers


class MatchSerializer(serializers.ModelSerializer):
    line_item_id = serializers.UUIDField(source="line_item.id", read_only=True)
    expected_reference = serializers.CharField(source="line_item.expected_reference", read_only=True)
    investor_name = serializers.CharField(source="line_item.investor_entity.name", read_only=True)
    line_item_remaining = serializers.DecimalField(
        source="line_item.remaining_amount",
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = models.Match
        fields = [
            "id",
            "status",
            "reason",
            "line_item_id",
            "expected_reference",
            "investor_name",
            "line_item_remaining",
        ]


class BankTransactionSerializer(serializers.ModelSerializer):
    matches = MatchSerializer(many=True, read_only=True)
    suggested_investor = serializers.SerializerMethodField()
    suggested_reference = serializers.SerializerMethodField()

    class Meta:
        model = models.BankTransaction
        fields = [
            "id",
            "date",
            "amount",
            "type",
            "reference",
            "status",
            "description",
            "reason",
            "suggested_investor",
            "suggested_reference",
            "matches",
        ]

    def get_suggested_investor(self, obj):
        first_match = obj.matches.filter(status__in=["proposed", "approved"]).select_related("line_item__investor_entity").first()
        if first_match:
            return first_match.line_item.investor_entity.name
        return None

    def get_suggested_reference(self, obj):
        first_match = obj.matches.filter(status__in=["proposed", "approved"]).select_related("line_item").first()
        if first_match:
            return first_match.line_item.expected_reference
        return None


class LineItemSerializer(serializers.ModelSerializer):
    investor_name = serializers.CharField(source="investor_entity.name", read_only=True)
    capital_call_number = serializers.IntegerField(source="capital_call.number", read_only=True)
    call_date = serializers.DateField(source="capital_call.call_date", read_only=True)
    due_date = serializers.DateField(source="capital_call.due_date", read_only=True)
    remaining = serializers.DecimalField(
        source="remaining_amount",
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = models.LineItem
        fields = [
            "id",
            "expected_reference",
            "investor_name",
            "capital_call_number",
            "call_date",
            "due_date",
            "amount_called",
            "amount_funded",
            "remaining",
            "status",
        ]