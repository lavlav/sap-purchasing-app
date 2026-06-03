-- Generate database and table schema for testing purposes
-- This is a small subset of the actual schema used in the SAP_TEST system,
-- sufficient for testing integration.
-- Create databases
IF DB_ID('HISTORICAL_TEST') IS NULL
    CREATE DATABASE HISTORICAL_TEST;
GO
IF DB_ID('SAP_TEST') IS NULL
    CREATE DATABASE SAP_TEST;
GO

-- Seed SAP_TEST database
USE SAP_TEST;
GO

CREATE TABLE OSPP (
    CardCode NVARCHAR(20),
    ItemCode NVARCHAR(20)
);

--

CREATE TABLE OCRD (
    CardType NVARCHAR(10),
    CardCode NVARCHAR(20)
);

--

CREATE TABLE OITM (
    ItemName NVARCHAR(50),
    ItemCode NVARCHAR(20),
    IsCommited BIT,
    OnOrder INT,
    ItmsGrpCod INT,
    MinLevel INT
    -- User-defined fields for vendor data go here
);

--

CREATE TABLE OPOR (
    CardCode NVARCHAR(20),
    CardName NVARCHAR(50),
    DocNum INT,
    DocDate DATE,
    DocEntry INT,
    DocDueDate DATE,
    Comments NVARCHAR(255)
);

--

CREATE TABLE OINV (
    DocEntry INT,
    DocDate DATE
);

--

CREATE TABLE INV1 (
    DocEntry INT,
    ItemCode NVARCHAR(20),
    Quantity INT
);

--

CREATE TABLE OITW (
    OnHand INT,
    WhsCode NVARCHAR(10),
    ItemCode NVARCHAR(20),
);

--

CREATE TABLE PDN1 (
    BaseDocNum INT,
    ActDelDate DATE,
    ItemCode NVARCHAR(20),
    InvQty INT
);

--

CREATE TABLE POR1 (
    ItemCode NVARCHAR(20),
    Dscription NVARCHAR(50),
    DocEntry INT,
    Quantity INT,
    Price DECIMAL(18,2),
    LineStatus NVARCHAR(10)
);

--

USE HISTORICAL_TEST;
GO

CREATE TABLE FactSales (
    Quantity INT,
    Linetotal DECIMAL(18,2),
    ItemKey NVARCHAR(20),
    CardKey NVARCHAR(20),
    DocDate DATE,
)

CREATE TABLE DimItem (
    ItemCode NVARCHAR(20),
    ItemName NVARCHAR(50),
    ItemKey NVARCHAR(20),
)

CREATE TABLE DimPartner (
    CardKey NVARCHAR(20),
    GroupCode NVARCHAR(50)
)

CREATE TABLE DimPartnerGroup (
    GroupCode NVARCHAR(50),
    GroupName NVARCHAR(50)
)

-- Create login and user for testing
IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = 'test-user')
    CREATE LOGIN [test-user] WITH PASSWORD = 'T3stP&ssword';
GO

USE HISTORICAL_TEST;
GO

-- Assign the login to the database
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'test-user')
    CREATE USER [test-user] FOR LOGIN [test-user];

-- Grant SELECT permissions on all tables in HISTORICAL_TEST to test-user
GRANT SELECT ON FactSales TO [test-user];
GRANT SELECT ON DimItem TO [test-user];
GRANT SELECT ON DimPartner TO [test-user];
GRANT SELECT ON DimPartnerGroup TO [test-user];

USE SAP_TEST;
GO

IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'test-user')
    CREATE USER [test-user] FOR LOGIN [test-user];
GO

GRANT SELECT ON OSPP TO [test-user];
GRANT SELECT ON OCRD TO [test-user];
GRANT SELECT ON OITM TO [test-user];
GRANT SELECT ON OPOR TO [test-user];
GRANT SELECT ON OINV TO [test-user];
GRANT SELECT ON INV1 TO [test-user];
GRANT SELECT ON OITW TO [test-user];
GRANT SELECT ON PDN1 TO [test-user];
GRANT SELECT ON POR1 TO [test-user];