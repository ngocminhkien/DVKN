// Configuration file for Frontend API endpoints
// This file exports the base URL of the Backend for Frontend (BFF) server.
// To change the BFF IP or port, modify this variable or specify VITE_API_BASE_URL in a .env file.
export const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || 'http://localhost:8000';
