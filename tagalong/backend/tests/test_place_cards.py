import pytest
from pydantic import ValidationError
from tagalong.discovery import normalize_places, page_images
from tagalong.models import Activity


def test_places_only_keep_names_and_photos_from_their_own_source():
    pages=[{'id':'page-0','url':'https://venue.example/','content':'# Garden Cafe\n10 Main Street\n![Dining room](https://venue.example/dining.jpg)','title':'Garden Cafe'}]
    rows=[{'source_id':'page-0','kind':'venue','name':'Garden Cafe','address':'10 Main Street','description':'Dining room','image_url':'https://venue.example/dining.jpg'},
          {'source_id':'page-0','kind':'article','name':'Garden Cafe','address':'','description':'','image_url':''},
          {'source_id':'page-0','kind':'venue','name':'Invented Restaurant','address':'','description':'','image_url':''}]
    result=normalize_places(rows,pages,'San Francisco','restaurants')
    assert len(result)==1
    assert result[0]['title']=='Garden Cafe'
    assert result[0]['image']=='https://venue.example/dining.jpg'
    assert result[0]['url']=='https://venue.example/'
    assert result[0]['map_url'].startswith('https://www.google.com/maps/search/')
    rows[0]['image_url']='https://unrelated.example/photo.jpg'
    assert normalize_places(rows[:1],pages,'San Francisco','restaurants')[0]['image'] is None


def test_page_images_reject_local_and_non_photo_links():
    content='![Logo](https://venue.example/logo.png) ![Room](http://127.0.0.1/a.jpg) ![Food](https://venue.example/food.jpg)'
    assert page_images(content,'https://venue.example/')==['https://venue.example/food.jpg']


def test_keenable_discovery_fetches_sources_and_excludes_articles(monkeypatch):
    import httpx
    from tagalong.places import KeenableSearch
    monkeypatch.delenv('KEENABLE_API_KEY',raising=False)
    def handler(request):
        if request.method=='POST':return httpx.Response(200,json={'results':[{'title':'Garden Cafe','url':'https://venue.example/'},{'title':'Top cafes','url':'https://guide.example/best'}]})
        assert request.url.path=='/v1/fetch/public'
        return httpx.Response(200,json={'content':'Garden Cafe\n![Room](https://venue.example/room.jpg)'})
    def extract(pages,*args):
        return [{'source_id':p['id'],'kind':'venue' if p['url']=='https://venue.example/' else 'article','name':'Garden Cafe','address':'','description':'','image_url':'https://venue.example/room.jpg'} for p in pages]
    result=KeenableSearch(httpx.MockTransport(handler),extract).venues('cafes','San Francisco','restaurants')
    assert len(result)==1 and result[0]['image']=='https://venue.example/room.jpg'


def test_discovered_activity_preserves_source_and_schedule():
    item=Activity(id='place-1',title='Cafe',time='18:00',category='Food & drink',location='10 Main Street',day='2026-12-18',source_url='https://venue.example/',map_url='https://www.google.com/maps/search/?api=1&query=Cafe',image_source_url='https://venue.example/')
    assert item.day=='2026-12-18' and item.source_url=='https://venue.example/'
    with pytest.raises(ValidationError):
        Activity(**{**item.model_dump(),'source_url':'javascript:alert(1)'})
    with pytest.raises(ValidationError):
        Activity(**{**item.model_dump(),'day':'not-a-date'})
    for image in ['http://127.0.0.1/a.jpg','https://router.local/a.jpg','javascript:alert(1)','/images/../api/config']:
        with pytest.raises(ValidationError):Activity(**{**item.model_dump(),'image':image})
