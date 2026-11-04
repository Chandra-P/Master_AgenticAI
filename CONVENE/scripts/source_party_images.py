import httpx
from pathlib import Path

assets = {
 'navajo.jpg': 'https://www.bexar.org/ImageRepository/Document?documentID=36425',
 'south-san.jpg': 'https://www.bexar.org/ImageRepository/Document?documentID=36436',
 'harlandale.jpg': 'https://www.bexar.org/ImageRepository/Document?documentID=36441',
 'belle.jpg': 'https://belleofballoons.com/wp-content/uploads/2025/09/balloon-arch-san-antonio-3-scaled.jpeg',
 'bewitchin.jpg': 'https://static.showit.co/800/lSmeHBLWgqcbmYuWjoOCxA/292386/474229121_3878256869080314_4013746621046669007_n.jpg',
}
with httpx.Client(timeout=25, follow_redirects=True, trust_env=False) as client:
 for filename, url in assets.items():
  response = client.get(url)
  response.raise_for_status()
  if not response.headers.get('content-type','').startswith('image/'):
   raise ValueError('Expected image for '+filename)
  Path('web/assets',filename).write_bytes(response.content)
  print(filename, len(response.content), 'bytes')
 response=client.get('https://confettiandcosatx.com/')
 print('Confetti status:',response.status_code)
 from html.parser import HTMLParser
 class Images(HTMLParser):
  def handle_starttag(self,tag,attrs):
   a=dict(attrs)
   if tag=='img' and a.get('src'): print('Confetti image:',a['src'])
 Images().feed(response.text)
