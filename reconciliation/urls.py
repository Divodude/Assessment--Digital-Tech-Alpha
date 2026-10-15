from django.urls import path
from .views import (
    OrganizationListView,
    TransactionView,
    LineItemView,
    TransactionImportView,
    ApproveMatchesView,
    RejectMatchView,
    IgnoreTransactionView,
)

urlpatterns = [
    path("organizations/", OrganizationListView.as_view(), name="organizations"),
    path("transactions/", TransactionView.as_view(), name="transactions"),
    path("line-items/", LineItemView.as_view(), name="line-items"),
    path("import/", TransactionImportView.as_view(), name="import-transactions"),
    path("matches/<uuid:match_id>/approve/", ApproveMatchesView.as_view(), name="approve-match"),
    path("matches/<uuid:match_id>/reject/", RejectMatchView.as_view(), name="reject-match"),
    path("transactions/<uuid:transaction_id>/ignore/", IgnoreTransactionView.as_view(), name="ignore-transaction"),
]