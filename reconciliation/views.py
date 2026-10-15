
from rest_framework.views import APIView, ListAPIView
from rest_framework.exceptions import ValidationError
from . import models
from .serializers import BankTransactionSerializer, LineItemSerializer
from rest_framework.exceptions import NotFound


from django.db import transaction as db_transaction
from rest_framework.response import Response
from rest_framework import status

class TransactionView(ListAPIView):
    
    serializer_class = BankTransactionSerializer
    def get_queryset(self):
        organization_slug = self.request.headers.get("X-Organization")
        
        if not organization_slug:
            raise ValidationError("X-Organization header is required")
        
        organization = models.Organisation.objects.filter(
            slug=organization_slug
        ).first()


        if not organization:
            raise NotFound("Organization not found")
        
        return models.BankTransaction.objects.filter(organisation=organization).order_by('-date')


class LineItemView(ListAPIView):
    serializer_class = LineItemSerializer
    def get_queryset(self):
        organization_slug = self.request.headers.get("X-Organization")
        
        if not organization_slug:
            raise ValidationError("X-Organization header is required")
        
        organization = models.Organisation.objects.filter(
            slug=organization_slug
        ).first()


        if not organization:
            raise NotFound("Organization not found")
        
        return models.LineItem.objects.filter(organisation=organization).order_by('-capital_call__call_date')
    
class TransactionImportView(APIView):

    def post(self, request):
        organization_slug = request.headers.get("X-Organization")

        if not organization_slug:
            raise ValidationError("X-Organization header is required")

        organization = models.Organisation.objects.filter(
            slug=organization_slug
        ).first()

        if not organization:
            raise NotFound("Organization not found")

        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            raise ValidationError("CSV file is required")

class ApproveMatchesView(APIView):
    def post(self, request,match_id):
        organization_slug = request.headers.get("X-Organization")

        if not organization_slug:
            raise ValidationError("X-Organization header is required")

        organization = models.Organisation.objects.filter(
            slug=organization_slug
        ).first()

        if not organization:
            raise NotFound("Organization not found")
    
        match = models.Match.objects.filter(
            id=match_id,
            transaction__organisation=organization
        ).first()

        if not match:
            raise NotFound("Match not found")
        if match.status!="proposed":
            raise ValidationError("Only proposed match can be approved")
        transaction = match.transaction
        line_item = match.line_item
        remaining = line_item.amount_called - line_item.amount_funded
        if remaining < transaction.amount:
            return Response(
                {"detail": "Payment exceeds remaining amount"},
                status=status.HTTP_409_CONFLICT
            )

        with db_transaction.atomic():

            line_item = models.LineItem.objects.select_for_update().get(
                id=line_item.id
            )

           
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
    def post(self, request,match_id):
        organization_slug = request.headers.get("X-Organization")

        if not organization_slug:
            raise ValidationError("X-Organization header is required")

        organization = models.Organisation.objects.filter(
            slug=organization_slug
        ).first()

        if not organization:
            raise NotFound("Organization not found")
    
        match = models.Match.objects.filter(
            id=match_id,
            transaction__organisation=organization
        ).first()

        if not match:
            raise NotFound("Match not found")

        if match.status != "proposed":
            raise ValidationError("Only proposed match can be rejected")
        match.status = "rejected"
        match.save()


        remaining_proposed = models.Match.objects.filter(
            transaction=match.transaction,
            status="proposed"
        ).exists()

        if not remaining_proposed:
            match.transaction.status = "needs_review"
            match.transaction.save()
        
        return Response(
            {"detail": "Match rejected successfully"},
            status=status.HTTP_200_OK
        )
        


class IgnoreTransactionView(APIView):
    def post(self, request, transaction_id):
        organization_slug = request.headers.get("X-Organization")

        if not organization_slug:
            raise ValidationError("X-Organization header is required")

        organization = models.Organisation.objects.filter(
            slug=organization_slug
        ).first()

        if not organization:
            raise NotFound("Organization not found")

        transaction = models.BankTransaction.objects.filter(
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
            raise ValidationError(
                "Only suggested or needs_review transactions can be ignored"
            )

        transaction.status = "ignored"
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