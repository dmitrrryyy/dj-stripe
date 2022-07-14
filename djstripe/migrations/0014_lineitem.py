# Generated by Django 3.2.16 on 2023-01-26 05:14

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import djstripe.enums
import djstripe.fields


class Migration(migrations.Migration):
    dependencies = [
        ("djstripe", "0013_product_default_price"),
    ]

    operations = [
        migrations.CreateModel(
            name="LineItem",
            fields=[
                ("djstripe_created", models.DateTimeField(auto_now_add=True)),
                ("djstripe_updated", models.DateTimeField(auto_now=True)),
                (
                    "djstripe_id",
                    models.BigAutoField(
                        primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("id", djstripe.fields.StripeIdField(max_length=255, unique=True)),
                (
                    "livemode",
                    models.BooleanField(
                        blank=True,
                        default=None,
                        help_text="Null here indicates that the livemode status is unknown or was previously unrecorded. Otherwise, this field indicates whether this record comes from Stripe test mode or live mode operation.",
                        null=True,
                    ),
                ),
                ("created", djstripe.fields.StripeDateTimeField(blank=True, null=True)),
                ("metadata", djstripe.fields.JSONField(blank=True, null=True)),
                (
                    "description",
                    models.TextField(
                        blank=True, help_text="A description of this object.", null=True
                    ),
                ),
                ("amount", djstripe.fields.StripeQuantumCurrencyAmountField()),
                (
                    "amount_excluding_tax",
                    djstripe.fields.StripeQuantumCurrencyAmountField(),
                ),
                ("currency", djstripe.fields.StripeCurrencyCodeField(max_length=3)),
                ("discount_amounts", djstripe.fields.JSONField(blank=True, null=True)),
                (
                    "discountable",
                    models.BooleanField(
                        default=False,
                        help_text="If True, discounts will apply to this line item. Always False for prorations.",
                    ),
                ),
                ("discounts", djstripe.fields.JSONField(blank=True, null=True)),
                ("period", djstripe.fields.JSONField()),
                ("period_end", djstripe.fields.StripeDateTimeField()),
                ("period_start", djstripe.fields.StripeDateTimeField()),
                ("price", djstripe.fields.JSONField()),
                (
                    "proration",
                    models.BooleanField(
                        default=False,
                        help_text="Whether or not the invoice item was created automatically as a proration adjustment when the customer switched plans.",
                    ),
                ),
                ("proration_details", djstripe.fields.JSONField()),
                ("tax_amounts", djstripe.fields.JSONField(blank=True, null=True)),
                ("tax_rates", djstripe.fields.JSONField(blank=True, null=True)),
                (
                    "type",
                    djstripe.fields.StripeEnumField(
                        enum=djstripe.enums.LineItem, max_length=12
                    ),
                ),
                (
                    "unit_amount_excluding_tax",
                    djstripe.fields.StripeDecimalCurrencyAmountField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "quantity",
                    models.IntegerField(
                        blank=True,
                        help_text="The quantity of the subscription, if the line item is a subscription or a proration.",
                        null=True,
                    ),
                ),
                (
                    "djstripe_owner_account",
                    djstripe.fields.StripeForeignKey(
                        blank=True,
                        help_text="The Stripe Account this object belongs to.",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="djstripe.account",
                        to_field=settings.DJSTRIPE_FOREIGN_KEY_TO_FIELD,
                    ),
                ),
                (
                    "invoice_item",
                    djstripe.fields.StripeForeignKey(
                        blank=True,
                        help_text="The ID of the invoice item associated with this line item if any.",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="djstripe.invoiceitem",
                        to_field=settings.DJSTRIPE_FOREIGN_KEY_TO_FIELD,
                    ),
                ),
                (
                    "subscription",
                    djstripe.fields.StripeForeignKey(
                        blank=True,
                        help_text="The subscription that the invoice item pertains to, if any.",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="djstripe.subscription",
                        to_field=settings.DJSTRIPE_FOREIGN_KEY_TO_FIELD,
                    ),
                ),
                (
                    "subscription_item",
                    djstripe.fields.StripeForeignKey(
                        blank=True,
                        help_text="The subscription item that generated this invoice item. Left empty if the line item is not an explicit result of a subscription.",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="djstripe.subscriptionitem",
                        to_field=settings.DJSTRIPE_FOREIGN_KEY_TO_FIELD,
                    ),
                ),
            ],
            options={
                "get_latest_by": "created",
                "abstract": False,
            },
        ),
    ]