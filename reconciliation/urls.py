from django.urls import path
from .views import TransactionView, LineItemView

urlpatterns = [
    path("transactions/", TransactionView.as_view(), name="transactions"),
    path("line-items/", LineItemView.as_view(), name="line-items"),
]