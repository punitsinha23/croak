from django.urls import path, re_path
from .views import (
    RegisterView,
    VerifyOtpView,
    LoginView,
    UserProfileView,
    listApiView,
    EditProfileView,
    FollowUnfollowView,
    RequestPasswordResetView,
    ResetPasswordView,
    GoogleLoginView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-otp/", VerifyOtpView.as_view(), name="verify_otp"),  
    path("login/", LoginView.as_view(), name="login"),
    path("me/", UserProfileView.as_view(), name="user-profile"),
    path("users/", listApiView.as_view(), name="user-list"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("update/", EditProfileView.as_view(), name="edit_profile"),
    path("<str:username>/follow/", FollowUnfollowView.as_view(), name="follow"),
    path("password-reset-request/", RequestPasswordResetView.as_view(), name="password_reset_request"),
    path("password-reset-confirm/", ResetPasswordView.as_view(), name="password_reset_confirm"),
    re_path(r"^google/?$", GoogleLoginView.as_view(), name="google_login"),
]
