

from django.db import transaction as db_transaction
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from . import models
from .serializers import BankTransactionSerializer, LineItemSerializer
from .services.csv_processor import import_bank_statement


def get_organization_from_request(request):
    organization_slug = request.headers.get("X-Organization")
    if not organization_slug:
        raise ValidationError("X-Organization header is required")

    organization = models.Organisation.objects.filter(slug=organization_slug).first()
    if not organization:
        raise NotFound("Organization not found")

    return organization


class OrganizationListView(APIView):
    def get(self, request):
        orgs = models.Organisation.objects.all().values("id", "name", "slug")
        return Response(list(orgs), status=status.HTTP_200_OK)


class TransactionView(ListAPIView):
    serializer_class = BankTransactionSerializer

    def get_queryset(self):
        organization = get_organization_from_request(self.request)
        return models.BankTransaction.objects.filter(
            organisation=organization
        ).prefetch_related(
            "matches__line_item__investor_entity"
        ).order_by("-date")


class LineItemView(ListAPIView):
    serializer_class = LineItemSerializer

    def get_queryset(self):
        organization = get_organization_from_request(self.request)
        return models.LineItem.objects.filter(
            organisation=organization
        ).select_related(
            "capital_call",
            "investor_entity"
        ).order_by("-capital_call__call_date")


class TransactionImportView(APIView):
    def post(self, request):
        organization = get_organization_from_request(request)
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            raise ValidationError("CSV file is required")

        try:
            summary = import_bank_statement(uploaded_file, organization)
            return Response(summary, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ApproveMatchesView(APIView):
    def post(self, request, match_id):
        organization = get_organization_from_request(request)

        with db_transaction.atomic():
            match = models.Match.objects.select_for_update().filter(
                id=match_id,
                transaction__organisation=organization
            ).select_related("transaction", "line_item").first()

            if not match:
                raise NotFound("Match not found")

            if match.status != "proposed" or match.transaction.status == "reconciled":
                return Response(
                    {"detail": "Match is not proposed or transaction is already reconciled"},
                    status=status.HTTP_409_CONFLICT
                )

            transaction = models.BankTransaction.objects.select_for_update().get(id=match.transaction.id)
            line_item = models.LineItem.objects.select_for_update().get(id=match.line_item.id)

            remaining = line_item.amount_called - line_item.amount_funded
            if remaining < transaction.amount:
                return Response(
                    {"detail": "Payment exceeds remaining amount"},
                    status=status.HTTP_409_CONFLICT
                )

            line_item.amount_funded += transaction.amount
            if line_item.amount_funded == line_item.amount_called:
                line_item.status = "funded"
            else:
                line_item.status = "partially_funded"
            line_item.save()

            match.status = "approved"
            match.save()

            models.Match.objects.filter(
                transaction=transaction,
                status="proposed"
            ).exclude(
                id=match.id
            ).update(
                status="rejected"
            )

            transaction.status = "reconciled"
            transaction.save()

        return Response(
            {"detail": "Match approved successfully"},
            status=status.HTTP_200_OK
        )


class RejectMatchView(APIView):
    def post(self, request, match_id):
        organization = get_organization_from_request(request)

        with db_transaction.atomic():
            match = models.Match.objects.select_for_update().filter(
                id=match_id,
                transaction__organisation=organization
            ).select_related("transaction").first()

            if not match:
                raise NotFound("Match not found")

            if match.status != "proposed":
                return Response(
                    {"detail": "Only proposed match can be rejected"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            match.status = "rejected"
            match.save()

            transaction = models.BankTransaction.objects.select_for_update().get(id=match.transaction.id)
            remaining_proposed = models.Match.objects.filter(
                transaction=transaction,
                status="proposed"
            ).exists()

            if not remaining_proposed and transaction.status != "reconciled":
                transaction.status = "needs_review"
                transaction.reason = "Proposed match was rejected"
                transaction.save()

        return Response(
            {"detail": "Match rejected successfully"},
            status=status.HTTP_200_OK
        )


class IgnoreTransactionView(APIView):
    def post(self, request, transaction_id):
        organization = get_organization_from_request(request)

        with db_transaction.atomic():
            transaction = models.BankTransaction.objects.select_for_update().filter(
                id=transaction_id,
                organisation=organization
            ).first()

            if not transaction:
                raise NotFound("Transaction not found")

            if transaction.status == "reconciled":
                return Response(
                    {"detail": "Reconciled transaction cannot be ignored"},
                    status=status.HTTP_409_CONFLICT
                )

            if transaction.status not in ["suggested", "needs_review"]:
                return Response(
                    {"detail": "Only suggested or needs_review transactions can be ignored"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            transaction.status = "ignored"
            transaction.reason = "Transaction ignored by user"
            transaction.save()

            models.Match.objects.filter(
                transaction=transaction
            ).update(
                status="rejected"
            )

        return Response(
            {"detail": "Transaction ignored successfully"},
            status=status.HTTP_200_OK
        )