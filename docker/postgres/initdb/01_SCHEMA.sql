CREATE extension IF NOT EXISTS postgis;

CREATE TABLE projects (
    project_id      SERIAL          PRIMARY KEY,
    project_name    VARCHAR(50)     NOT NULL,
    project_desc    TEXT,
    metadata        JSON,
    geom            Geography(MultiPolygon),
    created_date    TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_date    TIMESTAMPTZ     NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_project_id ON projects(project_id);

CREATE INDEX idx_wl_geom ON wetlands USING GIST (geom);
----------------------------------------------------

CREATE TABLE assessment_types (
    assessment_type_id      SERIAL          PRIMARY KEY,
    assessment_type_name    VARCHAR(50)     NOT NULL,
    created_date            TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_date            TIMESTAMPTZ     NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_assessment_type_id ON assessment_types(assessment_type_id);

INSERT INTO assessment_types (assessment_type_id, assessment_type_name) VALUES (1, 'Dam Survey');
INSERT INTO assessment_types (assessment_type_id, assessment_type_name) VALUES (1, 'Jam Survey');
INSERT INTO assessment_types (assessment_type_id, assessment_type_name) VALUES (2, 'Channel Units');
INSERT INTO assessment_types (assessment_type_id, assessment_type_name) VALUES (3, 'Geomorphic Units');
----------------------------------------------------

CREATE TABLE assessment_attributes (
    assessment_attribute_id     SERIAL          PRIMARY KEY,
    assessment_type_id          SMALLINT        NOT NULL REFERENCES assessment_types(assessment_type_id),
    display_name                VARCHAR(50)     NOT NULL,
    data_type                   VARCHAR(50)     NOT NULL,
    -- TODO: should data type be a lookup table as well, should these be postgres data types?
    created_date                TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_date                TIMESTAMPTZ     NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_assessment_attribute_id ON assessment_attributes(assessment_attribute_id);

INSERT INTO assessment_attributes (assessment_attribute_id, assessment_type_id, display_name, data_type) VALUES (1, 1, 'Dam Source', 'text');
INSERT INTO assessment_attributes (assessment_attribute_id, assessment_type_id, display_name, data_type) VALUES (2, 1, 'Dam Active', 'text');
INSERT INTO assessment_attributes (assessment_attribute_id, assessment_type_id, display_name, data_type) VALUES (3, 1, 'Dam Count', 'integer');
INSERT INTO assessment_attributes (assessment_attribute_id, assessment_type_id, display_name, data_type) VALUES (4, 2, 'Jam Source', 'text');
INSERT INTO assessment_attributes (assessment_attribute_id, assessment_type_id, display_name, data_type) VALUES (5, 3, 'Wood Count', 'integer');
--------------------------------------------------------------------------------------------------------

CREATE TABLE assessment_methods (
    assessment_method_id      SERIAL          PRIMARY KEY,
    assessment_method_name    VARCHAR(50)     NOT NULL,
    created_date              TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_date            TIMESTAMPTZ     NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_assessment_method_id ON assessment_methods(assessment_method_id);

INSERT INTO assessment_methods (assessment_method_id, assessment_method_name) VALUES (1, 'Desktop');
INSERT INTO assessment_methods (assessment_method_id, assessment_method_name) VALUES (2, 'Field');
INSERT INTO assessment_methods (assessment_method_id, assessment_method_name) VALUES (3, 'Model');
INSERT INTO assessment_methods (assessment_method_id, assessment_method_name) VALUES (4, 'Qualitative');
--------------------------------------------------------------------------------------------------------

CREATE TABLE assessments (
    assessment_id           SERIAL          PRIMARY KEY,
    project_id              SMALLINT        NOT NULL REFERENCES projects(project_id),
    assessment_type_id      SMALLINT        NOT NULL REFERENCES assessment_types(assessment_type_id),
    assessment_method_id    SMALLINT        NOT NULL REFERENCES assessment_methods(assessment_method_id),
    -- TODO: Should all references be specified as CONSTRAINTS?
    assessor                VARCHAR(50)     NOT NULL,
    assessment_date         DATE            NOT NULL,
    assessment_desc         TEXT,
    metadata                JSON,
    created_date            TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_date            TIMESTAMPTZ     NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_assessment_id ON assessments(assessment_id);
--------------------------------------------------------------------------------------------------------

CREATE TABLE assessment_points (
    assessment_point_id    SERIAL              PRIMARY KEY,
    assessment_id           SMALLINT            NOT NULL REFERENCES assessments(assessment_id),
    assessment_point_desc  TEXT,
    metadata                JSON,
    geom                    Geography(Point)
);

CREATE UNIQUE INDEX idx_assessment_point_id ON assessment_points(assessment_point_id);
--------------------------------------------------------------------------------------------------------

CREATE TABLE  assessment_lines (
    assessment_line_id    SERIAL              PRIMARY KEY,
    assessment_id          SMALLINT            NOT NULL REFERENCES assessments(assessment_id),
    assessment_line_desc  TEXT,
    metadata               JSON,
    geom                   Geography(LineString)
    -- TODO: Which line feature? Multi or LineString?
);

CREATE UNIQUE INDEX idx_assessment_line_id ON assessment_lines(assessment_line_id);
--------------------------------------------------------------------------------------------------------

CREATE TABLE  assessment_polygons (
    assessment_polygon_id       SERIAL            PRIMARY KEY,
    assessment_id               SMALLINT          NOT NULL REFERENCES assessments(assessment_id),
    assessment_polygon_desc     TEXT,
    metadata                    JSON,
    geom                        Geography(MultiPolygon)
);

CREATE UNIQUE INDEX idx_assessment_polygon_id ON assessment_polygons(assessment_polygon_id);

--------------------------------------------------------------------------------------------------------