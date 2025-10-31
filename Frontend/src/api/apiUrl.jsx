export const API_BASE = "http://127.0.0.1:5000";

export function apiUrl(path) {
    return `${API_BASE}${path}`;
}
