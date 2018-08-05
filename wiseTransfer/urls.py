from django.contrib import admin
from django.urls import path
from rest_framework.schemas import get_schema_view
from rest_framework_jwt.views import *
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer
from rest_framework_swagger.views import get_swagger_view

from app import views
schema_view = get_schema_view(title='Users API', renderer_classes=[OpenAPIRenderer, SwaggerUIRenderer])

urlpatterns = [
    path('', views.ApiRoot.as_view(), name=views.ApiRoot.name),
    path('docs/', schema_view),
    path('admin/', admin.site.urls),
    path('api-token-auth/', obtain_jwt_token),
    path('api-token-refresh/', refresh_jwt_token),
    path('api-token-verify/', verify_jwt_token),
    path('users/', views.Account.as_view(), name=views.Account.name),
    path('users/<int:pk>/', views.AccountDetail.as_view(), name=views.AccountDetail.name),
    path('wallet/', views.WalletDetail.as_view(), name=views.WalletDetail.name),
    path('transfers/', views.TransfersList.as_view(), name=views.TransfersList.name),
    path('transfers/<int:pk>/', views.TransferDetail.as_view(), name=views.TransferDetail.name),
    path('credit-cards/', views.CreditCardList.as_view(), name=views.CreditCardList.name),
    path('credit-cards/<int:pk>/', views.CreditCardDetail.as_view(), name=views.CreditCardDetail.name),
    path('banks/', views.BankList.as_view(), name=views.BankList.name),
    path('banks/<int:pk>/', views.BankDetail.as_view(), name=views.BankDetail.name),
    path('bank-accounts/', views.BankAccountList.as_view(), name=views.BankAccountList.name),
    path('bank-accounts/<int:pk>/', views.BankAccountDetail.as_view(), name=views.BankAccountDetail.name),
    path('wallet-to-banks/', views.TransferToBank.as_view(), name=views.TransferToBank.name),
    path('wallet-to-banks/<int:pk>/', views.TransferToBankDetail.as_view(), name=views.TransferToBankDetail.name),
]
