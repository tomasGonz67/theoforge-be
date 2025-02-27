// api.ts
const API_BASE_URL = "http://localhost:8000"; // FastAPI backend

export const login = async (username: string, password: string) => {
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);
  
  const response = await fetch(`${API_BASE_URL}/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    credentials: 'include', // Important for cookies
    body: formData
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Login failed');
  }
  console.log("Check cookie creation:");
  console.log(document.cookie);
  
  return response.json();
};

export const setCookie = async (accessToken: string) => {
  const response = await fetch(`${API_BASE_URL}/set-cookie`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    credentials: 'include', // Important for cookies
    body: JSON.stringify({ access_token: accessToken })
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to set cookie');
  }
  
  return response.json();
};

export const checkAuth = async () => {
  const response = await fetch(`${API_BASE_URL}/auth`, {
    method: 'GET',
    credentials: 'include', // Important for cookies
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Authentication failed');
  }
  
  return response.json();
};