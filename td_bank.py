import sys
import os
import requests
import time
from dateutil import parser
from pytz import timezone
from datetime import datetime, timedelta
import urllib
import subprocess
from StringIO import *
from bs4 import BeautifulSoup
import re
import pandas as pd
from unidecode import unidecode


class TDBank:
    
    def __init__(self, user_name=None, password=None, ques_dict=None):
        self.s = requests.session()
        self.s.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31'
        self.s.headers['Accept-Encoding'] = "gzip,deflate,sdch"
        self.s.headers['Accept'] = 'application/json, text/javascript, */*'
        self.s.headers['Accept-Language'] = 'en-US,en;q=0.8'
        self.s.headers['X-Requested-With'] = 'XMLHttpRequest'
        self.logged_in = False
        self.account_data = None
        self.user_name = user_name
        self.password = password
        if user_name is not None and password is not None:
            self.response_html = self.login()
    
    def login(self, user_name=None, password=None, ques_dict=None):
        if user_name is not None:
            self.user_name = user_name
        if password is not None:
            self.password = password
        ## Login Script
        # Create Session
        # Hit login Page
        login_page = 'https://onlinebanking.tdbank.com'
        res = self.s.get(login_page)
        # Pull login page with traceid
        lg_page = BeautifulSoup(res.text).findAll('frame')[0].get('src')

        res = self.s.get(lg_page)
        sub_page = 'https://onlinebanking.tdbank.com/voyLogin.asp?' + lg_page.split('?')[1]
        # Post Login Data
        data = {
        'user' : self.user_name, 'pin' : self.password
        }
        res = self.s.post(sub_page, data=data)
        # Check Login Success and Submit Secret Question if Needed
        self.logged_in=True
        return res.text

    def load_history(self, start_date=None, end_date=None):
        # Load Month of Data Page by Default
        if start_date is None:
            start_date=datetime.now() - timedelta(30)
        if end_date is None:
            end_date=datetime.now()
            
        # Load Accts if Needed
        if self.account_data is None:
            now = datetime.now()
            data = {
            'acctID' : '1',
            'useCache' : 'N',
            'sortKey' : '',
            'sortOrder' : '',
            'sortCheckNum' : '',
            'kirchDate' : str(now.strftime('%m/%d/%Y')),
            'searchType' : 'date',
            'selSearch' : 'last10',
            'searchFrom' : str((datetime.now() - timedelta(30)).strftime('%m/%d/%Y')),
            'searchTo' : str(datetime.now().strftime('%m/%d/%Y'))
            }
            acct_page = 'https://onlinebanking.tdbank.com/accts/acct_history.asp'
            res = self.s.post(acct_page, data=data)
            acct_dict = {}
            for l in BeautifulSoup(res.text).findAll('input', attrs={'type':'hidden'}):
                acct_dict[l['name']] = l['value']
                self.account_data = acct_dict
        else:
            acct_dict = self.account_data
        # Download CSV of a Month of Data
        csv_url = 'https://onlinebanking.tdbank.com/accts/qif.asp'
        data = {
        'format' : 'csv',
        'from' : str(start_date.strftime('%m/%d/%Y')), 
        'to' : str(end_date.strftime('%m/%d/%Y')),
        'AccountNumber' : acct_dict['AccountNumber'],
        'BankID' : acct_dict['BankID'],
        'fullAcctType' : acct_dict['fullAcctType'],
        'acctType' : acct_dict['acctType'],
        'totalBal' : acct_dict['totalBal'],
        'acctLedgerBal': acct_dict['acctLedgerBal'],
        'viewPS' : acct_dict['viewPS'],
        'acctDispType' : acct_dict['acctDispType'],
        'acctHost2' : acct_dict['acctHost2'],
        'acctHostAcct1' : acct_dict['acctHostAcct1'],
        'acctHostType' : acct_dict['acctHostType'],
        'selSearch' : acct_dict['selSearch'],
        'acctId' : acct_dict['acctId']
        }
        hist = self.s.post(csv_url, data=data)
        try:
            df = pd.read_csv(StringIO(hist.text))
        except Exception:
            print 'hi'
            # print res.text
        # Add Totals from Current Total
        try:
            final = float(acct_dict['totalBal'].strip('$').replace(',', ''))
        except Exception:
            final = 0
        df['total'] = [(final - sum(df[df.index < i].Amount)) for i in df.index]
        return df