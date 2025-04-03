from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from aiosmtplib.errors import SMTPResponseException

from .service import UserService
from .schemas import (
    UserCreateModel,
    UserLoginModel,
    UserBooksModel,
    EmailModel,
    PasswordResetRequestModel,
    PasswordResetConfirmModel,
)
from .utils import (
    create_access_token,
    verify_password,
    gennerate_passwd_hash,
    create_url_safe_token,
    decode_url_safe_token,
)
from .dependencies import (
    RefreshTokenBearer,
    AccessTokenBearer,
    get_current_user,
    RoleChecker,
)
from src.db.main import get_session
from src.db.redis import add_jti_to_blocklist
from src.errors import UserAlreadyExists, UserNotFound, InvalidCredentials, InvalidToken
from src.mail import mail, create_message
from src.celery_tasks import send_email
from src.config import Config


auth_router = APIRouter()
user_service = UserService()
role_checker = RoleChecker(["admin", "user"])

REFRESH_TOKEN_EXPIRY = 2


@auth_router.post("/send-mail")
async def send_mail(
    emails: EmailModel,
):
    emails = emails.addresses
    html = "<h1>Wecome to the app</h1>"
    subject = "Welcome to the app"
    # message = create_message(recipients=emails, subject="Wecome", body=html)
    # await mail.send_message(message)
    send_email.delay(emails, subject, html)
    return {"message": "Email send successfully"}


@auth_router.post(
    "/signup",
    # response_model=UserModel,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_account(
    user_data: UserCreateModel,
    bg_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """
    Create user account using email, username, first name, last name
    parmas:
        user_data: UserCreateModel
    """
    email = user_data.email
    user_exists = await user_service.user_exists(email, session)
    if user_exists:
        raise UserAlreadyExists()
    new_user = await user_service.create_user(user_data, session)
    token = create_url_safe_token({"email": email})
    link = f"http://{Config.DOMAIN}/api/v1/auth/verify/{token}"
    html = f"""
    <h1>Verify your Email</h1>
    <p>Please click this <a href="{link}">link</a> to verify your email</p>
    """
    # message = create_message(
    #     recipients=[email], subject="Verify you email", body=html_message
    # )
    # bg_tasks.add_task(mail.send_message, message)
    emails = [email]
    subject = "Verify you email"

    send_email.delay(emails, subject, html)
    return {
        "message": "Account Created! Check email to verify your account",
        "user": new_user,
    }


@auth_router.get("/verify/{token}")
async def verify_user_account(token: str, session: AsyncSession = Depends(get_session)):
    token_data = decode_url_safe_token(token)
    user_email = token_data.get("email")
    if user_email:
        user = await user_service.get_user_by_email(user_email, session)
        if not user:
            raise UserNotFound()
        await user_service.update_user(user, {"is_verufied": True}, session)
        return JSONResponse(
            content={"message": "Account verified successfully"},
            status_code=status.HTTP_200_OK,
        )
    return JSONResponse(
        content={"message": "Error occured during verification"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@auth_router.post("/login")
async def login_user(
    login_data: UserLoginModel, session: AsyncSession = Depends(get_session)
):
    email = login_data.email
    password = login_data.password
    user = await user_service.get_user_by_email(email, session)
    if user is not None:
        password_valid = verify_password(password, user.password_hash)
        if password_valid:
            access_token = create_access_token(
                user_data={
                    "email": user.email,
                    "user_uid": str(user.uid),
                    "role": user.role,
                },
            )
            refresh_token = create_access_token(
                user_data={"email": user.email, "user_uid": str(user.uid)},
                refresh=True,
                expiry=timedelta(days=REFRESH_TOKEN_EXPIRY),
            )
            return JSONResponse(
                content={
                    "message": "Login successful",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {"email": user.email, "uid": str(user.uid)},
                }
            )
    raise InvalidCredentials()


@auth_router.get("/refresh-token")
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    expiry_timestamp = token_details["exp"]

    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = create_access_token(user_data=token_details["user"])
        return JSONResponse(content={"access_token": new_access_token})

    raise InvalidToken()


@auth_router.get("/me", response_model=UserBooksModel)
async def get_current_user(
    user=Depends(get_current_user), _: bool = Depends(role_checker)
):
    return user


@auth_router.get("/logout")
async def revoke_token(token_datails: dict = Depends(AccessTokenBearer())):
    jti = token_datails["jti"]
    await add_jti_to_blocklist(jti)
    return JSONResponse(
        content={"message": "Logged Our Successfully"}, status_code=status.HTTP_200_OK
    )


"""
1. PROVIDE THE EMAIL -> password reset reques
2. SEND PASSWORD RESET LINK
3. RESET PASSWORD -> password reset confirm
"""


@auth_router.post("/password-reset-request")
async def password_reset_request(email_data: PasswordResetRequestModel):
    email = email_data.email
    token = create_url_safe_token({"email": email})
    link = f"http://{Config.DOMAIN}/api/v1/auth/password-reset-confirm/{token}"
    html_message = f"""
    <h1>Reset Your Password</h1>
    <p>Please click this <a href="{link}">link</a> to Reset</p>
    """
    message = create_message(
        recipients=[email], subject="Reset Your Password", body=html_message
    )
    try:
        await mail.send_message(message)
    except SMTPResponseException as exc:
        print("SMTPResponseException ignored:", exc)
    return JSONResponse(
        content={
            "message": "please check your email for instructions to reset your password"
        },
        status_code=status.HTTP_200_OK,
    )


@auth_router.post("/password-reset-confirm/{token}")
async def resrt_account_password(
    token: str,
    password: PasswordResetConfirmModel,
    session: AsyncSession = Depends(get_session),
):
    new_password = password.new_password
    confirm_password = password.confirm_new_password

    if new_password != confirm_password:
        raise HTTPException(
            detail="Passwords do not match",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    token_data = decode_url_safe_token(token)
    user_email = token_data.get("email")
    if user_email:
        user = await user_service.get_user_by_email(user_email, session)
        if not user:
            raise UserNotFound()
        password_hash = gennerate_passwd_hash(new_password)
        await user_service.update_user(user, {"password_hash": password_hash}, session)
        return JSONResponse(
            content={"message": "Password reset Successfully"},
            status_code=status.HTTP_200_OK,
        )
    return JSONResponse(
        content={"message": "Error occured during Password reset"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
