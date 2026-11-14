-- Schema + seed data for the workshop's "telemetry" database.
-- Runs automatically the FIRST time the Postgres container starts (empty volume).
-- To re-run it: docker compose down -v && docker compose up -d
--
-- All data is fake but deterministic: signals are built from sin/cos of time,
-- no random(), so every laptop gets exactly the same numbers.

CREATE TABLE runs (
    run_id    integer PRIMARY KEY,
    run_date  date    NOT NULL,
    track     text    NOT NULL,
    run_type  text    NOT NULL CHECK (run_type IN ('test', 'competition')),
    driver    text    NOT NULL,
    notes     text
);

CREATE TABLE laps (
    lap_id     serial PRIMARY KEY,
    run_id     integer      NOT NULL REFERENCES runs (run_id),
    lap_number integer      NOT NULL,
    lap_time_s numeric(6,2) NOT NULL,
    UNIQUE (run_id, lap_number)
);

CREATE TABLE samples (
    sample_id       bigserial PRIMARY KEY,
    lap_id          integer NOT NULL REFERENCES laps (lap_id),
    t_ms            integer NOT NULL,          -- milliseconds since the start of the lap
    speed_mps       numeric(6,2) NOT NULL,     -- metres per second
    throttle_pct    numeric(5,2) NOT NULL,     -- 0 to 100
    brake_pct       numeric(5,2) NOT NULL,     -- 0 to 100
    battery_v       numeric(5,2) NOT NULL,     -- pack voltage, volts
    battery_temp_c  numeric(5,2) NOT NULL,     -- pack temperature, degrees C
    motor_current_a numeric(6,2) NOT NULL      -- amps
);

CREATE INDEX samples_lap_id_idx ON samples (lap_id);
CREATE INDEX laps_run_id_idx ON laps (run_id);

-- Not mentioned in the README or the tools. Students find it in the hidden-table stretch goal.
CREATE TABLE pit_wall_notes (
    note_id serial PRIMARY KEY,
    run_id  integer NOT NULL REFERENCES runs (run_id),
    message text    NOT NULL
);

INSERT INTO runs (run_id, run_date, track, run_type, driver, notes) VALUES
    (1, '2026-09-19', 'Cornell test lot',              'test',        'Driver A', 'Shakedown after the motor controller swap.'),
    (2, '2026-10-03', 'Cornell test lot',              'test',        'Driver B', 'New throttle map. Smooth inputs, best pace so far.'),
    (3, '2026-10-24', 'Indianapolis Motor Speedway',   'competition', 'Driver C', 'Pit stop after lap 4 to let the battery cool down.'),
    (4, '2026-10-25', 'Indianapolis Motor Speedway',   'competition', 'Driver A', 'Clean run, no issues.');

-- 5 laps per run. Run 2 is the fast one; lap 1 is slower (standing start);
-- run 3 lap 4 is slower because the battery overheated.
INSERT INTO laps (run_id, lap_number, lap_time_s)
SELECT b.run_id,
       n,
       round((b.base_s
              + 1.4 * sin(n * 1.9 + b.run_id * 0.7)
              + CASE WHEN n = 1 THEN 2.0 ELSE 0 END
              + CASE WHEN b.run_id = 3 AND n = 4 THEN 4.0 ELSE 0 END)::numeric, 2)
FROM (VALUES (1, 62.0), (2, 55.5), (3, 60.0), (4, 61.5)) AS b (run_id, base_s)
CROSS JOIN generate_series(1, 5) AS n
ORDER BY b.run_id, n;

-- 10 Hz samples for every lap. x = fraction of the lap completed (0 to 1).
-- Planted finding: run 3, lap 4 has a battery temperature spike peaking ~38 s in.
INSERT INTO samples (lap_id, t_ms, speed_mps, throttle_pct, brake_pct,
                     battery_v, battery_temp_c, motor_current_a)
SELECT lap_id, t_ms,
       round(speed::numeric, 2),
       round(throttle::numeric, 2),
       round(brake::numeric, 2),
       round((50.4 - 0.35 * (lap_number - 1) - 0.8 * x - 0.03 * current)::numeric, 2),
       round(temp::numeric, 2),
       round(current::numeric, 2)
FROM (
    SELECT l.lap_id, l.run_id, l.lap_number, t AS t_ms, x,
           -- average speed = 900 m track / lap time, with 3 accelerate/brake cycles per lap
           (900.0 / l.lap_time_s::float) * (1 + 0.22 * sin(2 * pi() * 3 * x + l.run_id))
               * CASE WHEN l.lap_number = 1 THEN 1 - exp(-t / 3000.0) ELSE 1 END AS speed,
           greatest(0, least(100, 55 + 45 * cos(2 * pi() * 3 * x + l.run_id))) AS throttle,
           greatest(0, -35 * cos(2 * pi() * 3 * x + l.run_id) - 15) AS brake,
           greatest(0, 0.9 * greatest(0, least(100, 55 + 45 * cos(2 * pi() * 3 * x + l.run_id)))
                       + 2 * sin(2 * pi() * 17 * x)) AS current,
           27 + 0.5 * l.run_id + 1.1 * (l.lap_number - 1) + 2.5 * x + 0.4 * sin(2 * pi() * 5 * x)
               + CASE WHEN l.run_id = 3 AND l.lap_number = 4
                      THEN 17 * exp(-power((t - 38000) / 7000.0, 2)) ELSE 0 END AS temp
    FROM laps l
    CROSS JOIN LATERAL generate_series(0, (l.lap_time_s * 1000)::int, 100) AS t
    CROSS JOIN LATERAL (SELECT t / (l.lap_time_s::float * 1000)) AS frac (x)
) s
ORDER BY lap_id, t_ms;

INSERT INTO pit_wall_notes (run_id, message) VALUES
    (3, 'Code word: REGEN (tell Rhea or Ajay you found this). '
        'Lap 4: pack temp went past 48 C, so we called the driver in for a pit stop.');

ANALYZE;

-- Read-only login for server.py, so a buggy tool can't change or drop anything.
CREATE ROLE workshop_ro LOGIN PASSWORD 'workshop';
GRANT CONNECT ON DATABASE telemetry TO workshop_ro;
GRANT USAGE ON SCHEMA public TO workshop_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO workshop_ro;
ALTER ROLE workshop_ro SET default_transaction_read_only = on;
ALTER ROLE workshop_ro SET statement_timeout = '5s';
