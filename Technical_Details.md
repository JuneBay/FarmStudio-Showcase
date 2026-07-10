# FarmStudio - Technical Details

**Project:** FarmStudio (IoT Smart Farm Monitoring System)
**Role:** IoT Systems Developer
**Period:** Jan 2023 - Present
**Repository:** Private
**Local Path:** `c:\JoonBae_Works\FarmStudioDataCollector\`

---

## 📋 Project Overview

A **serverless IoT monitoring system** managing remote farms (100km+ away) using ESP32 sensors, CCTV, and smart switches. It utilizes an **email-based data pipeline** (SMTP/IMAP) to achieve $0 operational costs while ensuring high reliability in unstable network environments.

**Core Value:**
- **Remote Ops:** Real-time monitoring of farms 100km+ away
- **Unmanned:** "Set-and-forget" weekend setup for continuous weekly operation
- **Cost Efficiency:** $0 server cost via Email-as-Backend architecture
- **Maintenance:** Zero-touch maintenance via OTA firmware updates

---

## 🎯 Key Achievements & Metrics

### 1. Operations & Efficiency
- **Remote Control:** Fully unmanned weekly operation
- **Real-Time Data:** Temp, Humidity, Light, Images collected live
- **Alerts:** Instant email notifications for anomalies
- **High Delivery Reliability:** even in unstable rural networks

### 2. Operational Stability
- **OTA Updates:** Remote firmware updates without site visits
- **Data Backup:** Email inbox serves as a persistent backup
- **Self-Healing Data:** Regex normalization + Time-series interpolation for error recovery
- **Multi-Device:** Concurrent management of 5+ ESP32 devices

### 3. Cost Reduction
- **$0 Server Cost:** Replaced cloud IoT brokers with Gmail SMTP/IMAP
- **Low Infra Cost:** Utilized commodity hardware (ESP32, standard CCTV)
- **Maintenance:** Eliminated travel costs via remote OTA

### 4. Data Integration & Resilience
- **Multi-Format:** Parsed CSV, XLSX, and Email Body text
- **Standardization:** Unified schema for heterogeneous sensors
- **Regex Normalization:** Auto-correction of malformed sensor strings
- **Interpolation:** Auto-filling of missing data points
- **Visualization:** Automated graph generation

---

## 🏗️ System Architecture

### System Flow

```
[Remote Farm (100km+)]
   ├─ ESP32 Sensors (Temp/Hum/Light)
   ├─ ESP32-CAM (Images)
   └─ CCTV / Smart Switches
   ↓ (SMTP Email)
[Gmail IMAP Server]
   ↓ (Python Poller)
[Data Collection System]
   ├─ Email Receiver
   ├─ Photo Extractor
   ├─ Data Parser (Regex)
   └─ Data Cleaner
   ↓
[Data Storage]
   ├─ CSV / XLSX
   └─ Images (JPG)
   ↓
[Visualization]
   └─ Graph Generator
```

### Key Technical Implementations

#### 1. Email-Based Data Pipeline
- **SMTP Uplink:** Devices send data as emails (store-and-forward reliability)
- **IMAP Downlink:** Server polls emails to extract data
- **Result:** Highly resilient to network outages; zero cost.

#### 2. Self-Healing Data Mechanism
- **Regex Parsing:** Robust pattern matching to extract data even from malformed strings
- **Interpolation:** Linear interpolation to fill time-series gaps caused by network downtime

#### 3. OTA (Over-The-Air) Updates
- Remote firmware flashing triggered via specific email commands
- Version tracking and rollback capabilities

#### 4. Multi-Device Management
- Scalable design handling multiple ESP32 nodes (Aiden, Charlotte, Hannah, etc.)
- Unified dashboard for all device streams

---

## 💻 Tech Stack

### Hardware
- **ESP32:** Main sensor nodes
- **ESP32-CAM:** Visual monitoring
- **Sensors:** DHT22 (Temp/Hum), BH1750 (Light)

### Backend (Python)
- **imaplib / email:** Email protocol handling
- **pandas:** Data processing and cleaning
- **matplotlib:** Data visualization
- **openpyxl:** Excel report generation

---

## 🔧 Solved Technical Challenges

### 1. Serverless Operations
**Problem:** No budget/infrastructure for dedicated servers.
**Solution:** Repurposed Gmail as a free, reliable IoT backend.
**Result:** $0 operational cost, backed by Google's uptime SLA.

### 2. Unstable Rural Network
**Problem:** Frequent connection drops in remote areas.
**Solution:** Leveraged Email's store-and-forward nature.
**Result:** high data-delivery reliability (devices retry until sent).

### 3. Data Fragility
**Problem:** Sensor errors and string corruption.
**Solution:** Implemented Self-Healing Data (Regex + Interpolation).
**Result:** Continuous data streams despite hardware glitches.

### 4. Remote Maintenance
**Problem:** 100km distance makes physical debugging impossible.
**Solution:** Built OTA update mechanism.
**Result:** Zero physical maintenance trips required for software fixes.

---

## 📊 Performance Comparison

| Metric | Manual / Traditional | FarmStudio (Automated) | Improvement |
|--------|----------------------|------------------------|-------------|
| **Ops Model** | Monthly Site Visits | **Remote Unmanned** | **Fully Remote** |
| **Infra Cost** | Server + DB Fees | **$0** (Email) | **No Server Cost** |
| **Reliability** | Network Dependent | **Store-and-Forward** | **High Reliability** |
| **Maintenance** | On-Site Required | **OTA Remote** | **Cost Reduction** |

---

## 📁 Technical Documents
- **Repository:** Private
- **Local Path:** `c:\JoonBae_Works\FarmStudioDataCollector\`
