CREATE TEMPORARY TABLE `t_temp` 
as  (
   SELECT min(id) as id
   FROM `beletag_good_params`
   GROUP BY good_id, color_name, size, date
);

DELETE from `beletag_good_params`
WHERE `beletag_good_params`.id not in (
   SELECT id FROM t_temp
);