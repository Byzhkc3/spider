use spider;

# 个人基本信息表
drop table if exists `t_credit_person`;
create table `t_credit_person_record`(
  
  `id` int unsigned primary key auto_increment,
 
  `report_id` varchar(32) not null comment '报告id',
  `query_time` varchar(32) not null comment '查询时间',
  `report_time` varchar(32) not null comment '报告时间',

  `name` varchar(32) not null comment '姓名',
  `id_type` varchar(16) not null comment '证件类型',
  `id_card` varchar(32) not null comment '证件号码',
  `marriage` varchar(8) not null comment '婚姻状况',

   unique index `report` (`report_id`)

) engine=innodb default charset=utf8 auto_increment=1000 comment='个人基本信息表';



# 机构/个人查询记录明细表
drop table if exists `t_credit_query`;
create table `t_credit_query`(
  `id` int unsigned primary key auto_increment,
 
  `query_id` smallint not null comment '查询序号',
  `query_type` enum('0','1') comment '0代表个人查询,1代表机构查询',
  `query_time` date not null comment '查询时间',
  `query_operator` varchar(128) not null comment '查询操作员',
  `query_reason` varchar(128) not null comment '查询原因'

)engine=innodb default charset=utf8 auto_increment=1000 comment='机构/个人查询记录明细表';



# 信用卡记录明细表
drop table if exists `t_credit_card`;
create table `t_credit_card`(
  `id` int unsigned primary key auto_increment,

  `query_id` int  not null comment '查询序号',
  `bank` varchar(32) not null comment '发行银行',
  `release_date` varchar(32) not null comment '发行日期',
  `crad_type` varchar(32) not null comment '卡类型',
  `account_type` varchar(16) not null comment '账户类型',
  `due_date` varchar(32) not null comment '截止日期',
  `credit_amt` varchar(32) not null comment '信用额度',
  `used_amt` varchar(32) not null comment '已用额度',
  `over_due_amount` varchar(32) default null comment '逾期额度'

)engine=innodb default charset=utf8 auto_increment=1000 comment='信用卡账户明细表';



# 为他人担保记录明细
drop table if exists `t_credit_guarantee`;
create table `t_credit_card_guarantee`(

  `query_id` int  comment '查询编号',
  `guarantor` varchar(32)  comment '为谁担保',
  `guarantee_date` varchar(16)  comment '担保日期',
  `guarantee_place` varchar(64) comment '担保地址',
  `card_type` varchar(32) comment '证件类型',
  `card_num` varchar(32) comment '证件号',
  `loan_type` varchar(16) comment '贷款类型',
  `loan_count` varchar(32) comment '贷款额',
  `guarantee_count` varchar(32) comment '担保额',
  `due_date` varchar(16) comment '截至日期',
  `balance` varchar(32)  comment '余额

)engine=innodb default charset=utf8 auto_increment=1000 comment='为他人担保记录明细';





# 强制执行记录明细
drop table if exists `t_credit_enforce`;
create table `t_credit_enforce`(

  `query_id` int comment '查询编号',
  `exe_court` varchar(32) comment '执行法院',
  `case_no` varchar(32)  comment '案号',
  `exe_reason` varchar(64) comment '执行案由',
  `closed_way` varchar(32) comment '结案方式',
  `filing_time` varchar(32) comment '立案时间',
  `case_status` varchar(16) comment '案件状态',
  `app_exe` varchar(16) comment '申请执行标的',
  `executed` varchar(16) comment '已执行标的',
  `app_exe_amt` varchar(32)  comment '申请执行标的金额',
  `executed_amt` varchar(32) comment '已执行标的金额',
  `closed_time` varchar(32) comment '创建时间'

)engine=innodb default charset=utf8 auto_increment=1000 comment='强制执行记录明细';



# 房贷记录明细表



# 其他贷款记录明细