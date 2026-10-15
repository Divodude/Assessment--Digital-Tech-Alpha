from django.core.management.base import BaseCommand
from reconciliation import models
import datetime


class Command(BaseCommand):
    help = "Seed the database with demo data"

    def handle(self, *args, **options):
        # here i am using the get of create command so that runnig the seed command again and again doesnt create multiple data it shoud create if not exixt only 

        north_wind, _ = models.Organisation.objects.get_or_create(
            name="Northwind Ventures",
            slug="northwind"
        )

        blue_bird, _ = models.Organisation.objects.get_or_create(
            name="Bluebird Capital",
            slug="bluebird"
        )



        north_wind_call1, _ = models.CapitalCall.objects.get_or_create(
            organisation=north_wind,
            number=1,
            call_date=datetime.date(2026, 3, 25),
            due_date=datetime.date(2026, 4, 10)
        )

        north_wind_call2, _ = models.CapitalCall.objects.get_or_create(
            organisation=north_wind,
            number=2,
            call_date=datetime.date(2026, 4, 1),
            due_date=datetime.date(2026, 4, 20)
        )

        blue_bird_call1, _ = models.CapitalCall.objects.get_or_create(
            organisation=blue_bird,
            number=1,
            call_date=datetime.date(2026, 4, 1),
            due_date=datetime.date(2026, 4, 15)
        )



        haller, _ = models.InvestorEntity.objects.get_or_create(
            name="Haller Capital LLC",
            Organisation=north_wind
        )

        rahul, _ = models.InvestorEntity.objects.get_or_create(
            name="Rahul Shah Trust",
            Organisation=north_wind
        )

        patel, _ = models.InvestorEntity.objects.get_or_create(
            name="Patel Family Trust",
            Organisation=north_wind
        )

        meridian, _ = models.InvestorEntity.objects.get_or_create(
            name="Meridian Partners LP",
            Organisation=north_wind
        )

        oakridge, _ = models.InvestorEntity.objects.get_or_create(
            name="Oakridge Holdings LLC",
            Organisation=north_wind
        )

        cedar_grove, _ = models.InvestorEntity.objects.get_or_create(
            name="Cedar Grove Fund LP",
            Organisation=blue_bird
        )


        models.LineItem.objects.get_or_create(
            organisation=north_wind,
            capital_call=north_wind_call1,
            investor_entity=haller,
            expected_reference="CC-1001",
            amount_called=27500,
            amount_funded=0,
            status="open"
        )

        models.LineItem.objects.get_or_create(
            organisation=north_wind,
            capital_call=north_wind_call1,
            investor_entity=rahul,
            expected_reference="CC-1002",
            amount_called=25000,
            amount_funded=0,
            status="open"
        )

        models.LineItem.objects.get_or_create(
            organisation=north_wind,
            capital_call=north_wind_call1,
            investor_entity=patel,
            expected_reference="CC-1003",
            amount_called=12500,
            amount_funded=0,
            status="open"
        )

        models.LineItem.objects.get_or_create(
            organisation=north_wind,
            capital_call=north_wind_call1,
            investor_entity=meridian,
            expected_reference="CC-1004",
            amount_called=15000,
            amount_funded=0,
            status="open"
        )

        models.LineItem.objects.get_or_create(
            organisation=north_wind,
            capital_call=north_wind_call1,
            investor_entity=oakridge,
            expected_reference="CC-1005",
            amount_called=15000,
            amount_funded=0,
            status="open"
        )


        models.LineItem.objects.get_or_create(
            organisation=north_wind,
            capital_call=north_wind_call2,
            investor_entity=oakridge,
            expected_reference="CC-1006",
            amount_called=15000,
            amount_funded=0,
            status="open"
        )

   

        models.LineItem.objects.get_or_create(
            organisation=blue_bird,
            capital_call=blue_bird_call1,
            investor_entity=cedar_grove,
            expected_reference="CC-2001",
            amount_called=40000,
            amount_funded=0,
            status="open"
        )

        self.stdout.write(
            self.style.SUCCESS("Demo data seeded successfully!")
        )
        print("Done seeding demo data!")