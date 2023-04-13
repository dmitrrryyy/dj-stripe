import time


class DjStripeHTTPClient:
    """An HTTP client for all dj-stripe network calls to upstream Stripe."""

    # A class attribute to know if we are triggerring from within
    # pytest or not. Need that to ignore a few Stripe errors.
    _is_test = False

    def _should_retry(self, stripe_default_client, error, num_retries, kwargs_dict):
        """Returns True if the given request must be retried. False otherwise."""

        max_network_retries = (
            getattr(stripe_default_client, "_max_network_retries", lambda: None)() or 3
        )

        if num_retries >= max_network_retries:
            return False

        http_status = error.http_status
        headers = error.headers
        message = error.user_message

        print(f"http_status: {http_status}, headers: {headers}, message: {message}")

        if headers is not None and headers.get("idempotent-replayed") == "true":
            # https://github.com/stripe/stripe-ruby/pull/907
            # Stripe simply replays the error if a previous erroneous request was made
            # Hence resetting the idempotency_key to create a "new" request
            kwargs_dict["idempotency_key"] = kwargs_dict.get(
                "metadata", {"idempotency_key": None}
            )["idempotency_key"] = None

        # We retry for limit your requests exception only when running test
        if DjStripeHTTPClient._is_test:
            # Should only be retried when running in pytest
            # Happens when accounts are created rapidly.
            if http_status == 400 and "limit your requests" in message:
                return True

        # Retry on Rate Limit errors.
        if http_status == 429 or (
            http_status == 400 and "limit your requests" in message
        ):
            return True

        return False

    def _request_with_retries(
        self,
        func,
        id="",
        **kwargs,
    ) -> dict:
        """Attempts HTTP requests with exponential backoff until the
        limit for max network retried is reached."""
        from stripe import default_http_client

        num_retries = 0

        while True:
            try:
                if id:
                    response = func(id, **kwargs)
                else:
                    response = func(**kwargs)

                print("GOT RESPONSE!")
                return response
            except Exception as e:
                error = e

            if self._should_retry(default_http_client, error, num_retries, kwargs):
                num_retries += 1
                sleep_time = default_http_client._sleep_time_seconds(num_retries)

                print(f"retrying request {self}, {func}")
                print(f"sleeping for {sleep_time} seconds")
                time.sleep(sleep_time)

            else:
                raise error


djstripe_client = DjStripeHTTPClient()