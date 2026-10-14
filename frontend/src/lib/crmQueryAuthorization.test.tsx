import { expect, it } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderToStaticMarkup } from 'react-dom/server';
import { ApiError } from './api';
import { crmKey } from './crmQuery';
import Dashboard from '../features/crm/Dashboard';
import Pipeline from '../features/crm/Pipeline';
import { emptyMetricFilters, opportunityStages } from '../features/crm/types';

it('hides cached owner names on rejected authorization refresh in all views', async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const key = crmKey(1, '/summary?');
  const data = { company_count: 1, owners: [{ id: 1, name: 'Private cached owner' }],
    stages: Object.fromEntries(opportunityStages.map(stage => [stage, 1])) };
  client.setQueryData(key, data);
  await client.fetchQuery({ queryKey: key, queryFn: async () => { throw new ApiError(403, 'Pristup je opozvan'); } }).catch(() => {});
  const props = { unit: 1, filters: emptyMetricFilters, onFilters: () => {}, units: [{ id: 1, code: 'LUU', role: 'manager' }], onUnit: () => {} };
  const dashboard = renderToStaticMarkup(<QueryClientProvider client={client}><Dashboard {...props} userName="User" onPipeline={() => {}} onNavigate={() => {}} /></QueryClientProvider>);
  expect(dashboard).not.toContain('Private cached owner');
  const pipeline = renderToStaticMarkup(<QueryClientProvider client={client}><Pipeline {...props} companies={[]} /></QueryClientProvider>);
  expect(pipeline).not.toContain('Private cached owner');
  client.clear();
});
