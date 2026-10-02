export type RoomMetrics = {
    comfortIndex?: number;
    temperature?: number;
    humidity?: number;
    co2?: number;
    lighting?: number;
    noise?: number;
};

export type Room = {
    id: string;
    name: string;
    location: Location;
    deviceId?: string;
    hideRoom: boolean;
    metrics?: RoomMetrics;
};

export type User = {
    id: string;
    username: string;
    email?: string;
    role?: string;
};

export type Location = {
    id: string;
    name: string;
    adminId: string; // Changed from authorId to adminId
    userIds?: string[];
    deviceIds?: string[];
    createdAt?: string;
    rooms?: Room[]; // This can stay for your UI logic
};