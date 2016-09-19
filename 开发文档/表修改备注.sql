# 修改t_shixin_valid的索引
alter table t_shixin_valid drop index com_or_person; 
alter table t_shixin_valid add index `search`(`name`, `card_num`, `flag`);

# 修改t_shixin_invalid的索引
alter table t_shixin_invalid drop index re_err; 
alter table t_shixin_invalid add index `search`(`err_type`, `flag`);

# 备注
# 目前无法对被执行人数据进行分类[公司/个人]
