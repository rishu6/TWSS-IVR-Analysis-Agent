import { describe, expect, it } from 'vitest';
import { dateBoundary, duration, localTime,indiaDay,shiftDay } from './lib';

describe('report presentation', () => {
  it('shows offset timestamps in India regardless of browser timezone', () => {
    expect(localTime('2026-10-26T23:30:00-05:00')).toBe('10:00:00');
  });
  it('does not display unknown duration as zero', () => {
    expect(duration(null)).toBe('Unavailable');
    expect(duration(0)).toBe('0s');
    expect(duration(80)).toBe('1m 20s');
  });
  it('date filters cover the selected India calendar day', () => {
    expect(dateBoundary('2026-10-27')).toBe('2026-10-26T18:30:00.000Z');
    expect(dateBoundary('2026-10-27',true)).toBe('2026-10-27T18:30:00.000Z');
  });
  it('treats legacy naive API datetimes as UTC',()=>{
    expect(localTime('2026-10-27T04:30:00')).toBe('10:00:00');
    expect(localTime('not-a-time')).toBe('Unavailable');
  });
  it('quick date ranges use India calendar days',()=>{
    expect(indiaDay('2026-10-27T20:00:00Z')).toBe('2026-10-28');
    expect(shiftDay('2026-10-01',-1)).toBe('2026-09-30');
  });
});
