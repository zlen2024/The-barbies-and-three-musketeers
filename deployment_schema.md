# Deployment Database Schema (T-SQL)

The following Transact-SQL (T-SQL) script can be used to set up the deployment database and create all required tables.

```sql
-- 1. Users Table
CREATE TABLE users (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(100) NOT NULL UNIQUE,
    email NVARCHAR(200) UNIQUE,
    role NVARCHAR(50) NOT NULL,
    password_hash NVARCHAR(200) NOT NULL
);

-- 2. Core Data (Products & Locations)
CREATE TABLE product (
    product_id INT IDENTITY(1,1) PRIMARY KEY,
    model_code NVARCHAR(100) NOT NULL UNIQUE,
    category NVARCHAR(100),
    brand NVARCHAR(100),
    status NVARCHAR(50),
    product_name NVARCHAR(200)
);

CREATE TABLE location (
    location_id INT IDENTITY(1,1) PRIMARY KEY,
    loc_code NVARCHAR(50) NOT NULL UNIQUE,
    description NVARCHAR(200),
    type NVARCHAR(50),
    address NVARCHAR(500),
    region NVARCHAR(100)
);

CREATE TABLE user_location (
    ul_id INT IDENTITY(1,1) PRIMARY KEY,
    uid INT NOT NULL,
    location_id INT NOT NULL,
    CONSTRAINT FK_user_location_users FOREIGN KEY (uid) REFERENCES users(user_id),
    CONSTRAINT FK_user_location_location FOREIGN KEY (location_id) REFERENCES location(location_id)
);

CREATE TABLE product_loc (
    pl_id INT IDENTITY(1,1) PRIMARY KEY,
    product_id INT NOT NULL,
    location_id INT NOT NULL,
    quantity_on_hand INT DEFAULT 0,
    last_updated DATETIME2 DEFAULT GETUTCDATE(),
    updated_by INT,
    CONSTRAINT FK_product_loc_product FOREIGN KEY (product_id) REFERENCES product(product_id),
    CONSTRAINT FK_product_loc_location FOREIGN KEY (location_id) REFERENCES location(location_id),
    CONSTRAINT FK_product_loc_users FOREIGN KEY (updated_by) REFERENCES users(user_id)
);

-- 3. Supply Chain (Vendors & Ordering)
CREATE TABLE vendor (
    vendor_id INT IDENTITY(1,1) PRIMARY KEY,
    vendor_name NVARCHAR(200) NOT NULL,
    contact_person NVARCHAR(100),
    phone_number NVARCHAR(50),
    is_overseas BIT DEFAULT 0
);

CREATE TABLE product_vendor (
    pv_id INT IDENTITY(1,1) PRIMARY KEY,
    product_id INT NOT NULL,
    vendor_id INT NOT NULL,
    cost_price FLOAT,
    lead_time_days INT,
    CONSTRAINT FK_product_vendor_product FOREIGN KEY (product_id) REFERENCES product(product_id),
    CONSTRAINT FK_product_vendor_vendor FOREIGN KEY (vendor_id) REFERENCES vendor(vendor_id)
);

CREATE TABLE product_order (
    order_id INT IDENTITY(1,1) PRIMARY KEY,
    pv_id INT NOT NULL,
    ul_id INT NOT NULL,
    po_reference NVARCHAR(50),
    order_qty INT NOT NULL,
    ets_date DATETIME2,
    status NVARCHAR(50),
    confirmation_status NVARCHAR(50) DEFAULT 'Pending',
    created_by INT,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    CONSTRAINT FK_product_order_product_vendor FOREIGN KEY (pv_id) REFERENCES product_vendor(pv_id),
    CONSTRAINT FK_product_order_user_location FOREIGN KEY (ul_id) REFERENCES user_location(ul_id),
    CONSTRAINT FK_product_order_users FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- 4. Sales & Pricing
CREATE TABLE pricing (
    pricing_id INT IDENTITY(1,1) PRIMARY KEY,
    product_id INT NOT NULL,
    lsp_price FLOAT,
    wm_price FLOAT,
    em_price FLOAT,
    effective_date DATETIME2 DEFAULT GETUTCDATE(),
    CONSTRAINT FK_pricing_product FOREIGN KEY (product_id) REFERENCES product(product_id)
);

CREATE TABLE campaign (
    campaign_id INT IDENTITY(1,1) PRIMARY KEY,
    pricing_id INT NOT NULL,
    campaign_name NVARCHAR(200),
    gift_item NVARCHAR(200),
    start_date DATETIME2,
    end_date DATETIME2,
    CONSTRAINT FK_campaign_pricing FOREIGN KEY (pricing_id) REFERENCES pricing(pricing_id)
);

CREATE TABLE sale (
    sale_id INT IDENTITY(1,1) PRIMARY KEY,
    sale_date DATETIME2 DEFAULT GETUTCDATE(),
    customer_name NVARCHAR(200),
    client_email NVARCHAR(200),
    sold_by INT,
    location_id INT,
    status NVARCHAR(50) DEFAULT 'Paid',
    total_amount FLOAT DEFAULT 0.0,
    CONSTRAINT FK_sale_users FOREIGN KEY (sold_by) REFERENCES users(user_id),
    CONSTRAINT FK_sale_location FOREIGN KEY (location_id) REFERENCES location(location_id)
);

CREATE TABLE sale_item (
    si_id INT IDENTITY(1,1) PRIMARY KEY,
    sale_id INT NOT NULL,
    pl_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price FLOAT NOT NULL,
    subtotal FLOAT NOT NULL,
    CONSTRAINT FK_sale_item_sale FOREIGN KEY (sale_id) REFERENCES sale(sale_id),
    CONSTRAINT FK_sale_item_product_loc FOREIGN KEY (pl_id) REFERENCES product_loc(pl_id)
);

CREATE TABLE invoice (
    invoice_id INT IDENTITY(1,1) PRIMARY KEY,
    sale_id INT NOT NULL,
    invoice_number NVARCHAR(100) NOT NULL UNIQUE,
    generated_date DATETIME2 DEFAULT GETUTCDATE(),
    total_amount FLOAT NOT NULL,
    CONSTRAINT FK_invoice_sale FOREIGN KEY (sale_id) REFERENCES sale(sale_id)
);

-- 5. Forecast
CREATE TABLE forecast (
    id INT IDENTITY(1,1) PRIMARY KEY,
    product_id INT,
    projected_demand INT,
    confidence_score FLOAT,
    smart_why_rationale NVARCHAR(MAX),
    forecast_data NVARCHAR(MAX),
    last_updated DATETIME2 DEFAULT GETUTCDATE(),
    CONSTRAINT FK_forecast_product FOREIGN KEY (product_id) REFERENCES product(product_id)
);

-- 6. Internal Mail
CREATE TABLE internal_mail (
    mail_id INT IDENTITY(1,1) PRIMARY KEY,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    subject NVARCHAR(200),
    body NVARCHAR(MAX),
    timestamp DATETIME2 DEFAULT GETUTCDATE(),
    is_read BIT DEFAULT 0,
    CONSTRAINT FK_internal_mail_sender FOREIGN KEY (sender_id) REFERENCES users(user_id),
    CONSTRAINT FK_internal_mail_receiver FOREIGN KEY (receiver_id) REFERENCES users(user_id)
);
```