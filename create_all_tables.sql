-- ============================================================
-- ���� DDL������Դ.xlsx �� 46 �� sheet ��Ӧ�����ݿ��
-- ���ṹ���� enterprise_info_001�������� enterprise_info_001~046 ����
-- ����ʱ�䣺2026-07-17
-- ============================================================
-- ע�⣺������Ѵ��ڣ���ɾ�����ؽ��������ã�
-- USE <��Ĳ������ݿ�>;
-- GO

-- ============================================================
-- 001. ���ݽ���-��
-- ============================================================
-- ============================================================
IF OBJECT_ID('enterprise_info_001', 'U') IS NOT NULL DROP TABLE enterprise_info_001;
CREATE TABLE enterprise_info_001 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_001 PRIMARY KEY (id)
);
-- ============================================================
-- ============================================================
-- 002. ��������-��
-- ============================================================
IF OBJECT_ID('enterprise_info_002', 'U') IS NOT NULL DROP TABLE enterprise_info_002;
CREATE TABLE enterprise_info_002 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_002 PRIMARY KEY (id)
);

-- ============================================================
-- 003. ��ͨ����-��
-- ============================================================
IF OBJECT_ID('enterprise_info_003', 'U') IS NOT NULL DROP TABLE enterprise_info_003;
CREATE TABLE enterprise_info_003 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_003 PRIMARY KEY (id)
);

-- ============================================================
-- 004. ����-��
-- ============================================================
IF OBJECT_ID('enterprise_info_004', 'U') IS NOT NULL DROP TABLE enterprise_info_004;
CREATE TABLE enterprise_info_004 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_004 PRIMARY KEY (id)
);

-- ============================================================
-- 005. ��֯��ҵ-��
-- ============================================================
IF OBJECT_ID('enterprise_info_005', 'U') IS NOT NULL DROP TABLE enterprise_info_005;
CREATE TABLE enterprise_info_005 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_005 PRIMARY KEY (id)
);

-- ============================================================
-- 006. ��Դ����-��
-- ============================================================
IF OBJECT_ID('enterprise_info_006', 'U') IS NOT NULL DROP TABLE enterprise_info_006;
CREATE TABLE enterprise_info_006 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_006 PRIMARY KEY (id)
);

-- ============================================================
-- 007. ʳƷ��ҵ-��
-- ============================================================
IF OBJECT_ID('enterprise_info_007', 'U') IS NOT NULL DROP TABLE enterprise_info_007;
CREATE TABLE enterprise_info_007 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_007 PRIMARY KEY (id)
);

-- ============================================================
-- 008. ��������-��
-- ============================================================
IF OBJECT_ID('enterprise_info_008', 'U') IS NOT NULL DROP TABLE enterprise_info_008;
CREATE TABLE enterprise_info_008 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_008 PRIMARY KEY (id)
);

-- ============================================================
-- 009. ������Դ����-��
-- ============================================================
IF OBJECT_ID('enterprise_info_009', 'U') IS NOT NULL DROP TABLE enterprise_info_009;
CREATE TABLE enterprise_info_009 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_009 PRIMARY KEY (id)
);

-- ============================================================
-- 010. ��������-��
-- ============================================================
IF OBJECT_ID('enterprise_info_010', 'U') IS NOT NULL DROP TABLE enterprise_info_010;
CREATE TABLE enterprise_info_010 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_010 PRIMARY KEY (id)
);

-- ============================================================
-- 011. ���ĳ�-���
-- ============================================================
IF OBJECT_ID('enterprise_info_011', 'U') IS NOT NULL DROP TABLE enterprise_info_011;
CREATE TABLE enterprise_info_011 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_011 PRIMARY KEY (id)
);

-- ============================================================
-- 012. װ��װ��-���
-- ============================================================
IF OBJECT_ID('enterprise_info_012', 'U') IS NOT NULL DROP TABLE enterprise_info_012;
CREATE TABLE enterprise_info_012 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_012 PRIMARY KEY (id)
);

-- ============================================================
-- 013. ��������-���
-- ============================================================
IF OBJECT_ID('enterprise_info_013', 'U') IS NOT NULL DROP TABLE enterprise_info_013;
CREATE TABLE enterprise_info_013 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_013 PRIMARY KEY (id)
);

-- ============================================================
-- 014. ��е�豸-���
-- ============================================================
IF OBJECT_ID('enterprise_info_014', 'U') IS NOT NULL DROP TABLE enterprise_info_014;
CREATE TABLE enterprise_info_014 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_014 PRIMARY KEY (id)
);

-- ============================================================
-- 015. ���󹤳�-���
-- ============================================================
IF OBJECT_ID('enterprise_info_015', 'U') IS NOT NULL DROP TABLE enterprise_info_015;
CREATE TABLE enterprise_info_015 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_015 PRIMARY KEY (id)
);

-- ============================================================
-- 016. ʯ�ͻ���-���
-- ============================================================
IF OBJECT_ID('enterprise_info_016', 'U') IS NOT NULL DROP TABLE enterprise_info_016;
CREATE TABLE enterprise_info_016 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_016 PRIMARY KEY (id)
);

-- ============================================================
-- 017. ��ֲҵ-��
-- ============================================================
IF OBJECT_ID('enterprise_info_017', 'U') IS NOT NULL DROP TABLE enterprise_info_017;
CREATE TABLE enterprise_info_017 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_017 PRIMARY KEY (id)
);

-- ============================================================
-- 018. ����ҵ-��
-- ============================================================
IF OBJECT_ID('enterprise_info_018', 'U') IS NOT NULL DROP TABLE enterprise_info_018;
CREATE TABLE enterprise_info_018 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_018 PRIMARY KEY (id)
);

-- ============================================================
-- 019. ��ҵ-��
-- ============================================================
IF OBJECT_ID('enterprise_info_019', 'U') IS NOT NULL DROP TABLE enterprise_info_019;
CREATE TABLE enterprise_info_019 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_019 PRIMARY KEY (id)
);

-- ============================================================
-- 020. ��ҵ-��
-- ============================================================
IF OBJECT_ID('enterprise_info_020', 'U') IS NOT NULL DROP TABLE enterprise_info_020;
CREATE TABLE enterprise_info_020 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_020 PRIMARY KEY (id)
);

-- ============================================================
-- 021. ũҵ����-��
-- ============================================================
IF OBJECT_ID('enterprise_info_021', 'U') IS NOT NULL DROP TABLE enterprise_info_021;
CREATE TABLE enterprise_info_021 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_021 PRIMARY KEY (id)
);

-- ============================================================
-- 022. ұ����-��
-- ============================================================
IF OBJECT_ID('enterprise_info_022', 'U') IS NOT NULL DROP TABLE enterprise_info_022;
CREATE TABLE enterprise_info_022 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_022 PRIMARY KEY (id)
);

-- ============================================================
-- 023. ��ɳ-��
-- ============================================================
IF OBJECT_ID('enterprise_info_023', 'U') IS NOT NULL DROP TABLE enterprise_info_023;
CREATE TABLE enterprise_info_023 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_023 PRIMARY KEY (id)
);

-- ============================================================
-- 024. ��������-��
-- ============================================================
IF OBJECT_ID('enterprise_info_024', 'U') IS NOT NULL DROP TABLE enterprise_info_024;
CREATE TABLE enterprise_info_024 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_024 PRIMARY KEY (id)
);

-- ============================================================
-- 025. ��������-��
-- ============================================================
IF OBJECT_ID('enterprise_info_025', 'U') IS NOT NULL DROP TABLE enterprise_info_025;
CREATE TABLE enterprise_info_025 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_025 PRIMARY KEY (id)
);

-- ============================================================
-- 026. ���ӿƼ�-��
-- ============================================================
IF OBJECT_ID('enterprise_info_026', 'U') IS NOT NULL DROP TABLE enterprise_info_026;
CREATE TABLE enterprise_info_026 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_026 PRIMARY KEY (id)
);

-- ============================================================
-- 027. �����Ӫ-��
-- ============================================================
IF OBJECT_ID('enterprise_info_027', 'U') IS NOT NULL DROP TABLE enterprise_info_027;
CREATE TABLE enterprise_info_027 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_027 PRIMARY KEY (id)
);

-- ============================================================
-- 028. �Ի��ӿ�-��
-- ============================================================
IF OBJECT_ID('enterprise_info_028', 'U') IS NOT NULL DROP TABLE enterprise_info_028;
CREATE TABLE enterprise_info_028 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_028 PRIMARY KEY (id)
);

-- ============================================================
-- 029. ���ɷ���-��ƽ
-- ============================================================
IF OBJECT_ID('enterprise_info_029', 'U') IS NOT NULL DROP TABLE enterprise_info_029;
CREATE TABLE enterprise_info_029 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_029 PRIMARY KEY (id)
);

-- ============================================================
-- 030. ���ز�-��ƽ
-- ============================================================
IF OBJECT_ID('enterprise_info_030', 'U') IS NOT NULL DROP TABLE enterprise_info_030;
CREATE TABLE enterprise_info_030 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_030 PRIMARY KEY (id)
);

-- ============================================================
-- 031. �Ϳվ���-��ƽ
-- ============================================================
IF OBJECT_ID('enterprise_info_031', 'U') IS NOT NULL DROP TABLE enterprise_info_031;
CREATE TABLE enterprise_info_031 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_031 PRIMARY KEY (id)
);

-- ============================================================
-- 032. ��̬����-��ƽ
-- ============================================================
IF OBJECT_ID('enterprise_info_032', 'U') IS NOT NULL DROP TABLE enterprise_info_032;
CREATE TABLE enterprise_info_032 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_032 PRIMARY KEY (id)
);

-- ============================================================
-- 033. ������Ӫ-��ƽ
-- ============================================================
IF OBJECT_ID('enterprise_info_033', 'U') IS NOT NULL DROP TABLE enterprise_info_033;
CREATE TABLE enterprise_info_033 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_033 PRIMARY KEY (id)
);

-- ============================================================
-- 034. ������Ʒ-��ƽ
-- ============================================================
IF OBJECT_ID('enterprise_info_034', 'U') IS NOT NULL DROP TABLE enterprise_info_034;
CREATE TABLE enterprise_info_034 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_034 PRIMARY KEY (id)
);

-- ============================================================
-- 035. ҽҩ��ҵ-��ƽ
-- ============================================================
IF OBJECT_ID('enterprise_info_035', 'U') IS NOT NULL DROP TABLE enterprise_info_035;
CREATE TABLE enterprise_info_035 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_035 PRIMARY KEY (id)
);

-- ============================================================
-- 036. ͨ�Ź���-��ƽ
-- ============================================================
IF OBJECT_ID('enterprise_info_036', 'U') IS NOT NULL DROP TABLE enterprise_info_036;
CREATE TABLE enterprise_info_036 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_036 PRIMARY KEY (id)
);

-- ============================================================
-- 037. ˮ������-��ƽ
-- ============================================================
IF OBJECT_ID('enterprise_info_037', 'U') IS NOT NULL DROP TABLE enterprise_info_037;
CREATE TABLE enterprise_info_037 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_037 PRIMARY KEY (id)
);

-- ============================================================
-- 038. ����-��ӱ
-- ============================================================
IF OBJECT_ID('enterprise_info_038', 'U') IS NOT NULL DROP TABLE enterprise_info_038;
CREATE TABLE enterprise_info_038 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_038 PRIMARY KEY (id)
);

-- ============================================================
-- 039. ����-��ӱ
-- ============================================================
IF OBJECT_ID('enterprise_info_039', 'U') IS NOT NULL DROP TABLE enterprise_info_039;
CREATE TABLE enterprise_info_039 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_039 PRIMARY KEY (id)
);

-- ============================================================
-- 040. ��������-��ӱ
-- ============================================================
IF OBJECT_ID('enterprise_info_040', 'U') IS NOT NULL DROP TABLE enterprise_info_040;
CREATE TABLE enterprise_info_040 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_040 PRIMARY KEY (id)
);

-- ============================================================
-- 041. ���ƹ���-��ӱ
-- ============================================================
IF OBJECT_ID('enterprise_info_041', 'U') IS NOT NULL DROP TABLE enterprise_info_041;
CREATE TABLE enterprise_info_041 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_041 PRIMARY KEY (id)
);

-- ============================================================
-- 042. ��Ϣ����-��ӱ
-- ============================================================
IF OBJECT_ID('enterprise_info_042', 'U') IS NOT NULL DROP TABLE enterprise_info_042;
CREATE TABLE enterprise_info_042 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_042 PRIMARY KEY (id)
);

-- ============================================================
-- 043. ��չ����-��ӱ
-- ============================================================
IF OBJECT_ID('enterprise_info_043', 'U') IS NOT NULL DROP TABLE enterprise_info_043;
CREATE TABLE enterprise_info_043 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_043 PRIMARY KEY (id)
);

-- ============================================================
-- 044. ���պ���-��ӱ
-- ============================================================
IF OBJECT_ID('enterprise_info_044', 'U') IS NOT NULL DROP TABLE enterprise_info_044;
CREATE TABLE enterprise_info_044 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_044 PRIMARY KEY (id)
);

-- ============================================================
-- 045. ��������Ṥ��-��ӱ
-- ============================================================
IF OBJECT_ID('enterprise_info_045', 'U') IS NOT NULL DROP TABLE enterprise_info_045;
CREATE TABLE enterprise_info_045 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_045 PRIMARY KEY (id)
);

-- ============================================================
-- 046. ��������ҵ��ȡ
-- ============================================================
IF OBJECT_ID('enterprise_info_046', 'U') IS NOT NULL DROP TABLE enterprise_info_046;
CREATE TABLE enterprise_info_046 (
    id bigint IDENTITY(1,1) NOT NULL,
    company_name nvarchar(500) COLLATE Chinese_PRC_CI_AS NOT NULL,
    industry nvarchar(100) COLLATE Chinese_PRC_CI_AS NOT NULL,
    sub_category_2 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    sub_category_3 nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    [source] nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    org_type nvarchar(100) COLLATE Chinese_PRC_CI_AS NULL,
    status nvarchar(200) COLLATE Chinese_PRC_CI_AS NULL,
    link nvarchar(1000) COLLATE Chinese_PRC_CI_AS NULL,
    team nvarchar(50) COLLATE Chinese_PRC_CI_AS NULL,
    collected_at date NULL,
    system_reply nvarchar(MAX) COLLATE Chinese_PRC_CI_AS NULL,
    created_at datetime2 NULL,
    updated_at datetime2 NULL,
    CONSTRAINT PK_enterprise_info_046 PRIMARY KEY (id)
);


PRINT 'ȫ�� 46 �ű��Ѵ�����ϡ�';
