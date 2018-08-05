import decimal
import uuid
from django.db import models
from django.contrib.auth.models import User as U
from datetime import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver


class User(models.Model):
    name = models.CharField(max_length=255, null=True)
    code = models.UUIDField()
    owner = models.OneToOneField(U, null=False, on_delete=models.CASCADE)

    def get_wallet(self):
        return Wallet.objects.get(owner=self.id)

    def __str__(self):
        return self.name


class Wallet(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=6, decimal_places=2, default=10)

    @receiver(post_save, sender=User)
    def update_perfil(sender, instance, created, **kwargs):
        if created:
            Wallet.objects.create(owner=User.objects.latest('id'))

    def withdraw(self, amount):
        withdraw = decimal.Decimal(amount)

        if withdraw < 0:
            withdraw = withdraw * -1

        if withdraw > self.balance:
            return False

        self.balance = self.balance - withdraw
        self.save()
        return True

    def deposit(self, amount):
        deposit = decimal.Decimal(amount)

        if deposit < 0:
            deposit = deposit * -1

        self.balance = self.balance + deposit
        self.save()
        return True


class CreditCard(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='cards')
    holder = models.CharField(max_length=255, null=False)
    card_token = models.UUIDField()
    digits = models.CharField(max_length=19, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def validate(self):
        sum = 0
        digits = self.digits
        length = len(digits)
        odd_part = length & 1

        for i in range(0, length):
            digit = int(digits[i])

            if not ((i & 1) ^ odd_part):
                digit = digit * 2
            if digit > 9:
                digit = digit - 9

            sum = sum + digit

        return (sum % 10) == 0

    def capture(self, amount):
        if amount > 20:
            return False
        return True

    # def save(self, *args, **kwargs):
    #     self.card_token = uuid.uuid4().hex
    #     super(CreditCard, self).save(*args, **kwargs)


class Transfer(models.Model):
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donor')
    donee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donee')
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    was_transferred = models.BooleanField(default=False)
    date = models.DateTimeField(default=datetime.now, blank=True)

    def make_transfer(self):
        donor_wallet = self.donor.wallet
        donee_wallet = self.donee.wallet

        if donor_wallet.withdraw(self.amount):
            if donee_wallet.deposit(self.amount):
                self.was_transferred = True
                self.save()
                return True
            else:
                donor_wallet.deposit(self.amount)

        return False


class Bank(models.Model):
    name = models.CharField(max_length=255, null=False)

    def __str__(self):
        return self.name


class BankAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='back_account')
    agency = models.CharField(max_length=15, null=False)
    cc = models.CharField(max_length=15, null=False)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)

    def __str__(self):
        return 'Account: ' + self.cc + ' / Agency: ' + self.agency


class BankAccountTransfer(models.Model):
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='bank_account_transfer')
    amount = models.DecimalField(max_digits=6, decimal_places=2)

    def make_transfer(self, amount):
        wallet = self.bank_account.user.wallet

        if wallet.withdraw(amount):
            return True
        return False

