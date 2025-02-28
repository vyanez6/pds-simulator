#
# Copyright (c) 2023 JCPenney Co. All rights reserved.
#
from flask import Flask, request, abort, make_response

import os
import time
import json
import datetime

app = Flask(__name__)


def open_response(response_to_load):
    cur_path = os.path.abspath(os.path.dirname(__file__))
    response_path = os.path.join(cur_path, response_to_load)
    with open(response_path, "r", encoding="utf-8") as infile:
        response = json.load(infile)
    now = datetime.datetime.now()
    if "Response" in response and "OriginalDateTime" in response["Response"]:
        response["Response"]["OriginalDateTime"] = now.strftime("%Y-%m-%dT%H:%M:%S")
    return response


def gc_balance():
    print("\nGift Card Balance Inquiry\n")
    balance = float(input("Enter initial GC balance: "))
    return None, balance


def gc_load(body):
    print("\nSimulating Gift Card Load\n")
    amount = float(body["Amount"]) if "Amount" in body else 0.0
    balance = input(
        f"Enter initial GC balance (requested amount {amount} - enter to use this amount): ")
    if len(balance) == 0:
        balance = 0.0
    else:
        balance = float(balance)
    balance = balance + amount
    return amount, balance


def tender(body):
    print("\nSimulating Tender\n")
    amount = float(body["Amount"]) if "Amount" in body else 0.0
    tender = input(f"Enter tender amount (requested amount {amount} - enter to use this amount): ")
    if len(tender) == 0:
        tender = amount
    else:
        tender = float(tender)
    return tender, 0.0


def poa_posting(body):
    print("\nSimulating POA Posting\n")
    amount = float(body["Amount"]) if "Amount" in body else 0.0
    return amount, 0.0


def update_response(response, balance, amount):
    if balance is not None and "Response" in response and "Balance" in response["Response"]:
        response["Response"]["Balance"] = balance

    if amount is not None and "Response" in response and "Amount" in response["Response"]:
        response["Response"]["Amount"] = amount


@app.post("/PaymentDeviceService/api/v1/Payment/AuthorizePayment")
def authorize_payment():
    print()
    print("<<< Authorize payment request", time.time())
    body = request.get_json()
    print("<<<", body)

    balance = None
    amount = None
    response_to_load = None
    if "PaymentTenderType" in body:
        if body["PaymentTenderType"] == "gift" and "ProcessCode" in body:
            response_to_load = "authorize_payment_gc_response.json"
            if body["ProcessCode"] == "BalanceInquiry":
                amount, balance = gc_balance()
            elif body["ProcessCode"] == "AddValue":
                amount, balance = gc_load(body)
        elif body["PaymentTenderType"] == "credit" and "ProcessCode" in body and body[
            "ProcessCode"] == "JCPPaymentExchangeOut":
            response_to_load = "authorize_payment_poa_posting.json"
            amount, balance = poa_posting(body)

    if response_to_load is None:
        abort(404)
        return

    response = open_response(response_to_load)

    update_response(response, balance, amount)

    print(">>>", response)

    return response


enable_payment_responses = {
    "DUAL ICAPS ACCT INFO": "enable_payment_cc_response.json",
    "PLCC ICAPS ACCT INFO": "enable_payment_cc_response.json",
    "GC INQUIRY": "enable_payment_gc_response.json",
    "POA PLCC SWIPE": "enable_payment_poa_plcc_response.json",
    "POA DUAL SWIPE": "enable_payment_poa_dual_response.json",
    "MRV LOAD": "enable_payment_mrv_return_response.json",
    "DEBIT TENDER": "enable_payment_debit_tender_response.json",
    "Error": ""
}


@app.post("/PaymentDeviceService/api/v1/Payment/EnablePayment")
def enable_payment():
    print()
    print("<<< Enable payment request", time.time())
    body = request.get_json()
    print("<<<", body)
    print("Select an option:")
    response_types = list(enable_payment_responses.keys())
    for index, value in enumerate(response_types):
        print("   ", index, value)
    input_message = f"Enter selection to send card data [0-{len(response_types) - 1}]: "
    input_data = input(input_message)
    input_data = int(input_data)

    if response_types[input_data] == "Error":
        # fail the request... In theory these come from PDS as 200 with error inside
        abort(500)

    amount = None
    balance = None
    if response_types[input_data].startswith("MRV"):
        amount, balance = gc_load(body)
    elif response_types[input_data].endswith("TENDER"):
        amount, balance = tender(body)

    response_to_load = enable_payment_responses[response_types[input_data]]
    response = open_response(response_to_load)
    update_response(response, balance, amount)
    print(">>>", response)
    return response


@app.post("/PaymentDeviceService/api/v1/PaymentDevice/DisplayMessage")
def display_message():
    print()
    print("<<<", request.headers.get('message'), time.time())
    response = {
        "Response": {"Status": "started"},
        "ResponseSummary": {
            "Message": "Success",
            "ResponseCode": "OK"
        },
        "Error": None
    }
    print(">>>", response)
    return response


@app.post("/PaymentDeviceService/api/v1/PaymentDevice/DisplayPrompt")
def display_prompt():
    # {"promptName":"SOCIALSECURITYENTRY"}
    print()
    body = request.get_json()
    print("<<<", body)
    input_data = input("Enter data: ")
    if input_data.upper() == 'ZZZ':
        # We're going to simulate a TERMINAL IN USE response
        response = {
            "Response": None,
            "ResponseSummary": {"Message": "Error", "ResponseCode": "OK"},
            "Error": {"Message": "TERMINAL IN USE", "StatusCode": 503}
        }
    else:
        response = {
            "Response": {
                "InputData": input_data,
                "PinData": None
            },
            "ResponseSummary": {
                "Message": "Success",
                "ResponseCode": "OK"
            },
            "Error": None
        }
    response_body = json.dumps(response, separators=(',', ':'))
    print(">>>", response_body, "<<<", sep='')
    response = make_response(response_body, 200)
    response.mimetype = "application/json"
    print(response)
    return response


@app.post("/PaymentDeviceService/api/v1/PaymentDevice/DisplayForm")
def display_form():
    # {
    #   "displayFormName": "ECONFIRMDISPLAY",
    #   "buttonsName": ["OK", "CANCEL"],
    #   "message": "Enter data",
    #   "isReset": false
    # }
    print()
    body = request.get_json()
    buttons = body["buttonsName"][:]
    buttons.append("TERMINAL IN USE")
    print("<<<", body)
    print("Select an option:")
    for index, value in enumerate(buttons):
        print("   ", index, value)
    input_data = input(f"Enter selection [0-{len(buttons) - 1}]: ")
    if input_data == str(len(buttons) - 1):
        # We're going to simulate a TERMINAL IN USE response
        response = {
            "Response": None,
            "ResponseSummary": {"Message": "Error", "ResponseCode": "OK"},
            "Error": {"Message": "TERMINAL IN USE", "StatusCode": 503}
        }
    else:
        response = {
            "Response": {
                "InputData": body['buttonsName'][int(input_data)],
                "PinData": None
            },
            "ResponseSummary": {
                "Message": "Success",
                "ResponseCode": "OK"
            },
            "Error": None
        }
    print(">>>", response)
    return response


@app.get("/PaymentDeviceService/api/v1/DevicePairing/GetPaymentDevices")
def get_payment_devices():
    response = {
        "Response": [
            {
                "StoreNo": "",
                "TerminalNo": "",
                "IpAddress": "10.136.161.10",
                "SerialNo": "3011023907668470",
                "AssetTag": "VV70410",
                "FriendlyName": ""
            }
        ],
        "ResponseSummary": {"Message": "Success", "ResponseCode": "OK"},
        "Error": None
    }
    return response


return_responses = {
    "SUCCESS": "",
    "NOT FOUND": "not_found_return_response.json",
    "Error": "error_return_response.json"
}


@app.post("/POSReturnsDataService/api/v1/returnsdata/FindTransaction")
def post_return_find_transaction():
    print()
    body = request.get_json()
    print("<<<", body)
    print("Select an option:")
    response_types = list(return_responses.keys())
    for index, value in enumerate(response_types):
        print("   ", index, value)
    input_message = f"Enter selection to send return response [0-{len(response_types) - 1}]: "
    input_data = input(input_message)
    input_data = int(input_data)

    response_to_load = return_responses[response_types[input_data]]
    if response_types[input_data] == 'SUCCESS':
        response_to_load = f"{body['storeNum']}_{body['tranNum']}_{body['workstNum']}_return_response.json"

    response = open_response(response_to_load)
    print(">>>", response)
    return response
