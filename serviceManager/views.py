# dockerapp/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RestartContainerSerializer
import docker


class RestartContainerView(APIView):
    def post(self, request):
        serializer = RestartContainerSerializer(data=request.data)
        
        if serializer.is_valid():
            container_id = serializer.validated_data['container_id']
            try:
                # Create a Docker client
                client = docker.from_env()

                # Get the specified container
                container = client.containers.get(container_id)

                # Restart the container
                container.restart()

                return Response({"message": f"Container '{container_id}' restarted successfully."}, status=status.HTTP_200_OK)
            except docker.errors.NotFound:
                return Response({"error": "Container not found."}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)