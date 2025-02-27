from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, timedelta
import math

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

class LoanDetails(BaseModel):
    disbursement_date: date
    principal: float
    tenure: int  # in months
    emi_frequency: str  # 'monthly', 'quarterly'
    interest_rate: float  # annual interest rate
    moratorium_period: int  # in months

def calculate_emi(principal, interest_rate, tenure):
    monthly_rate = (interest_rate / 100) / 12
    if monthly_rate == 0:
        return principal / tenure
    emi = (principal * monthly_rate * math.pow(1 + monthly_rate, tenure)) / (math.pow(1 + monthly_rate, tenure) - 1)
    return round(emi, 2)

def generate_repayment_schedule(details: LoanDetails):
    schedule = []
    disbursement_date = details.disbursement_date
    principal = details.principal
    tenure = details.tenure
    interest_rate = details.interest_rate
    moratorium_period = details.moratorium_period

    # If moratorium period exists, interest accumulates
    if moratorium_period > 0:
        moratorium_interest = (principal * (interest_rate / 100) * moratorium_period) / 12
        principal += moratorium_interest

    # Calculate EMI
    emi = calculate_emi(principal, interest_rate, tenure)

    # Determine EMI frequency (monthly or quarterly)
    frequency_map = {"monthly": 1, "quarterly": 3}
    months_gap = frequency_map.get(details.emi_frequency, 1)

    # Generate schedule
    outstanding_balance = principal
    payment_date = disbursement_date + timedelta(days=moratorium_period * 30)

    for i in range(1, tenure + 1, months_gap):
        interest_component = (outstanding_balance * (interest_rate / 100) * months_gap) / 12
        principal_component = emi * months_gap - interest_component
        outstanding_balance -= principal_component

        schedule.append({
            "installment_no": i,
            "payment_date": payment_date.strftime("%Y-%m-%d"),
            "emi": round(emi * months_gap, 2),
            "principal": round(principal_component, 2),
            "interest": round(interest_component, 2),
            "balance": round(outstanding_balance, 2)
        })

        payment_date += timedelta(days=months_gap * 30)

    return schedule

@app.post("/generate_schedule")
def generate_schedule(details: LoanDetails):
    schedule = generate_repayment_schedule(details)
    return {"schedule": schedule}
