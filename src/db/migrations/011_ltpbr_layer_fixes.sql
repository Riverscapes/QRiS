-- Strategic felling is spelled Startegic in the options for structure types. So it isn't getting symbolized correctly.
UPDATE lookup_list_values SET list_value = 'Strategic Felling' WHERE id = 101;

-- Get rid of the () in the Active Channels and Centerlines layer names. It's inconsistent with all the rest of the layer names and is asking for trouble when writing calculations
UPDATE layers SET display_name = 'Active Channels' WHERE fc_name = 'active_channel';
UPDATE layers SET display_name = 'Centerlines of Active Channels' WHERE fc_name = 'centerlines';