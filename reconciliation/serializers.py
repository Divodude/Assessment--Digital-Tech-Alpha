from . import models
from rest_framework import serializers


class BankTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BankTransaction
        fields = '__all__'


class LineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LineItem
        fields = '__all__'


class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Match
        fields = '__all__'