// API Configuration for Django Backend Integration
// Set VITE_API_URL in your .env file to point to your Django backend

import { UserRole } from "@/types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

// Token management
export const getAuthToken = (): string | null => {
  return localStorage.getItem("auth_token");
};

export const setAuthToken = (token: string): void => {
  localStorage.setItem("auth_token", token);
};

export const removeAuthToken = (): void => {
  localStorage.removeItem("auth_token");
};

// API request helper
type ApiRequestOptions = RequestInit & {
  auth?: boolean;
};

export const apiRequest = async (
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<any> => {
  const token = getAuthToken();
  const { auth = true, ...fetchOptions } = options;

  const headers: HeadersInit = {
    ...fetchOptions.headers,
  };

  // Add Authorization header if token exists
  if (auth && token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Add Content-Type for JSON requests (unless it's FormData)
  if (!(fetchOptions.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || `API Error: ${response.status}`);
  }

  return response.json();
};

// Authentication API
export const authAPI = {
  login: async (email: string, password: string) => {
    const data = await apiRequest("/auth/login/", {
      method: "POST",
      body: JSON.stringify({ email, password }),
      auth: false,
    });
    if (data.token) {
      setAuthToken(data.token);
    }
    return data;
  },

  logout: () => {
    removeAuthToken();
  },

  getCurrentUser: async () => {
    return apiRequest("/auth/user/");
  },
};

// Purchase Requests API
export const requestsAPI = {
  list: async () => {
    const data = await apiRequest("/requests/");
    if (Array.isArray(data)) {
      return data;
    }
    return data.results ?? [];
  },

  get: async (id: string) => {
    return apiRequest(`/requests/${id}/`);
  },

  create: async (data: FormData) => {
    return apiRequest("/requests/", {
      method: "POST",
      body: data,
    });
  },

  update: async (id: string, data: any) => {
    return apiRequest(`/requests/${id}/`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  approve: async (id: string, comment?: string) => {
    return apiRequest(`/requests/${id}/approve/`, {
      method: "PATCH",
      body: JSON.stringify({ comment }),
    });
  },

  reject: async (id: string, comment?: string) => {
    return apiRequest(`/requests/${id}/reject/`, {
      method: "PATCH",
      body: JSON.stringify({ comment }),
    });
  },

  submitReceipt: async (id: string, receipt: File) => {
    const formData = new FormData();
    formData.append("receipt", receipt);
    return apiRequest(`/requests/${id}/submit-receipt/`, {
      method: "POST",
      body: formData,
    });
  },
};
