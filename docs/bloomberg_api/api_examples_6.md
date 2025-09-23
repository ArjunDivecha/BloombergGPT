
# BLPAPI Python Examples

## Reference Data Request Example
```python
import blpapi

session = blpapi.Session()
session.start()

service = session.getService("//blp/refdata")
request = service.createRequest("ReferenceDataRequest")

# Add securities
request.getElement("securities").appendValue("AAPL US Equity")
request.getElement("securities").appendValue("MSFT US Equity")

# Add fields
fields = request.getElement("fields")
fields.appendValue("PX_LAST")
fields.appendValue("MARKET_CAP")
fields.appendValue("DVD_EX_DT")
fields.appendValue("VOLUME")

session.sendRequest(request)
```

## Historical Data Request Example
```python
request = service.createRequest("HistoricalDataRequest")
request.getElement("securities").appendValue("SPX Index")
fields = request.getElement("fields")
fields.appendValue("PX_LAST")
fields.appendValue("VOLUME")

periodicity = request.getElement("periodicityAdjustment")
periodicity.setChoice("DAILY")

start_date = request.getElement("startDate")
start_date.setValue("20230101")

end_date = request.getElement("endDate")
end_date.setValue("20231231")

session.sendRequest(request)
```

## Error Handling
```python
try:
    response = session.nextEvent()
    if response.eventType() == blpapi.Event.RESPONSE:
        # Process response
        pass
except Exception as e:
    print(f"Error: {e}")
```

## Best Practices
1. Always check for response errors
2. Use appropriate overrides
3. Batch requests for efficiency
4. Handle session lifecycle properly
5. Use proper date formats


Additional examples for section 6