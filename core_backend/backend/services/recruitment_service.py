"""
Recruitment Service for AI Labs Africa

Handles job application submissions including:
- Application data validation and storage
- CV/resume file uploads to Hetzner Storage Box
- Email notifications to careers@ailabsafrica.com
- Application status management

Author: AI Labs Africa
"""

import logging
import os
import secrets
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, EmailStr

logger = logging.getLogger(__name__)


class JobApplication(BaseModel):
    """Job application model."""
    application_id: str
    name: str
    email: EmailStr
    phone: str
    position: str
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    cover_letter: str
    resume_filename: Optional[str] = None
    resume_url: Optional[str] = None
    status: str = "new"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    notes: List[Dict[str, Any]] = Field(default_factory=list)


class RecruitmentService:
    """
    Service for managing job applications at AI Labs Africa.
    """

    # Valid job positions
    VALID_POSITIONS = [
        "Machine Learning Engineer",
        "Full Stack Developer",
        "AI Research Scientist",
        "Product Manager",
        "Sales Executive",
        "Customer Success Manager",
        "Sales and Marketing Team Lead",
        "General Application"
    ]

    # Valid application statuses
    VALID_STATUSES = ["new", "reviewing", "interviewed", "hired", "rejected"]

    def __init__(self, db=None):
        """
        Initialize recruitment service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self._storage = None
        self._email_service = None

        # Initialize storage
        try:
            from apps.shared.storage.hetzner_storage_box import HetznerStorageBox
            self._storage = HetznerStorageBox()
            logger.info("Hetzner storage initialized for recruitment")
        except Exception as e:
            logger.warning(f"Hetzner storage not available: {e}")

        # Initialize email service
        try:
            from apps.shared.services.unified_email_service import get_email_service
            self._email_service = get_email_service()
            logger.info("Email service initialized for recruitment")
        except Exception as e:
            logger.warning(f"Email service not available: {e}")

    def set_db(self, db):
        """Set MongoDB database instance."""
        self.db = db

    def generate_application_id(self) -> str:
        """Generate unique application ID."""
        return f"APP-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"

    async def upload_resume(
        self,
        file_content: bytes,
        filename: str,
        applicant_name: str
    ) -> Optional[str]:
        """
        Upload resume file to Hetzner Storage Box.

        Args:
            file_content: File content as bytes
            filename: Original filename
            applicant_name: Applicant's name for naming

        Returns:
            URL to uploaded file or None if upload failed
        """
        if self._storage is None:
            logger.warning("Storage not available, skipping resume upload")
            return None

        import tempfile

        try:
            # Connect to storage if not connected
            if not self._storage.connected:
                await self._storage.connect()

            # Generate unique filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            safe_name = "".join(
                c for c in applicant_name if c.isalnum() or c in ' -_'
            ).strip().replace(' ', '_')
            file_ext = os.path.splitext(filename)[1].lower()
            unique_filename = f"cv_{safe_name}_{timestamp}_{secrets.token_hex(4)}{file_ext}"

            # Save to temporary file first
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name

            try:
                # Upload to storage
                remote_path = f"recruitment/resumes/{unique_filename}"
                result = await self._storage.upload_file(
                    local_path=tmp_path,
                    remote_path=remote_path
                )

                if result:
                    # Construct the public URL
                    resume_url = f"https://u497034-sub1.your-storagebox.de/recruitment/resumes/{unique_filename}"
                    logger.info(f"Resume uploaded: {resume_url}")
                    return resume_url

                return None
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"Resume upload error: {e}")
            return None

    async def send_notification(self, application: JobApplication) -> bool:
        """
        Send email notification about new application.

        Args:
            application: JobApplication object

        Returns:
            True if notification sent successfully
        """
        if not self._email_service:
            logger.warning("Email service not available, skipping notification")
            return False

        try:
            subject = f"New Job Application: {application.position} - {application.name}"

            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; }}
                    .header {{
                        background: linear-gradient(135deg, #1e3a8a, #d97706);
                        color: white;
                        padding: 20px;
                        border-radius: 8px 8px 0 0;
                    }}
                    .content {{
                        background: #f9fafb;
                        padding: 20px;
                        border: 1px solid #e5e7eb;
                        border-radius: 0 0 8px 8px;
                    }}
                    .field {{
                        margin-bottom: 15px;
                        padding: 10px;
                        background: white;
                        border-radius: 4px;
                        border-left: 3px solid #1e3a8a;
                    }}
                    .field-label {{
                        font-weight: bold;
                        color: #374151;
                        margin-bottom: 5px;
                    }}
                    .cover-letter {{
                        background: white;
                        padding: 15px;
                        border-radius: 8px;
                        border: 1px solid #e5e7eb;
                        white-space: pre-wrap;
                    }}
                    .action-btn {{
                        display: inline-block;
                        background: #1e3a8a;
                        color: white;
                        padding: 10px 20px;
                        border-radius: 4px;
                        text-decoration: none;
                        margin-right: 10px;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2 style="margin: 0;">New Job Application Received</h2>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Application ID: {application.application_id}</p>
                </div>

                <div class="content">
                    <h3 style="color: #1e3a8a; margin-top: 0;">Applicant Details</h3>

                    <div class="field">
                        <div class="field-label">Position</div>
                        <div style="color: #d97706; font-weight: bold; font-size: 18px;">{application.position}</div>
                    </div>

                    <div class="field">
                        <div class="field-label">Full Name</div>
                        <div>{application.name}</div>
                    </div>

                    <div class="field">
                        <div class="field-label">Email</div>
                        <div><a href="mailto:{application.email}">{application.email}</a></div>
                    </div>

                    <div class="field">
                        <div class="field-label">Phone</div>
                        <div><a href="tel:{application.phone}">{application.phone}</a></div>
                    </div>

                    {f'<div class="field"><div class="field-label">LinkedIn</div><div><a href="{application.linkedin}" target="_blank">{application.linkedin}</a></div></div>' if application.linkedin else ''}

                    {f'<div class="field"><div class="field-label">Portfolio</div><div><a href="{application.portfolio}" target="_blank">{application.portfolio}</a></div></div>' if application.portfolio else ''}

                    <h3 style="color: #1e3a8a;">Cover Letter</h3>
                    <div class="cover-letter">{application.cover_letter}</div>

                    <h3 style="color: #1e3a8a;">Resume/CV</h3>
                    {f'<a href="{application.resume_url}" class="action-btn" target="_blank">Download Resume</a>' if application.resume_url else '<p>No resume uploaded</p>'}

                    <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                        <a href="mailto:{application.email}?subject=Re: Your Application for {application.position} at AI Labs Africa" class="action-btn">
                            Reply to Applicant
                        </a>
                    </div>

                    <p style="margin-top: 20px; color: #6b7280; font-size: 12px;">
                        Received: {application.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
                    </p>
                </div>
            </body>
            </html>
            """

            plain_body = f"""
New Job Application Received
Application ID: {application.application_id}

Position: {application.position}
Name: {application.name}
Email: {application.email}
Phone: {application.phone}
LinkedIn: {application.linkedin or 'Not provided'}
Portfolio: {application.portfolio or 'Not provided'}

Cover Letter:
{application.cover_letter}

Resume URL: {application.resume_url or 'Not uploaded'}

Received: {application.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
            """

            # Send to careers email
            result = await self._email_service.send_email(
                to="careers@ailabsafrica.com",
                subject=subject,
                body=plain_body,
                html_body=html_body,
                from_email="noreply@ailabsafrica.com"
            )

            if result.get("success"):
                logger.info(f"Notification sent for {application.application_id}")
                return True

            logger.error(f"Failed to send notification: {result.get('error')}")
            return False

        except Exception as e:
            logger.error(f"Notification error: {e}")
            return False

    async def send_applicant_confirmation(self, application: JobApplication) -> bool:
        """
        Send confirmation email to the applicant.

        Args:
            application: JobApplication object

        Returns:
            True if confirmation sent successfully
        """
        if not self._email_service:
            logger.warning("Email service not available, skipping applicant confirmation")
            return False

        try:
            subject = f"Application Received: {application.position} - AI Labs Africa"

            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333; }}
                    .header {{
                        background: linear-gradient(135deg, #1e3a8a, #d97706);
                        color: white;
                        padding: 30px;
                        text-align: center;
                        border-radius: 8px 8px 0 0;
                    }}
                    .header img {{
                        max-width: 150px;
                        margin-bottom: 15px;
                    }}
                    .content {{
                        background: #ffffff;
                        padding: 30px;
                        border: 1px solid #e5e7eb;
                        border-radius: 0 0 8px 8px;
                    }}
                    .highlight {{
                        background: #f0f9ff;
                        border-left: 4px solid #1e3a8a;
                        padding: 15px;
                        margin: 20px 0;
                        border-radius: 0 8px 8px 0;
                    }}
                    .app-id {{
                        font-family: monospace;
                        background: #e5e7eb;
                        padding: 5px 10px;
                        border-radius: 4px;
                        font-weight: bold;
                    }}
                    .footer {{
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #e5e7eb;
                        color: #6b7280;
                        font-size: 12px;
                        text-align: center;
                    }}
                    .social-links a {{
                        color: #1e3a8a;
                        text-decoration: none;
                        margin: 0 10px;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1 style="margin: 0; font-size: 24px;">AI Labs Africa</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Revolutionizing Africa with AI</p>
                </div>

                <div class="content">
                    <h2 style="color: #1e3a8a; margin-top: 0;">Thank You for Your Application!</h2>

                    <p>Dear {application.name},</p>

                    <p>Thank you for your interest in joining AI Labs Africa! We have received your application for the <strong>{application.position}</strong> position.</p>

                    <div class="highlight">
                        <p style="margin: 0;"><strong>Application Reference:</strong> <span class="app-id">{application.application_id}</span></p>
                        <p style="margin: 10px 0 0 0;"><strong>Position:</strong> {application.position}</p>
                        <p style="margin: 5px 0 0 0;"><strong>Submitted:</strong> {application.created_at.strftime('%B %d, %Y at %H:%M UTC')}</p>
                    </div>

                    <h3 style="color: #1e3a8a;">What's Next?</h3>
                    <ol style="line-height: 1.8;">
                        <li>Our recruitment team will review your application</li>
                        <li>If your profile matches our requirements, we'll reach out to schedule an interview</li>
                        <li>You can expect to hear from us within <strong>5 business days</strong></li>
                    </ol>

                    <p>Please keep your application reference number handy for any future correspondence.</p>

                    <p style="margin-top: 25px;">
                        Best regards,<br>
                        <strong>AI Labs Africa Recruitment Team</strong>
                    </p>

                    <div class="footer">
                        <p class="social-links">
                            <a href="https://ailabsafrica.com">Website</a> |
                            <a href="https://linkedin.com/company/ailabsafrica">LinkedIn</a> |
                            <a href="https://twitter.com/ailabsafrica">Twitter</a>
                        </p>
                        <p>AI Labs Africa | Accra, Ghana</p>
                        <p style="color: #9ca3af; font-size: 11px;">
                            This is an automated message. Please do not reply directly to this email.<br>
                            For inquiries, contact us at <a href="mailto:careers@ailabsafrica.com" style="color: #1e3a8a;">careers@ailabsafrica.com</a>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """

            plain_body = f"""
Thank You for Your Application!

Dear {application.name},

Thank you for your interest in joining AI Labs Africa! We have received your application for the {application.position} position.

Application Reference: {application.application_id}
Position: {application.position}
Submitted: {application.created_at.strftime('%B %d, %Y at %H:%M UTC')}

What's Next?
1. Our recruitment team will review your application
2. If your profile matches our requirements, we'll reach out to schedule an interview
3. You can expect to hear from us within 5 business days

Please keep your application reference number handy for any future correspondence.

Best regards,
AI Labs Africa Recruitment Team

---
AI Labs Africa | Accra, Ghana
Website: https://ailabsafrica.com
For inquiries: careers@ailabsafrica.com
            """

            result = await self._email_service.send_email(
                to=application.email,
                subject=subject,
                body=plain_body,
                html_body=html_body,
                from_email="AI Labs Africa Careers <careers@ailabsafrica.com>"
            )

            if result.get("success"):
                logger.info(f"Confirmation email sent to {application.email} for {application.application_id}")
                return True

            logger.error(f"Failed to send confirmation: {result.get('error')}")
            return False

        except Exception as e:
            logger.error(f"Confirmation email error: {e}")
            return False

    async def submit_application(
        self,
        name: str,
        email: str,
        phone: str,
        position: str,
        cover_letter: str,
        linkedin: Optional[str] = None,
        portfolio: Optional[str] = None,
        resume_content: Optional[bytes] = None,
        resume_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit a new job application.

        Args:
            name: Applicant's full name
            email: Email address
            phone: Phone number
            position: Position applying for
            cover_letter: Cover letter text
            linkedin: LinkedIn profile URL
            portfolio: Portfolio URL
            resume_content: Resume file content
            resume_filename: Original resume filename

        Returns:
            Submission result with application ID
        """
        try:
            # Validate position
            if position not in self.VALID_POSITIONS:
                return {
                    "success": False,
                    "error": f"Invalid position. Valid options: {', '.join(self.VALID_POSITIONS)}"
                }

            # Upload resume if provided
            resume_url = None
            if resume_content and resume_filename:
                resume_url = await self.upload_resume(
                    file_content=resume_content,
                    filename=resume_filename,
                    applicant_name=name
                )

            # Generate application ID
            application_id = self.generate_application_id()

            # Create application object
            application = JobApplication(
                application_id=application_id,
                name=name,
                email=email,
                phone=phone,
                position=position,
                linkedin=linkedin,
                portfolio=portfolio,
                cover_letter=cover_letter,
                resume_filename=resume_filename,
                resume_url=resume_url,
                status="new",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Save to database
            if self.db is not None:
                application_dict = application.dict()
                result = await self.db.job_applications.insert_one(application_dict)

                if not result.inserted_id:
                    return {
                        "success": False,
                        "error": "Failed to save application to database"
                    }

            logger.info(f"Application submitted: {application_id} for {position}")

            # Send internal notification to careers team
            await self.send_notification(application)

            # Send confirmation email to applicant
            await self.send_applicant_confirmation(application)

            return {
                "success": True,
                "message": f"Application submitted successfully! Your application ID is {application_id}. We'll review your application and get back to you within 5 business days.",
                "application_id": application_id,
                "resume_url": resume_url
            }

        except Exception as e:
            logger.error(f"Application submission error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_applications(
        self,
        status: Optional[str] = None,
        position: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> Dict[str, Any]:
        """
        List job applications.

        Args:
            status: Filter by status
            position: Filter by position
            limit: Max results
            skip: Results to skip

        Returns:
            List of applications
        """
        if self.db is None:
            return {"success": False, "error": "Database not available"}

        try:
            query = {}
            if status:
                query["status"] = status
            if position:
                query["position"] = position

            cursor = self.db.job_applications.find(query).sort(
                "created_at", -1
            ).skip(skip).limit(limit)

            applications = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                applications.append(doc)

            total = await self.db.job_applications.count_documents(query)

            return {
                "success": True,
                "count": total,
                "applications": applications
            }

        except Exception as e:
            logger.error(f"Error listing applications: {e}")
            return {"success": False, "error": str(e)}

    async def get_application(self, application_id: str) -> Dict[str, Any]:
        """
        Get a specific application.

        Args:
            application_id: Application ID

        Returns:
            Application details
        """
        if self.db is None:
            return {"success": False, "error": "Database not available"}

        try:
            application = await self.db.job_applications.find_one(
                {"application_id": application_id}
            )

            if not application:
                return {
                    "success": False,
                    "error": f"Application not found: {application_id}"
                }

            application["_id"] = str(application["_id"])

            return {
                "success": True,
                "application": application
            }

        except Exception as e:
            logger.error(f"Error getting application: {e}")
            return {"success": False, "error": str(e)}

    async def update_status(
        self,
        application_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update application status.

        Args:
            application_id: Application ID
            status: New status
            notes: Optional notes

        Returns:
            Update result
        """
        if self.db is None:
            return {"success": False, "error": "Database not available"}

        if status not in self.VALID_STATUSES:
            return {
                "success": False,
                "error": f"Invalid status. Valid options: {', '.join(self.VALID_STATUSES)}"
            }

        try:
            update_doc = {
                "$set": {
                    "status": status,
                    "updated_at": datetime.utcnow()
                }
            }

            if notes:
                update_doc["$push"] = {
                    "notes": {
                        "text": notes,
                        "status": status,
                        "timestamp": datetime.utcnow()
                    }
                }

            result = await self.db.job_applications.update_one(
                {"application_id": application_id},
                update_doc
            )

            if result.matched_count == 0:
                return {
                    "success": False,
                    "error": f"Application not found: {application_id}"
                }

            return {
                "success": True,
                "message": f"Status updated to: {status}",
                "application_id": application_id
            }

        except Exception as e:
            logger.error(f"Error updating application: {e}")
            return {"success": False, "error": str(e)}

    def get_positions(self) -> List[str]:
        """Get list of valid positions."""
        return self.VALID_POSITIONS

    def get_statuses(self) -> List[str]:
        """Get list of valid statuses."""
        return self.VALID_STATUSES


# Global service instance
recruitment_service = RecruitmentService()


def get_recruitment_service() -> RecruitmentService:
    """Get the recruitment service instance."""
    return recruitment_service
