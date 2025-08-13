import json
import os

from django.core.management.base import BaseCommand
from django.test import RequestFactory
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.permissions import AllowAny


class Command(BaseCommand):
    """
    Django management command to generate OpenAPI schema (Swagger) JSON and
    write it to interfaces/openapi.json.
    """

    # PUBLIC_INTERFACE
    def handle(self, *args, **options):
        """Generate OpenAPI schema and save it to interfaces/openapi.json."""
        factory = RequestFactory()
        django_request = factory.get("/api/?format=openapi")

        schema_view = get_schema_view(
            openapi.Info(
                title="Notes Backend API",
                default_version="v1",
                description="REST API for authentication, notes CRUD, and organization by tags and categories.",
            ),
            public=True,
            permission_classes=(AllowAny,),
        )

        # Call the view with the raw Django HttpRequest
        response = schema_view.without_ui(cache_timeout=0)(django_request)
        response.render()

        openapi_schema = json.loads(response.content.decode())

        output_dir = "interfaces"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "openapi.json")

        with open(output_path, "w") as f:
            json.dump(openapi_schema, f, indent=2)
