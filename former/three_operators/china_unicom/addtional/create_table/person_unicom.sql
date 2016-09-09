use spider;

# 中国联通-用户信息表
drop table if exists `t_china_unicom_user`;
create table `t_china_unicom_user`(

    `id` int unsigned primary key auto_increment comment 'id',
    `alter_time` timestamp not null default current_timestamp comment '创建时间',

    `login_name` varchar(32) not null comment '登录名:手机号/邮箱/固话',
    `password` varchar(32) not null comment '登录密码:测试不加密',

    `name` varchar(32) default null comment '姓名',
    `sex` varchar(8)  default null comment '性别',
    `address` varchar(128) default null comment '地址',
    `cert_type` varchar(16) default '身份证' comment '证件类型',
    `cert_id` char(32) not null comment '证件号码',

    `phone` char(16) not null comment '手机号',
    `home`  varchar(128) not null comment '归属地',
    `brand` varchar(32) not null comment '用户套餐',
    `level` varchar(32) not null comment '用户等级',
    `status` varchar(32) default '有效期' comment '用户状态',
    `open_date` datetime not null comment '入网时间',
    `balance` float not null default 0 comment '账户余额',
    `puk_id` varchar(32) not null comment 'PUK码',

    `user_valid` tinyint default 1 comment '有效性:默认为1有效,0为无效',

    unique key `unique_user`(`cert_id`, `phone`)

)engine=innodb default charset=utf8 auto_increment=1000 comment='联通-用户信息表';


# 中国联通-用户通话记录表
drop table if exists `t_china_unicom_call`;
create table `t_china_unicom_call`(

	`id` int unsigned primary key auto_increment,
    `alter_time` timestamp not null default current_timestamp comment '创建时间',
	
    `cert_id` char(32) comment '身份证号/指回t_unicom_usr.cert_id',

    `phone` char(16) not null comment '手机号/指回t_unicom_usr.phone',
    `call_area` varchar(128) not null comment '通话地点 ',
    `call_date` date not null comment '通话日期(年-月-日)',
    `call_time` time not null comment '通话时间(时:分:秒)',
	`call_cost` varchar(16) not null comment '通话费',
	`call_long` varchar(16) not null comment '通话时长',

    `other_phone` varchar(16) not null comment '对方号码 ',
    `call_type` varchar(32) not null comment '呼叫类型(主叫/被叫)',
    `land_type` varchar(16) default null comment '通话类型(本地通话...)',
    
    index `user` (`cert_id`,`phone`) comment '建立索引便于快速inner join',
    unique key `unique_call` (`phone`, `call_date`, `call_time`, `other_phone`)

)engine=innodb default charset=utf8 auto_increment=1000 comment='联通-通话记录表';
