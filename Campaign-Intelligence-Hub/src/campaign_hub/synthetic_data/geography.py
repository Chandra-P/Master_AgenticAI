"""Fictional aggregate locations around approximate regional city centers."""
CENTERS={
    'TX':[(30.267,-97.743,'Austin'),(32.777,-96.797,'Dallas'),(29.760,-95.370,'Houston'),(29.424,-98.494,'San Antonio'),(32.756,-97.331,'Fort Worth')],
    'CA':[(34.052,-118.244,'Los Angeles'),(32.716,-117.161,'San Diego'),(37.338,-121.886,'San Jose'),(38.582,-121.494,'Sacramento'),(36.738,-119.787,'Fresno')],
    'IL':[(41.878,-87.630,'Chicago'),(39.782,-89.650,'Springfield'),(41.751,-88.154,'Naperville'),(40.694,-89.589,'Peoria'),(42.271,-89.094,'Rockford')],
    'FL':[(25.762,-80.192,'Miami'),(28.538,-81.379,'Orlando'),(27.951,-82.457,'Tampa'),(30.332,-81.656,'Jacksonville'),(30.438,-84.281,'Tallahassee')],
    'NY':[(40.713,-74.006,'New York'),(42.653,-73.756,'Albany'),(42.886,-78.878,'Buffalo'),(43.157,-77.609,'Rochester'),(43.048,-76.147,'Syracuse')],
}


def split(total):
    values=[total*w//100 for w in [35,25,18,14]]
    return values+[total-sum(values)]


def campaign_geography(record,index):
    rows=[]
    for channel,stats in record['channel_results'].items():
        counts=split(stats['activations'])
        exposures=split(stats['exposures'])
        for n,((lat,lon,city),count,exposed) in enumerate(zip(CENTERS[record['region']],counts,exposures)):
            # Integer cents; every geographic amount reconciles to campaign totals.
            balance=count*(250000+(index%7)*45000+n*7500)
            rows.append({'campaign_id':record['campaign_id'],'client_name':record['client_name'],'period':record['period'],
                'channel':channel,'region':record['region'],'location':city,'latitude':lat,'longitude':lon,
                'accounts':count,'exposures':exposed,'balance_cents':balance,'as_of':stats['as_of']})
        stats['balance_cents']=sum(r['balance_cents'] for r in rows if r['channel']==channel)
    return rows
