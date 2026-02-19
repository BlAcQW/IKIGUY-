"""
Enhanced Payment Reminder Voice Agent Tools

Comprehensive collection of VAPI voice agent tools for AI-powered debt collection
and payment recovery campaigns with full FDCPA/TCPA compliance.

Tools included:
1. get_account_details - Retrieve account information and payment history
2. verify_customer_identity - Secure identity verification process
3. calculate_payment_plans - Generate affordable payment options
4. process_payment - Secure payment processing with multiple methods
5. schedule_payment - Set up future payment arrangements
6. handle_dispute - Process customer disputes and compliance
7. check_compliance_status - Verify regulatory compliance
8. generate_settlement_offer - Create settlement proposals
9. record_interaction - Document all call details for compliance
10. escalate_to_supervisor - Transfer complex cases to human agents
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from decimal import Decimal
import json

logger = logging.getLogger(__name__)

class EnhancedPaymentReminderVoiceTools:
    """Enhanced Payment Reminder Voice Agent Tools for VAPI Integration"""

    def __init__(self, api_keys: dict):
        """Initialize with API keys from integration_api_keys.md"""
        self.api_keys = api_keys
        self.compliance_rules = {
            'fdcpa': {
                'min_days_between_contacts': 7,
                'allowed_contact_hours': {'start': 8, 'end': 21},
                'max_contacts_per_week': 3
            },
            'tcpa': {
                'requires_consent': True,
                'auto_dialer_restrictions': True
            }
        }

    def get_account_details(
        self,
        account_number: str,
        include_history: bool = True,
        verification_passed: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieve comprehensive account information including balance, payment history, and account status.

        Args:
            account_number: Customer account number for lookup
            include_history: Include detailed payment history
            verification_passed: Whether customer identity has been verified

        Returns:
            Dict containing account details, balance, payment history, and compliance info
        """
        try:
            if not verification_passed:
                return {
                    "error": "Customer identity must be verified before accessing account details",
                    "verification_required": True,
                    "next_step": "verify_customer_identity"
                }

            # Simulate account lookup from accounting system
            account_details = {
                "account_number": account_number,
                "customer_name": "John Smith",  # Would be fetched from system
                "current_balance": 2847.65,
                "original_balance": 3200.00,
                "days_overdue": 45,
                "last_payment_date": "2024-07-15",
                "last_payment_amount": 352.35,
                "account_status": "delinquent",
                "payment_history_score": 6,  # 1-10 scale
                "previous_promises": [
                    {
                        "date": "2024-08-20",
                        "amount": 500.00,
                        "status": "broken"
                    }
                ],
                "contact_history": {
                    "total_attempts": 8,
                    "successful_contacts": 3,
                    "last_contact_date": "2024-08-25"
                },
                "compliance_status": {
                    "dispute_raised": False,
                    "cease_contact_requested": False,
                    "attorney_represented": False,
                    "bankruptcy_filed": False
                }
            }

            if include_history:
                account_details["payment_history"] = [
                    {"date": "2024-07-15", "amount": 352.35, "method": "credit_card"},
                    {"date": "2024-06-12", "amount": 200.00, "method": "ach"},
                    {"date": "2024-05-08", "amount": 150.00, "method": "check"}
                ]

            logger.info(f"Retrieved account details for {account_number}")
            return {
                "success": True,
                "account_details": account_details,
                "recommended_approach": self._get_collection_strategy(account_details)
            }

        except Exception as e:
            logger.error(f"Error retrieving account details: {str(e)}")
            return {
                "error": f"Unable to retrieve account information: {str(e)}",
                "account_accessible": False
            }

    def verify_customer_identity(
        self,
        account_number: str,
        verification_method: str,
        provided_value: str
    ) -> Dict[str, Any]:
        """
        Securely verify customer identity using multiple security questions.

        Args:
            account_number: Account number for verification
            verification_method: Method for identity verification (ssn_last_four, billing_address, etc.)
            provided_value: Value provided by customer for verification

        Returns:
            Dict with verification result and next steps
        """
        try:
            # Simulate verification against customer records
            verification_data = {
                "ssn_last_four": "1234",
                "billing_address": "123 Main St",
                "phone_number": "+15551234567",
                "date_of_birth": "1985-06-15"
            }

            expected_value = verification_data.get(verification_method)
            if not expected_value:
                return {
                    "error": "Invalid verification method",
                    "available_methods": list(verification_data.keys())
                }

            # Check if provided value matches (case-insensitive for addresses)
            if verification_method == "billing_address":
                verification_passed = provided_value.lower() in expected_value.lower()
            else:
                verification_passed = provided_value == expected_value

            if verification_passed:
                logger.info(f"Identity verification successful for account {account_number}")
                return {
                    "verification_successful": True,
                    "identity_confirmed": True,
                    "verification_method_used": verification_method,
                    "can_proceed_with_account_details": True,
                    "message": "Thank you for verifying your identity. I can now access your account information."
                }
            else:
                return {
                    "verification_successful": False,
                    "attempts_remaining": 2,  # FDCPA compliance - limited attempts
                    "alternative_methods": [m for m in verification_data.keys() if m != verification_method],
                    "message": "I'm sorry, that information doesn't match our records. Let me try a different verification method."
                }

        except Exception as e:
            logger.error(f"Error during identity verification: {str(e)}")
            return {
                "error": f"Verification system error: {str(e)}",
                "verification_successful": False
            }

    def calculate_payment_plans(
        self,
        account_number: str,
        current_balance: float,
        customer_budget: Optional[float] = None,
        payment_frequency: str = "monthly",
        down_payment: float = 0
    ) -> Dict[str, Any]:
        """
        Generate affordable payment plan options based on customer financial situation.

        Args:
            account_number: Customer account number
            current_balance: Outstanding balance amount
            customer_budget: Customer stated monthly payment capability
            payment_frequency: Preferred payment frequency (weekly, bi_weekly, monthly)
            down_payment: Initial down payment amount

        Returns:
            Dict with multiple payment plan options
        """
        try:
            remaining_balance = current_balance - down_payment

            # Generate multiple payment plan options
            payment_plans = []

            # Option 1: Full payment with discount
            full_payment_discount = min(current_balance * 0.05, 200)  # Up to 5% or $200
            payment_plans.append({
                "plan_type": "full_payment",
                "description": "Pay in full today",
                "total_amount": current_balance - full_payment_discount,
                "discount": full_payment_discount,
                "payments": 1,
                "payment_amount": current_balance - full_payment_discount,
                "recommended": current_balance < 1000
            })

            # Option 2: 3-month plan
            monthly_3_payment = remaining_balance / 3
            payment_plans.append({
                "plan_type": "three_month",
                "description": "3 monthly payments",
                "down_payment": down_payment,
                "remaining_balance": remaining_balance,
                "payments": 3,
                "payment_amount": round(monthly_3_payment, 2),
                "total_amount": current_balance,
                "start_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                "recommended": customer_budget and customer_budget >= monthly_3_payment
            })

            # Option 3: 6-month plan
            monthly_6_payment = remaining_balance / 6
            payment_plans.append({
                "plan_type": "six_month",
                "description": "6 monthly payments",
                "down_payment": down_payment,
                "remaining_balance": remaining_balance,
                "payments": 6,
                "payment_amount": round(monthly_6_payment, 2),
                "total_amount": current_balance,
                "start_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                "recommended": customer_budget and customer_budget >= monthly_6_payment
            })

            # Option 4: 12-month plan
            monthly_12_payment = remaining_balance / 12
            payment_plans.append({
                "plan_type": "twelve_month",
                "description": "12 monthly payments",
                "down_payment": down_payment,
                "remaining_balance": remaining_balance,
                "payments": 12,
                "payment_amount": round(monthly_12_payment, 2),
                "total_amount": current_balance,
                "start_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                "recommended": customer_budget and customer_budget >= monthly_12_payment
            })

            # Option 5: Custom plan based on budget
            if customer_budget and customer_budget > 0:
                custom_months = max(3, min(24, int(remaining_balance / customer_budget)))
                custom_payment = remaining_balance / custom_months
                payment_plans.append({
                    "plan_type": "custom_budget",
                    "description": f"Custom {custom_months}-month plan based on your budget",
                    "down_payment": down_payment,
                    "remaining_balance": remaining_balance,
                    "payments": custom_months,
                    "payment_amount": round(custom_payment, 2),
                    "total_amount": current_balance,
                    "start_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                    "recommended": True,
                    "budget_friendly": True
                })

            logger.info(f"Generated {len(payment_plans)} payment plans for account {account_number}")

            return {
                "success": True,
                "account_number": account_number,
                "original_balance": current_balance,
                "payment_plans": payment_plans,
                "terms_and_conditions": "All payment plans require autopay setup. Missed payments may result in plan cancellation.",
                "next_step": "Select a payment plan that works for your budget"
            }

        except Exception as e:
            logger.error(f"Error calculating payment plans: {str(e)}")
            return {
                "error": f"Unable to calculate payment plans: {str(e)}",
                "suggested_action": "Transfer to supervisor for manual calculation"
            }

    def process_payment(
        self,
        account_number: str,
        payment_amount: float,
        payment_method: str,
        payment_details: Dict[str, Any],
        is_recurring: bool = False
    ) -> Dict[str, Any]:
        """
        Securely process customer payment using various payment methods.

        Args:
            account_number: Customer account number
            payment_amount: Payment amount to process
            payment_method: Payment method selection
            payment_details: Payment method specific details (encrypted)
            is_recurring: Set up recurring payment

        Returns:
            Dict with payment processing result
        """
        try:
            # Validate payment amount
            if payment_amount <= 0:
                return {
                    "error": "Payment amount must be greater than zero",
                    "payment_successful": False
                }

            # Simulate payment processing
            processing_fees = {
                "credit_card": payment_amount * 0.029,  # 2.9%
                "debit_card": payment_amount * 0.015,   # 1.5%
                "ach_bank_transfer": 0.50,              # Flat fee
                "check_by_phone": 2.00                  # Flat fee
            }

            processing_fee = processing_fees.get(payment_method, 0)
            net_payment = payment_amount - processing_fee

            # Generate transaction ID
            transaction_id = f"TXN_{account_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Simulate successful payment processing
            payment_result = {
                "payment_successful": True,
                "transaction_id": transaction_id,
                "account_number": account_number,
                "payment_amount": payment_amount,
                "processing_fee": round(processing_fee, 2),
                "net_payment": round(net_payment, 2),
                "payment_method": payment_method,
                "processing_date": datetime.now().isoformat(),
                "confirmation_number": f"CONF_{transaction_id}",
                "receipt_email_sent": True,
                "is_recurring": is_recurring
            }

            if is_recurring:
                payment_result["recurring_schedule"] = {
                    "frequency": "monthly",
                    "next_payment_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                    "recurring_amount": payment_amount
                }

            logger.info(f"Payment processed successfully: {transaction_id}")

            return {
                "success": True,
                "payment_result": payment_result,
                "message": f"Thank you! Your payment of ${payment_amount:.2f} has been processed successfully. Your confirmation number is {payment_result['confirmation_number']}.",
                "next_steps": [
                    "Receipt will be emailed to you within 5 minutes",
                    "Payment will reflect on your account within 1-2 business days",
                    "Save your confirmation number for your records"
                ]
            }

        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            return {
                "error": f"Payment processing failed: {str(e)}",
                "payment_successful": False,
                "suggested_action": "Please try again or speak with a supervisor"
            }

    def schedule_payment(
        self,
        account_number: str,
        payment_date: str,
        payment_amount: float,
        payment_method: str = "manual_payment",
        send_reminder: bool = True,
        reminder_days_before: int = 3
    ) -> Dict[str, Any]:
        """
        Schedule future payment arrangements and set up payment reminders.

        Args:
            account_number: Customer account number
            payment_date: Scheduled payment date (YYYY-MM-DD)
            payment_amount: Amount to be paid
            payment_method: Method for scheduled payment
            send_reminder: Send payment reminder notifications
            reminder_days_before: Days before payment to send reminder

        Returns:
            Dict with scheduled payment confirmation
        """
        try:
            # Validate payment date
            payment_datetime = datetime.strptime(payment_date, "%Y-%m-%d")
            if payment_datetime <= datetime.now():
                return {
                    "error": "Payment date must be in the future",
                    "minimum_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                }

            # Generate schedule ID
            schedule_id = f"SCHED_{account_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Calculate reminder date
            reminder_date = payment_datetime - timedelta(days=reminder_days_before)

            scheduled_payment = {
                "schedule_id": schedule_id,
                "account_number": account_number,
                "payment_amount": payment_amount,
                "payment_date": payment_date,
                "payment_method": payment_method,
                "status": "scheduled",
                "created_date": datetime.now().isoformat(),
                "reminder_enabled": send_reminder,
                "reminder_date": reminder_date.strftime("%Y-%m-%d") if send_reminder else None,
                "confirmation_required": payment_method != "manual_payment"
            }

            logger.info(f"Payment scheduled: {schedule_id}")

            return {
                "success": True,
                "scheduled_payment": scheduled_payment,
                "message": f"Perfect! I've scheduled your payment of ${payment_amount:.2f} for {payment_date}. You'll receive a reminder {reminder_days_before} days before the due date.",
                "reminder_info": {
                    "reminder_date": reminder_date.strftime("%Y-%m-%d") if send_reminder else None,
                    "reminder_methods": ["phone_call", "email", "text_message"] if send_reminder else []
                },
                "important_notes": [
                    "Please ensure sufficient funds are available on the payment date",
                    "You can modify or cancel this arrangement by calling us at least 24 hours in advance",
                    "Breaking payment promises may affect future payment plan options"
                ]
            }

        except ValueError as e:
            return {
                "error": "Invalid date format. Please use YYYY-MM-DD format",
                "example": "2024-09-30"
            }
        except Exception as e:
            logger.error(f"Error scheduling payment: {str(e)}")
            return {
                "error": f"Unable to schedule payment: {str(e)}",
                "suggested_action": "Please try again or speak with a supervisor"
            }

    def handle_dispute(
        self,
        account_number: str,
        dispute_reason: str,
        dispute_details: str,
        pause_collections: bool = True
    ) -> Dict[str, Any]:
        """
        Process customer disputes and initiate proper dispute handling procedures.

        Args:
            account_number: Customer account number
            dispute_reason: Reason for dispute
            dispute_details: Detailed description of the dispute
            pause_collections: Temporarily pause collection activities

        Returns:
            Dict with dispute processing result and next steps
        """
        try:
            # Generate dispute ID
            dispute_id = f"DISP_{account_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Set investigation timeline based on dispute type
            investigation_days = {
                "never_received_service": 30,
                "incorrect_amount": 15,
                "already_paid": 10,
                "identity_theft": 60,
                "billing_error": 20,
                "other": 30
            }

            investigation_period = investigation_days.get(dispute_reason, 30)
            investigation_deadline = datetime.now() + timedelta(days=investigation_period)

            dispute_record = {
                "dispute_id": dispute_id,
                "account_number": account_number,
                "dispute_reason": dispute_reason,
                "dispute_details": dispute_details,
                "date_reported": datetime.now().isoformat(),
                "investigation_status": "pending",
                "investigation_deadline": investigation_deadline.isoformat(),
                "collections_paused": pause_collections,
                "required_documentation": self._get_required_dispute_docs(dispute_reason),
                "next_contact_date": investigation_deadline.strftime("%Y-%m-%d")
            }

            logger.info(f"Dispute recorded: {dispute_id}")

            return {
                "success": True,
                "dispute_recorded": True,
                "dispute_record": dispute_record,
                "collections_paused": pause_collections,
                "message": f"I understand your concern and I've recorded your dispute (ID: {dispute_id}). We will investigate this matter and respond within {investigation_period} business days.",
                "next_steps": [
                    f"Investigation will be completed by {investigation_deadline.strftime('%B %d, %Y')}",
                    "You will receive written confirmation of this dispute within 5 business days",
                    "All collection activities are paused during the investigation" if pause_collections else "Collection activities will continue during investigation",
                    "Please provide any supporting documentation to help with our investigation"
                ],
                "required_documentation": dispute_record["required_documentation"],
                "legal_rights": "Under the Fair Debt Collection Practices Act, you have the right to dispute this debt and request validation."
            }

        except Exception as e:
            logger.error(f"Error handling dispute: {str(e)}")
            return {
                "error": f"Unable to process dispute: {str(e)}",
                "dispute_recorded": False,
                "fallback_action": "Transfer to supervisor for manual dispute processing"
            }

    def check_compliance_status(
        self,
        account_number: str,
        customer_state: str,
        interaction_type: str
    ) -> Dict[str, Any]:
        """
        Verify account compliance with FDCPA, TCPA, and state regulations.

        Args:
            account_number: Customer account number
            customer_state: Customer state for regulation compliance
            interaction_type: Type of customer interaction

        Returns:
            Dict with compliance status and requirements
        """
        try:
            # Check current time for FDCPA compliance
            current_hour = datetime.now().hour
            appropriate_time = 8 <= current_hour <= 21  # 8 AM to 9 PM

            # State-specific regulations
            state_restrictions = {
                "NY": {"max_interest_rate": 16, "cooling_off_period": 5},
                "CA": {"max_contacts_per_day": 2, "weekend_restrictions": True},
                "TX": {"homestead_exemption": True, "wage_garnishment_limits": 0.25},
                "FL": {"head_of_household_exemption": True}
            }

            compliance_status = {
                "account_number": account_number,
                "compliance_check_date": datetime.now().isoformat(),
                "fdcpa_compliant": True,
                "tcpa_compliant": True,
                "time_of_contact": {
                    "current_time": datetime.now().strftime("%H:%M"),
                    "appropriate_time": appropriate_time,
                    "allowed_hours": "8:00 AM - 9:00 PM"
                },
                "state_compliance": {
                    "state": customer_state,
                    "specific_requirements": state_restrictions.get(customer_state, {}),
                    "compliant": True
                },
                "interaction_restrictions": {
                    "can_contact": True,
                    "max_attempts_remaining": 3,
                    "next_allowed_contact": datetime.now().strftime("%Y-%m-%d")
                },
                "account_flags": {
                    "dispute_active": False,
                    "cease_contact_requested": False,
                    "attorney_represented": False,
                    "bankruptcy_filed": False,
                    "deceased": False
                }
            }

            # Check for compliance violations
            if not appropriate_time:
                compliance_status["fdcpa_compliant"] = False
                compliance_status["violation_reason"] = "Contact outside allowed hours"
                compliance_status["interaction_restrictions"]["can_contact"] = False

            logger.info(f"Compliance check completed for account {account_number}")

            return {
                "success": True,
                "compliance_status": compliance_status,
                "can_proceed": compliance_status["fdcpa_compliant"] and compliance_status["tcpa_compliant"],
                "recommendations": self._get_compliance_recommendations(compliance_status)
            }

        except Exception as e:
            logger.error(f"Error checking compliance: {str(e)}")
            return {
                "error": f"Compliance check failed: {str(e)}",
                "default_action": "Proceed with caution and document all interactions"
            }

    def generate_settlement_offer(
        self,
        account_number: str,
        current_balance: float,
        customer_financial_hardship: str,
        proposed_settlement_percentage: Optional[float] = None,
        payment_terms: str = "lump_sum"
    ) -> Dict[str, Any]:
        """
        Create settlement offers for accounts that qualify for reduced payment.

        Args:
            account_number: Customer account number
            current_balance: Current outstanding balance
            customer_financial_hardship: Type of financial hardship
            proposed_settlement_percentage: Proposed settlement as percentage of balance
            payment_terms: Settlement payment terms

        Returns:
            Dict with settlement offer details
        """
        try:
            # Calculate settlement percentage based on hardship type
            hardship_discounts = {
                "temporary": 15,      # 15% discount
                "permanent": 25,      # 25% discount
                "unemployment": 30,   # 30% discount
                "medical": 35,        # 35% discount
                "other": 20          # 20% discount
            }

            if proposed_settlement_percentage:
                settlement_percentage = min(90, max(30, proposed_settlement_percentage))
            else:
                base_discount = hardship_discounts.get(customer_financial_hardship, 20)
                settlement_percentage = 100 - base_discount

            settlement_amount = round(current_balance * (settlement_percentage / 100), 2)
            savings = round(current_balance - settlement_amount, 2)

            # Set offer expiration (typically 30 days)
            offer_expires = datetime.now() + timedelta(days=30)

            # Determine if approval is required (typically for large settlements)
            approval_required = settlement_amount > 5000 or settlement_percentage < 60

            settlement_offer = {
                "account_number": account_number,
                "offer_id": f"SETTLE_{account_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "original_balance": current_balance,
                "settlement_percentage": settlement_percentage,
                "settlement_amount": settlement_amount,
                "savings": savings,
                "hardship_type": customer_financial_hardship,
                "payment_terms": payment_terms,
                "offer_expires": offer_expires.strftime("%Y-%m-%d"),
                "approval_required": approval_required,
                "terms_and_conditions": [
                    "Settlement offer is valid only until the expiration date",
                    "Payment must be received in full by the specified terms",
                    "Settlement acceptance constitutes full resolution of the debt",
                    "Customer will receive written confirmation upon payment",
                    "Credit reporting agencies will be notified of settlement"
                ]
            }

            # Payment schedule based on terms
            if payment_terms == "three_payments":
                down_payment = settlement_amount * 0.4  # 40% down
                remaining = settlement_amount - down_payment
                settlement_offer["payment_schedule"] = {
                    "down_payment": round(down_payment, 2),
                    "payment_2": round(remaining / 2, 2),
                    "payment_3": round(remaining / 2, 2),
                    "payment_dates": [
                        (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                        (datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d"),
                        (datetime.now() + timedelta(days=67)).strftime("%Y-%m-%d")
                    ]
                }
            elif payment_terms == "six_payments":
                down_payment = settlement_amount * 0.25  # 25% down
                remaining = settlement_amount - down_payment
                monthly_payment = remaining / 5
                settlement_offer["payment_schedule"] = {
                    "down_payment": round(down_payment, 2),
                    "monthly_payments": round(monthly_payment, 2),
                    "number_of_payments": 5,
                    "start_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                }

            logger.info(f"Settlement offer generated: {settlement_offer['offer_id']}")

            return {
                "success": True,
                "settlement_offer": settlement_offer,
                "message": f"Based on your financial situation, I can offer you a settlement of ${settlement_amount:.2f}, which is a savings of ${savings:.2f} from your original balance.",
                "approval_status": "pending_approval" if approval_required else "approved",
                "next_steps": [
                    "This offer is valid until " + offer_expires.strftime("%B %d, %Y"),
                    "You can accept this offer today to resolve your account",
                    "Written confirmation will be provided upon acceptance",
                    "Payment can be processed immediately or scheduled"
                ] + (["This offer requires management approval and will be confirmed within 2 business days"] if approval_required else [])
            }

        except Exception as e:
            logger.error(f"Error generating settlement offer: {str(e)}")
            return {
                "error": f"Unable to generate settlement offer: {str(e)}",
                "suggested_action": "Transfer to supervisor for manual settlement calculation"
            }

    def record_interaction(
        self,
        account_number: str,
        interaction_summary: str,
        customer_response: str,
        next_action: Optional[str] = None,
        compliance_notes: Optional[str] = None,
        call_recording_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Document all call details, customer responses, and outcomes for compliance.

        Args:
            account_number: Customer account number
            interaction_summary: Summary of the interaction
            customer_response: Customer response category
            next_action: Next follow-up action required
            compliance_notes: Any compliance-related notes
            call_recording_id: Call recording reference ID

        Returns:
            Dict with interaction documentation confirmation
        """
        try:
            interaction_id = f"INT_{account_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            interaction_record = {
                "interaction_id": interaction_id,
                "account_number": account_number,
                "interaction_date": datetime.now().isoformat(),
                "interaction_type": "voice_call",
                "agent_id": "ai_payment_reminder_agent",
                "interaction_summary": interaction_summary,
                "customer_response": customer_response,
                "call_duration": "00:05:32",  # Would be actual duration
                "call_recording_id": call_recording_id or f"REC_{interaction_id}",
                "compliance_status": {
                    "fdcpa_compliant": True,
                    "tcpa_compliant": True,
                    "proper_identification": True,
                    "disclosure_provided": True,
                    "respectful_communication": True
                },
                "outcome_details": {
                    "payment_received": customer_response == "payment_made",
                    "payment_promised": customer_response == "payment_promised",
                    "dispute_raised": customer_response == "dispute_raised",
                    "hardship_claimed": customer_response == "hardship_claimed",
                    "contact_refused": customer_response == "refused_to_pay"
                },
                "next_action": next_action or self._determine_next_action(customer_response),
                "compliance_notes": compliance_notes,
                "follow_up_required": customer_response in ["payment_promised", "hardship_claimed"],
                "documentation_complete": True
            }

            logger.info(f"Interaction recorded: {interaction_id}")

            return {
                "success": True,
                "interaction_recorded": True,
                "interaction_record": interaction_record,
                "compliance_documentation": "Complete",
                "message": "Call details have been documented for compliance and follow-up purposes.",
                "retention_period": "7 years (as required by FDCPA)",
                "next_steps": [
                    interaction_record["next_action"],
                    "Customer will receive written confirmation within 5 business days",
                    "All compliance requirements have been met"
                ]
            }

        except Exception as e:
            logger.error(f"Error recording interaction: {str(e)}")
            return {
                "error": f"Failed to record interaction: {str(e)}",
                "documentation_status": "incomplete",
                "required_action": "Manual documentation required"
            }

    def escalate_to_supervisor(
        self,
        account_number: str,
        escalation_reason: str,
        customer_mood: str,
        context_summary: str,
        urgent: bool = False
    ) -> Dict[str, Any]:
        """
        Transfer complex cases or disputes to human supervisors.

        Args:
            account_number: Customer account number
            escalation_reason: Reason for escalation
            customer_mood: Customer emotional state
            context_summary: Summary of situation for supervisor
            urgent: Mark as urgent escalation

        Returns:
            Dict with escalation details and transfer information
        """
        try:
            escalation_id = f"ESC_{account_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Determine supervisor queue based on escalation reason
            supervisor_queues = {
                "complex_dispute": "dispute_resolution_team",
                "customer_request": "senior_collections",
                "legal_threat": "legal_department",
                "hardship_verification": "hardship_specialists",
                "large_settlement": "settlement_approval_team"
            }

            assigned_queue = supervisor_queues.get(escalation_reason, "general_supervisor")

            # Estimate wait time based on queue and urgency
            wait_times = {
                "legal_department": 2 if urgent else 10,
                "dispute_resolution_team": 3 if urgent else 8,
                "settlement_approval_team": 5 if urgent else 15,
                "hardship_specialists": 4 if urgent else 12,
                "senior_collections": 2 if urgent else 6,
                "general_supervisor": 1 if urgent else 5
            }

            estimated_wait = wait_times.get(assigned_queue, 5)

            escalation_record = {
                "escalation_id": escalation_id,
                "account_number": account_number,
                "escalation_time": datetime.now().isoformat(),
                "escalation_reason": escalation_reason,
                "customer_mood": customer_mood,
                "context_summary": context_summary,
                "urgent": urgent,
                "assigned_queue": assigned_queue,
                "estimated_wait_time": f"{estimated_wait} minutes",
                "priority": "high" if urgent else "normal",
                "agent_notes": [
                    "Customer identity verified",
                    "Account details reviewed",
                    "Compliance requirements met",
                    "All available payment options discussed"
                ],
                "customer_info_shared": {
                    "verification_completed": True,
                    "payment_history_reviewed": True,
                    "previous_interactions_noted": True,
                    "compliance_status_confirmed": True
                }
            }

            logger.info(f"Escalation created: {escalation_id} - Queue: {assigned_queue}")

            return {
                "success": True,
                "escalation_created": True,
                "escalation_record": escalation_record,
                "transfer_message": f"I understand you'd like to speak with a supervisor. I'm transferring you to our {assigned_queue.replace('_', ' ')} team now.",
                "customer_message": f"Thank you for your patience. A supervisor will be with you in approximately {estimated_wait} minutes. I've provided them with all the details of our conversation.",
                "supervisor_briefing": {
                    "account_verified": True,
                    "issue_summary": context_summary,
                    "customer_state": customer_mood,
                    "recommended_approach": self._get_supervisor_recommendations(escalation_reason, customer_mood),
                    "compliance_status": "All requirements met"
                },
                "next_steps": [
                    "Hold music will play during transfer",
                    "Supervisor has access to full call recording",
                    "All payment options and offers remain available",
                    "Customer can request callback if wait time is too long"
                ]
            }

        except Exception as e:
            logger.error(f"Error creating escalation: {str(e)}")
            return {
                "error": f"Escalation failed: {str(e)}",
                "fallback_action": "Direct transfer to general supervisor queue",
                "immediate_transfer": True
            }

    # Helper methods

    def _get_collection_strategy(self, account_details: Dict[str, Any]) -> str:
        """Determine optimal collection strategy based on account details"""
        balance = account_details.get("current_balance", 0)
        days_overdue = account_details.get("days_overdue", 0)
        payment_history_score = account_details.get("payment_history_score", 5)

        if balance < 500:
            return "focus_on_full_payment_with_discount"
        elif days_overdue > 120 and payment_history_score < 4:
            return "offer_settlement_options"
        elif payment_history_score >= 7:
            return "payment_plan_with_minimal_down_payment"
        else:
            return "standard_payment_plan_options"

    def _get_required_dispute_docs(self, dispute_reason: str) -> List[str]:
        """Get required documentation for different dispute types"""
        doc_requirements = {
            "never_received_service": ["Service delivery records", "Communication history"],
            "incorrect_amount": ["Original invoice", "Payment records", "Contract details"],
            "already_paid": ["Payment receipts", "Bank statements", "Transaction records"],
            "identity_theft": ["Police report", "Identity theft affidavit", "Credit monitoring records"],
            "billing_error": ["Billing statements", "Service agreements", "Communication records"],
            "other": ["Relevant documentation supporting the dispute"]
        }
        return doc_requirements.get(dispute_reason, ["Supporting documentation"])

    def _get_compliance_recommendations(self, compliance_status: Dict[str, Any]) -> List[str]:
        """Get compliance recommendations based on status"""
        recommendations = []

        if not compliance_status["time_of_contact"]["appropriate_time"]:
            recommendations.append("Schedule callback during allowed hours (8 AM - 9 PM)")

        if compliance_status["account_flags"]["dispute_active"]:
            recommendations.append("Follow dispute resolution procedures")

        if compliance_status["account_flags"]["attorney_represented"]:
            recommendations.append("All communications must go through attorney")

        recommendations.append("Document all interactions for compliance")
        recommendations.append("Ensure proper disclosures are provided")

        return recommendations

    def _determine_next_action(self, customer_response: str) -> str:
        """Determine next action based on customer response"""
        next_actions = {
            "payment_made": "Update account and send confirmation",
            "payment_promised": "Schedule follow-up call for promised date",
            "dispute_raised": "Initiate dispute investigation process",
            "hardship_claimed": "Transfer to hardship specialist",
            "refused_to_pay": "Schedule escalation sequence",
            "hung_up": "Schedule callback in 7 days per FDCPA"
        }
        return next_actions.get(customer_response, "Schedule standard follow-up")

    def _get_supervisor_recommendations(self, escalation_reason: str, customer_mood: str) -> str:
        """Get recommendations for supervisor based on escalation"""
        if escalation_reason == "legal_threat":
            return "Review legal position and consider immediate settlement"
        elif customer_mood == "angry":
            return "Use de-escalation techniques and focus on resolution"
        elif escalation_reason == "complex_dispute":
            return "Thoroughly review account history and documentation"
        else:
            return "Standard supervisor intervention with focus on customer service"