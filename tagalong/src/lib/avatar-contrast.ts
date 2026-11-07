/** Choose legible initials without changing a participant's saved avatar color. */
export function avatarTextColor(background:string):string {
 const hex=background.replace(/^#/, '');
 if(!/^(?:[\da-f]{3}|[\da-f]{6})$/i.test(hex))return '#20343f';
 const full=hex.length===3?[...hex].map(char=>char+char).join(''):hex;
 const channels=[0,2,4].map(offset=>parseInt(full.slice(offset,offset+2),16)/255);
 const luminance=channels.map(value=>value<=.04045?value/12.92:((value+.055)/1.055)**2.4).reduce((sum,value,index)=>sum+value*[.2126,.7152,.0722][index],0);
 // Compare white with the same deep navy used throughout the interface.
 const navyLuminance=.0314;
 if((luminance+.05)/(navyLuminance+.05)>=4.5)return '#20343f';
 return 1.05/(luminance+.05)>=4.5?'#ffffff':'#000000';
}
