# **Project 02: E-Commerce KPI Dashboard (ETL + AWS Cloud Deployment)**

*A complete analytics workflow demonstrating ETL engineering, KPI computation, and cloud deployment.*

---

# **1. Executive Overview**

This project performs end-to-end analytics on an online retail (e-commerce) dataset using:

* **Python ETL** (`src/preprocess.py`)
* **KPI calculations:** daily metrics, product performance, RFM segmentation
* **Interactive BI dashboard:** Streamlit (`src/dashboard/app.py`)
* **Cloud deployment:** AWS EC2 Free Tier (t2.micro) + S3

The purpose is to demonstrate capability in:

* **ETL / Data engineering**
* **Analytical modelling**
* **Cloud architecture (AWS)**
* **Dashboard development**
* **Production readiness and reproducibility**

No paid AWS services are used — **100% free-tier compatible**.

---

# **📁 2. Repository Structure**

```
project-02-kpi-dashboard/
│
├── data/
│   ├── raw/               # input datasets (ignored by git)
│   └── processed/         # ETL outputs (CSV)
│
├── src/
│   ├── preprocess.py      # canonical ETL + KPI computation
│   ├── dashboard/
│   │   └── app.py         # Streamlit dashboard
│   └── venv/              # virtual environment (ignored by git)
│
├── notebooks/
│   └── 01_eda_kpis.ipynb
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

# **3. ETL Pipeline Overview**

### 🔧 **ETL Entry Point:**

```
python -m src.preprocess --raw data/raw/online_retail.csv --out data/processed --steps all
```

### 🧱 **Pipeline Steps (in preprocess.py)**

| Step                             | Description                                                                 |
| -------------------------------- | --------------------------------------------------------------------------- |
| **1. Defensive CSV Loader**      | Handles broken date formats, encoding issues, missing columns               |
| **2. Canonical Transform**       | Standardises dtypes, parses dates, creates LineTotal, detects cancellations |
| **3. Data Quality Checks**       | Identifies negative revenue, missing CustomerID, malformed invoices         |
| **4. Daily KPI Computation**     | tx counts, revenue, AOV, cancellations                                      |
| **5. Product-Level Aggregation** | revenue leaders, quantity leaders, meta-SKU detection                       |
| **6. RFM Segmentation**          | recency, frequency, monetary, quartile scoring                              |
| **7. Exports**                   | CSV outputs for dashboard consumption                                       |

### 📤 ETL Output Files (data/processed/):

| File                         | Purpose                                 |
| ---------------------------- | --------------------------------------- |
| **sample_kpis.csv**          | First 500 clean operational rows for QA |
| **daily_kpis.csv**           | Daily-level business metrics            |
| **top_products_summary.csv** | SKU-level revenue + volume insights     |
| **rfm_customers.csv**        | Segmented customer table                |

---

# **📊 4. Dashboard (Streamlit) Overview**

The dashboard reads ETL outputs from `data/processed/` and exposes:

### **KPIs**

* Total revenue
* Total transactions
* Total customers
* Cancellation rate

### **Visuals**

* Daily trends (tx, revenue, AOV)
* Top products (revenue & quantity), with description roll-ups
* RFM segmentation charts
* Downloadable CSVs for each panel

### Run Locally

```
streamlit run src/dashboard/app.py
```

---

# **☁️ 5. AWS Deployment — Using AWS Console (No CLI Required)**

This is the detailed, portfolio-quality walkthrough showing your **AWS Solutions Architect** skills.

---

# **5.1 Architecture Diagram (ASCII)**

```
+-------------------------+
|      Laptop / User      |
+-----------+-------------+
            |
            v
+-----------+-------------+
|      AWS EC2 (t2.micro) |  <-- runs Streamlit on port 8501
| Ubuntu 22.04 + Python   |
+-----------+-------------+
            |
            v
+-----------+-------------+
|       S3 Bucket         |  <-- stores processed CSVs
| data/processed/*.csv    |
+-------------------------+
```

---

# **5.2 Create S3 Bucket (Console)**

1. Go to **S3 Console → Create Bucket**
2. Name: `project02-kpi-yourname`
3. Region: same as EC2 (e.g., **us-east-1**)
4. Block public access: **ON** (default)
5. Create bucket
6. Upload folder:

   ```
   data/processed/
   ```

---

# **5.3 Create IAM Role for EC2**

1. Go to **IAM → Roles → Create Role**
2. Select: **EC2**
3. Attach policies:

   * `AmazonS3ReadOnlyAccess`
4. Name the role: **EC2_Project02_S3ReadOnly**
5. Create role.

---

# **5.4 Launch EC2 Instance**

1. AWS Console → EC2 → Launch Instance
2. Name: **Project02-KPI-Dashboard**
3. Amazon Machine Image: **Ubuntu 22.04 LTS**
4. Instance type: **t2.micro (Free Tier)**
5. IAM Role: **EC2_Project02_S3ReadOnly**
6. Storage: default (8GB)
7. Security Group:

   * Allow port **22** (SSH)
   * Allow port **8501** (Streamlit)
   * Allow port **80** (if using nginx reverse proxy later)
8. Launch and download Key Pair.

---

# **5.5 Connect to EC2 & Install Dependencies**

```bash
ssh -i yourkey.pem ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com
```

### Install Python

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv
```

### Create project directory

```bash
mkdir project02 && cd project02
```

### Pull from GitHub

```bash
git clone https://github.com/yourusername/project-02-kpi-dashboard.git .
```

### Create venv

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install requirements

```bash
pip install -r requirements.txt
```

---

# **5.6 Make Streamlit App Use S3 Instead of Local Files**

Modify your `app.py` so it loads:

```python
import pandas as pd
import s3fs

fs = s3fs.S3FileSystem()

daily = pd.read_csv("s3://project02-kpi-yourname/daily_kpis.csv", storage_options={'anon': False})
products = pd.read_csv("s3://project02-kpi-yourname/top_products_summary.csv", storage_options={'anon': False})
rfm = pd.read_csv("s3://project02-kpi-yourname/rfm_customers.csv", storage_options={'anon': False})
```

The EC2 IAM Role automatically authorises S3 reads.

---

# **5.7 Run Streamlit App on EC2**

```bash
streamlit run src/dashboard/app.py --server.port 8501 --server.address 0.0.0.0
```

Visit:

```
http://ec2-xx-xx-xx-xx.compute.amazonaws.com:8501
```

---

# **5.8 Run Streamlit Permanently (systemd Service)**

Create service file:

```bash
sudo nano /etc/systemd/system/streamlit.service
```

Paste:

```ini
[Unit]
Description=Streamlit Dashboard
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/project02
Environment="PATH=/home/ubuntu/project02/venv/bin"
ExecStart=/home/ubuntu/project02/venv/bin/streamlit run src/dashboard/app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable streamlit
sudo systemctl start streamlit
sudo systemctl status streamlit
```

Now your dashboard runs **24/7** like a real production service.

---

# **5.9 Free-Tier Cost Controls**

| Service       | Cost                 |
| ------------- | -------------------- |
| EC2 t2.micro  | Free 750 hours/month |
| S3 Storage    | First 5GB free       |
| Data transfer | Free to your browser |
| IAM Role      | Free                 |

Turn off EC2 to avoid charges:

```bash
sudo shutdown now
```

---

# **6. KPI Examples Demonstrated in Dashboard**

### 💰 **Daily Metrics**

* Revenue trend
* Cancellation trend
* Transaction volumes
* Average Order Value (AOV)

### 📦 **Top Products**

* Revenue leaders
* Quantity leaders
* Meta-SKU filtering
* SKU roll-ups by description

### 🧍 **Customer Analytics**

* RFM segmentation
* Identification of high-value customers
* Recency distribution (cohort-like)

---

# **7. How This Project Demonstrates Real Industry Skills**

### ✔ Data Engineering

* Defensive CSV parsing
* Canonical transformations
* Normalised analytic datasets
* Scripted ETL Runner (`preprocess.py`)
* Logging & error handling

### ✔ Analytics Engineering

* KPI design
* Cohort-like recency metrics
* Product-level modelling
* RFM segmentation

### ✔ Cloud Architecture (AWS)

* IAM role design
* EC2 setup & networking
* S3 integration
* Production service with systemd

### ✔ BI Engineering

* Streamlit interactive dashboard
* Multi-panel analytics
* Optimised tables and charts

---

# **8. Reproducing Everything Locally**

### 1. Create venv

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install requirements

```bash
pip install -r requirements.txt
```

### 3. Run ETL

```bash
python -m src.preprocess --raw data/raw/online_retail.csv --out data/processed --steps all
```

### 4. Run Dashboard

```bash
streamlit run src/dashboard/app.py
```

---

# **9. Future Enhancements**

* Replace EC2 with **AWS Lightsail** (still free-tier compatible)
* Serve dashboard via **Nginx reverse proxy + SSL**
* Add **customer lifetime value (CLV)** model
* Introduce **Airflow** for scheduled ETL
* Store processed outputs in **Parquet** for efficiency
