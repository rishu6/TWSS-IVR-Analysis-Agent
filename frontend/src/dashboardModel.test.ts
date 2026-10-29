import {describe,it,expect} from 'vitest';
import {callTrend,outcomeMix} from './dashboardModel';
import type {Metrics} from './types';
const hour=(at:string,total:number,answered:number,missed:number)=>({at,total,answered,missed,customer_missed:0});
describe('dashboard call totals',()=>{
  it('fills inactive hours without joining separate busy periods',()=>{
    const rows=callTrend([hour('2026-10-29T04:30:00+00:00',3,2,1),hour('2026-10-29T06:30:00+00:00',1,0,0)],false);
    expect(rows).toHaveLength(3);expect(rows[1].total).toBe(0);expect(rows[2].other).toBe(1);
    expect(rows.reduce((n,r)=>n+r.total,0)).toBe(4);
  });
  it('groups by India dates across UTC midnight and includes quiet days',()=>{
    const rows=callTrend([hour('2026-10-28T18:30:00Z',2,1,1),hour('2026-10-29T03:30:00Z',3,2,1),hour('2026-10-30T18:30:00Z',1,1,0)],true);
    expect(rows.map(r=>[r.at,r.total])).toEqual([['2026-10-29',5],['2026-10-30',0],['2026-10-31',1]]);
  });
  it('keeps missed department calls inside total missed, not as an extra outcome',()=>{
    const mix=outcomeMix({total:10,ANSWERED:4,MISSED:5,customer_missed:2,missed_without_department:3} as Metrics);
    expect(mix.map(r=>r.value)).toEqual([4,2,3,1]);expect(mix.reduce((n,r)=>n+r.value,0)).toBe(10);
  });
  it('handles no activity',()=>expect(callTrend([],false)).toEqual([]));
});
