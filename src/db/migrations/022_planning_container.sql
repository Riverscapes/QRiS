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
    planning_container_id INTEGER REFERENCES planning_containers(id) ON DELETE CASCADE,
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
    phase_type TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_planning_container_events PRIMARY KEY (planning_container_id, event_id)
);

UPDATE lkp_representation SET name = 'Contemporary' WHERE id = 1;
UPDATE lkp_representation SET name = 'Predicted' WHERE id = 3;