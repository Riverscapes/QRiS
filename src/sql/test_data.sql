-- a test project with a jam and dam survey

INSERT INTO projects (fid, name) VALUES (1, 'Asotin IMW');
INSERT INTO projects (fid, name) VALUES (2, 'Whychus Creek');


INSERT INTO assessments (fid, project_id, start_date) VALUES (1, 1,'2021/10/31');
INSERT INTO assessments (fid, project_id, start_date) VALUES (2, 1,'2020/6/23');
INSERT INTO assessments (fid, project_id, start_date) VALUES (3, 2,'2020/6/23');


INSERT INTO assessment_methods (fid, assessment_id, method_id, platform_id) VALUES (1, 1, 3, 1);
INSERT INTO assessment_methods (fid, assessment_id, method_id, platform_id) VALUES (2, 1, 1, 1);
INSERT INTO assessment_methods (fid, assessment_id, method_id, platform_id) VALUES (3, 1, 1, 1);
INSERT INTO assessment_methods (fid, assessment_id, method_id, platform_id) VALUES (4, 3, 1, 1);
INSERT INTO assessment_methods (fid, assessment_id, method_id, platform_id) VALUES (5, 3, 3, 1);

