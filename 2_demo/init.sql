IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'BusinessDB')
BEGIN
    CREATE DATABASE BusinessDB;
END
GO

USE BusinessDB;
GO

-- 1. Bảng Khách hàng
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Customers' and xtype='U')
BEGIN
    CREATE TABLE Customers (
        CustomerID INT IDENTITY(1,1) PRIMARY KEY,
        CustomerName NVARCHAR(255) NOT NULL,
        Region NVARCHAR(100),
        SignupDate DATE
    );

    INSERT INTO Customers (CustomerName, Region, SignupDate) VALUES
    (N'Nguyễn Văn A', N'Miền Bắc', '2023-01-15'),
    (N'Trần Thị B', N'Miền Nam', '2023-02-20'),
    (N'Lê Văn C', N'Miền Trung', '2023-03-10'),
    (N'Phạm Thị D', N'Miền Bắc', '2023-04-05'),
    (N'Hoàng Văn E', N'Miền Nam', '2023-05-12');
END
GO

-- 2. Bảng Sản phẩm
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Products' and xtype='U')
BEGIN
    CREATE TABLE Products (
        ProductID INT IDENTITY(1,1) PRIMARY KEY,
        ProductName NVARCHAR(255) NOT NULL,
        Category NVARCHAR(100),
        Price DECIMAL(18,2)
    );

    INSERT INTO Products (ProductName, Category, Price) VALUES
    (N'Laptop Dell XPS', N'Điện tử', 25000000),
    (N'iPhone 14', N'Điện thoại', 20000000),
    (N'Bàn phím cơ', N'Phụ kiện', 1500000),
    (N'Chuột Logitech', N'Phụ kiện', 500000);
END
GO

-- 3. Bảng Đơn hàng
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Orders' and xtype='U')
BEGIN
    CREATE TABLE Orders (
        OrderID INT IDENTITY(1,1) PRIMARY KEY,
        CustomerID INT FOREIGN KEY REFERENCES Customers(CustomerID),
        OrderDate DATE,
        TotalAmount DECIMAL(18,2),
        Status NVARCHAR(50)
    );

    INSERT INTO Orders (CustomerID, OrderDate, TotalAmount, Status) VALUES
    (1, '2024-03-01', 25500000, N'Hoàn thành'),
    (2, '2024-03-05', 20000000, N'Hoàn thành'),
    (3, '2024-03-10', 1500000, N'Đang giao'),
    (1, '2024-03-15', 500000, N'Hoàn thành'),
    (4, '2024-03-20', 26500000, N'Hoàn thành'),
    (5, '2024-04-01', 20000000, N'Đã hủy');
END
GO

-- 4. Bảng Chi tiết chiến dịch Marketing
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='MarketingCampaigns' and xtype='U')
BEGIN
    CREATE TABLE MarketingCampaigns (
        CampaignID INT IDENTITY(1,1) PRIMARY KEY,
        CampaignName NVARCHAR(255),
        StartDate DATE,
        EndDate DATE,
        Budget DECIMAL(18,2),
        Conversions INT
    );

    INSERT INTO MarketingCampaigns (CampaignName, StartDate, EndDate, Budget, Conversions) VALUES
    (N'Khuyến mãi tháng 3', '2024-03-01', '2024-03-31', 50000000, 150),
    (N'Xả hàng hè', '2024-04-01', '2024-04-30', 30000000, 80);
END
GO
