import os
import sys
import asyncio
from unittest.mock import patch, MagicMock
import shutil

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'CM-Dasboard')))

from app.db.session import AsyncSessionLocal
from app.models.complaint import Complaint
from app.models.attachment import Attachment
from app.models.user import User

from httpx import AsyncClient
from app.main import app

async def test_complaints_flow():
    print("Starting Complaint Submission Service integration tests...")

    test_email = "citizen_complaint_test@delhi.gov.in"

    # Clean up any existing records from this test email
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        res_comp = await session.execute(select(Complaint).filter(Complaint.citizen_email == test_email))
        complaints = res_comp.scalars().all()
        for comp in complaints:
            await session.delete(comp)
        await session.commit()
        print(" -> Cleaned up old test complaints.")

    # Base directory for uploads cleanup
    UPLOAD_DIR = os.path.join("app", "static", "uploads")

    import httpx
    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # --- Test 1: Successful Submission (No category provided, triggers ML classifier fallback) ---
        print("\nTest 1: Submitting complaint without category (ML classifier fallback)...")
        payload = {
            "citizen_name": "Arvind Kumar",
            "citizen_email": test_email,
            "citizen_phone": "+919876543210",
            "title": "Water Leakage in Sector 5 Rohini",
            "description": "Clean drinking water is leaking from the main pipe in Sector 5 Rohini for the last 3 days. Huge wastage of water.",
            "district": "North Delhi"
        }
        
        response = await client.post("/api/v1/complaints/", data=payload)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        res_data = response.json()
        assert "ticket_id" in res_data
        assert res_data["status"] == "OPEN"
        assert "estimated_sla" in res_data
        
        ticket_id_1 = res_data["ticket_id"]
        print(f" -> PASSED: Complaint submitted. Issued Ticket ID: {ticket_id_1}, Status: {res_data['status']}, SLA: {res_data['estimated_sla']}")

        # Verify DB entry & classification output
        async with AsyncSessionLocal() as session:
            res_db = await session.execute(select(Complaint).filter(Complaint.ticket_id == ticket_id_1))
            db_complaint = res_db.scalars().first()
            assert db_complaint is not None
            assert db_complaint.category != ""
            assert db_complaint.department != ""
            print(f" -> Verified database storage: Category='{db_complaint.category}', Department='{db_complaint.department}', Priority='{db_complaint.priority}'")

        # --- Test 2: Validation of Invalid Email and Phone Format ---
        print("\nTest 2: Validation of malformed email format...")
        bad_payload = payload.copy()
        bad_payload["citizen_email"] = "not-an-email"
        response = await client.post("/api/v1/complaints/", data=bad_payload)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "Invalid email format" in response.json()["detail"]
        print(" -> PASSED: Rejected invalid email format.")

        print(" -> Validation of malformed phone number format...")
        bad_payload = payload.copy()
        bad_payload["citizen_phone"] = "12345" # Too short
        response = await client.post("/api/v1/complaints/", data=bad_payload)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "Invalid phone number format" in response.json()["detail"]
        print(" -> PASSED: Rejected invalid phone format.")

        # --- Test 3: Duplicate submission check (within 5 minutes) ---
        print("\nTest 3: Duplicate submission check...")
        # Submitting the same payload again immediately should throw HTTP 400
        response = await client.post("/api/v1/complaints/", data=payload)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "Duplicate complaint submitted" in response.json()["detail"]
        print(" -> PASSED: Rejected duplicate submission within 5-minute threshold.")

        # --- Test 4: Submission with attachments ---
        print("\nTest 4: Submitting complaint with valid attachments...")
        # Create some files in memory
        files = [
            ("attachments", ("test_doc.pdf", b"%PDF-1.4 dummy pdf content", "application/pdf")),
            ("attachments", ("image.png", b"\x89PNG\r\n\x1a\n dummy png content", "image/png"))
        ]
        new_payload = payload.copy()
        new_payload["title"] = "Broken Streetlight in Rohini"
        new_payload["description"] = "Streetlight is broken near pocket B4 Rohini. Extremely dark at night."
        
        response = await client.post("/api/v1/complaints/", data=new_payload, files=files)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        ticket_id_2 = response.json()["ticket_id"]
        print(f" -> PASSED: Complaint with attachments registered successfully. Ticket ID: {ticket_id_2}")

        # Check DB attachments
        async with AsyncSessionLocal() as session:
            res_db = await session.execute(select(Complaint).filter(Complaint.ticket_id == ticket_id_2))
            comp_rec = res_db.scalars().first()
            assert comp_rec is not None
            
            res_attach = await session.execute(select(Attachment).filter(Attachment.complaint_id == comp_rec.id))
            db_attachments = res_attach.scalars().all()
            assert len(db_attachments) == 2
            
            for attachment in db_attachments:
                file_url = attachment.file_url
                assert file_url.startswith("/static/uploads/")
                # Verify file actually written to local disk
                local_path = os.path.join("app", file_url.lstrip("/"))
                assert os.path.exists(local_path), f"File {local_path} does not exist on disk!"
                print(f" -> Verified attachment stored on disk at: {local_path}")
            print(" -> PASSED: Attachments successfully registered in DB and saved on disk.")

        # --- Test 5: File Upload Restrictions (Too many files, forbidden extension, size limit) ---
        print("\nTest 5: Attachment count limit (max 5)...")
        six_files = [
            ("attachments", (f"file_{i}.jpg", b"dummy content", "image/jpeg")) for i in range(6)
        ]
        response = await client.post("/api/v1/complaints/", data=payload, files=six_files)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "Too many files" in response.json()["detail"]
        print(" -> PASSED: Rejected upload of > 5 files.")

        print(" -> Attachment extension validation (forbidden extension)...")
        bad_ext_file = [
            ("attachments", ("danger.txt", b"some plain text description", "text/plain"))
        ]
        response = await client.post("/api/v1/complaints/", data=payload, files=bad_ext_file)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "Unsupported file extension" in response.json()["detail"]
        print(" -> PASSED: Rejected unsupported file extension (.txt).")

        print(" -> Attachment size limit (max 10 MB)...")
        large_file_content = b"a" * (10 * 1024 * 1024 + 100) # 10MB + 100 bytes
        large_file = [
            ("attachments", ("huge.jpg", large_file_content, "image/jpeg"))
        ]
        response = await client.post("/api/v1/complaints/", data=payload, files=large_file)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "exceeds the 10 MB size limit" in response.json()["detail"]
        print(" -> PASSED: Rejected file exceeding 10 MB limit.")

        # --- Test 6: Virus infected file detection (EICAR check) ---
        print("\nTest 6: EICAR virus signature check...")
        eicar_content = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
        virus_file = [
            ("attachments", ("virus.jpg", eicar_content, "image/jpeg"))
        ]
        response = await client.post("/api/v1/complaints/", data=payload, files=virus_file)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "Virus detected" in response.json()["detail"]
        print(" -> PASSED: Detected virus signature and rejected upload.")

        # --- Test 7: Storage failure & database rollback ---
        print("\nTest 7: Storage failure database rollback...")
        fail_files = [
            ("attachments", ("save_fail.png", b"dummy png", "image/png"))
        ]
        fail_payload = payload.copy()
        fail_payload["title"] = "Should Rollback Complaint"
        fail_payload["description"] = "A unique description explaining rollback validation test"

        # Mock writing to a file to raise OSError to simulate disk failure
        with patch("app.api.routes.complaints.open", side_effect=OSError("Disk full or write permission error")):
            response = await client.post("/api/v1/complaints/", data=fail_payload, files=fail_files)
            assert response.status_code == 500, f"Expected 500, got {response.status_code}"
            assert "Failed to register complaint due to storage" in response.json()["detail"]

        # Verify that complaint was NOT added to the database
        async with AsyncSessionLocal() as session:
            res_db = await session.execute(select(Complaint).filter(Complaint.description == "A unique description explaining rollback validation test"))
            rolled_back_comp = res_db.scalars().first()
            assert rolled_back_comp is None, "Complaint record was not rolled back upon storage failure!"
            print(" -> PASSED: Verified storage write failure rolls back the database transaction.")

        # --- Test 8: Non-blocking email dispatch failure check ---
        print("\nTest 8: Email delivery failure handling...")
        email_fail_payload = payload.copy()
        email_fail_payload["title"] = "Succeeds Even if Email Fails"
        email_fail_payload["description"] = "Valid description for testing email failures."

        with patch("app.services.email.smtp.sync_send_email", side_effect=Exception("SMTP Connection timed out")):
            response = await client.post("/api/v1/complaints/", data=email_fail_payload)
            assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
            print(" -> PASSED: Submission succeeds even when the SMTP email fails to deliver.")

    # Cleanup DB records
    async with AsyncSessionLocal() as session:
        res_comp = await session.execute(select(Complaint).filter(Complaint.citizen_email == test_email))
        complaints = res_comp.scalars().all()
        for comp in complaints:
            await session.delete(comp)
        await session.commit()
        print("\n -> Cleaned up database test complaints.")

    # Cleanup uploads folder test artifacts
    if os.path.exists(UPLOAD_DIR):
        for fn in os.listdir(UPLOAD_DIR):
            # Clean only UUID generated test files
            if len(fn) > 32 and "_" in fn:
                try:
                    os.remove(os.path.join(UPLOAD_DIR, fn))
                except Exception:
                    pass
        print(" -> Cleaned up uploaded files from test script.")

    print("\nAll complaint submission service integration tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_complaints_flow())
