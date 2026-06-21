import axios from 'axios';

// --- Configuration ---
const API_TIMEOUT = 10000; // 10 seconds

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- Request Interceptor ---
api.interceptors.request.use(
  (config) => {
    // 1. Attach Auth Token securely
    // In a real app, retrieve this from HttpOnly cookies or secure local storage
    const token = localStorage.getItem('auth_token'); 
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // 2. Logging in dev mode
    if (process.env.NODE_ENV !== 'production') {
      console.log(`[API Request] ${config.method.toUpperCase()} ${config.url}`, config.data || '');
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// --- Response Interceptor ---
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 1. Handle Request Cancellation
    if (axios.isCancel(error)) {
      console.log(`[API Request Canceled] ${error.message}`);
      return Promise.reject(new Error('Request was canceled.'));
    }

    // 2. Parse errors into standard user-friendly format
    let errorMessage = 'An unexpected error occurred. Please try again.';

    if (!error.response) {
      // Network error or Timeout
      if (error.code === 'ECONNABORTED') {
        errorMessage = 'Request timed out. Please check your internet connection.';
      } else {
        errorMessage = 'Unable to connect to the server. Please check your internet connection.';
      }
    } else {
      // Server responded with a status code outside of 2xx
      const status = error.response.status;
      const data = error.response.data;

      if (status === 401) {
        errorMessage = 'Your session has expired. Please log in again.';
        // Optionally trigger a logout action here
      } else if (status === 403) {
        errorMessage = 'You do not have permission to perform this action.';
      } else if (status === 404) {
        errorMessage = 'The requested resource was not found.';
      } else if (status >= 500) {
        errorMessage = 'Our servers are currently experiencing issues. Please try again later.';
      } else if (data && data.detail) {
        errorMessage = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      }
    }

    // 3. Log errors centrally
    console.error(`[API Error] ${errorMessage}`, error);

    // Reject with a standardized Error object
    return Promise.reject(new Error(errorMessage));
  }
);

// --- API Service Methods ---
// We pass config explicitly so that React Query can inject an AbortSignal

export const submitComplaint = async (data, config = {}) => {
  const response = await api.post('/complaints/', data, config);
  return response.data;
};

export const trackComplaint = async (id, config = {}) => {
  const response = await api.get(`/complaints/track/${id}`, config);
  return response.data;
};

export const getOfficerComplaints = async (config = {}) => {
  const response = await api.get('/admin/complaints', config);
  return response.data;
};

export const updateComplaintStatus = async (id, status, config = {}) => {
  const response = await api.patch(`/admin/complaints/${id}`, { status }, config);
  return response.data;
};

export const getDashboardStats = async (config = {}) => {
  const response = await api.get('/admin/complaints', config);
  return response.data;
};

export const submitFeedback = async (data, config = {}) => {
  const response = await api.post('/feedback/', data, config);
  return response.data;
};

export default api;
