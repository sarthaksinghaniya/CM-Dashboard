import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from './api';

// --- QUERIES ---

export const useOfficerComplaints = () => {
  return useQuery({
    queryKey: ['complaints', 'officer'],
    queryFn: ({ signal }) => api.getOfficerComplaints({ signal }),
    staleTime: 5 * 60 * 1000, // 5 minutes cache
  });
};

export const useTrackComplaint = (id) => {
  return useQuery({
    queryKey: ['complaint', id],
    queryFn: ({ signal }) => api.trackComplaint(id, { signal }),
    enabled: !!id, // Only run the query if an ID is provided
    retry: 1, // Only retry once for 404s to fail fast
    staleTime: 60 * 1000, // 1 minute cache for tracking updates
  });
};

// --- MUTATIONS ---

export const useSubmitComplaint = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data) => api.submitComplaint(data),
    onSuccess: () => {
      // Invalidate dashboard stats so they refetch next time
      queryClient.invalidateQueries({ queryKey: ['complaints'] });
    },
  });
};

export const useSubmitFeedback = () => {
  return useMutation({
    mutationFn: (data) => api.submitFeedback(data),
  });
};

export const useUpdateComplaintStatus = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, status }) => api.updateComplaintStatus(id, status),
    onSuccess: (_, variables) => {
      // Invalidate both the list and the specific tracked complaint
      queryClient.invalidateQueries({ queryKey: ['complaints'] });
      queryClient.invalidateQueries({ queryKey: ['complaint', variables.id] });
    },
  });
};
