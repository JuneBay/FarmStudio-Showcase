"""
FarmStudio - Core IoT Data Pipeline Logic

This file demonstrates the architectural patterns used in FarmStudio:
- Email-based asynchronous data collection
- Multi-format sensor data parsing
- Data standardization and cleaning
- Error handling and quality flags

These patterns enable zero-cost infrastructure while maintaining long-term operational stability.
"""

import re
import imaplib
import email
from email.header import decode_header, make_header
from email.message import Message
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np


# ============================================================================
# MULTI-FORMAT EMAIL PARSING
# ============================================================================

# Regex patterns for different data formats
DICT_LINE = re.compile(r"\{.*\}", re.DOTALL)
KV_FLOAT = re.compile(
    r"\b([A-Za-z][A-Za-z0-9_ ]{0,31})\s*[:=]\s*(-?\d+(?:\.\d+)?)\b"
)


def parse_text_body_to_record(body: str, fallback_dt: datetime) -> Optional[Dict]:
    """
    Parses sensor data from email body supporting multiple formats.
    
    Architecture Pattern: Flexible parsing enables handling heterogeneous
    device formats without requiring device firmware standardization.
    
    Supported formats:
    1. Dictionary string: {'Date': '2025-10-28', 'Time': '01:26:18', 'Location1': 15.4, ...}
    2. Key-value pairs: Location1: 32.0, Location2: 15.0, Temperature: 25.5 ...
    
    @param body: Email body text
    @param fallback_dt: Fallback datetime if not found in body
    @returns: Parsed record dictionary or None
    
    Example:
        body = "Time: 2025/12/16 10:40:45\\nHumidity: 58.70 %\\nTemperature: 8.60 °C"
        record = parse_text_body_to_record(body, datetime.now())
        # Returns: {'Date': '2025-12-16', 'Time': '10:40:45', 'Humidity': 58.70, 'Temperature': 8.60}
    """
    body1 = body.strip()
    
    # Format 1: Dictionary string parsing
    m = DICT_LINE.search(body1)
    if m:
        text = m.group(0)
        # Extract key-value pairs from dictionary string
        kv_pairs = re.findall(
            r"'([^']+)'\s*:\s*'([^']*)'|\"([^\"]+)\"\s*:\s*\"([^\"]*)\"|([A-Za-z0-9_]+)\s*:\s*(-?\d+(?:\.\d+)?)",
            text
        )
        rec_raw = {}
        for pair in kv_pairs:
            if pair[0] and pair[1]:
                key, val = pair[0], pair[1]
            elif pair[2] and pair[3]:
                key, val = pair[2], pair[3]
            else:
                key, val = pair[4], pair[5]
            # Convert numeric strings to float
            if re.fullmatch(r"-?\d+(?:\.\d+)?", val or ""):
                val = float(val)
            rec_raw[key.strip()] = val
        
        # Extract date/time from parsed data
        dt_local = fallback_dt
        date_s = str(rec_raw.get("Date", "")).strip()
        time_s = str(rec_raw.get("Time", "")).strip()
        if date_s and time_s:
            try:
                dt_local = datetime.fromisoformat(f"{date_s} {time_s}")
            except Exception:
                pass
        
        # Build standardized output
        out = {
            "Date": dt_local.strftime("%Y-%m-%d"),
            "Time": dt_local.strftime("%H:%M:%S"),
            "DateTime": dt_local.strftime("%Y-%m-%d %H:%M:%S")
        }
        # Add sensor readings (excluding Date/Time)
        for k, v in rec_raw.items():
            if k in ("Date", "Time"):
                continue
            out[k] = v
        return out
    
    # Format 2: Key-value pair parsing
    kvs = dict()
    for k, v in KV_FLOAT.findall(body1.replace(",", " ")):
        key = k.strip().replace(" ", "_")
        try:
            val = float(v)
        except Exception:
            continue
        kvs[key] = val
    
    if kvs:
        # Prevent Time/Date from being parsed as numeric values
        kvs.pop("Time", None)
        kvs.pop("Date", None)
        dt_local = fallback_dt
        base = {
            "Date": dt_local.strftime("%Y-%m-%d"),
            "Time": dt_local.strftime("%H:%M:%S"),
            "DateTime": dt_local.strftime("%Y-%m-%d %H:%M:%S"),
        }
        base.update(kvs)  # Date/Time from header takes precedence
        return base
    
    return None


def get_msg_body(msg: Message) -> str:
    """
    Extracts text body from email message (handles multipart).
    
    Architecture Pattern: Robust email parsing handles various
    email formats and encodings without failing.
    
    @param msg: Email message object
    @returns: Decoded email body text
    """
    if msg.is_multipart():
        # Walk through multipart message
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "").lower()
            # Extract text/plain part (not attachment)
            if ctype == "text/plain" and "attachment" not in disp:
                charset = part.get_content_charset() or "utf-8"
                try:
                    return part.get_payload(decode=True).decode(charset, errors="replace")
                except Exception:
                    return part.get_payload(decode=True).decode("utf-8", errors="replace")
        # Fallback: last part
        part = msg.get_payload()[-1]
        charset = part.get_content_charset() or "utf-8"
        return part.get_payload(decode=True).decode(charset, errors="replace")
    else:
        # Single-part message
        charset = msg.get_content_charset() or "utf-8"
        payload = msg.get_payload(decode=True)
        if payload is None:
            return msg.get_payload()
        return payload.decode(charset, errors="replace")


def parse_date_from_header(msg: Message) -> Optional[datetime]:
    """
    Extracts datetime from email header.
    
    @param msg: Email message object
    @returns: Parsed datetime or None
    """
    try:
        dt = parsedate_to_datetime(msg["Date"])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone()
    except Exception:
        return None


# ============================================================================
# DATA STANDARDIZATION AND CLEANING
# ============================================================================

def combine_and_clean(df_old: pd.DataFrame, df_new: pd.DataFrame) -> pd.DataFrame:
    """
    Combines old and new dataframes with cleaning and standardization.
    
    Architecture Pattern: Automatic data cleaning ensures data quality
    without manual intervention, enabling long-term unattended operation.
    
    Cleaning steps:
    1. Convert to numeric where possible
    2. Remove duplicates (based on DateTime)
    3. Standardize error values (-127 → NaN)
    4. Sort by time for interpolation
    5. Forward-fill and backward-fill missing values
    6. Sort by time descending (most recent first)
    
    @param df_old: Existing dataframe
    @param df_new: Newly parsed dataframe
    @returns: Combined and cleaned dataframe
    
    Example:
        old_df = pd.DataFrame({'DateTime': ['2025-01-01 10:00'], 'Temperature': [25.0]})
        new_df = pd.DataFrame({'DateTime': ['2025-01-01 11:00'], 'Temperature': [-127.0]})
        cleaned = combine_and_clean(old_df, new_df)
        # Returns: DataFrame with -127 converted to NaN and filled
    """
    # Merge column sets
    all_cols = list(dict.fromkeys(
        ["Date", "Time", "DateTime"] + 
        list(df_old.columns) + 
        list(df_new.columns)
    ))
    df_old = df_old.reindex(columns=all_cols)
    df_new = df_new.reindex(columns=all_cols)
    
    # Combine dataframes
    df = pd.concat([df_old, df_new], ignore_index=True)
    
    # Convert to numeric where possible
    for c in df.columns:
        if c in ("Date", "Time", "DateTime"):
            continue
        try:
            df[c] = pd.to_numeric(df[c])
        except Exception:
            pass
    
    # Remove duplicates (keep most recent)
    if "DateTime" in df.columns:
        df.drop_duplicates(subset=["DateTime"], keep="last", inplace=True)
    
    # Standardize error values: -127 → NaN
    # (ESP32 sensors return -127 on error)
    num_cols = [c for c in df.columns if c not in ("Date", "Time", "DateTime")]
    for c in num_cols:
        if pd.api.types.is_numeric_dtype(df[c]):
            df.loc[df[c] == -127, c] = np.nan
    
    # Sort by time for interpolation
    if "DateTime" in df.columns:
        df["_dt"] = pd.to_datetime(df["DateTime"], errors="coerce")
        df.sort_values("_dt", inplace=True)
    
    # Forward-fill then backward-fill missing values
    # This handles sensor errors and temporary disconnections
    for c in num_cols:
        if pd.api.types.is_numeric_dtype(df[c]):
            df[c] = df[c].ffill().bfill()
    
    # Final sort: most recent first
    if "_dt" in df.columns:
        df.sort_values("_dt", ascending=False, inplace=True)
        df.drop(columns=["_dt"], inplace=True)
    
    df.reset_index(drop=True, inplace=True)
    return df


# ============================================================================
# IMAP EMAIL RETRIEVAL
# ============================================================================

def imap_connect(host: str, user: str, password: str, mailbox: str = "INBOX") -> imaplib.IMAP4_SSL:
    """
    Connects to IMAP server and selects mailbox.
    
    Architecture Pattern: Email-based transport eliminates need for
    dedicated message queue infrastructure.
    
    @param host: IMAP server hostname
    @param user: Email username
    @param password: Email password (app password for Gmail)
    @param mailbox: Mailbox name (default: "INBOX")
    @returns: IMAP connection object
    """
    print("📬 IMAP connecting...")
    M = imaplib.IMAP4_SSL(host)
    M.login(user, password)
    M.select(mailbox)
    return M


def imap_search_subject_any(M: imaplib.IMAP4_SSL, subjects: List[str]) -> List[bytes]:
    """
    Searches for emails matching any of the given subjects.
    
    Architecture Pattern: Subject-based filtering enables device-specific
    email routing without complex message routing infrastructure.
    
    @param M: IMAP connection
    @param subjects: List of subject strings to search for
    @returns: List of message IDs (bytes)
    
    Example:
        msg_ids = imap_search_subject_any(M, ["ESP32-Hannah - Data Report"])
        # Returns: [b'123', b'124', b'125']
    """
    found = set()
    for s in subjects:
        crit = f'(SUBJECT "{s}")'
        status, data = M.search(None, crit)
        if status == "OK":
            ids = data[0].split()
            for i in ids:
                found.add(i)
    return sorted(list(found), key=lambda x: int(x))


def imap_fetch_message(M: imaplib.IMAP4_SSL, msg_id: bytes) -> Tuple[Message, bytes]:
    """
    Fetches email message and extracts UID.
    
    @param M: IMAP connection
    @param msg_id: Message ID
    @returns: Tuple of (Message object, UID)
    """
    status, data = M.fetch(msg_id, "(RFC822 UID)")
    if status != "OK" or not data or data[0] is None:
        raise RuntimeError("IMAP fetch failed")
    
    # Extract raw email bytes
    raw = None
    for part in data:
        if isinstance(part, tuple):
            if len(part) >= 2 and isinstance(part[1], (bytes, bytearray)):
                raw = part[1]
                break
        elif isinstance(part, (bytes, bytearray)):
            raw = part
    if raw is None:
        raw = data[0][1]
    
    msg = email.message_from_bytes(raw)
    
    # Extract UID
    uid = None
    for item in data:
        seq = item if isinstance(item, tuple) else (item,)
        for p in seq:
            try:
                if isinstance(p, (bytes, bytearray)):
                    m = re.search(rb"UID\s+(\d+)", p)
                    if m:
                        uid = m.group(1)
                        break
            except Exception:
                continue
        if uid:
            break
    
    return msg, uid or b""


# ============================================================================
# DEVICE PROCESSING PIPELINE
# ============================================================================

def process_device_emails(
    M: imaplib.IMAP4_SSL,
    device_name: str,
    subjects: List[str],
    existing_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Processes emails for a specific device and returns updated dataframe.
    
    Architecture Pattern: Device-specific processing enables handling
    heterogeneous device formats while maintaining unified output schema.
    
    @param M: IMAP connection
    @param device_name: Device identifier (e.g., "Hannah")
    @param subjects: Email subjects to search for
    @param existing_df: Existing dataframe to merge with
    @returns: Updated dataframe with new records
    
    Example:
        df = pd.DataFrame(columns=['Date', 'Time', 'DateTime', 'Temperature'])
        df = process_device_emails(M, "Hannah", ["ESP32-Hannah - Data Report"], df)
    """
    # Search for device emails
    msg_ids = imap_search_subject_any(M, subjects)
    print(f"🔎 [{device_name}] Found {len(msg_ids)} emails")
    
    new_records = []
    
    for idx, mid in enumerate(msg_ids, 1):
        try:
            # Fetch email
            msg, uid = imap_fetch_message(M, mid)
            
            # Extract datetime from header
            dt_local = parse_date_from_header(msg) or datetime.now().astimezone()
            
            # Extract body
            body = get_msg_body(msg)
            
            # Parse sensor data
            rec = parse_text_body_to_record(body, dt_local)
            if rec:
                print(f"📄 [{device_name}] {rec.get('Date','')} {rec.get('Time','')} | {rec}")
                new_records.append(rec)
        
        except Exception as e:
            print(f"⚠️ [{device_name}] Parse error on msg {mid}: {e}")
    
    # Create dataframe from new records
    df_new = pd.DataFrame(new_records) if new_records else pd.DataFrame(
        columns=["Date", "Time", "DateTime"]
    )
    
    # Combine and clean
    df_combined = combine_and_clean(existing_df, df_new)
    
    return df_combined


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("FarmStudio - IoT Data Pipeline Examples")
    print("=" * 80)
    
    # Example 1: Parse email body
    print("\n1. Email Body Parsing:")
    print("-" * 80)
    
    sample_body = """
    Time: 2025/12/16 10:40:45
    Internal IP: 192.168.0.102
    LDR: 14
    Humidity: 58.70 %
    Temperature (DHT): 8.60 °C
    Temperature (Waterproof): 7.56 °C
    """
    
    record = parse_text_body_to_record(sample_body, datetime.now())
    if record:
        print("✅ Parsed record:")
        for key, value in record.items():
            print(f"   {key}: {value}")
    
    # Example 2: Data cleaning
    print("\n2. Data Cleaning:")
    print("-" * 80)
    
    old_df = pd.DataFrame({
        'DateTime': ['2025-01-01 10:00:00', '2025-01-01 11:00:00'],
        'Temperature': [25.0, 24.5],
        'Humidity': [60.0, 61.0]
    })
    
    new_df = pd.DataFrame({
        'DateTime': ['2025-01-01 12:00:00', '2025-01-01 13:00:00'],
        'Temperature': [-127.0, 26.0],  # -127 is sensor error
        'Humidity': [62.0, -127.0]
    })
    
    cleaned_df = combine_and_clean(old_df, new_df)
    print("✅ Cleaned dataframe:")
    print(cleaned_df.to_string())
    print(f"\n   -127 values converted to NaN and filled")
    print(f"   Duplicates removed")
    print(f"   Sorted by DateTime (most recent first)")
    
    print("\n" + "=" * 80)
    print("✅ Examples completed")
    print("=" * 80)

# Export for use in other modules
__all__ = [
    'parse_text_body_to_record',
    'get_msg_body',
    'parse_date_from_header',
    'combine_and_clean',
    'imap_connect',
    'imap_search_subject_any',
    'imap_fetch_message',
    'process_device_emails'
]
