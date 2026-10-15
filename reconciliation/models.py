from datetime import date
from django.db import models


import uuid
class Organisation(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    name=models.CharField(max_length=100)
    slug=models.SlugField()

class InvestorEntity(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    name=models.CharField(max_length=100)
    Organisation=models.ForeignKey(Organisation,on_delete=models.CASCADE)
    
class CapitalCall(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    organisation=models.ForeignKey(Organisation,on_delete=models.CASCADE)
    number=models.IntegerField()
    call_date=models.DateField()
    due_date=models.DateField()
  
class LineItem(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    organisation=models.ForeignKey(Organisation,on_delete=models.CASCADE)
    capital_call=models.ForeignKey(CapitalCall,on_delete=models.CASCADE)
    investor_entity=models.ForeignKey(InvestorEntity,on_delete=models.CASCADE)
    expected_reference=models.CharField(max_length=100)
    amount_called=models.DecimalField(max_digits=10,decimal_places=2)
    amount_funded=models.DecimalField(max_digits=10,decimal_places=2)
    status=models.CharField(max_length=100)
   

class BankTransaction(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    organisation=models.ForeignKey(Organisation,on_delete=models.CASCADE)
    date=models.DateField()
    amount=models.DecimalField(max_digits=10,decimal_places=2)
    type=models.CharField(max_length=100)
    refrence=models.CharField(max_length=100)
    status=models.CharField(max_length=100)
    
    
class Match(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    transaction=models.ForeignKey(BankTransaction,on_delete=models.CASCADE)
    line_item=models.ForeignKey(LineItem,on_delete=models.CASCADE)
    status=models.CharField(max_length=100)
    reason=models.CharField(max_length=100)
    
