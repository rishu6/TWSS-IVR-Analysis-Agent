import { describe,it,expect } from 'vitest';
import { missedAgents,orderedAgentEvents } from './callAgents';
import { resolveTheme,appearanceTheme } from './themes';
import type { Participant } from './types';
const person={id:'1',provider_agent_id:'A',agent_name:'Test Agent',agent_number:null,dialed_at:[],answered_at:['2026-01-01T00:00:00Z'],reported_missed:true,missed_at:null} satisfies Participant;
describe('agent evidence',()=>{
  it('counts a reported person once even if answered too or repeated',()=>expect(missedAgents({reported_missed_agents:[person,{...person,id:'2'}]})).toHaveLength(1));
  it('distinguishes missing summary from an empty report',()=>{expect(missedAgents({})).toBeUndefined();expect(missedAgents({reported_missed_agents:[]})).toEqual([]);});
  it('does not infer missed agents from dial events or unanswered participants',()=>expect(missedAgents({participants:[{...person,reported_missed:false,answered_at:[]}]})).toEqual([]));
  it('sorts only agent activity without modifying source data',()=>{const events=[{event_id:'2',type:'Agent',at:'2026-01-01T00:02:00Z'},{event_id:'1',type:'Agent',at:'2026-01-01T00:01:00Z'},{event_id:'0',type:'init',at:'2026-01-01T00:00:00Z'}];expect(orderedAgentEvents({events}).map(e=>e.event_id)).toEqual(['1','2']);expect(events[0].event_id).toBe('2');});
});
describe('colour preferences',()=>{
  it('accepts saved palettes and migrates the existing dark preference',()=>{expect(resolveTheme('midnight')).toBe('midnight');expect(resolveTheme(null,'dark')).toBe('forest-dark');});
  it('recovers from invalid preferences',()=>expect(resolveTheme('unknown')).toBe('forest'));
});

it('preserves the saved light or dark mode when simplifying palettes',()=>{expect(appearanceTheme('midnight')).toBe('soft-charcoal');expect(appearanceTheme('ocean')).toBe('corporate-navy');expect(appearanceTheme(null,'dark')).toBe('soft-charcoal');});
