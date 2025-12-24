from decimal import Decimal

from django.db import models
from django.utils.translation import gettext as _
from profile.models import Profile

class UserWallet(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        related_name='user_user_wallets',
        verbose_name=_("Wallets owner User Profile")
    )
    balance = models.DecimalField(
        max_digits=18, decimal_places=8, default=Decimal('0.00000000'),
        verbose_name=_("Wallet balance")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Create date"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Update date"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active Wallet?"))

    class Meta:
        verbose_name = _("Useer wallets")
        verbose_name_plural = _("User wallet")
        ordering = ['-id']
        indexes = [
            models.Index(fields=['profile', 'is_active']),
        ]

    def __str__(self):
        return f"Wallet type  {self.profile.user.username}: {self.balance}"


class UserTransaction(models.Model):
    class TransactionType(models.IntegerChoices):
        INCOMING = 0

    class TransactionStatus(models.IntegerChoices):
        PENDING = 0
        COMPLETED = 1
        FAILED = 2

    transaction_type = models.PositiveSmallIntegerField(choices=TransactionType.choices,
                                                        verbose_name=_("Transaction type"))
    transaction_status = models.PositiveSmallIntegerField(choices=TransactionStatus.choices,
                                                          verbose_name=_("Transaction status"))
    wallet_from = models.ForeignKey(UserWallet, on_delete=models.PROTECT,
                                      related_name='wallet_from_transactions')
    wallet_to = models.ForeignKey(UserWallet, on_delete=models.PROTECT,
                                      related_name='wallet_to_transactions')
    wallet_fee = models.ForeignKey(UserWallet, null=True, on_delete=models.PROTECT,
                                      related_name='wallet_fee_transactions')
    amount_from = models.DecimalField(max_digits=18, decimal_places=8, verbose_name=_("Amount from"))
    amount_to = models.DecimalField(max_digits=18, decimal_places=8, verbose_name=_("Amount to"))
    amount_fee = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0.00000000'),
                                     verbose_name=_("Amount fee"))
    txid = models.CharField(max_length=64, unique=True, db_index=True, help_text="Transaction key")
    description = models.CharField(max_length=300, blank=True, default='',
                                   verbose_name=_("Transaction Description"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
        ordering = ['-created_at']

    def __str__(self):
        return f"TX {self.pk}: {self.txid} / {self.amount_from} / {self.amount_to} / {self.amount_fee}"