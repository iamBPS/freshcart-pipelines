
import json
import gzip
from datetime import datetime, timezone
from pathlib import Path

from config import LANDING_DIR


MOCK_WEB_ORDERS = [
    {
        "order_id": "ORD-1001",
        "cust_email": " Priya.R@Gmail.com ",
        "cust_name": "priya r",
        "order_date": "2026-09-01",
        "amount": "1,250.00",
        "currency": "INR",
        "pincode": "600041",
        "updated_at": "2026-09-01 10:02:00"
    },
    {
        "order_id": "ORD-1003",
        "cust_email": "meera@outlook.com",
        "cust_name": "MEERA S",
        "order_date": "2026-09-02",
        "amount": None,
        "currency": "INR",
        "pincode": "400050",
        "updated_at": "2026-09-02 09:10:00"
    },
    {
        "order_id": "ORD-1002",
        "cust_email": "Arjun.K@Yahoo.in ",
        "cust_name": "Arjun K",
        "order_date": "2026-09-01",
        "amount": "42.50",
        "currency": "USD",
        "pincode": "560034",
        "updated_at": "2026-09-01 11:15:00"
    },
    {
        "order_id": "ORD-1004",
        "cust_email": "rahul.m@gmail.com",
        "cust_name": "Rahul M",
        "order_date": "Sep 3, 2026",
        "amount": "-500",
        "currency": "INR",
        "pincode": "110001",
        "updated_at": "2026-09-03 12:00:00"
    },
    {
        "order_id": "ORD-1005",
        "cust_email": "priya.r@gmail.com",
        "cust_name": "Priya R.",
        "order_date": "2026-09-03",
        "amount": "₹ 899",
        "currency": "inr",
        "pincode": "600041",
        "updated_at": "2026-09-03 16:45:00"
    },
    {
        "order_id": "ORD-1006",
        "cust_email": "vikram@@mail",
        "cust_name": "Vikram",
        "order_date": "2026-09-04",
        "amount": 30,
        "currency": "EUR",
        "pincode": "99999",
        "updated_at": "2026-09-04 08:30:00"
    }
]

MOCK_MOBILE_ORDERS = [
    {
        "orderId": "ORD-1002",
        "customer": {
            "email": "arjun.k@yahoo.in",
            "name": "Arjun K"
        },
        "orderDate": "01/09/2026",
        "total": {
            "value": "42.50",
            "currency": "usd"
        },
        "deliveryPin": "560034",
        "updatedAt": "2026-09-01T11:15:00"
    },
    {
        "orderId": "ORD-1003",
        "customer": {
            "email": "Meera@Outlook.com",
            "name": "Meera S"
        },
        "orderDate": "02/09/2026",
        "total": {
            "value": "2,100.00",
            "currency": "INR"
        },
        "deliveryPin": "400050",
        "updatedAt": "2026-09-02T18:40:00"
    }
]

MOCK_CRM_TIER_EVENTS = [
    {
        "cust_id": "CUST-01",
        "email": "priya.r@gmail.com",
        "tier": "Silver",
        "effective_from": "2023-04-10"
    },
    {
        "cust_id": "CUST-01",
        "email": "priya.r@gmail.com",
        "tier": "Gold",
        "effective_from": "2026-09-03"
    },
{
    "cust_id": "CUST-02",
    "email": "arjun.k@yahoo.in",
    "tier": "Gold",
    "effective_from": "2026-08-15"
},
   
    {
        "cust_id": "CUST-03",
        "email": "meera@outlook.com",
        "tier": "Platinum",
        "effective_from": "2022-11-01"
    }
]

MOCK_FX_RESPONSES = [
    {
        "amount": 1.0,
        "base": "USD",
        "start_date": "2026-09-01",
        "end_date": "2026-09-03",
        "rates": {
            "2026-09-01": {"INR": 83.20},
            "2026-09-02": {"INR": 83.35},
            "2026-09-03": {"INR": 83.10}
        }
    }
]

MOCK_PINCODES = {
    "600041": ("Chennai", "Tamil Nadu"),
    "560034": ("Bengaluru", "Karnataka"),
    "400050": ("Mumbai", "Maharashtra")
}


def write_landing(source, records, run_id):
    """Write untouched API records as compressed JSON Lines."""
    folder = LANDING_DIR / source
    folder.mkdir(parents=True, exist_ok=True)

    path = folder / f"{source}__{run_id}.json.gz"
    extracted_at = datetime.now(timezone.utc).isoformat()

    with gzip.open(path, "wt", encoding="utf-8") as file:
        for record in records:
            envelope = {
                "source": source,
                "run_id": run_id,
                "extracted_at": extracted_at,
                "data": record
            }
            file.write(json.dumps(envelope, ensure_ascii=False) + "\n")

    print(f"{source}: {len(records)} records saved")
    return path



def extract_all(run_id):
    """Extract all FreshCart mock API sources."""
    pincode_records = [
        {
            "pincode": pin,
            "city": details[0],
            "state": details[1]
        }
        for pin, details in MOCK_PINCODES.items()
    ]

    return {
        "web": write_landing("web", MOCK_WEB_ORDERS, run_id),
        "mobile": write_landing("mobile", MOCK_MOBILE_ORDERS, run_id),
        "crm": write_landing("crm", MOCK_CRM_TIER_EVENTS, run_id),
        "fx": write_landing("fx", MOCK_FX_RESPONSES, run_id),
        "pincode": write_landing("pincode", pincode_records, run_id)
    }
