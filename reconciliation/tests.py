from datetime import date
from decimal import Decimal
import io
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from . import models


class ReconciliationTechnicalAssessmentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        call_command("seed_demo")
        self.northwind = models.Organisation.objects.get(slug="northwind")
        self.bluebird = models.Organisation.objects.get(slug="bluebird")

    def test_missing_column_rejects_file_and_saves_nothing(self):
        csv_content = "date,description,amount,type\n2026-04-03,WIRE INCOMING,1000.00,credit\n"
        uploaded_file = SimpleUploadedFile("statement.csv", csv_content.encode("utf-8"), content_type="text/csv")

        response = self.client.post(
            "/api/import/",
            {"file": uploaded_file},
            format="multipart",
            HTTP_X_ORGANIZATION="northwind"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Missing required columns", response.data.get("detail", ""))
        self.assertEqual(models.BankTransaction.objects.filter(organisation=self.northwind).count(), 0)

    def test_amount_parsing_and_validations(self):
        csv_content = (
            "date,description,amount,type,reference\n"
            '2026-04-03,Valid Credit,"25,000.50",credit,REF_VALID\n'
            '2026-04-04,Negative Credit,-500.00,credit,REF_NEG_CREDIT\n'
            '2026-04-05,Positive Debit,500.00,debit,REF_POS_DEBIT\n'
            '2026-04-31,Invalid Date,100.00,credit,REF_BAD_DATE\n'
        )
        uploaded_file = SimpleUploadedFile("statement.csv", csv_content.encode("utf-8"), content_type="text/csv")

        response = self.client.post(
            "/api/import/",
            {"file": uploaded_file},
            format="multipart",
            HTTP_X_ORGANIZATION="northwind"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["imported"], 1)
        self.assertEqual(len(response.data["errors"]), 3)

        error_lines = [err["line"] for err in response.data["errors"]]
        self.assertIn(3, error_lines)
        self.assertIn(4, error_lines)
        self.assertIn(5, error_lines)

        txn = models.BankTransaction.objects.get(reference="REF_VALID")
        self.assertIsInstance(txn.amount, Decimal)
        self.assertEqual(txn.amount, Decimal("25000.50"))

    def test_duplicates_detection(self):
        csv_content = (
            "date,description,amount,type,reference\n"
            "2026-04-03,Wire 1,1000.00,credit,DUP_REF_01\n"
            "2026-04-03,Wire Duplicate,1000.00,credit,DUP_REF_01\n"
            "2026-04-04,Wire 2,2000.00,credit,DUP_REF_02\n"
        )
        file1 = SimpleUploadedFile("statement.csv", csv_content.encode("utf-8"), content_type="text/csv")

        res1 = self.client.post("/api/import/", {"file": file1}, format="multipart", HTTP_X_ORGANIZATION="northwind")
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(res1.data["imported"], 2)
        self.assertEqual(res1.data["duplicates"], 1)

        file2 = SimpleUploadedFile("statement.csv", csv_content.encode("utf-8"), content_type="text/csv")
        res2 = self.client.post("/api/import/", {"file": file2}, format="multipart", HTTP_X_ORGANIZATION="northwind")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data["imported"], 0)
        self.assertEqual(res2.data["duplicates"], 3)

    def test_reference_match_including_normalized_and_partial_payment(self):
        csv_content = (
            "date,description,amount,type,reference\n"
            "2026-04-04,ACH CREDIT HALLER CAPITAL cc1001,20000.00,credit,TXN_REF_01\n"
        )
        uploaded = SimpleUploadedFile("statement.csv", csv_content.encode("utf-8"), content_type="text/csv")
        res = self.client.post("/api/import/", {"file": uploaded}, format="multipart", HTTP_X_ORGANIZATION="northwind")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        txn = models.BankTransaction.objects.get(reference="TXN_REF_01")
        self.assertEqual(txn.status, "suggested")
        matches = txn.matches.all()
        self.assertEqual(matches.count(), 1)
        match = matches.first()
        self.assertEqual(match.line_item.expected_reference, "CC-1001")
        self.assertEqual(match.status, "proposed")
        self.assertIn("partial payment", match.reason.lower())

    def test_name_and_amount_match_single_and_multiple_candidates(self):
        csv_content = (
            "date,description,amount,type,reference\n"
            "2026-04-07,WIRE INCOMING PATEL FAMILY TRUST,12500.00,credit,TXN_PATEL\n"
            "2026-04-11,WIRE INCOMING OAKRIDGE HOLDINGS LLC,15000.00,credit,TXN_OAKRIDGE\n"
        )
        uploaded = SimpleUploadedFile("statement.csv", csv_content.encode("utf-8"), content_type="text/csv")
        res = self.client.post("/api/import/", {"file": uploaded}, format="multipart", HTTP_X_ORGANIZATION="northwind")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        patel_txn = models.BankTransaction.objects.get(reference="TXN_PATEL")
        self.assertEqual(patel_txn.status, "suggested")
        self.assertEqual(patel_txn.matches.count(), 1)
        self.assertEqual(patel_txn.matches.first().line_item.expected_reference, "CC-1003")

        oak_txn = models.BankTransaction.objects.get(reference="TXN_OAKRIDGE")
        self.assertEqual(oak_txn.status, "needs_review")
        self.assertEqual(oak_txn.matches.count(), 2)
        matched_refs = {m.line_item.expected_reference for m in oak_txn.matches.all()}
        self.assertEqual(matched_refs, {"CC-1005", "CC-1006"})

    def test_overpayment_becomes_needs_review_with_no_match(self):
        csv_content = (
            "date,description,amount,type,reference\n"
            "2026-04-15,WIRE PATEL FAMILY TRUST CC-1003,13000.00,credit,TXN_OVERPAY\n"
        )
        uploaded = SimpleUploadedFile("statement.csv", csv_content.encode("utf-8"), content_type="text/csv")
        res = self.client.post("/api/import/", {"file": uploaded}, format="multipart", HTTP_X_ORGANIZATION="northwind")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        txn = models.BankTransaction.objects.get(reference="TXN_OVERPAY")
        self.assertEqual(txn.status, "needs_review")
        self.assertEqual(txn.matches.count(), 0)
        self.assertIn("exceeds remaining", txn.reason.lower())

    def test_approval_updates_funding_and_second_approval_returns_409(self):
        line_item = models.LineItem.objects.get(expected_reference="CC-1002")
        self.assertEqual(line_item.amount_funded, Decimal("0.00"))
        self.assertEqual(line_item.status, "open")

        txn = models.BankTransaction.objects.create(
            organisation=self.northwind,
            date=date(2026, 4, 3),
            amount=Decimal("25000.00"),
            type="credit",
            reference="TXN_APPROVE_TEST",
            status="suggested",
            description="WIRE RAHUL SHAH TRUST CC-1002"
        )
        match = models.Match.objects.create(
            transaction=txn,
            line_item=line_item,
            status="proposed",
            reason="Reference CC-1002 found"
        )

        url = f"/api/matches/{match.id}/approve/"
        res1 = self.client.post(url, HTTP_X_ORGANIZATION="northwind")
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        line_item.refresh_from_db()
        txn.refresh_from_db()
        match.refresh_from_db()

        self.assertEqual(line_item.amount_funded, Decimal("25000.00"))
        self.assertEqual(line_item.status, "funded")
        self.assertEqual(txn.status, "reconciled")
        self.assertEqual(match.status, "approved")

        res2 = self.client.post(url, HTTP_X_ORGANIZATION="northwind")
        self.assertEqual(res2.status_code, status.HTTP_409_CONFLICT)

        line_item.refresh_from_db()
        self.assertEqual(line_item.amount_funded, Decimal("25000.00"))

    def test_organization_isolation(self):
        res_missing = self.client.get("/api/transactions/")
        self.assertEqual(res_missing.status_code, status.HTTP_400_BAD_REQUEST)

        res_unknown = self.client.get("/api/transactions/", HTTP_X_ORGANIZATION="unknown-org")
        self.assertEqual(res_unknown.status_code, status.HTTP_404_NOT_FOUND)

        txn_northwind = models.BankTransaction.objects.create(
            organisation=self.northwind,
            date=date(2026, 4, 3),
            amount=Decimal("1000.00"),
            type="credit",
            reference="NW_SECRET_TXN",
            status="suggested",
            description="Northwind payment"
        )
        line_item_nw = models.LineItem.objects.filter(organisation=self.northwind).first()
        match_nw = models.Match.objects.create(
            transaction=txn_northwind,
            line_item=line_item_nw,
            status="proposed",
            reason="Test match"
        )

        res_bluebird = self.client.get("/api/transactions/", HTTP_X_ORGANIZATION="bluebird")
        self.assertEqual(res_bluebird.status_code, status.HTTP_200_OK)
        refs = [t["reference"] for t in res_bluebird.data["results"] if "results" in res_bluebird.data] if isinstance(res_bluebird.data, dict) else [t["reference"] for t in res_bluebird.data]
        self.assertNotIn("NW_SECRET_TXN", refs)

        res_cross_org_approve = self.client.post(
            f"/api/matches/{match_nw.id}/approve/",
            HTTP_X_ORGANIZATION="bluebird"
        )
        self.assertEqual(res_cross_org_approve.status_code, status.HTTP_404_NOT_FOUND)
