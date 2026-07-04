import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './client';

// Contacts
export function useContacts(page = 1, filters: Record<string, string> = {}) {
  const params = new URLSearchParams({ page: String(page), per_page: '50', ...filters });
  return useQuery({ queryKey: ['contacts', page, filters], queryFn: () => api.get(`/contacts?${params}`) });
}

export function useContact(id: string) {
  return useQuery({ queryKey: ['contact', id], queryFn: () => api.get(`/contacts/${id}`), enabled: !!id });
}

// Campaigns
export function useCampaigns(page = 1, status?: string) {
  const params = new URLSearchParams({ page: String(page) });
  if (status) params.set('status', status);
  return useQuery({ queryKey: ['campaigns', page, status], queryFn: () => api.get(`/campaigns?${params}`) });
}

export function useCampaign(id: string) {
  return useQuery({ queryKey: ['campaign', id], queryFn: () => api.get(`/campaigns/${id}`), enabled: !!id });
}

export function useCreateCampaign() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (data: unknown) => api.post('/campaigns', data), onSuccess: () => qc.invalidateQueries({ queryKey: ['campaigns'] }) });
}

export function useSendCampaign() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => api.post(`/campaigns/${id}/send`), onSuccess: () => qc.invalidateQueries({ queryKey: ['campaigns'] }) });
}

export function useGenerateCampaign() {
  return useMutation({ mutationFn: (data: unknown) => api.post('/campaigns/generate', data) });
}

// Segments
export function useSegments() {
  return useQuery({ queryKey: ['segments'], queryFn: () => api.get('/segments') });
}

export function useCreateSegment() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (data: unknown) => api.post('/segments', data), onSuccess: () => qc.invalidateQueries({ queryKey: ['segments'] }) });
}

// Analytics
export function useOverview() {
  return useQuery({ queryKey: ['overview'], queryFn: () => api.get('/analytics/overview') });
}

export function useEngagement(days = 30) {
  return useQuery({ queryKey: ['engagement', days], queryFn: () => api.get(`/analytics/engagement?days=${days}`) });
}

export function useCampaignComparison() {
  return useQuery({ queryKey: ['campaign-comparison'], queryFn: () => api.get('/analytics/campaigns') });
}

// Imports
export function useImports() {
  return useQuery({ queryKey: ['imports'], queryFn: () => api.get('/imports') });
}

export function useImportCSV() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (formData: FormData) => api.post('/imports', formData),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['imports'] }); qc.invalidateQueries({ queryKey: ['contacts'] }); },
  });
}

// Workflows
export function useWorkflows() {
  return useQuery({ queryKey: ['workflows'], queryFn: () => api.get('/workflows') });
}

// Auth
export function useLogin() {
  return useMutation({ mutationFn: (data: { email: string; password: string }) => api.post<{ access_token: string }>('/auth/login', data) });
}

export function useSetup() {
  return useMutation({ mutationFn: (data: { email: string; password: string; name: string }) => api.post('/auth/setup', data) });
}
