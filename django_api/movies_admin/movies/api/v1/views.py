# views.py
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView
from ...models import FilmWork, Person, Genre


class MoviesApiMixin:
    model = FilmWork
    http_method_names = ['get']

    def get_queryset(self):
        return FilmWork.objects \
            .prefetch_related('persons', 'genres') \
            .annotate(
                genres_list=ArrayAgg(
                    'genres__name',
                    distinct=True
                ),
                actors_list=ArrayAgg(
                    'persons__full_name',
                    filter=Q(personfilmwork__role='actor'),
                    distinct=True
                ),
                directors_list=ArrayAgg(
                    'persons__full_name',
                    filter=Q(personfilmwork__role='director'),
                    distinct=True
                ),
                writers_list=ArrayAgg(
                    'persons__full_name',
                    filter=Q(personfilmwork__role='writer'),
                    distinct=True
                )
            ).values(
                'id', 'title', 'description', 'creation_date', 'rating', 'type',
                'genres_list', 'actors_list', 'directors_list', 'writers_list'
            )

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class MoviesListApi(MoviesApiMixin, BaseListView):
    paginate_by = 50

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.get_queryset()
        paginator, page, queryset, is_paginated = self.paginate_queryset(queryset, self.paginate_by)

        context = {
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'prev': page.previous_page_number() if page.has_previous() else None,
            'next': page.next_page_number() if page.has_next() else None,

            'results': list(queryset),
        }

        for movie in context['results']:
            movie['genres'] = movie.pop('genres_list') or []
            movie['actors'] = movie.pop('actors_list') or []
            movie['directors'] = movie.pop('directors_list') or []
            movie['writers'] = movie.pop('writers_list') or []

            if movie['rating'] is None:
                movie['rating'] = 0.0

        return context


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):
    pk_url_kwarg = 'id'

    def render_to_response(self, context, **response_kwargs):
        obj = self.get_object()

        genres_list = obj['genres_list'] or []
        actors_list = obj['actors_list'] or []
        directors_list = obj['directors_list'] or []
        writers_list = obj['writers_list'] or []

        rating_value = obj['rating']
        if rating_value is None:
            rating_value = 0.0

        data = {
            'id': str(obj['id']),
            'title': obj['title'],
            'description': obj['description'],
            'creation_date': obj['creation_date'],
            'rating': rating_value,
            'type': obj['type'],
            'genres': genres_list,
            'actors': actors_list,
            'directors': directors_list,
            'writers': writers_list,
        }
        return JsonResponse(data)
