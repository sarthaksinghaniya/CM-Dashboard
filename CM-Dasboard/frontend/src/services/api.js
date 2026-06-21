import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for generic error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // You can integrate a toast library here for global error handling
    console.error('API Error:', error.response?.data?.detail || error.message);
    return Promise.reject(error);
  }
);

export const submitComplaint = async (data) => {
  const response = await api.post('/complaints/', data);
  return response.data;
};

export const trackComplaint = async (id) => {
  const response = await api.get(`/complaints/${id}`);
  return response.data;
};

export const getOfficerComplaints = async () => {
  // Assuming a hypothetical endpoint for officer complaints
  const response = await api.get('/complaints/');
  return response.data;
};

export const updateComplaintStatus = async (id, status) => {
  const response = await api.patch(`/complaints/${id}`, { status });
  return response.data;
};

export const getDashboardStats = async () => {
  // A hypothetical admin stats endpoint. In a real app, this might be a specific aggregate endpoint
  const response = await api.get('/complaints/');
  return response.data;
};

export const submitFeedback = async (data) => {
  const response = await api.post('/feedback/', data);
  return response.data;
};

export default api;
