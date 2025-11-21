"""
Comprehensive unit tests for the accounts app.
Tests cover User model, authentication views, and serializers.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model."""

    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            name="Test User",
            role=User.Roles.STAFF,
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.role, User.Roles.STAFF)
        self.assertTrue(user.check_password("testpass123"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("adminpass123"))

    def test_user_str(self):
        """Test user string representation."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            name="Test User",
        )
        self.assertEqual(str(user), "Test User")

        # Without name, should use email
        user2 = User.objects.create_user(
            email="test2@example.com",
            password="testpass123",
        )
        self.assertEqual(str(user2), "test2@example.com")

    def test_user_roles(self):
        """Test user role choices."""
        self.assertEqual(User.Roles.STAFF, "staff")
        self.assertEqual(User.Roles.APPROVER_L1, "approver-level-1")
        self.assertEqual(User.Roles.APPROVER_L2, "approver-level-2")
        self.assertEqual(User.Roles.FINANCE, "finance")

    def test_email_unique(self):
        """Test email must be unique."""
        User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )

        with self.assertRaises(Exception):
            User.objects.create_user(
                email="test@example.com",
                password="testpass123",
            )

    def test_username_is_none(self):
        """Test username field is None."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        self.assertIsNone(user.username)


class LoginViewTest(TestCase):
    """Test login API endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            name="Test User",
            role=User.Roles.STAFF,
        )

    def test_login_success(self):
        """Test successful login."""
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "test@example.com",
                "password": "testpass123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("refresh_token", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], "test@example.com")

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "test@example.com",
                "password": "wrongpassword",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("token", response.data)

    def test_login_nonexistent_user(self):
        """Test login with non-existent user."""
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "nonexistent@example.com",
                "password": "testpass123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inactive_user(self):
        """Test login with inactive user."""
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "test@example.com",
                "password": "testpass123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_fields(self):
        """Test login with missing required fields."""
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "test@example.com",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CurrentUserViewTest(TestCase):
    """Test current user API endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            name="Test User",
            role=User.Roles.STAFF,
        )

    def test_get_current_user_authenticated(self):
        """Test getting current user when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/auth/user/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertEqual(response.data["name"], "Test User")
        self.assertEqual(response.data["role"], User.Roles.STAFF)

    def test_get_current_user_unauthenticated(self):
        """Test getting current user when not authenticated."""
        response = self.client.get("/api/auth/user/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserSerializerTest(TestCase):
    """Test UserSerializer."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            name="Test User",
            role=User.Roles.APPROVER_L1,
        )

    def test_serializer_fields(self):
        """Test serializer includes correct fields."""
        from accounts.serializers import UserSerializer

        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertIn("id", data)
        self.assertIn("email", data)
        self.assertIn("name", data)
        self.assertIn("role", data)
        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["name"], "Test User")
        self.assertEqual(data["role"], User.Roles.APPROVER_L1)

    def test_serializer_excludes_password(self):
        """Test serializer does not include password."""
        from accounts.serializers import UserSerializer

        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertNotIn("password", data)


class LoginSerializerTest(TestCase):
    """Test LoginSerializer."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )

    def test_valid_login(self):
        """Test serializer validates correct credentials."""
        from accounts.serializers import LoginSerializer
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.post("/api/auth/login/")

        serializer = LoginSerializer(
            data={
                "email": "test@example.com",
                "password": "testpass123",
            },
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["user"], self.user)

    def test_invalid_credentials(self):
        """Test serializer rejects invalid credentials."""
        from accounts.serializers import LoginSerializer
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.post("/api/auth/login/")

        serializer = LoginSerializer(
            data={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())

    def test_email_required(self):
        """Test email field is required."""
        from accounts.serializers import LoginSerializer
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.post("/api/auth/login/")

        serializer = LoginSerializer(
            data={"password": "testpass123"},
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())

    def test_password_required(self):
        """Test password field is required."""
        from accounts.serializers import LoginSerializer
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.post("/api/auth/login/")

        serializer = LoginSerializer(
            data={"email": "test@example.com"},
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
