use spider;

# 失信个人记录表
drop table if exists `t_shixin_person`;
create table `t_shixin_person` (

  `id` int unsigned primary key auto_increment comment 'id',
  `alter_time` timestamp default current_timestamp on update current_timestamp,

  `sys_id` int unsigned not null comment '查询id',
  `name` varchar(128) not null comment '姓名',
  `age` varchar(8) not null comment '年龄',
  `sex` varchar(8) not null comment '性别',
  `card_num` varchar(32) not null comment '身份证号',

  `area_name` varchar(64) not null comment '地区',
  `case_code` varchar(128) not null comment '案号',
  `reg_date` varchar(128) not null comment '立案时间',
  `publish_date` varchar(128) not null comment '发布时间',
  `gist_id` varchar(128) not null comment '执行依据文号',
  `court_name` varchar(128) not null comment '执行法院',
  `gist_unit` varchar(128) not null comment '做出执行依据单位',
  `duty` text not null comment '生效法律文书确定的义务',
  `performance` varchar(128) not null comment '被执行人的履行情况',
  `disrupt_type_name` varchar(128) not null comment '失信被执行人行为具体情形',

  `party_type_name` varchar(128)  not null comment '含义未知字段',

   unique key `sys_id_key`(`sys_id`)

) engine=innodb default charset=utf8 auto_increment=1000 comment='失信个人表';


# 导入宇豪之前爬取得历史数据
load data infile "/home/user/spider/data/t_shixin_person.csv" into table `t_shixin_person`
character set utf8
fields terminated by ',' optionally enclosed by '"'
lines terminated by '\r\n'
ignore 1 lines
(sys_id,name, case_code, age, sex, card_num, court_name, area_name, 
	party_type_name, gist_id, reg_date, gist_unit, duty, performance, disrupt_type_name, publish_date);


# 导入爬取的数据
insert into t_shixin_person(sys_id, name, age, sex, card_num, area_name, case_code, 
  reg_date, publish_date, gist_id, court_name ,gist_unit, duty, performance, disrupt_type_name, party_type_name)
select sys_id, iname, age, sexy, cardNum, areaName, caseCode,
regDate, publishDate, gistId, courtName, gistUnit, duty, performance, disruptTypeName, partyTypeName from spider_temp.t_shixin_person;