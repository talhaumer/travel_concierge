import requests
from typing import Dict, Any
from ratelimit import limits, sleep_and_retry


@sleep_and_retry
@limits(calls=5, period=60)  # 5 calls per minute
def convert_currency(
    amount: float, from_currency: str, to_currency: str
) -> Dict[str, Any]:
    """Convert currency using freecurrencyapi.com (free tier)"""
    try:
        # Using freecurrencyapi.com (requires free API key)
        api_key = os.getenv("CURRENCY_API_KEY", "")
        if api_key:
            url = f"https://api.freecurrencyapi.com/v1/latest"
            params = {
                "apikey": api_key,
                "base_currency": from_currency.upper(),
                "currencies": to_currency.upper(),
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            rate = data["data"][to_currency.upper()]
            converted_amount = amount * rate

            return {
                "original_amount": amount,
                "original_currency": from_currency,
                "converted_amount": converted_amount,
                "target_currency": to_currency,
                "exchange_rate": rate,
            }
        else:
            # Fallback without API key
            return get_fallback_conversion(amount, from_currency, to_currency)

    except Exception as e:
        print(f"Error converting currency: {e}")
        return get_fallback_conversion(amount, from_currency, to_currency)


def get_fallback_conversion(
    amount: float, from_currency: str, to_currency: str
) -> Dict[str, Any]:
    """Fallback currency conversion with approximate rates"""
    conversion_rates = {
        "USD": {"EUR": 0.85, "GBP": 0.75, "JPY": 110.0},
        "EUR": {"USD": 1.18, "GBP": 0.88, "JPY": 130.0},
        "GBP": {"USD": 1.33, "EUR": 1.14, "JPY": 150.0},
    }

    from_curr = from_currency.upper()
    to_curr = to_currency.upper()

    if from_curr in conversion_rates and to_curr in conversion_rates[from_curr]:
        rate = conversion_rates[from_curr][to_curr]
    else:
        rate = 1.0  # Default to 1:1 if unknown currencies

    return {
        "original_amount": amount,
        "original_currency": from_currency,
        "converted_amount": amount * rate,
        "target_currency": to_currency,
        "exchange_rate": rate,
    }
