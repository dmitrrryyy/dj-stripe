"""
dj-stripe System Checks
"""
import re

import stripe
from django.core import checks
from django.db.utils import DatabaseError

from djstripe.models.api import get_api_key_details_by_prefix

STRIPE_API_VERSION_PATTERN = re.compile(
    r"(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})(; [\w=]*)?$"
)


@checks.register("djstripe")
def check_stripe_api_key(app_configs=None, **kwargs):
    """Check the user has configured API live/test keys correctly."""

    from djstripe.models import APIKey

    messages = []

    try:
        # get all APIKey objects in the db
        api_qs = APIKey.objects.all()

        if not api_qs.exists():
            msg = (
                "You don't have any API Keys in the database. Did you forget to add"
                " them?"
            )
            hint = (
                "Add STRIPE_TEST_SECRET_KEY and STRIPE_LIVE_SECRET_KEY directly from"
                " the Django Admin."
            )
            messages.append(checks.Warning(msg, hint=hint, id="djstripe.W003"))

        if stripe.api_key:
            # Warn the user if stripe.api_key is set
            msg = "You have set stripe.api_key. Please unset it and add Stripe keys from admin to the DB."
            messages.append(checks.Info(msg, id="djstripe.I001"))

            key_type, livemode = get_api_key_details_by_prefix(stripe.api_key)

            if APIKey.objects.filter(type=key_type, livemode=livemode).exists():
                msg = (
                    "You have configured both stripe.api_key and keys from the admin. Please unset stripe.api_key."
                    " dj-stripe may not work properly due to ambiguity in fetching keys."
                )
                messages.append(checks.Warning(msg, id="djstripe.W004"))

    except DatabaseError:
        # Skip the check - Database most likely not migrated yet
        return []

    return messages


def validate_stripe_api_version(version):
    """
    Check the API version is formatted correctly for Stripe.

    The expected format is `YYYY-MM-DD` (an iso8601 date) or
    for access to alpha or beta releases the expected format is: `YYYY-MM-DD; modelname_version=version_number`.
    Ex "2020-08-27; orders_beta=v3"

    :param version: The version to set for the Stripe API.
    :type version: ``str``
    :returns bool: Whether the version is formatted correctly.
    """
    return re.match(STRIPE_API_VERSION_PATTERN, version)


@checks.register("djstripe")
def check_stripe_api_version(app_configs=None, **kwargs):
    """Check the user has configured API version correctly."""
    from .settings import djstripe_settings

    messages = []
    default_version = djstripe_settings.DEFAULT_STRIPE_API_VERSION
    version = djstripe_settings.STRIPE_API_VERSION

    if not validate_stripe_api_version(version):
        msg = f"Invalid Stripe API version: {version!r}"
        hint = "STRIPE_API_VERSION should be formatted as: YYYY-MM-DD"
        messages.append(checks.Critical(msg, hint=hint, id="djstripe.C004"))

    if version != default_version:
        msg = (
            f"The Stripe API version has a non-default value of '{version!r}'. "
            "Non-default versions are not explicitly supported, and may "
            "cause compatibility issues."
        )
        hint = f"Use the dj-stripe default for Stripe API version: {default_version}"
        messages.append(checks.Warning(msg, hint=hint, id="djstripe.W001"))

    return messages


@checks.register("djstripe")
def check_stripe_api_host(app_configs=None, **kwargs):
    """
    Check that STRIPE_API_HOST is not being used in production.
    """
    from django.conf import settings

    messages = []

    if not settings.DEBUG and hasattr(settings, "STRIPE_API_HOST"):
        messages.append(
            checks.Warning(
                (
                    "STRIPE_API_HOST should not be set in production! "
                    "This is most likely unintended."
                ),
                hint="Remove STRIPE_API_HOST from your Django settings.",
                id="djstripe.W002",
            )
        )

    return messages


@checks.register("djstripe")
def check_webhook_endpoint_has_secret(app_configs=None, **kwargs):
    """Checks if all Webhook Endpoints have not empty secrets."""
    from djstripe.models import WebhookEndpoint

    messages = []

    try:
        qs = list(WebhookEndpoint.objects.filter(secret="").all())
    except DatabaseError:
        # Skip the check - Database most likely not migrated yet
        return []

    for webhook in qs:
        webhook_url = webhook.get_stripe_dashboard_url()
        messages.append(
            checks.Warning(
                (
                    f"The secret of Webhook Endpoint: {webhook} is not populated "
                    "in the db. Events sent to it will not work properly."
                ),
                hint=(
                    "This can happen if it was deleted and resynced as Stripe "
                    "sends the webhook secret ONLY on the creation call. "
                    "Please use the django shell and update the secret with "
                    f"the value from {webhook_url}"
                ),
                id="djstripe.W005",
            )
        )

    return messages


@checks.register("djstripe")
def check_subscriber_key_length(app_configs=None, **kwargs):
    """
    Check that DJSTRIPE_SUBSCRIBER_CUSTOMER_KEY fits in metadata.

    Docs: https://stripe.com/docs/api#metadata
    """
    from .settings import djstripe_settings

    messages = []

    key = djstripe_settings.SUBSCRIBER_CUSTOMER_KEY
    key_max_length = 40
    if key and len(key) > key_max_length:
        messages.append(
            checks.Error(
                (
                    "DJSTRIPE_SUBSCRIBER_CUSTOMER_KEY must be no more than "
                    f"{key_max_length} characters long"
                ),
                hint=f"Current value: {key!r}",
                id="djstripe.E001",
            )
        )

    return messages


@checks.register("djstripe")
def check_webhook_event_callback_accepts_api_key(app_configs=None, **kwargs):
    """
    Checks if the custom callback accepts atleast 2 mandatory positional arguments
    """
    from inspect import signature

    from .settings import djstripe_settings

    messages = []

    # callable can have exactly 2 arguments or
    # if more than two, the rest need to be optional.
    callable = djstripe_settings.WEBHOOK_EVENT_CALLBACK

    if callable:
        # Deprecated in 2.8.0. Raise a warning.
        messages.append(
            checks.Warning(
                (
                    "DJSTRIPE_WEBHOOK_EVENT_CALLBACK is deprecated. See release notes"
                    " for details."
                ),
                hint=(
                    "If you need to trigger a function during webhook processing, "
                    "you can use djstripe.signals instead.\n"
                    "Available signals:\n"
                    "- djstripe.signals.webhook_pre_validate\n"
                    "- djstripe.signals.webhook_post_validate\n"
                    "- djstripe.signals.webhook_pre_process\n"
                    "- djstripe.signals.webhook_post_process\n"
                    "- djstripe.signals.webhook_processing_error"
                ),
            )
        )

        sig = signature(callable)
        signature_sz = len(sig.parameters.keys())

        if signature_sz < 2:
            messages.append(
                checks.Error(
                    f"{callable} accepts {signature_sz} arguments.",
                    hint=(
                        "You may have forgotten to add api_key parameter to your custom"
                        " callback."
                    ),
                    id="djstripe.E004",
                )
            )

    return messages
