'use client';
import Image from 'next/image';
import {safeActivityImage} from '@/services/place-links';
const venuePhotos:{marker:string;image:string;source:string;alt:string}[]=[
 {marker:'Lone Star Court',image:'https://valenciacollection.b-cdn.net/wp-content/uploads/sites/6/2026/09/ls-hero.jpg',source:'https://www.lonestarcourt.com/',alt:'Lone Star Court photo from its official website'},
 {marker:'Bouldin Creek Cafe',image:'https://static.spotapps.co/spots/70/ea739e1c294c98808954e4a9162ef1/:original',source:'https://bouldincreekcafe.com/',alt:'Photo from the official Bouldin Creek Cafe website'},
 {marker:'Lady Bird Lake',image:'https://austin.widen.net/content/73fc83a3-6ed9-4e07-9b7c-a6a7ab0d48ac/web/Boardwalk_GO_pier.jpg',source:'https://www.austintexas.gov/parks/locations/ann-and-roy-butler-hike-and-bike-trail-and-boardwalk-lady-bird-lake',alt:'Boardwalk photo from the City of Austin website'},
];
export function StoryPhoto({image,label=''}:{image:string;label?:string}){
 const venue=venuePhotos.find(photo=>label.includes(photo.marker));const src=safeActivityImage(venue?.image||image);if(!src)return null;
 return <figure className="demo-story-photo"><Image src={src} alt={venue?.alt||'Illustrative scenery, not a photo of the selected venue'} width={360} height={180} unoptimized referrerPolicy="no-referrer"/><figcaption>{venue?<><a href={venue.source} target="_blank" rel="noopener noreferrer">Source photo</a> · current details unverified</>:'Illustrative photo · not the selected venue'}</figcaption></figure>;
}
