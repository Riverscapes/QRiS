CREATE extension IF NOT EXISTS postgis;

CREATE TABLE projects (
    project_id      INT                 GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    project_name    VARCHAR(255)        NOT NULL,
    project_desc    TEXT,
    metadata        JSON,
    geom            Geography(MultiPolygon),
    created_by      VARCHAR(255)        NOT NULL,
    created_date    TIMESTAMPTZ         NOT NULL DEFAULT now(),
    updated_date    TIMESTAMPTZ         NOT NULL DEFAULT now(),

    -- TODO: add length constraints for all NOT NULL fields
    CONSTRAINT ck_projects_project_name CHECK (length(project_name) > 0)
);

-- TODO: Use ux throughout instead of idx
-- TODO: No indexes on PRIMARY KEY

CREATE UNIQUE INDEX ux_projects_project_name ON projects(project_name, created_by);
----------------------------------------------------

CREATE TABLE assessment_types (
    assessment_type_id      INT             GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    assessment_type_name    VARCHAR(255)    NOT NULL,
    created_date            TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_date            TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT ck_assessment_types_assessment_type_name CHECK (length(assessment_type_name) > 0)
);
----------------------------------------------------

CREATE TYPE assessment_attributes_data_type AS ENUM ('integer', 'text', 'float');

CREATE TABLE assessment_attributes (
    assessment_attribute_id     INT             GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    assessment_type_id          INT             NOT NULL,
    display_name                VARCHAR(255)    NOT NULL,
    data_type                   assessment_attributes_data_type     NOT NULL,
    created_date                TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_date                TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT fk_assessment_attributes_assessment_type_id FOREIGN KEY (assessment_type_id) REFERENCES assessment_types(assessment_type_id) ON DELETE CASCADE
);

CREATE INDEX fx_assessment_attributes_assessment_type_id ON assessment_attributes(assessment_type_id);
--------------------------------------------------------------------------------------------------------

CREATE TABLE assessment_methods (
    assessment_method_id        INT           GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    assessment_method_name      VARCHAR(255)  NOT NULL,
    created_date                TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_date                TIMESTAMPTZ   NOT NULL DEFAULT now()
);
--------------------------------------------------------------------------------------------------------

CREATE TABLE assessments (
    assessment_id           INT             GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    project_id              INT             NOT NULL,
    assessment_type_id      INT             NOT NULL,
    assessment_method_id    INT             NOT NULL,
    assessor_name           VARCHAR(255)    NOT NULL,
    assessment_date         DATE            NOT NULL,
    assessment_desc         TEXT,
    metadata                JSON,
    created_date            TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_date            TIMESTAMPTZ     NOT NULL DEFAULT now(),

    CONSTRAINT fk_assessments_project_id FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    CONSTRAINT fk_assessments_assessment_type_id FOREIGN KEY (assessment_type_id) REFERENCES assessment_types(assessment_type_id),
    CONSTRAINT fk_assessment_method_id FOREIGN KEY (assessment_method_id) REFERENCES assessment_methods(assessment_method_id),

    CONSTRAINT ck_assessments_assessor_name CHECK (length(assessor_name) > 0)
);

CREATE INDEX fx_assessments_project_id ON assessments(project_id);
CREATE INDEX fx_assessments_assessment_type_id ON assessments(assessment_type_id);
CREATE INDEX fx_assessments_assessment_method_id ON assessments(assessment_method_id);

--------------------------------------------------------------------------------------------------------

CREATE TABLE assessment_points (
    assessment_point_id     INT            GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    assessment_id           INT            NOT NULL,
    assessment_point_desc   TEXT,
    metadata                JSON,
    geom                    Geography(Point) NOT NULL,

    CONSTRAINT fk_assessment_points_assessment_id FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id) ON DELETE CASCADE
);

CREATE INDEX fx_assessment_points_assessment_id ON assessment_points(assessment_id);
--------------------------------------------------------------------------------------------------------

CREATE TABLE  assessment_lines (
    assessment_line_id    INT              GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    assessment_id         INT            NOT NULL,
    assessment_line_desc  TEXT,
    metadata              JSON,
    geom                  Geography(LineString) NOT NULL,

    CONSTRAINT fk_assessment_lines_assessment_id FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id) ON DELETE CASCADE

);

CREATE INDEX fx_assessment_lines_assessment_id ON assessment_lines(assessment_id);

--------------------------------------------------------------------------------------------------------

CREATE TABLE  assessment_polygons (
    assessment_polygon_id       INT            GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    assessment_id               INT            NOT NULL REFERENCES assessments(assessment_id),
    assessment_polygon_desc     TEXT,
    metadata                    JSON,
    geom                        Geography(MultiPolygon) NOT NULL,

    CONSTRAINT fk_assessment_polygons_assessment_id FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id) ON DELETE CASCADE
);

CREATE INDEX fx_assessment_polygons_assessment_id ON assessment_polygons(assessment_id);


--------------------------------------------------------------------------------------------------------