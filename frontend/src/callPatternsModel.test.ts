import {describe,it,expect} from 'vitest';
import {callPatterns,hourRange} from './callPatternsModel';
const row=(at:string,total:number)=>({at,total,answered:0,missed:0,customer_missed:0});
describe('weekly call patterns',()=>{
  it('uses India weekdays and hours and combines repeated weekdays across weeks',()=>{
    const p=callPatterns([row('2026-10-25T18:30:00Z',2),row('2026-11-02T04:30:00Z',3),row('2026-10-31T18:30:00Z',3)]);
    expect(p.grid[0][0]).toBe(2);expect(p.grid[0][10]).toBe(3);expect(p.grid[6][0]).toBe(3);
    expect(p.bestDays.map(d=>d.name)).toEqual(['Monday']);expect(p.dayMax).toBe(5);
    expect(p.bestHours.map(h=>h.hour)).toEqual([0]);expect(p.hourMax).toBe(5);
    expect(p.bestSlots).toHaveLength(2);
    expect(p.total).toBe(8);expect(p.grid.flat().reduce((a,b)=>a+b,0)).toBe(8);
    expect(p.hours.reduce((n,h)=>n+h.total,0)).toBe(8);
  });
  it('shows all tied leaders',()=>{
    const p=callPatterns([row('2026-10-26T04:30:00Z',2),row('2026-10-27T05:30:00Z',2)]);
    expect(p.bestDays.map(d=>d.name)).toEqual(['Monday','Tuesday']);
    expect(p.bestHours.map(h=>h.hour)).toEqual([10,11]);expect(p.bestSlots).toHaveLength(2);
  });
  it('does not invent a best day when no timed calls exist',()=>{
    const p=callPatterns([row('invalid',5)]);expect(p.total).toBe(0);
    expect(p.bestDays).toEqual([]);expect(p.bestHours).toEqual([]);expect(p.bestSlots).toEqual([]);
  });
  it('formats the midnight boundary',()=>expect(hourRange(23)).toBe('23:00–00:00'));
});
