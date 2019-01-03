from datetime import datetime as dt
from datetime import timezone

from rest_framework.generics import GenericAPIView
from rest_framework.permissions import (
    IsAuthenticated
)
from django.apps import apps
from rest_framework.response import Response
from rest_framework import status, serializers
import readtime
from authors.apps.articles.serializers import ArticleSerializer, get_article

Readers = apps.get_model('read_stats', 'Readers')


class AddRead(GenericAPIView):
    """Mark an article as read."""

    permission_classes = (IsAuthenticated,)
    serializer_class = ArticleSerializer

    def get(self, request, slug):
        """Mark an article as read and eliminate fake reads."""
        article = get_article(slug)
        profile = request.user.profile
        # Check if the user has read the article before
        read_before = Readers.objects.filter(article=article,
                                             reader=profile).last()

        if read_before:
            # Get the time difference between this reading and the last reading
            between_reads = dt.now(timezone.utc) - read_before.last_read
            article_read_time = readtime.of_text(article.body).minutes
            # Check if its less than the read time, break if so

            if (between_reads.total_seconds() / 60.0) < article_read_time:
                raise serializers.ValidationError(
                    "Read for less time than the read-time.")
        # If user hasn't read it before

        read = Readers(article=article, reader=profile)
        read.save()
        message = {
            "success": "Article '{}' read.".format(article.title)}
        return Response(message, status=status.HTTP_200_OK)


class GetReads(GenericAPIView):

    permission_classes = (IsAuthenticated,)
    serializer_class = ArticleSerializer

    def get(self, request):
        """Get my reads."""
        profile = request.user.profile

        reads = Readers.objects.filter(
            reader=profile).values(
            'article__title', 'article__slug').distinct()
        message = {"reads": reads}
        return Response(message, status=status.HTTP_200_OK)
