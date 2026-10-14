import { expect,it,vi,afterEach } from 'vitest';
import { toInstant,toLocalInput } from './workTypes';
afterEach(()=>vi.unstubAllEnvs());
it('preserves a scheduled instant across the Belgrade daylight-saving boundary',()=>{
  vi.stubEnv('TZ','Europe/Belgrade');
  expect(toLocalInput('2026-03-29T12:30:00.000Z')).toBe('2026-03-29T14:30');
  expect(toInstant('2026-03-29T14:30')).toBe('2026-03-29T12:30:00.000Z');
  expect(toLocalInput('2026-10-25T12:30:00.000Z')).toBe('2026-10-25T13:30');
  expect(toInstant('2026-10-25T13:30')).toBe('2026-10-25T12:30:00.000Z');
});
it('does not invent a reminder when its optional input is empty',()=>{
  expect(toInstant('')).toBeNull();expect(toLocalInput(null)).toBe('');
});
