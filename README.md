> ## 📦 ARCHIVED — 통합되었습니다 / Consolidated
>
> **이 Showcase 레포는 [`JuneBay/JuneBay`](https://github.com/JuneBay) 메인 포트폴리오로 통합되었습니다.**
> This Showcase repo has been consolidated into the [`JuneBay/JuneBay`](https://github.com/JuneBay) main portfolio.
>
> 👉 **케이스 스터디 / Case study**: [projects/farm-studio.md](https://github.com/JuneBay/JuneBay/blob/main/projects/farm-studio.md)
> 👉 **외주 문의 / Project inquiries**: [Upwork](https://www.upwork.com/freelancers/~01b49808a51af3b53c) · [Fiverr](https://www.fiverr.com/sellers/junebay) · [크몽](https://kmong.com/@JuneBay) · [위시켓](https://www.wishket.com/partners/p/somster/)
>
> *(이 레포는 history 보존을 위해 archive 처리되었습니다 / Archived for history preservation.)*

---

# FarmStudio — Architecture Showcase

**Remote IoT Monitoring System | SMTP-as-Backend**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-junebay-blue?style=flat&logo=linkedin)](https://linkedin.com/in/junebay)

---

## Overview

Serverless IoT data collection system for remote farm monitoring. Collects sensor and image data from 5 ESP32 devices located 100km+ away, using email (SMTP/IMAP) as the data transport layer — no dedicated server infrastructure.

Running continuously for **3+ years** at **$0/month**.

### At a Glance

| Item | Detail |
|------|--------|
| **Devices** | 5 ESP32 modules |
| **Distance** | 100km+ remote |
| **Transport** | SMTP/IMAP (email-based pipeline) |
| **Server Cost** | $0/month |
| **Uptime** | 3+ years continuous |
| **Data Reliability** | >99% delivery rate |
| **Status** | Production, actively running |

---

## Architecture

```
┌──────────────┐     SMTP      ┌──────────────┐
│  ESP32 #1    │──────────────▶│              │
│  ESP32 #2    │──────────────▶│   Gmail      │
│  ESP32 #3    │──────────────▶│   (SMTP)     │
│  ESP32 #4    │──────────────▶│              │
│  ESP32 #5    │──────────────▶│              │
└──────────────┘               └──────┬───────┘
                                      │ IMAP
                               ┌──────▼───────┐
                               │  Data Parser │
                               │  (Python)    │
                               │  - Regex     │
                               │  - Normalize │
                               │  - Interpolate│
                               └──────┬───────┘
                                      │
                               ┌──────▼───────┐
                               │  Dashboard   │
                               │  (Streamlit) │
                               └──────────────┘
```

**Why email?**
- ESP32 can send SMTP natively — no custom protocol needed
- Gmail provides free, reliable store-and-forward
- Works in unstable rural networks where HTTP connections drop
- Zero server costs, zero maintenance

---

## Key Technical Decisions

### SMTP-as-Backend
- Email as asynchronous, resilient data transport
- Store-and-forward: data survives network outages automatically
- No server to maintain, no database to manage
- Result: **$0/month infrastructure** for 3+ years

### Self-Healing Data Pipeline
- Regex normalization handles inconsistent sensor output formats
- Time-series interpolation fills gaps from missed transmissions
- Multi-format sensor data standardized into unified schema

### OTA Firmware Updates
- Remote firmware deployment to devices 100km+ away
- Zero-touch maintenance — no physical site visits required

### Network Resilience
- >99% data delivery rate in unstable rural environments
- Automatic retry built into SMTP protocol
- No dependency on stable HTTP connections

---

## Tech Stack

- **ESP32** — sensor data collection, SMTP transmission
- **Python** — data parsing, normalization, interpolation
- **Streamlit** — monitoring dashboard
- **SMTP/IMAP** — data transport layer (Gmail)
- **Flask** — lightweight API endpoints

---

## Related

- **Profile**: [github.com/JuneBay](https://github.com/JuneBay)
- **LinkedIn**: [linkedin.com/in/junebay](https://linkedin.com/in/junebay)

- **Web**: [macrobay.kr](https://macrobay.kr)
