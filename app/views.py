import django_filters
from django.db.models import Q
from django.http import Http404, HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import APIException
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.utils import json
from django.contrib.auth.hashers import make_password

from .serializers import *
from app.models import *
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User as U


class ApiRoot(generics.GenericAPIView):
    name = 'api-root'
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        return Response({
            'users': reverse(Account.name, request=request),
            'wallet': reverse(WalletDetail.name, request=request),
            'transfers': reverse(TransfersList.name, request=request),
            'credit-cards': reverse(CreditCardList.name, request=request),
            'banks': reverse(BankList.name, request=request),
            'bank-accounts': reverse(BankAccountList.name, request=request),
            'wallet-to-banks': reverse(TransferToBank.name, request=request),
         })


class Account(generics.ListCreateAPIView):
    name = 'user'
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['post', 'get']
    # permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('name', 'code')

    def post(self, request, format=None):
        data = JSONParser().parse(request)
        serializer = SaveUserSerializer(data=data)

        if not serializer.is_valid():
            return Response(serializer.errors)

        try:
            user_obj = U.objects.create(username=serializer.data["username"],
                                        password=make_password(serializer.data["password"]),
                                        email=serializer.data["email"],
                                        last_login="2018-08-01 00:00")
            User.objects.create(name=serializer.data["name"], code=uuid.uuid4().hex, owner=user_obj)
        except Exception as e:
            raise APIException(e)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AccountDetail(generics.CreateAPIView):
    name = 'user-detail'
    queryset = User.objects.all()
    serializer_class = SaveUserSerializer
    http_method_names = ['post', 'get']
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk, format=None):
        try:
            user = User.objects.get(id=pk)
        except Exception as e:
            raise APIException(e)

        serializer = UserDetailSerializer(user, many=False, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class TransfersList(generics.ListCreateAPIView):
    name = 'transfer-list'
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    http_method_names = ['post', 'get']
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_fields = ('was_transferred', 'donor', 'donee')
    search_fields = ('donor__name', 'donee__name')
    ordering_fields = ('date',)

    def get_queryset(self):
        return Transfer.objects.filter(Q(donor_id=self.request.user.id) | Q(donee_id=self.request.user.id)).all()

    def post(self, request, format=None):

        data = JSONParser().parse(request)
        serializer = SaveTransferSerializer(data=data, context={'request': request})

        if not serializer.is_valid():
            return Response(serializer.errors)

        try:
            receiver_user = User.objects.get(id=serializer.data["donee"])
        except Exception as e:
            raise APIException(e)

        transfer = Transfer.objects.create(donor_id=request.user.id, donee=receiver_user, amount=serializer.data["amount"])

        if not transfer.make_transfer():
            return Response({"error": "Could't transfer the money. You may not have enough money?"}, status=status.HTTP_409_CONFLICT)

        return Response(status=status.HTTP_201_CREATED)


class TransferDetail(generics.ListAPIView):
    name = 'transfer-detail'
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    http_method_names = ['get']
    permission_classes = (IsAuthenticated,)
    pagination_class = None

    def list(self, request, pk):
        print(pk)
        self.queryset = Transfer.objects.get(id=pk)
        serializer = TransferSerializer(self.get_queryset(), many=False, context={"request": request})
        return Response(serializer.data)


class CardToWallet(generics.CreateAPIView):
    name = 'card-to-wallet-list'
    queryset = Wallet.objects.all()
    serializer_class = TransferSerializer
    http_method_names = ['post', 'get']
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        data = JSONParser().parse(request)

        serializer = TransferSerializer(data)

        if not serializer.is_valid():
            return Response(serializer.errors)

        try:
            receiver = User.objects.get(code=serializer.data.hash)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

        transfer = TransfersList.create(donor=request.user, donee=receiver, amount=serializer.data.amount)

        if not transfer.make_transfer():
            return Response({"error": "Could't transfer the money. You may not have enough money."}, status=status.HTTP_409_CONFLICT)

        return Response(status=status.HTTP_201_CREATED)


class WalletDetail(generics.ListAPIView):
    name = 'wallet-detail'
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    http_method_names = ['get']
    permission_classes = (IsAuthenticated,)
    pagination_class = None

    def list(self, request):
        print(request.user.id)
        self.queryset = Wallet.objects.get(owner_id=request.user.id)
        serializer = WalletSerializer(self.get_queryset(), many=False, context={"request": request})
        return Response(serializer.data)


class CreditCardList(generics.ListCreateAPIView):

    name = 'card-list'
    queryset = CreditCard.objects.all()
    serializer_class = CreditCardSerializer
    http_method_names = ['get', 'post']
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return CreditCard.objects.filter(wallet__owner_id=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(
            wallet_id=Wallet.objects.get(owner_id=self.request.user.id).id,
            card_token=uuid.uuid4().hex
        )


class CreditCardDetail(generics.ListAPIView):

    name = 'creditcard-detail'
    queryset = CreditCard.objects.all()
    serializer_class = CreditCardSerializer
    http_method_names = ['get', 'put']
    permission_classes = (IsAuthenticated,)
    pagination_class = None

    def get_queryset(self):
        return CreditCard.objects.get(wallet__owner_id=self.request.query_params['pk'])


class BankList(generics.ListAPIView):
    name = 'bank-list'
    queryset = Bank.objects.all()
    serializer_class = BankSerializer
    http_method_names = ['get']
    permission_classes = (IsAuthenticated,)


class BankDetail(generics.ListAPIView):
    name = 'bank-detail'
    queryset = Bank.objects.all()
    serializer_class = BankSerializer
    http_method_names = ['get']
    permission_classes = (IsAuthenticated,)

    def list(self, request, pk):
        print(pk)
        self.queryset = Bank.objects.get(id=pk)
        serializer = TransferSerializer(self.get_queryset(), many=False, context={"request": request})
        return Response(serializer.data)


class BankAccountList(generics.ListCreateAPIView):
    name = 'bankaccount-list'
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    http_method_names = ['get', 'post']
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return BankAccount.objects.filter(user_id=self.request.user.id).all()

    def perform_create(self, serializer):
        serializer.save(
            user_id=self.request.user.id
        )


class BankAccountDetail(generics.ListAPIView):
    name = 'bankaccount-detail'
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    http_method_names = ['get']
    permission_classes = (IsAuthenticated,)

    def list(self, request, pk):
        self.queryset = BankAccount.objects.get(user_id=request.user.id, id=pk)
        serializer = BankAccountSerializer(self.get_queryset(), many=False, context={"request": request})
        return Response(serializer.data)


class TransferToBank(generics.ListCreateAPIView):
    name = 'transfertobank-list'
    queryset = BankAccountTransfer.objects.all()
    serializer_class = SaveBankAccountTransferSerializer
    http_method_names = ['get', 'post']
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return BankAccountTransfer.objects.filter(bank_account__user_id=self.request.user.id).all()

    def perform_create(self, serializer):
        # self.serializer_class = SaveBankAccountTransferSerializer
        serializer.save(
            bank_account_id=str(self.request.data["bank_account"])
        )


class TransferToBankDetail(generics.ListAPIView):
    name = 'transfertobank-list'
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    http_method_names = ['get']
    permission_classes = (IsAuthenticated,)

    def list(self, request):
        # print(pk)
        self.queryset = BankAccount.objects.filter(user_id=request.user.id)
        serializer = BankAccountSerializer(self.get_queryset(), many=False, context={"request": request})
        return Response(serializer.data)

