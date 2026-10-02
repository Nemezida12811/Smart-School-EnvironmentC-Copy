export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001';

export const API_ENDPOINTS = {
    AUTH: {
        REGISTER: `${API_BASE_URL}/api/auth/register`,
        LOGIN: `${API_BASE_URL}/api/auth/login`,
        LOGOUT: `${API_BASE_URL}/api/auth/logout`,
        ME: `${API_BASE_URL}/api/auth/me`,
    },

    COMFORT: {
        LEVEL: (audienceId: string) => `${API_BASE_URL}/api/comfort/${audienceId}`,
        RECOMMENDATIONS: (audienceId: string) => `${API_BASE_URL}/api/comfort/${audienceId}/recommendations`,
        SENSORS: (deviceId: string) => `${API_BASE_URL}/api/comfort/${deviceId}/sensors`,
    },

    LOCATIONS: {
        BASE: `${API_BASE_URL}/api/locations`,
        BY_ID: (id: string) => `${API_BASE_URL}/api/locations/${id}`,
        USERS: (id: string) => `${API_BASE_URL}/api/locations/${id}/users`,
        REMOVE_USER: (id: string, userId: string) => `${API_BASE_URL}/api/locations/${id}/users/${userId}`,
        DEVICES: (id: string) => `${API_BASE_URL}/api/locations/${id}/devices`,
        REMOVE_DEVICE: (id: string, deviceId: string) => `${API_BASE_URL}/api/locations/${id}/devices/${deviceId}`,
    }
};

// === AUTH API ===
export const authApi = {
    register(data: { username: string; email: string; password: string; }) {
        return request<{
            message: string;
            token: string;
            user: {
                id: string;
                username: string;
                email: string;
                role: string;
            };
        }>(API_ENDPOINTS.AUTH.REGISTER, 'POST', data);
    },

    login(data: { email: string; password: string; }) {
        return request<{
            message: string;
            token: string;
            user: {
                id: string;
                username: string;
                email: string;
                role: string;
                createdAt: string;
            };
        }>(API_ENDPOINTS.AUTH.LOGIN, 'POST', data);
    },

    logout(token: string) {
        return request<{ message: string }>(API_ENDPOINTS.AUTH.LOGOUT, 'POST', undefined, token);
    },

    me(token: string) {
        return request<{
            id: string;
            username: string;
            email: string;
            role: string;
            ownedLocationIds: string[];
            accessibleLocationIds: string[];
            createdAt: string;
        }>(API_ENDPOINTS.AUTH.ME, 'GET', undefined, token);
    },
};

// === COMFORT API ===
export const comfortApi = {
    getComfortLevel(audienceId: string, token?: string) {
        return request<{
            audienceId: string;
            comfortPercentage: number;
            timestamp: string;
        }>(API_ENDPOINTS.COMFORT.LEVEL(audienceId), 'GET', undefined, token);
    },

    getRecommendations(audienceId: string, token?: string) {
        return request<{
            audienceId: number;
            recommendations: {
                id: number;
                priority: 'low' | 'medium' | 'high';
                type: string;
                message: string;
                reason: string;
            }[];
            generatedAt: string;
        }>(API_ENDPOINTS.COMFORT.RECOMMENDATIONS(audienceId), 'GET', undefined, token);
    },

    getLatestSensors(deviceId: string, token?: string) {
        return request<{
            deviceId: string;
            name: string;
            hidden: boolean;
            latestReading: {
                temperature: number;
                humidity: number;
                gas: number;
                light: number;
                sound: number;
                units: {
                    temperature: string;
                    humidity: string;
                    gas: string;
                    light: string;
                    sound: string;
                };
            };
            timestamp: string;
        }>(API_ENDPOINTS.COMFORT.SENSORS(deviceId), 'GET', undefined, token);
    },
};

// === LOCATION API ===
export const locationApi = {
    create(data: { name: string; }, token: string) {
        return request<{
            id: string;
            name: string;
            adminId: string;
        }>(API_ENDPOINTS.LOCATIONS.BASE, 'POST', data, token);
    },

    list(token: string) {
        return request<{
            created: {
                id: string;
                name: string;
                adminId: string;
                userIds: string[];
                deviceIds: string[];
                createdAt: string;
            }[];
            joined: {
                id: string;
                name: string;
                adminId: string;
                userIds: string[];
                deviceIds: string[];
                createdAt: string;
            }[];
        }>(API_ENDPOINTS.LOCATIONS.BASE, 'GET', undefined, token);
    },

    get(id: string, token: string) {
        return request<{
            id: string;
            name: string;
            adminId: string;
            userIds: string[];
            deviceIds: string[];
            createdAt: string;
        }>(API_ENDPOINTS.LOCATIONS.BY_ID(id), 'GET', undefined, token);
    },

    updateName(id: string, name: string, token: string) {
        return request<{ message: string; name: string }>(API_ENDPOINTS.LOCATIONS.BY_ID(id), 'PATCH', { name }, token);
    },

    delete(id: string, token: string) {
        return request<{ message: string }>(API_ENDPOINTS.LOCATIONS.BY_ID(id), 'DELETE', undefined, token);
    },

    addUser(id: string, targetUserId: string, token: string) {
        return request<{ message: string }>(API_ENDPOINTS.LOCATIONS.USERS(id), 'POST', { targetUserId }, token);
    },

    removeUser(id: string, targetUserId: string, token: string) {
        return request<{ message: string }>(API_ENDPOINTS.LOCATIONS.REMOVE_USER(id, targetUserId), 'DELETE', undefined, token);
    },

    addDevice(id: string, deviceId: string, name: string | undefined, token: string) {
        return request<{ message: string }>(API_ENDPOINTS.LOCATIONS.DEVICES(id), 'POST', { deviceId, name }, token);
    },

    hideDevice(id: string, deviceId: string, token: string) {
        return request<{ message: string }>(`${API_ENDPOINTS.LOCATIONS.DEVICES(id)}/${deviceId}/hide`, 'PATCH', undefined, token);
    },

    showDevice(id: string, deviceId: string, token: string) {
        return request<{ message: string }>(`${API_ENDPOINTS.LOCATIONS.DEVICES(id)}/${deviceId}/show`, 'PATCH', undefined, token);
    },

    removeDevice(id: string, deviceId: string, token: string) {
        return request<{ message: string }>(API_ENDPOINTS.LOCATIONS.REMOVE_DEVICE(id, deviceId), 'DELETE', undefined, token);
    },

    updateDeviceSettings(id: string, deviceId: string, data: {
        name?: string;
        units?: string;
        ntpHost?: string;
        brokerAddress?: string;
        wifiSsid?: string;
        wifiPassword?: string;
        interval?: number;
    }, token: string) {
        return request<{
            message: string;
            topic: string;
            settings: any;
        }>(`${API_ENDPOINTS.LOCATIONS.BY_ID(id)}/devices/${deviceId}/settings`, 'PATCH', data, token);
    }
};

// === HTTP helper ===
async function request<T>(url: string, method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH', body?: unknown, token?: string): Promise<T> {
    const res = await fetch(url, {
        method,
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
        const error = await res.json();
        throw new Error(error?.message || 'API Error');
    }

    const json = await res.json();
    return json.data as T;
}

// For testing uncomment the following lines, and run the file with "node restApiService.ts"

// (async () => {
//   const res = await comfortApi.getComfortLevel('pico-001');
//   console.log(res);
// })();
