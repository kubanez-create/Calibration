-- DELETE FROM predictions.raw_predictions WHERE id = 2;

-- SELECT * FROM predictions.raw_predictions LIMIT 10, 10;

SELECT COUNT(*) FROM predictions.raw_predictions;

-- SELECT tot_acc_50 / tot_num_pred AS calibration_50,
--        tot_acc_90 / tot_num_pred AS calibration_90
--   FROM (
--       SELECT COUNT(id) AS tot_num_pred,
--        SUM(acc_50) AS tot_acc_50,
--        SUM(acc_90) AS tot_acc_90
--   FROM (
--     SELECT
--        id, user_id,
--        pred_low_50_conf <= actual_outcome AND
--        pred_high_50_conf >= actual_outcome AS acc_50,
--        pred_low_90_conf <= actual_outcome AND
--        pred_high_90_conf >= actual_outcome AS acc_90
--     FROM predictions.raw_predictions
--     WHERE user_id = 411347820 
--       AND task_category = 'food'
--       AND actual_outcome IS NOT NULL) AS base_table
--  GROUP BY user_id
--   ) AS outer_table;

-- SELECT DISTINCT task_category
--   FROM predictions.raw_predictions;
