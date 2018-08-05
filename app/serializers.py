from rest_framework import serializers
from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.reverse import reverse
from .models import *


class SaveUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField()
    password = serializers.CharField()
    email = serializers.CharField()

    class Meta:
        model = User
        fields = ("name", "username", "password", "email")


class UserSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = User
        fields = ("url", "name", "code")


class OwnerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = U
        fields = ("username", "email")


class UserDetailSerializer(serializers.HyperlinkedModelSerializer):
    owner = OwnerSerializer()

    class Meta:
        model = User
        fields = ("name", "code", "owner")


class TransferSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Transfer
        read_only_fields = ("id", "donor", "date", "was_transferred")
        fields = ("url", "id", "donor", "donee", "amount", "date", "was_transferred")


class SaveTransferSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transfer
        read_only_fields = ("id", "donor", "date", "was_transferred")
        fields = ("donee", "amount")


class WalletSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Wallet
        read_only_fields = ("owner", "balance")
        fields = ("owner", "balance")


class CreditCardSerializer(serializers.HyperlinkedModelSerializer):
    wallet = WalletSerializer()

    class Meta:
        model = CreditCard
        read_only_fields = ("wallet", "card_token")
        fields = ("url", "holder", "digits", "card_token", "wallet",)


class BankSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Bank
        fields = '__all__'


class BankAccountSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = BankAccount
        fields = '__all__'


class BankAccountTransferSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = BankAccountTransfer
        fields = '__all__'


class SaveBankAccountTransferSerializer(serializers.ModelSerializer):

    class Meta:
        model = BankAccountTransfer
        fields = '__all__'

    def create(self, validated_data):
        transfer = BankAccountTransfer.objects.create(**validated_data)
        transfer.make_transfer(validated_data.get("amount", None))

        return transfer
