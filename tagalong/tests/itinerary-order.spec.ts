import {test,expect} from '@playwright/test';
import {orderActivities} from '../src/services/itinerary-order';
test('orders mixed manual and discovered times chronologically without moving unassigned slots',()=>{
 const activities=[{time:'10:00 AM'},{time:'Time to decide'},{time:'9:00 AM'},{time:'19:00'},{time:'12:00 PM'},{time:'12:00 AM'}];
 expect(orderActivities(activities).map(a=>a.time)).toEqual(['12:00 AM','Time to decide','9:00 AM','10:00 AM','12:00 PM','19:00']);
 expect(activities[0].time).toBe('10:00 AM');
});
