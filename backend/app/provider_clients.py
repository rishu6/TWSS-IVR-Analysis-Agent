"""Read-only provider contracts. No provider mutation or call-placement API exists here."""
import time
from datetime import UTC, datetime
from urllib.parse import urlsplit

import httpx

TRUSTED_LSQ = {'api.leadsquared.com','api-us11.leadsquared.com','api-in21.leadsquared.com',
               'api-in22.leadsquared.com','api-me61.leadsquared.com','api-ir31.leadsquared.com','api-ca12.leadsquared.com'}


class ProviderError(ConnectionError):
    pass


class ReadOnlyTransport:
    def __init__(self, host, headers, transport=None, interval=2.0, sleep=time.sleep):
        self.host, self.headers, self.interval, self.sleep = host, headers, interval, sleep
        self.http = httpx.Client(timeout=30, follow_redirects=False, trust_env=False, transport=transport)
        self.last_request = 0

    def request(self, method, path, **kwargs):
        for attempt in range(3):
            self.sleep(max(0, self.interval-(time.monotonic()-self.last_request)))
            self.last_request = time.monotonic()
            try:
                response = self.http.request(method, self.host+path, headers=self.headers, **kwargs)
            except httpx.RequestError:
                if attempt == 2:
                    raise ProviderError('Provider network or TLS error') from None
                self.sleep(2**attempt)
                continue
            if response.status_code == 429 or response.status_code >= 500:
                if attempt < 2:
                    try:
                        delay = min(30, max(1, float(response.headers.get('Retry-After', 2**attempt))))
                    except ValueError:
                        delay = 2**attempt
                    self.sleep(delay)
                    continue
            if response.status_code != 200:
                raise ProviderError(f'Provider HTTP {response.status_code}; check credentials, scope and quota')
            try:
                data = response.json()
            except ValueError:
                raise ProviderError('Provider returned invalid JSON') from None
            if isinstance(data, dict) and data.get('Status') == 'Error':
                raise ProviderError('Provider returned an application error')
            return data
        raise ProviderError('Provider retry limit reached')

    def close(self):
        self.http.close()


class LiveAcefoneClient:
    """https://docs.acefone.in/reference/call-detail-records-2.md"""
    def __init__(self, token=None, **kwargs):
        if not token:
            raise RuntimeError('Acefone credentials unverified: token required')
        self.transport = ReadOnlyTransport('https://api.acefone.in',
            {'Authorization':'Bearer '+token,'Accept':'application/json'}, **kwargs)

    def record_page(self, start, end, page=1, limit=100,direction=None):
        params={
            'from_date':start.strftime('%Y-%m-%d %H:%M:%S'),'to_date':end.strftime('%Y-%m-%d %H:%M:%S'),
            'page':str(page),'limit':str(limit)}
        if direction:params['direction']=direction
        data = self.transport.request('GET','/v1/call/records',params=params)
        if not isinstance(data, dict) or not isinstance(data.get('results'), list):
            raise ProviderError('Unexpected Acefone CDR schema')
        if int(data.get('page', page)) != page:
            raise ProviderError('Acefone pagination did not advance')
        effective_limit=int(data.get('limit') or limit)
        if effective_limit<1:raise ProviderError('Invalid Acefone page size')
        return {'rows':data['results'],'page':page,'limit':effective_limit,
                'has_more':len(data['results'])>=effective_limit}

    def records(self,start,end,page=1,limit=100,direction=None):
        return self.record_page(start,end,page,limit,direction)['rows']

    def close(self):
        self.transport.close()


class LiveLeadSquaredClient:
    """Read-only enumeration for complete normalized Phone/Mobile matching.

    https://apidocs.leadsquared.com/search-by-lead-criteria/
    All pages must finish before the local candidate set is treated as complete.
    """
    def __init__(self, credentials=None, **kwargs):
        if not credentials:
            raise RuntimeError('LeadSquared credentials unverified: configuration required')
        host = urlsplit(credentials['LEADSQUARED_API_HOST'])
        if (host.scheme != 'https' or host.hostname not in TRUSTED_LSQ or host.username or host.password
                or host.query or host.fragment or host.port not in (None,443) or host.path not in ('','/','/v2','/v2/')):
            raise ValueError('Unverified LeadSquared API host')
        self.transport = ReadOnlyTransport('https://'+host.hostname,
            {'x-LSQ-AccessKey':credentials['LEADSQUARED_ACCESS_KEY'],
             'x-LSQ-SecretKey':credentials['LEADSQUARED_SECRET_KEY'],'Accept':'application/json'}, **kwargs)

    def users(self):
        """Official read-only directory: https://apidocs.leadsquared.com/get-users/"""
        data=self.transport.request('GET','/v2/UserManagement.svc/Users.Get')
        if not isinstance(data,list) or any(not isinstance(row,dict) or not row.get('ID') for row in data):
            raise ProviderError('Unexpected LeadSquared user-directory schema')
        return data

    def page(self, index=1, size=100):
        data = self.transport.request('POST','/v2/LeadManagement.svc/Leads.Get',json={
            'Parameter':{'LookupName':'CreatedOn','LookupValue':'1970-01-01 00:00:00','SqlOperator':'>='},
            'Columns':{'Include_CSV':'ProspectID,FirstName,LastName,Phone,Mobile,CreatedOn,ProspectStage,OwnerId,Source'},
            'Sorting':{'ColumnName':'CreatedOn','Direction':'0'},'Paging':{'PageIndex':index,'PageSize':size}})
        if not isinstance(data,list) or any(not isinstance(row,dict) or not row.get('ProspectID') for row in data):
            raise ProviderError('Unexpected LeadSquared lead-list schema')
        return data

    def phone_candidates(self, phone):
        """Documented Leads.Get criteria; normalize results before accepting a match.

        A suffix search includes country-code prefixes and common stored formats.
        Both Phone and Mobile are searched; every result page must complete.
        """
        digits=''.join(c for c in phone if c.isdigit())
        if len(digits)<7:raise ValueError('Invalid phone number')
        found={}
        for field in ('Phone','Mobile'):
            for page in range(1,11):
                rows=self.transport.request('POST','/v2/LeadManagement.svc/Leads.Get',json={
                    'Parameter':{'LookupName':field,'LookupValue':'%'+digits[-4:],'SqlOperator':'LIKE'},
                    'Columns':{'Include_CSV':'ProspectID,FirstName,LastName,Phone,Mobile,CreatedOn,ProspectStage,OwnerId,Source'},
                    'Sorting':{'ColumnName':'CreatedOn','Direction':'1'},
                    'Paging':{'PageIndex':page,'PageSize':1000}})
                if not isinstance(rows,list) or any(not isinstance(r,dict) or not r.get('ProspectID') for r in rows):
                    raise ProviderError('Unexpected LeadSquared lead-list schema')
                for row in rows:found[row['ProspectID']]=row
                if len(rows)<1000:break
            else:raise ProviderError('Phone search incomplete; retry required')
        return list(found.values())

    def close(self):
        self.transport.close()
