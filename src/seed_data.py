"""Synthetic seed data: 12 fictional households for demo purposes.

None of the names, numbers, or situations below describe a real person,
household, or account. They are illustrative examples only, built to cover a
realistic range of practice-management scenarios: young professionals, a
single parent, families with children, business owners, and households
approaching retirement.

Dates for goals, meetings, and tasks are computed relative to "today" so the
demo always looks current, no matter when it is installed and run.
"""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from src import models

ADVISORS = ["Avery Simmons", "Priya Malhotra"]


def _d(offset_days: int) -> str:
    return (date.today() + timedelta(days=offset_days)).isoformat()


def _years_out(years: float) -> str:
    return (date.today() + timedelta(days=int(years * 365))).isoformat()


# ---------------------------------------------------------------------------
# Household specifications
# ---------------------------------------------------------------------------

HOUSEHOLDS: list[dict] = [
    # 1. Young professional couple
    {
        "name": "Rivera-Chen Household",
        "advisor": "Avery Simmons",
        "risk_tolerance": "Aggressive",
        "contact_preference": "Email",
        "notes": "Dual-income couple, no children yet, saving for a first home.",
        "people": [
            {"name": "Jordan Rivera", "relationship": "Self", "dob": "1996-04-12"},
            {"name": "Sam Chen", "relationship": "Spouse", "dob": "1995-11-02"},
        ],
        "financial_items": [
            {"category": "asset", "subcategory": "Cash & Checking", "amount": 8000},
            {"category": "asset", "subcategory": "Savings", "amount": 5000},
            {"category": "asset", "subcategory": "Emergency Fund", "amount": 9000},
            {"category": "asset", "subcategory": "Investments - Brokerage", "amount": 12000},
            {"category": "asset", "subcategory": "Retirement Accounts", "amount": 21000},
            {"category": "liability", "subcategory": "Student Loan", "amount": 18000},
            {"category": "income", "subcategory": "Combined Salary", "amount": 9500, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Housing (Rent)", "amount": 2200, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Transportation", "amount": 400, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Food", "amount": 700, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Other Living Expenses", "amount": 600, "frequency": "monthly"},
            {"category": "debt_payment", "subcategory": "Student Loan Payment", "amount": 350, "frequency": "monthly"},
        ],
        "goals": [
            {"name": "Retirement", "goal_type": "retirement", "target_amount": 2_200_000,
             "years_out": 35, "current_savings": 21000, "monthly_contribution": 900, "priority": "High"},
            {"name": "First home down payment", "goal_type": "major_purchase", "target_amount": 90000,
             "years_out": 3, "current_savings": 22000, "monthly_contribution": 1600, "priority": "High"},
        ],
        "crm_stage": "Discovery",
        "meetings": [
            {"offset_days": -60, "status": "Completed", "notes": "Initial discovery meeting. Gathered income and expense details.",
             "recommendations": "Recommend review of student loan refinance options with a licensed lender."},
            {"offset_days": 6, "status": "Scheduled"},
        ],
        "tasks": [
            {"description": "Send prior-year tax return", "assigned_to": "Jordan Rivera", "due_offset_days": -4, "status": "Open"},
            {"description": "Gather recent pay stubs", "assigned_to": "Sam Chen", "due_offset_days": 9, "status": "Open"},
            {"description": "Open discovery questionnaire", "assigned_to": "Advisor", "due_offset_days": -70, "status": "Complete"},
        ],
        "checklist_overrides": [
            {"item_name": "Life insurance coverage reviewed", "status": "Needs follow-up", "note": "Neither spouse has coverage yet."},
        ],
    },
    # 2. Young professional single / freelancer
    {
        "name": "Dubois Household",
        "advisor": "Priya Malhotra",
        "risk_tolerance": "Moderate",
        "contact_preference": "Phone",
        "notes": "Freelance graphic designer with variable monthly income.",
        "people": [
            {"name": "Morgan Dubois", "relationship": "Self", "dob": "1993-02-18"},
        ],
        "financial_items": [
            {"category": "asset", "subcategory": "Cash & Checking", "amount": 4200},
            {"category": "asset", "subcategory": "Emergency Fund", "amount": 7500},
            {"category": "asset", "subcategory": "Retirement Accounts", "amount": 16000},
            {"category": "liability", "subcategory": "Credit Card", "amount": 2100},
            {"category": "income", "subcategory": "Freelance Income (avg.)", "amount": 5400, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Housing (Rent)", "amount": 1500, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Food", "amount": 450, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Other Living Expenses", "amount": 500, "frequency": "monthly"},
            {"category": "debt_payment", "subcategory": "Credit Card Payment", "amount": 150, "frequency": "monthly"},
        ],
        "goals": [
            {"name": "Retirement", "goal_type": "retirement", "target_amount": 1_500_000,
             "years_out": 32, "current_savings": 16000, "monthly_contribution": 500, "priority": "Medium"},
            {"name": "6-month emergency reserve", "goal_type": "other", "target_amount": 9000,
             "years_out": 1, "current_savings": 7500, "monthly_contribution": 150, "priority": "High"},
        ],
        "crm_stage": "Prospect",
        "meetings": [
            {"offset_days": 10, "status": "Scheduled"},
        ],
        "tasks": [
            {"description": "Send intake form", "assigned_to": "Morgan Dubois", "due_offset_days": 5, "status": "Open"},
        ],
        "checklist_overrides": [],
    },
    # 3. Young professional couple, minimal onboarding (intentionally sparse)
    {
        "name": "Singh Household",
        "advisor": "Avery Simmons",
        "risk_tolerance": "Moderate",
        "contact_preference": "Email",
        "notes": "New prospect referral. Only initial contact info collected so far.",
        "people": [
            {"name": "Arjun Singh", "relationship": "Self", "dob": "1994-07-09"},
        ],
        "financial_items": [
            {"category": "income", "subcategory": "Salary", "amount": 7200, "frequency": "monthly"},
        ],
        "goals": [],
        "crm_stage": "Prospect",
        "meetings": [
            {"offset_days": 3, "status": "Scheduled"},
        ],
        "tasks": [
            {"description": "Schedule initial discovery meeting", "assigned_to": "Advisor", "due_offset_days": 2, "status": "Open"},
        ],
        "checklist_overrides": [],
    },
    # 4. Family, 2 kids, dual income
    {
        "name": "Okafor Family",
        "advisor": "Priya Malhotra",
        "risk_tolerance": "Moderate",
        "contact_preference": "Email",
        "notes": "Two working parents, two school-age children.",
        "people": [
            {"name": "Adaeze Okafor", "relationship": "Self", "dob": "1988-05-20"},
            {"name": "Chinedu Okafor", "relationship": "Spouse", "dob": "1987-09-14"},
            {"name": "Ngozi Okafor", "relationship": "Child", "dob": "2015-03-01", "dependant": True},
            {"name": "Kwame Okafor", "relationship": "Child", "dob": "2018-08-22", "dependant": True},
        ],
        "financial_items": [
            {"category": "asset", "subcategory": "Cash & Checking", "amount": 12000},
            {"category": "asset", "subcategory": "Emergency Fund", "amount": 18000},
            {"category": "asset", "subcategory": "Retirement Accounts", "amount": 145000},
            {"category": "asset", "subcategory": "529 Education Savings", "amount": 22000},
            {"category": "asset", "subcategory": "Real Estate (Primary Home)", "amount": 420000},
            {"category": "liability", "subcategory": "Mortgage", "amount": 310000},
            {"category": "liability", "subcategory": "Auto Loan", "amount": 14000},
            {"category": "income", "subcategory": "Combined Salary", "amount": 13500, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Housing", "amount": 2600, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Childcare", "amount": 1800, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Transportation", "amount": 700, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Food", "amount": 1300, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Other Living Expenses", "amount": 900, "frequency": "monthly"},
            {"category": "debt_payment", "subcategory": "Mortgage Payment", "amount": 1950, "frequency": "monthly"},
            {"category": "debt_payment", "subcategory": "Auto Loan Payment", "amount": 380, "frequency": "monthly"},
        ],
        "goals": [
            {"name": "Retirement", "goal_type": "retirement", "target_amount": 2_800_000,
             "years_out": 24, "current_savings": 145000, "monthly_contribution": 1800, "priority": "High"},
            {"name": "Children's college fund", "goal_type": "other", "target_amount": 180000,
             "years_out": 12, "current_savings": 22000, "monthly_contribution": 500, "priority": "Medium"},
        ],
        "crm_stage": "Analysis",
        "meetings": [
            {"offset_days": -30, "status": "Completed", "notes": "Reviewed cash flow and college funding gap.",
             "recommendations": "Suggest household consult a tax professional about 529 state deduction eligibility."},
            {"offset_days": 11, "status": "Scheduled"},
        ],
        "tasks": [
            {"description": "Provide mortgage statement", "assigned_to": "Chinedu Okafor", "due_offset_days": -2, "status": "Open"},
            {"description": "Review beneficiary designations", "assigned_to": "Advisor", "due_offset_days": 20, "status": "Open"},
        ],
        "checklist_overrides": [
            {"item_name": "Will in place and current", "status": "Complete", "note": "Updated last year after second child."},
            {"item_name": "Beneficiary designations reviewed", "status": "Needs follow-up"},
        ],
    },
    # 5. Family, 1 kid, single income, tight cash flow
    {
        "name": "Nguyen Family",
        "advisor": "Avery Simmons",
        "risk_tolerance": "Conservative",
        "contact_preference": "Phone",
        "notes": "Single income household; one parent recently left the workforce to care for a toddler.",
        "people": [
            {"name": "Linh Nguyen", "relationship": "Self", "dob": "1990-01-30"},
            {"name": "Minh Nguyen", "relationship": "Spouse", "dob": "1991-06-11"},
            {"name": "Anh Nguyen", "relationship": "Child", "dob": "2022-02-14", "dependant": True},
        ],
        "financial_items": [
            {"category": "asset", "subcategory": "Cash & Checking", "amount": 3000},
            {"category": "asset", "subcategory": "Emergency Fund", "amount": 4000},
            {"category": "asset", "subcategory": "Retirement Accounts", "amount": 38000},
            {"category": "liability", "subcategory": "Auto Loan", "amount": 9000},
            {"category": "liability", "subcategory": "Credit Card", "amount": 3200},
            {"category": "income", "subcategory": "Salary", "amount": 6200, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Housing (Rent)", "amount": 1900, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Childcare", "amount": 1100, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Transportation", "amount": 450, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Food", "amount": 800, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Other Living Expenses", "amount": 600, "frequency": "monthly"},
            {"category": "debt_payment", "subcategory": "Auto Loan Payment", "amount": 280, "frequency": "monthly"},
            {"category": "debt_payment", "subcategory": "Credit Card Payment", "amount": 150, "frequency": "monthly"},
        ],
        "goals": [
            {"name": "Retirement", "goal_type": "retirement", "target_amount": 1_400_000,
             "years_out": 30, "current_savings": 38000, "monthly_contribution": 250, "priority": "Medium"},
            {"name": "Rebuild emergency fund", "goal_type": "other", "target_amount": 11400,
             "years_out": 2, "current_savings": 4000, "monthly_contribution": 200, "priority": "High"},
        ],
        "crm_stage": "Discovery",
        "meetings": [
            {"offset_days": -14, "status": "Completed", "notes": "Discussed tight monthly cash flow after income reduction.",
             "recommendations": "Recommend household meet with a credit counselor regarding credit card balance."},
            {"offset_days": 8, "status": "Scheduled"},
        ],
        "tasks": [
            {"description": "Build a bare-bones budget worksheet", "assigned_to": "Linh Nguyen", "due_offset_days": -6, "status": "Open"},
        ],
        "checklist_overrides": [
            {"item_name": "Emergency fund target defined", "status": "Complete"},
            {"item_name": "Emergency fund funding progress reviewed", "status": "Needs follow-up"},
        ],
    },
    # 6. Family, dual income, incomplete discovery profile
    {
        "name": "Kowalski Family",
        "advisor": "Priya Malhotra",
        "risk_tolerance": "Moderate",
        "contact_preference": "Email",
        "notes": "Discovery in progress -- liabilities and goals not yet collected.",
        "people": [
            {"name": "Anna Kowalski", "relationship": "Self", "dob": "1985-10-05"},
            {"name": "Piotr Kowalski", "relationship": "Spouse", "dob": "1984-12-19"},
            {"name": "Zofia Kowalski", "relationship": "Child", "dob": "2012-04-30", "dependant": True},
        ],
        "financial_items": [
            {"category": "asset", "subcategory": "Cash & Checking", "amount": 9500},
            {"category": "asset", "subcategory": "Retirement Accounts", "amount": 96000},
            {"category": "income", "subcategory": "Combined Salary", "amount": 11200, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Housing", "amount": 2100, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Food", "amount": 950, "frequency": "monthly"},
        ],
        "goals": [],
        "crm_stage": "Discovery",
        "meetings": [
            {"offset_days": -7, "status": "Completed", "notes": "First discovery session; household will gather debt statements before next meeting."},
            {"offset_days": 13, "status": "Scheduled"},
        ],
        "tasks": [
            {"description": "Send list of all outstanding debts", "assigned_to": "Anna Kowalski", "due_offset_days": -1, "status": "Open"},
            {"description": "Discuss family financial goals", "assigned_to": "Advisor", "due_offset_days": 13, "status": "Open"},
        ],
        "checklist_overrides": [],
    },
    # 7. Family saving for college, longtime client
    {
        "name": "Martinez Family",
        "advisor": "Avery Simmons",
        "risk_tolerance": "Moderate",
        "contact_preference": "Email",
        "notes": "Longtime client household; annual review cadence.",
        "people": [
            {"name": "Elena Martinez", "relationship": "Self", "dob": "1982-03-11"},
            {"name": "Diego Martinez", "relationship": "Spouse", "dob": "1981-07-23"},
            {"name": "Sofia Martinez", "relationship": "Child", "dob": "2010-09-17", "dependant": True},
        ],
        "financial_items": [
            {"category": "asset", "subcategory": "Cash & Checking", "amount": 15000},
            {"category": "asset", "subcategory": "Emergency Fund", "amount": 24000},
            {"category": "asset", "subcategory": "Investments - Brokerage", "amount": 85000},
            {"category": "asset", "subcategory": "Retirement Accounts", "amount": 320000},
            {"category": "asset", "subcategory": "529 Education Savings", "amount": 45000},
            {"category": "asset", "subcategory": "Real Estate (Primary Home)", "amount": 510000},
            {"category": "liability", "subcategory": "Mortgage", "amount": 240000},
            {"category": "income", "subcategory": "Combined Salary", "amount": 16800, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Housing", "amount": 2900, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Transportation", "amount": 800, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Food", "amount": 1400, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Other Living Expenses", "amount": 1600, "frequency": "monthly"},
            {"category": "debt_payment", "subcategory": "Mortgage Payment", "amount": 1600, "frequency": "monthly"},
        ],
        "goals": [
            {"name": "Retirement", "goal_type": "retirement", "target_amount": 3_200_000,
             "years_out": 18, "current_savings": 320000, "monthly_contribution": 2500, "priority": "High"},
            {"name": "College funding", "goal_type": "other", "target_amount": 160000,
             "years_out": 8, "current_savings": 45000, "monthly_contribution": 700, "priority": "High"},
        ],
        "crm_stage": "Ongoing Service",
        "meetings": [
            {"offset_days": -180, "status": "Completed", "notes": "Annual review. Portfolio rebalanced in line with target allocation.",
             "recommendations": "No changes recommended at this time; continue current contribution levels."},
            {"offset_days": 9, "status": "Scheduled"},
        ],
        "tasks": [
            {"description": "Prepare annual review summary", "assigned_to": "Advisor", "due_offset_days": 7, "status": "Open"},
        ],
        "checklist_overrides": [
            {"item_name": "Will in place and current", "status": "Complete"},
            {"item_name": "Powers of attorney (financial & healthcare) in place", "status": "Complete"},
            {"item_name": "Beneficiary designations reviewed", "status": "Complete"},
            {"item_name": "Life insurance coverage reviewed", "status": "Complete"},
        ],
    },
    # 8. Single parent family
    {
        "name": "Reyes Household",
        "advisor": "Priya Malhotra",
        "risk_tolerance": "Moderate",
        "contact_preference": "Phone",
        "notes": "Single parent, recently navigated a change in household structure.",
        "people": [
            {"name": "Camila Reyes", "relationship": "Self", "dob": "1989-08-02"},
            {"name": "Mateo Reyes", "relationship": "Child", "dob": "2016-05-19", "dependant": True},
        ],
        "financial_items": [
            {"category": "asset", "subcategory": "Cash & Checking", "amount": 5200},
            {"category": "asset", "subcategory": "Emergency Fund", "amount": 6000},
            {"category": "asset", "subcategory": "Retirement Accounts", "amount": 52000},
            {"category": "liability", "subcategory": "Auto Loan", "amount": 11000},
            {"category": "income", "subcategory": "Salary", "amount": 6800, "frequency": "monthly"},
            {"category": "income", "subcategory": "Child Support", "amount": 600, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Housing (Rent)", "amount": 1850, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Childcare", "amount": 900, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Food", "amount": 650, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Other Living Expenses", "amount": 550, "frequency": "monthly"},
            {"category": "debt_payment", "subcategory": "Auto Loan Payment", "amount": 320, "frequency": "monthly"},
        ],
        "goals": [
            {"name": "Retirement", "goal_type": "retirement", "target_amount": 1_600_000,
             "years_out": 28, "current_savings": 52000, "monthly_contribution": 400, "priority": "Medium"},
            {"name": "Son's college fund", "goal_type": "other", "target_amount": 90000,
             "years_out": 13, "current_savings": 0, "monthly_contribution": 150, "priority": "Medium"},
        ],
        "crm_stage": "Recommendations",
        "meetings": [
            {"offset_days": -21, "status": "Completed", "notes": "Reviewed updated beneficiary needs and life insurance gap.",
             "recommendations": "Recommend household consult a licensed insurance professional about term life coverage."},
            {"offset_days": 5, "status": "Scheduled"},
        ],
        "tasks": [
            {"description": "Update beneficiary on retirement account", "assigned_to": "Camila Reyes", "due_offset_days": -3, "status": "Open"},
            {"description": "Share term life insurance quotes", "assigned_to": "Advisor", "due_offset_days": 4, "status": "Open"},
        ],
        "checklist_overrides": [
            {"item_name": "Life insurance coverage reviewed", "status": "Needs follow-up", "note": "No coverage currently in place."},
            {"item_name": "Powers of attorney (financial & healthcare) in place", "status": "Needs follow-up"},
        ],
    },
    # 9. Business owner (S-corp)
    {
        "name": "Patel Household",
        "advisor": "Avery Simmons",
        "risk_tolerance": "Aggressive",
        "contact_preference": "Email",
        "notes": "Owns a small S-corp consultancy; income varies seasonally.",
        "people": [
            {"name": "Rohan Patel", "relationship": "Self", "dob": "1979-11-28"},
            {"name": "Meera Patel", "relationship": "Spouse", "dob": "1980-02-16"},
        ],
        "financial_items": [
            {"category": "asset", "subcategory": "Cash & Checking", "amount": 42000},
            {"category": "asset", "subcategory": "Emergency Fund", "amount": 60000},
            {"category": "asset", "subcategory": "Investments - Brokerage", "amount": 180000},
            {"category": "asset", "subcategory": "Retirement Accounts", "amount": 410000},
            {"category": "asset", "subcategory": "Business Ownership Interest", "amount": 350000},
            {"category": "asset", "subcategory": "Real Estate (Primary Home)", "amount": 620000},
            {"category": "liability", "subcategory": "Mortgage", "amount": 280000},
            {"category": "income", "subcategory": "Owner Distributions (avg.)", "amount": 19000, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Housing", "amount": 3400, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Transportation", "amount": 900, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Food", "amount": 1500, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Other Living Expenses", "amount": 2000, "frequency": "monthly"},
            {"category": "debt_payment", "subcategory": "Mortgage Payment", "amount": 1850, "frequency": "monthly"},
        ],
        "goals": [
            {"name": "Retirement", "goal_type": "retirement", "target_amount": 4_000_000,
             "years_out": 15, "current_savings": 410000, "monthly_contribution": 4000, "priority": "High"},
            {"name": "Business succession planning", "goal_type": "other", "target_amount": 350000,
             "years_out": 10, "current_savings": 350000, "monthly_contribution": 0, "priority": "Medium"},
        ],
        "crm_stage": "Recommendations",
        "meetings": [
            {"offset_days": -45, "status": "Completed", "notes": "Discussed business cash reserves and owner compensation structure.",
             "recommendations": "Recommend household meet with a tax professional about retirement plan options for the business (e.g. a defined contribution plan)."},
            {"offset_days": 15, "status": "Scheduled"},
        ],
        "tasks": [
            {"description": "Request business financial statements", "assigned_to": "Rohan Patel", "due_offset_days": -5, "status": "Open"},
            {"description": "Research small-business retirement plan options", "assigned_to": "Advisor", "due_offset_days": 12, "status": "Open"},
        ],
        "checklist_overrides": [
            {"item_name": "Property & liability (home/auto) coverage reviewed", "status": "Complete"},
            {"item_name": "Umbrella liability policy considered", "status": "Needs follow-up", "note": "Business ownership increases liability exposure."},
        ],
        "scenario_overrides": {
            "baseline": {"annual_return": 0.065, "withdrawal_rate": 0.04},
        },
    },
    # 10. Business owner, sole proprietor, pre-retirement blend
    {
        "name": "Johansson Household",
        "advisor": "Priya Malhotra",
        "risk_tolerance": "Moderate",
        "contact_preference": "Phone",
        "notes": "Sole proprietor of a landscaping business, planning a gradual wind-down over the next decade.",
        "people": [
            {"name": "Erik Johansson", "relationship": "Self", "dob": "1967-06-30"},
            {"name": "Ingrid Johansson", "relationship": "Spouse", "dob": "1968-01-12"},
        ],
        "financial_items": [
            {"category": "asset", "subcategory": "Cash & Checking", "amount": 22000},
            {"category": "asset", "subcategory": "Emergency Fund", "amount": 30000},
            {"category": "asset", "subcategory": "Retirement Accounts", "amount": 560000},
            {"category": "asset", "subcategory": "Business Ownership Interest", "amount": 120000},
            {"category": "asset", "subcategory": "Real Estate (Primary Home)", "amount": 390000},
            {"category": "liability", "subcategory": "Mortgage", "amount": 60000},
            {"category": "income", "subcategory": "Business Income (avg.)", "amount": 10500, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Housing", "amount": 1700, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Transportation", "amount": 500, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Food", "amount": 900, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Other Living Expenses", "amount": 1100, "frequency": "monthly"},
            {"category": "debt_payment", "subcategory": "Mortgage Payment", "amount": 900, "frequency": "monthly"},
        ],
        "goals": [
            {"name": "Retirement", "goal_type": "retirement", "target_amount": 1_200_000,
             "years_out": 8, "current_savings": 560000, "monthly_contribution": 2200, "priority": "High"},
        ],
        "crm_stage": "Implementation",
        "meetings": [
            {"offset_days": -90, "status": "Completed", "notes": "Discussed business wind-down timeline and retirement account consolidation.",
             "recommendations": "Recommend household consult a business attorney regarding sale or transfer of the business."},
            {"offset_days": 18, "status": "Scheduled"},
        ],
        "tasks": [
            {"description": "Consolidate old retirement accounts", "assigned_to": "Erik Johansson", "due_offset_days": 25, "status": "Open"},
            {"description": "Draft business wind-down timeline", "assigned_to": "Advisor", "due_offset_days": -8, "status": "Open"},
        ],
        "checklist_overrides": [
            {"item_name": "Social Security claiming strategy discussed", "status": "Needs follow-up"},
            {"item_name": "Retirement account asset allocation reviewed", "status": "Complete"},
        ],
    },
    # 11. Pre-retirement couple
    {
        "name": "Thompson Household",
        "advisor": "Avery Simmons",
        "risk_tolerance": "Conservative",
        "contact_preference": "Email",
        "notes": "Both spouses plan to retire within five years.",
        "people": [
            {"name": "Barbara Thompson", "relationship": "Self", "dob": "1964-09-05"},
            {"name": "Richard Thompson", "relationship": "Spouse", "dob": "1963-04-21"},
        ],
        "financial_items": [
            {"category": "asset", "subcategory": "Cash & Checking", "amount": 35000},
            {"category": "asset", "subcategory": "Emergency Fund", "amount": 45000},
            {"category": "asset", "subcategory": "Investments - Brokerage", "amount": 220000},
            {"category": "asset", "subcategory": "Retirement Accounts", "amount": 780000},
            {"category": "asset", "subcategory": "Real Estate (Primary Home)", "amount": 450000},
            {"category": "liability", "subcategory": "Mortgage", "amount": 40000},
            {"category": "income", "subcategory": "Combined Salary", "amount": 14000, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Housing", "amount": 1900, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Transportation", "amount": 600, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Food", "amount": 1100, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Healthcare", "amount": 700, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Other Living Expenses", "amount": 900, "frequency": "monthly"},
            {"category": "debt_payment", "subcategory": "Mortgage Payment", "amount": 700, "frequency": "monthly"},
        ],
        "goals": [
            {"name": "Retirement", "goal_type": "retirement", "target_amount": 1_300_000,
             "years_out": 5, "current_savings": 780000, "monthly_contribution": 3000, "priority": "High"},
            {"name": "Gift fund for grandchildren", "goal_type": "other", "target_amount": 50000,
             "years_out": 6, "current_savings": 8000, "monthly_contribution": 300, "priority": "Low"},
        ],
        "crm_stage": "Ongoing Service",
        "meetings": [
            {"offset_days": -120, "status": "Completed", "notes": "Reviewed retirement income plan and Social Security claiming ages.",
             "recommendations": "Continue current contribution levels; revisit claiming strategy annually."},
            {"offset_days": 4, "status": "Scheduled"},
        ],
        "tasks": [
            {"description": "Request Social Security benefit estimate statements", "assigned_to": "Richard Thompson", "due_offset_days": -2, "status": "Open"},
        ],
        "checklist_overrides": [
            {"item_name": "Will in place and current", "status": "Complete"},
            {"item_name": "Powers of attorney (financial & healthcare) in place", "status": "Complete"},
            {"item_name": "Social Security claiming strategy discussed", "status": "Needs follow-up"},
        ],
        "scenario_overrides": {
            "optimistic": {"annual_return": 0.06, "withdrawal_rate": 0.04},
        },
    },
    # 12. Pre-retirement single, stalled in CRM pipeline
    {
        "name": "Alvarez Household",
        "advisor": "Priya Malhotra",
        "risk_tolerance": "Conservative",
        "contact_preference": "Phone",
        "notes": "Analysis phase has been inactive for some time; needs re-engagement.",
        "people": [
            {"name": "Teresa Alvarez", "relationship": "Self", "dob": "1965-12-08"},
        ],
        "financial_items": [
            {"category": "asset", "subcategory": "Cash & Checking", "amount": 9000},
            {"category": "asset", "subcategory": "Emergency Fund", "amount": 14000},
            {"category": "asset", "subcategory": "Retirement Accounts", "amount": 310000},
            {"category": "liability", "subcategory": "Mortgage", "amount": 85000},
            {"category": "income", "subcategory": "Salary", "amount": 6100, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Housing", "amount": 1300, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Food", "amount": 500, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Healthcare", "amount": 400, "frequency": "monthly"},
            {"category": "expense", "subcategory": "Other Living Expenses", "amount": 500, "frequency": "monthly"},
            {"category": "debt_payment", "subcategory": "Mortgage Payment", "amount": 650, "frequency": "monthly"},
        ],
        "goals": [
            {"name": "Retirement", "goal_type": "retirement", "target_amount": 650000,
             "years_out": 7, "current_savings": 310000, "monthly_contribution": 900, "priority": "High"},
        ],
        "crm_stage": "Analysis",
        "_stalled_days": 75,
        "meetings": [
            {"offset_days": -80, "status": "Completed", "notes": "Initial analysis of retirement readiness. No follow-up meeting scheduled yet.",
             "recommendations": "Recommend catch-up retirement contributions be discussed with household."},
        ],
        "tasks": [
            {"description": "Re-engage household for follow-up meeting", "assigned_to": "Advisor", "due_offset_days": -20, "status": "Open"},
        ],
        "checklist_overrides": [
            {"item_name": "Social Security claiming strategy discussed", "status": "Needs follow-up"},
        ],
    },
]


def _create_household_from_spec(conn: sqlite3.Connection, spec: dict) -> int:
    household_id = models.create_household(
        conn,
        name=spec["name"],
        advisor=spec["advisor"],
        risk_tolerance=spec.get("risk_tolerance", "Moderate"),
        contact_preference=spec.get("contact_preference", "Email"),
        notes=spec.get("notes", ""),
        crm_stage="Prospect",
        actor="Seed Script",
    )

    for person in spec.get("people", []):
        models.add_person(
            conn,
            household_id,
            name=person["name"],
            relationship=person["relationship"],
            date_of_birth=person.get("dob"),
            is_dependant=person.get("dependant", False),
            actor="Seed Script",
        )

    for item in spec.get("financial_items", []):
        models.add_financial_item(
            conn,
            household_id,
            category=item["category"],
            subcategory=item["subcategory"],
            amount=item["amount"],
            description=item.get("description", ""),
            frequency=item.get("frequency", "one_time"),
            actor="Seed Script",
        )

    goal_ids = {}
    for goal in spec.get("goals", []):
        goal_id = models.add_goal(
            conn,
            household_id,
            name=goal["name"],
            goal_type=goal["goal_type"],
            target_amount=goal["target_amount"],
            target_date=_years_out(goal["years_out"]),
            current_savings=goal.get("current_savings", 0),
            monthly_contribution=goal.get("monthly_contribution", 0),
            priority=goal.get("priority", "Medium"),
            actor="Seed Script",
        )
        goal_ids[goal["name"]] = goal_id

    scenario_overrides = spec.get("scenario_overrides", {})
    if scenario_overrides and goal_ids:
        retirement_goal_id = next(iter(goal_ids.values()))
        for scenario_name, assumption in scenario_overrides.items():
            models.set_scenario_assumption(
                conn,
                retirement_goal_id,
                scenario_name,
                annual_return=assumption["annual_return"],
                withdrawal_rate=assumption.get("withdrawal_rate"),
                notes="Custom assumption set during seeding",
                actor="Seed Script",
            )

    # Target CRM stage: replay the standard pipeline up to (not including a
    # second insert of) the target stage so crm_history shows a realistic
    # progression, then stamp the final stage.
    stage_order = [
        "Prospect",
        "Discovery",
        "Analysis",
        "Recommendations",
        "Implementation",
        "Ongoing Service",
    ]
    target_stage = spec.get("crm_stage", "Prospect")
    target_index = stage_order.index(target_stage)
    for stage in stage_order[1 : target_index + 1]:
        models.change_crm_stage(
            conn, household_id, stage, actor="Seed Script", note="Pipeline progression"
        )

    if "_stalled_days" in spec:
        backdated = (date.today() - timedelta(days=spec["_stalled_days"])).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        conn.execute(
            """
            UPDATE crm_history SET changed_at = ?
            WHERE household_id = ? AND id = (
                SELECT id FROM crm_history WHERE household_id = ? ORDER BY id DESC LIMIT 1
            )
            """,
            (backdated, household_id, household_id),
        )
        conn.commit()

    for override in spec.get("checklist_overrides", []):
        row = conn.execute(
            "SELECT id FROM checklist_items WHERE household_id = ? AND item_name = ?",
            (household_id, override["item_name"]),
        ).fetchone()
        if row:
            models.update_checklist_item(
                conn,
                row["id"],
                status=override["status"],
                note=override.get("note", ""),
                actor="Seed Script",
            )

    meeting_ids = []
    for meeting in spec.get("meetings", []):
        meeting_date = _d(meeting["offset_days"])
        meeting_id = models.create_meeting(
            conn,
            household_id,
            meeting_date=meeting_date,
            agenda=models.generate_agenda(conn, household_id),
            actor="Seed Script",
        )
        meeting_ids.append(meeting_id)
        update_fields = {"status": meeting["status"]}
        if "notes" in meeting:
            update_fields["notes"] = meeting["notes"]
        if "recommendations" in meeting:
            update_fields["recommendations"] = meeting["recommendations"]
        models.update_meeting(conn, meeting_id, actor="Seed Script", **update_fields)

    for task in spec.get("tasks", []):
        task_id = models.create_task(
            conn,
            household_id,
            description=task["description"],
            assigned_to=task.get("assigned_to", "Advisor"),
            due_date=_d(task["due_offset_days"]) if task.get("due_offset_days") is not None else None,
            actor="Seed Script",
        )
        if task.get("status") == "Complete":
            models.complete_task(conn, task_id, actor="Seed Script")

    return household_id


def seed_all(conn: sqlite3.Connection) -> list[int]:
    """Seed all synthetic households. Safe to call only on an empty database."""
    existing = conn.execute("SELECT COUNT(*) AS n FROM households").fetchone()["n"]
    if existing > 0:
        raise RuntimeError(
            "Database already contains households. Use src.db.reset_db() first if you "
            "want to reseed from scratch."
        )
    return [_create_household_from_spec(conn, spec) for spec in HOUSEHOLDS]
