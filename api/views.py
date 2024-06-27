import logging
from .models import Post
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from .serializers import PostSerializer, UserSerializer
from rest_framework.decorators import api_view, action
from django.contrib.auth.models import User
from .permissions import IsOwnerOrReadOnly
from django.http import Http404
from rest_framework.views import APIView
from django.core.files.storage import default_storage
from rest_framework.parsers import MultiPartParser


#VIEWSET POST
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = [MultiPartParser]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    def create(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        file_obj = request.data.get('file')
        title = request.data.get('title')
        content = request.data.get('content')

        if not file_obj or not title or not content:
            return Response({"message": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            post = Post(title=title, content=content, author=self.request.user)
            post.save()
            file_name = f'{post.id}_{file_obj.name}'
            default_storage.save(file_name, file_obj)
            post.image = file_name
            post.save()
            return Response({"message": "Post created and file uploaded successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error("Error creating post: %s", str(e))
            return Response({"message": "Error creating post"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        try:
            instance = self.get_object()
            title = instance.title
            self.perform_destroy(instance)
            return Response({"message": f"Post '{title}' deletado com sucesso."}, status=status.HTTP_204_NO_CONTENT)
        except Http404:
            logger.warning("Post não encontrado.")
            return Response({"message": "Post não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("Erro ao deletar o post: %s", str(e))
            return Response({"message": "Erro ao deletar o post."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if instance.author != self.request.user:
            return Response({"message": "Sem permissão para editar este post."}, status=status.HTTP_403_FORBIDDEN)
        
        image_url = instance.image.url if instance.image else None

        try:
            serializer.save()
            file_obj = request.data.get('file')
            if file_obj:
                # Excluindo a imagem anterior, se existir
                if image_url:
                    default_storage.delete(image_url)

            # Salvando a nova imagem e atualizando o post
            file_name = f'{instance.id}_{file_obj.name}'
            default_storage.save(file_name, file_obj)
            instance.image = file_name
            instance.save()
            return Response(serializer.data)
        except Exception as e:
            return Response({"message": "Erro ao editar o post."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#VIEWSET CRIAR USUARIO
class UserViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def create_user(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"user_id": user.id}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)