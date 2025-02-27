import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000"; // FastAPI backend

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Important for cookies
  headers: {
    "Content-Type": "application/x-www-form-urlencoded", // Form encoding
  },
});

export const login = async (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);
  
    return await api.post("/login", formData);
};

export const setCookie = async (accessToken: string) => {
    try {
        const response = await fetch('http://127.0.0.1:8000/set-cookie', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json', // Set the content type to JSON
                'Accept': 'application/json',
            },
            body: JSON.stringify({ access_token: accessToken }), // Match the TokenResponse model
        });

        if (!response.ok) {
            throw new Error('Failed to set cookie');
        }

        const result = await response.json();
        console.log(result.message); // Log the success message
    } catch (error) {
        console.error("Error setting cookie:", error);
    }
};

export const checkAuth = async () => {
  const response = await api.get("/me"); // Endpoint to check cookie auth
  return response.data;
};

export default api;
