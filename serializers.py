from decimal import Decimal

from django.db import transaction, IntegrityError
from rest_framework import serializers, status
from django.utils.translation import gettext as _
from .models import UserTransaction, UserWallet

MINIMUM_AMOUNT_FOR_FEE = Decimal('1000')
FEE_COMMISSION = Decimal('0.1')
WALLET_FEE_ID = 1

class TransactionSerializer(serializers.Serializer):
    wallet_from_id = serializers.IntegerField()
    wallet_to_id = serializers.IntegerField()
    amount = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        min_value=Decimal('0.01')
    )
    txid = serializers.CharField(max_length=64, required=True)

    def validate_txid(self, value):
        try:
            existing_transaction = UserTransaction.objects.get(txid=value)

            if existing_transaction.transaction_status == UserTransaction.TransactionStatus.COMPLETED:
                self.idempotency_result = {
                    "status": status.HTTP_200_OK,
                    "response_data": {"detail": _("Request with idempotency_key %s has already been executed.") % value}
                }
            elif existing_transaction.transaction_status == UserTransaction.TransactionStatus.PENDING:
                self.idempotency_result = {
                    "status": status.HTTP_200_OK,
                    "response_data": {"details": _("Request with idempotency_key %s is already processing.") % value}
                }
            elif existing_transaction.transaction_status == UserTransaction.TransactionStatus.FAILED:
                self.idempotency_result = {
                    "status": status.HTTP_200_OK,
                    "response_data": {"detail": _("Request with idempotency_key %s has already been executed with error.") % value}
                }
        except Exception:
            pass

        return value

    def validate_wallet_from_id(self, value):
        try:
            UserWallet.objects.get(pk=value, is_active=True)
        except UserWallet.DoesNotExist:
            raise serializers.ValidationError(
                _("The sender's wallet with ID %d is missing or inactive.") % value
            )
        return value

    def validate_wallet_to_id(self, value):
        try:
            UserWallet.objects.get(pk=value, is_active=True)
        except UserWallet.DoesNotExist:
            raise serializers.ValidationError(
                _("The recipient's wallet with ID %d is missing or inactive.") % value
            )
        return value

    def validate(self, attrs):
        wallet_from_id = attrs.get('wallet_from_id')
        wallet_to_id = attrs.get('wallet_to_id')

        if wallet_from_id == wallet_to_id:
            raise serializers.ValidationError(
                _("The sender's wallet and the recipient's wallet must be different.")
            )

        return attrs

    def create(self, validated_data):
        amount = validated_data['amount']
        txid = validated_data['txid']

        if hasattr(self, 'idempotency_result'):
            return UserTransaction.objects.get(txid=txid)

        try:
            with transaction.atomic():
                wallet_from = UserWallet.objects.select_for_update().get(
                    pk=validated_data['wallet_from_id'], is_active=True
                )
                wallet_to = UserWallet.objects.select_for_update().get(
                    pk=validated_data['wallet_to_id'], is_active=True
                )

                if wallet_from.balance < amount:
                    raise serializers.ValidationError(
                        {"detail": _("Insufficient funds on balance.")},
                        code='insufficient_funds'
                    )

                if amount > MINIMUM_AMOUNT_FOR_FEE:
                    wallet_fee = UserWallet.objects.select_for_update().get(
                        pk=WALLET_FEE_ID, is_active=True
                    )
                    amount_fee = amount * FEE_COMMISSION
                    amount_to = amount - amount_fee
                else:
                    wallet_fee = None
                    amount_fee = Decimal('0.0')
                    amount_to = amount

                amount_from = amount

                wallet_from.balance -= amount_from
                wallet_to.balance += amount_to

                wallet_from.save()
                wallet_to.save()

                if wallet_fee:
                    wallet_fee.balance += amount_fee
                    wallet_fee.save()

                new_transaction = UserTransaction.objects.create(
                    transaction_type=UserTransaction.TransactionType.INCOMING,
                    transaction_status=UserTransaction.TransactionStatus.COMPLETED,
                    wallet_from=wallet_from,
                    wallet_to=wallet_to,
                    wallet_fee=wallet_fee,
                    amount_from=amount_from,
                    amount_to=amount_to,
                    amount_fee=amount_fee,
                    txid=txid
                )

                return new_transaction

        except UserWallet.DoesNotExist as e:
            raise serializers.ValidationError(
                {"detail": f"Wallet ID not found: {e.args[0]}"},
                code='wallet_not_found'
            )
        except IntegrityError:
            raise serializers.ValidationError(
                {"detail": _("A transaction with this ID is already being processed or exists.")},
                code='integrity_violation'
            )