from decimal import Decimal

from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import TransactionSerializer
from .task import message_notification_api_call

class TransactionAPIView(generics.CreateAPIView):
    permission_classes = []
    serializer_class = TransactionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if hasattr(serializer, 'idempotency_result'):
            result = serializer.idempotency_result
            return Response(
                result['response_data'],
                status=result['status']
            )

        instance = serializer.save()

        message_notification_api_call.delay(instance.txid)

        return Response(
            {
                "txid": instance.txid,
                "transaction_id": instance.id,
                "wallet_from_balance": instance.wallet_from.balance,
                "wallet_to_balance": instance.wallet_to.balance
            },
            status=status.HTTP_201_CREATED
        )