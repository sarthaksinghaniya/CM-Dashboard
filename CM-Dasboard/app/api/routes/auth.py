import secrets
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.user import User, RoleEnum
from app.models.otp import OTP
from app.schemas.auth import OTPRequest, OTPVerify
from app.schemas.token import Token
from app.core import security
from app.core.config import settings
from app.services.email.smtp import async_send_otp_email

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/request-otp", status_code=status.HTTP_200_OK)
async def request_otp(
    payload: OTPRequest,
    db: AsyncSession = Depends(get_db)
):
    email = payload.email.lower().strip()
    
    # 1. Check existing OTP record for lockout state
    res = await db.execute(select(OTP).filter(OTP.email == email))
    otp_record = res.scalars().first()
    
    now = datetime.utcnow()
    
    if otp_record and otp_record.attempts >= 5:
        # Check if 15 minute lockout window is still active
        otp_created_naive = otp_record.created_at.replace(tzinfo=None) if otp_record.created_at.tzinfo else otp_record.created_at
        lockout_expiry = otp_created_naive + timedelta(minutes=15)
        if now < lockout_expiry:
            remaining_minutes = int((lockout_expiry - now).total_seconds() / 60) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many verification failures. Account locked out. Try again in {remaining_minutes} minutes."
            )
        else:
            # Lockout period expired; reset efforts
            otp_record.attempts = 0
            await db.commit()
            
    # 2. Check/Auto-Create Citizen User
    res_user = await db.execute(select(User).filter(User.email == email))
    user = res_user.scalars().first()
    
    if not user:
        logger.info(f"Auto-creating citizen user for email: {email}")
        user = User(
            name=email.split("@")[0].title(),
            email=email,
            role=RoleEnum.CITIZEN
        )
        try:
            db.add(user)
            await db.commit()
            await db.refresh(user)
        except IntegrityError:
            await db.rollback()
            # Parallel request created the user; fetch it
            res_user = await db.execute(select(User).filter(User.email == email))
            user = res_user.scalars().first()
            
    # 3. Generate Cryptographically Secure 6-digit OTP
    # SystemRandom is cryptographically secure
    otp_code = f"{secrets.SystemRandom().randint(100000, 999999):06d}"
    hashed_otp = security.get_password_hash(otp_code)
    
    # 4. Upsert OTP record
    if not otp_record:
        otp_record = OTP(
            email=email,
            otp_hash=hashed_otp,
            expiry=now + timedelta(minutes=4),
            attempts=0,
            created_at=now
        )
        db.add(otp_record)
    else:
        otp_record.otp_hash = hashed_otp
        otp_record.expiry = now + timedelta(minutes=4)
        otp_record.attempts = 0
        otp_record.created_at = now
        
    await db.commit()
    
    # 5. Send SMTP Email (Async thread wrapper)
    try:
        await async_send_otp_email(email, otp_code)
    except Exception as e:
        logger.error(f"Failed to deliver OTP email to {email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to send OTP verification email. Please check your credentials or try again later."
        )
        
    return {"status": "success", "message": "OTP verification code dispatched to email."}

@router.post("/verify-otp")
async def verify_otp(
    payload: OTPVerify,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    email = payload.email.lower().strip()
    
    # 1. Fetch OTP record
    res = await db.execute(select(OTP).filter(OTP.email == email))
    otp_record = res.scalars().first()
    
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP verification code has not been requested or has expired."
        )
        
    now = datetime.utcnow()
    
    # 2. Check Lockout State
    if otp_record.attempts >= 5:
        otp_created_naive = otp_record.created_at.replace(tzinfo=None) if otp_record.created_at.tzinfo else otp_record.created_at
        lockout_expiry = otp_created_naive + timedelta(minutes=15)
        if now < lockout_expiry:
            remaining_minutes = int((lockout_expiry - now).total_seconds() / 60) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUEST,
                detail=f"Account is locked out due to too many failed attempts. Try again in {remaining_minutes} minutes."
            )
        else:
            # Reset attempts if lockout expired
            otp_record.attempts = 0
            await db.commit()
            
    # 3. Check Expiry
    otp_expiry_naive = otp_record.expiry.replace(tzinfo=None) if otp_record.expiry.tzinfo else otp_record.expiry
    if now > otp_expiry_naive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP verification code has expired. Please request a new code."
        )
        
    # 4. Verify OTP Hash
    if not security.verify_password(payload.otp, otp_record.otp_hash):
        otp_record.attempts += 1
        
        # If max attempts reached, trigger lockout start (save current timestamp)
        if otp_record.attempts >= 5:
            otp_record.created_at = now
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect OTP. Too many failed attempts. Account locked out for 15 minutes."
            )
        else:
            await db.commit()
            remaining_attempts = 5 - otp_record.attempts
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Incorrect OTP code. {remaining_attempts} attempts remaining."
            )
            
    # 5. Success - Fetch User Profile
    res_user = await db.execute(select(User).filter(User.email == email))
    user = res_user.scalars().first()
    
    if not user:
        # Fallback creation just in case
        user = User(
            name=email.split("@")[0].title(),
            email=email,
            role=RoleEnum.CITIZEN
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    # 6. Delete OTP record from database
    await db.delete(otp_record)
    await db.commit()
    
    # 7. Issue JWT Token with Claims
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(
        subject=user.id,
        email=user.email,
        role=user.role.value,
        expires_delta=access_token_expires
    )
    
    refresh_token = security.create_refresh_token(subject=user.id)
    
    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        secure=False, # Set True in prod
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    return {
        "accessToken": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value
        }
    }

# --- Traditional Email/Password Auth ---

from app.schemas.auth import SignupRequest, LoginRequest, UserResponse
from app.api.deps import CurrentUser

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    email = payload.email.lower().strip()
    
    # Check if user exists
    res = await db.execute(select(User).filter(User.email == email))
    existing_user = res.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
        
    # Map string role to enum, default to CITIZEN if invalid
    try:
        user_role = RoleEnum(payload.role.upper())
    except ValueError:
        user_role = RoleEnum.CITIZEN
        
    # Create new user with hashed password
    hashed_password = security.get_password_hash(payload.password)
    user = User(
        name=payload.name.title(),
        email=email,
        password=hashed_password,
        role=user_role
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user

@router.post("/login")
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    email = payload.email.lower().strip()
    
    res = await db.execute(select(User).filter(User.email == email))
    user = res.scalars().first()
    
    if not user or not user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not security.verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(
        subject=user.id,
        email=user.email,
        role=user.role.value,
        expires_delta=access_token_expires
    )
    
    refresh_token = security.create_refresh_token(subject=user.id)
    
    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        secure=False, # Set True in prod
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    return {
        "accessToken": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value
        }
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: CurrentUser
):
    """
    Get current user profile based on JWT token.
    """
    return current_user

@router.post("/refresh")
async def refresh_token(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("refreshToken")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token found")
        
    try:
        payload = jwt.decode(token, settings.REFRESH_SECRET_KEY, algorithms=[security.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=403, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid refresh token")
        
    import uuid
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid user id in token")
        
    res = await db.execute(select(User).filter(User.id == user_uuid))
    user = res.scalars().first()
    
    if not user:
        raise HTTPException(status_code=403, detail="User not found")
        
    new_access_token = security.create_access_token(
        subject=user.id,
        email=user.email,
        role=user.role.value,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"accessToken": new_access_token}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("refreshToken", httponly=True, samesite="lax")
    return {"msg": "Logged out successfully"}
