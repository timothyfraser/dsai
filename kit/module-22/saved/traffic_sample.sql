-- traffic_sample.sql
-- A saved slice of the traffic table, so the lineage check runs with no database server.
-- Course kit, module 22

CREATE TABLE traffic (
  metro_id    INTEGER,
  monitor_id  TEXT,
  observed_at TEXT,
  vehicles    INTEGER,
  speed       REAL,
  occupancy   REAL,
  PRIMARY KEY (metro_id, monitor_id, observed_at)
);

INSERT INTO traffic VALUES (1, 'SGN02', '2026-04-15T07:59:00Z', 97, 28.0, 0.10);
INSERT INTO traffic VALUES (1, 'SGN02', '2026-04-15T08:00:00Z', 101, 30.5, 0.12);
INSERT INTO traffic VALUES (1, 'SGN02', '2026-04-15T08:15:00Z', 96, 33.0, 0.11);
INSERT INTO traffic VALUES (1, 'SGN02', '2026-04-15T08:30:00Z', 110, 29.8, 0.13);
INSERT INTO traffic VALUES (1, 'SGN02', '2026-04-15T08:45:00Z', 105, 31.5, 0.12);
INSERT INTO traffic VALUES (1, 'SGN02', '2026-04-15T09:00:00Z', 88, 35.1, 0.09);
INSERT INTO traffic VALUES (1, 'BAU01', '2026-04-15T08:00:00Z', 40, 45.0, 0.04);
