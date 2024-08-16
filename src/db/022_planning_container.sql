-- Add planning table to store the planning containers
CREATE TABLE planning_containers
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE planning_container_events
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    planning_container_id INTEGER REFERENCES planning_containers(id) ON DELETE CASCADE,
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
    phase_type TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Add the planning layers to regular dce event types
