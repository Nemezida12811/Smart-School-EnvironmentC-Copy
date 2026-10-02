/*import type { Room, Location, User } from "./components/types.tsx";


export const mockUsers: User[] = [
    {
        id: "user-1",
        username: "alice",
    },
    {
        id: "user-2",
        username: "bob",
    },
];

export const currentUser = mockUsers[0]; // alice


export const baseLocations: Location[] = [
    {
        id: "loc-1",
        name: "Letná 9",
        adminId: "user-1",
    },
    {
        id: "loc-2",
        name: "TUKE – Main Building",
        adminId: "user-1",
        rooms: [],
    },
    {
        id: "loc-3",
        name: "Science Park",
        adminId: "user-2",
    },
];


export const mockRooms: Room[] = [
    {
        id: "room-1",
        name: "A101",
        location: baseLocations[0],
        deviceId: "device-001",
        hideRoom: false,
        metrics: {
            comfortIndex: 82,
            temperature: 22.5,
            humidity: 45,
            co2: 700,
            lighting: 80,
            noise: 30,
        },
    },
    {
        id: "room-2",
        name: "A102",
        location: baseLocations[0],
        deviceId: "device-002",
        hideRoom: false,
        metrics: {
            comfortIndex: 65,
            temperature: 24,
            humidity: 55,
            co2: 1200,
        },
    },
    {
        id: "room-3",
        name: "A103",
        location: baseLocations[0],
        hideRoom: false,
        metrics: {
            comfortIndex: 0,
        },
    },
    {
        id: "room-4",
        name: "A104 (Storage)",
        location: baseLocations[0],
        hideRoom: true,
    },
    {
        id: "room-5",
        name: "Lecture Hall 1",
        location: baseLocations[0],
        deviceId: "device-010",
        hideRoom: false,
        metrics: {
            comfortIndex: 95,
            temperature: 21,
            humidity: 40,
            co2: 500,
            lighting: 90,
            noise: 20,
        },
    },
    {
        id: "room-6",
        name: "Lecture Hall 2",
        location: baseLocations[0],
        hideRoom: false,
        metrics: {
            comfortIndex: 35,
            temperature: 27,
            co2: 2500,
            noise: 75,
        },
    },
    {
        id: "room-7",
        name: "Lab α-12",
        location: baseLocations[2],
        deviceId: "device-α12",
        hideRoom: false,
        metrics: {
            comfortIndex: 78,
            temperature: 23,
            humidity: 48,
        },
    },
    {
        id: "room-8",
        name: "Basement",
        location: baseLocations[2],
        hideRoom: false,
        metrics: undefined,
    },
];


export const locationsWithRooms: Location[] = baseLocations.map((location) => ({
    ...location,
    rooms: mockRooms.filter((room) => room.location.id === location.id),
}));


// Locations created by current user (alice)
export const createdLocations: Location[] = locationsWithRooms.filter(
    (location) => location.adminId === currentUser.id
);

// Locations joined by current user (not author)
export const joinedLocations: Location[] = locationsWithRooms.filter(
    (location) => location.adminId !== currentUser.id
);
*/

import type { User, Location, Room } from "./components/types.tsx";

// 1. Mock Users
export const MOCK_USER: User = {
    id: "u1",
    username: "AlexDev"
};

export const OTHER_USER: User = {
    id: "u2",
    username: "JohnDoe"
};

// 2. Mock Locations (Initial setup without rooms to avoid circular errors)
export const MOCK_LOCATIONS: Location[] = [
    {
        id: "loc-1",
        name: "Main University Campus",
        adminId: "u1",
        rooms: [] // Will be filled below
    },
    {
        id: "loc-2",
        name: "Innovation Hub",
        adminId: "u1",
        rooms: []
    },
    {
        id: "loc-3",
        name: "Public Library",
        adminId: "u2", // Someone else's location
        rooms: []
    }
];

// 3. Mock Rooms
export const MOCK_ROOMS: Room[] = [
    {
        id: "r1",
        name: "Lecture Hall A",
        location: MOCK_LOCATIONS[0],
        deviceId: "dev-001",
        hideRoom: false,
        metrics: {
            humidity: 45,
            co2: 600,
            lighting: 400,
            noise: 35
        }
    },
    {
        id: "r2",
        name: "Biology Lab",
        location: MOCK_LOCATIONS[0],
        deviceId: "dev-002",
        hideRoom: false,
        metrics: {
            comfortIndex: 62,
            temperature: 19,
            humidity: 30,
            co2: 900,
            lighting: 500,
            noise: 40
        }
    },
    {
        id: "r3",
        name: "Study Pod 1",
        location: MOCK_LOCATIONS[1],
        deviceId: "dev-003",
        hideRoom: true, // This one is hidden
        metrics: {
            comfortIndex: 98,
            temperature: 23,
            humidity: 40,
            co2: 400,
            lighting: 300,
            noise: 20
        }
    },
    {
        id: "r4",
        name: "Silent Reading Room",
        location: MOCK_LOCATIONS[2],
        deviceId: "dev-004",
        hideRoom: false,
        metrics: {
            comfortIndex: 75,
            temperature: 21,
            humidity: 50,
            co2: 800,
            lighting: 200,
            noise: 15
        }
    }
];

// 4. Link Rooms back to Locations
MOCK_LOCATIONS[0].rooms = [MOCK_ROOMS[0], MOCK_ROOMS[1]];
MOCK_LOCATIONS[1].rooms = [MOCK_ROOMS[2]];
MOCK_LOCATIONS[2].rooms = [MOCK_ROOMS[3]];

// Export helper for easy use in App.tsx
export const ALL_LOCATIONS = MOCK_LOCATIONS;