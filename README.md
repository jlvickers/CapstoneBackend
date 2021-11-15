# Capstone Backend
Capstone project was to create a mobile app to analyze historical stock data over a variety of timeframes and automatically run technical analysis indicators against the collected data.

# Database Methodology + interaction
We chose to store the raw data in the database rather than cache TA indicators, since the script can handle any timeframe from 1 min - 4+ hours and every minute would have a different value depending on the indicator. 

Since the API we're using doesn't have real-time data, the database allows us to reduce the amount of API calls made by storing data once per API timeframe (1 min, 5 min, 15 min, 30 min, 60 min) and checking against the stored timeframe in secQueryInfo. If lastQueried in secQueryInfo matches the current date, the script loads a dataframe from the database. If not, it makes an API call and appends the information to the database to be used later if any similar calls are made.

# Script Details
The customUpdater file is used by our flask API hosted on an AWS EC2 instance and takes command line args to specify what the user requests on our front-end.

-n: ticker name, any supported by AlphaVantage

-tf: timeframe of ticker, supports any int in minutes (2h = 120)

-vol, -volatil, -trend, -momo: different indicators defined by their grouping in the technical analysis library we're using. any amount of supported indicators can be used delimited by commas. Custom timeframes for individual indicators can also be added to indicators delimited by semi-colons.

Example: -n SPY -tf 120 -trend ema_indicator;9,ema_indicator;12

Output is sent in JSON format for easy parsing on our frontend system.
