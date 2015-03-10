# TD-Bank-Scraper
This is a python data scraper that allows you to scrape TD Bank data from a single account.  
  - I'm still planning to add an option for the security questions auto-submit


# To use this module, simply:
## This Will Login Automatically
```python
td = TDBank(USERNAME, PASSWORD)
```

## You Can also use 
```python
td = TDBank()
td.login(USERNAME, PASSWORD)
```

## Auto Load 30 days of history from account
```python
df = td.load_history()
```
