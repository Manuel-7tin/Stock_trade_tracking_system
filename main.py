import requests
from _datetime import datetime, timedelta
from twilio.rest import Client

# You can get your Alpha api key at "https://www.alphavantage.co/"
# Alpha vantage is a Realtime & historical stock market data API
AlPHA_APIKEY = "Your alpha api key"
# You can get your News api key at "https://newsapi.org/"
# Newsapi is a News API is a simple, easy-to-use REST API
NEWS_APIKEY = "Your news api key"
STOCK = "input Company's Ticker symbol e.g TSLA for tesla"
COMPANY_NAME = "input Company's name e.g Tesla Inc"


# Create needed functions
def get_required_dates(jsonf_data) -> dict:
    """Analyzes the stock api json data to determine last update date"""
    date_updated = jsonf_data["Meta Data"]["3. Last Refreshed"]
    today = datetime.today()
    date_index = len(date_updated)
    while True:
        a_date = datetime.isoformat(today)[:date_index]
        if date_updated == a_date:
            day_b4 = today - timedelta(days=1)
            day_b4 = datetime.isoformat(day_b4)[:date_index]
            while day_b4 not in jsonf_data["Time Series (Daily)"]:
                today -= timedelta(days=1)
                day_b4 = datetime.isoformat(today)[:date_index]
            return {"last updated": a_date, "day_b4": day_b4}
        else:
            today = today - timedelta(days=1)


# STEP 1: Use https://www.alphavantage.co
# Get stock price data
stock_params = {
    "function": "TIME_SERIES_DAILY_ADJUSTED",
    "symbol": STOCK,
    "apikey": AlPHA_APIKEY
}
# Get stock data
response = requests.get(url="https://www.alphavantage.co/query?", params=stock_params)
response.raise_for_status()
stock_data = response.json()

# Get Last updated stock dates
required_dates = get_required_dates(jsonf_data=stock_data)
present_date = required_dates["last updated"]
previous_date = required_dates["day_b4"]

# Get Last two dates stock data
present_date_data = stock_data["Time Series (Daily)"][present_date]
previous_date_data = stock_data["Time Series (Daily)"][previous_date]

# Get Last two dates close prices
present_date_price = float(present_date_data["4. close"])
previous_date_price = float(previous_date_data["4. close"])

# Get price rise or fall in percentage
price_change = (present_date_price - previous_date_price)/present_date_price * 100


# STEP 2: Use https://newsapi.org
# Get relevant news
if price_change > 4 or price_change < -4:
    news_param = {
        "q": "tesla",
        "from": previous_date,
        "to": present_date,
        "sortBy": "relevance",
        "apiKey": NEWS_APIKEY
    }
    response = requests.get(url="https://newsapi.org/v2/everything?", params=news_param)
    response.raise_for_status()
    news_data = response.json()
    all_news = news_data["articles"]
    news_list = [news for news in all_news if news["publishedAt"][:10] == present_date]

    # Create/structure message
    company_name = stock_data["Meta Data"]["2. Symbol"]
    emoji = "🔺"
    for num in range(3):
        if num >= len(news_list):
            break
        news_source = news_list[num]["source"]["name"]
        news_headline = news_list[num]["title"]
        news_summary = news_list[num]["description"]
        if price_change < 0:
            emoji = "🔻"
            price_change *= -1
        msg = f"{company_name}: {emoji}{price_change}%\nSource: {news_source}.\nHeadline: {news_headline}.\nBrief: {news_summary}."

        # STEP 3: Use https://www.twilio.com
        # You can get your twilio variables at "https://www.twilio.com/en-us"
        # Twilio is a Twilio is a trusted platform that efficiently powers your customer engagement
        # Send message to recipients phone number.
        account_sid = "your twilio account sid"
        auth_token = "your twilio auth token"
        client = Client(account_sid, auth_token)

        message = client.messages.create(
                             body=msg,
                             from_='your twilio number',
                             to='Recipient/Customer number'
        )
        print(message.sid)
        print(message.status)
