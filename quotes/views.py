import random

from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now, timedelta

from .forms import QuoteForm, CustomUserCreationForm
from .models import Quote, QuoteVote

User = get_user_model()


def random_quote(request):
    """
    Возвращает случайную цитату с учетом веса. Увеличивает счетчик
    просмотров и отображает статус голосования текущего пользователя.
    """
    quotes = list(Quote.objects.all())
    if not quotes:
        return render(request, 'quotes/quote.html', {'quote': None})

    total_weight = sum(quote.weight for quote in quotes)
    random_weight = random.uniform(0, total_weight)
    upto = 0
    for quote in quotes:
        if upto + quote.weight >= random_weight:
            selected = quote
            break
        upto += quote.weight

    selected.views += 1
    selected.save()

    user_vote = None
    if request.user.is_authenticated:
        try:
            vote_obj = QuoteVote.objects.get(
                user=request.user, quote=selected
            )
            user_vote = vote_obj.vote_type
        except QuoteVote.DoesNotExist:
            pass

    return render(
        request,
        'quotes/quote.html',
        {'quote': selected, 'user_vote': user_vote},
    )


@login_required
def vote(request, quote_id, vote_type):
    """
    Обрабатывает голосование пользователя (лайк/дизлайк) по цитате.
    """
    quote = get_object_or_404(Quote, id=quote_id)

    if vote_type not in ['like', 'dislike']:
        return JsonResponse(
            {'error': 'Неверный тип голосования'}, status=400
        )

    try:
        vote_obj, created = QuoteVote.objects.get_or_create(
            user=request.user,
            quote=quote,
            defaults={'vote_type': vote_type},
        )
        if not created:
            if vote_obj.vote_type == vote_type:
                return JsonResponse(
                    {'error': 'Вы уже голосовали этим способом'}, status=400
                )
            if vote_obj.vote_type == 'like':
                quote.likes -= 1
                quote.dislikes += 1
            else:
                quote.dislikes -= 1
                quote.likes += 1
            vote_obj.vote_type = vote_type
            vote_obj.save()
        else:
            if vote_type == 'like':
                quote.likes += 1
            else:
                quote.dislikes += 1
        quote.save()
        return JsonResponse(
            {'likes': quote.likes, 'dislikes': quote.dislikes}
        )
    except IntegrityError:
        return JsonResponse(
            {'error': 'Ошибка при сохранении голосования'}, status=400
        )


def top_quotes(request):
    """
    Возвращает 10 цитат с наибольшим количеством лайков.
    """
    quotes = Quote.objects.order_by('-likes')[:10]
    return render(request, 'quotes/top_quotes.html', {'quotes': quotes})


def add_quote(request):
    """
    Добавление новой цитаты через форму.
    """
    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            quote = form.save(commit=False)
            if request.user.is_authenticated:
                quote.author = request.user
            quote.save()
            return redirect('random_quote')
        return render(request, 'quotes/add_quote.html', {'form': form})
    else:
        form = QuoteForm()
    return render(request, 'quotes/add_quote.html', {'form': form})


def register(request):
    """
    Регистрация нового пользователя.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'quotes/register.html', {'form': form})


def random_source_quotes(request):
    """
    Возвращает цитаты случайного источника с фильтром по типу источника.
    """
    type_filter = request.GET.get('type')
    sources_qs = Quote.objects.all()
    if type_filter:
        sources_qs = sources_qs.filter(type_of_source=type_filter)

    sources = sources_qs.values_list('source', flat=True).distinct()
    if not sources:
        quotes = []
        source = None
    else:
        source = random.choice(list(sources))
        quotes = Quote.objects.filter(source=source)

    context = {
        'quotes': quotes,
        'source': source,
        'type_filter': type_filter,
        'user': request.user,
    }
    return render(request, 'quotes/quotes_by_source.html', context)


@login_required
def dashboard(request):
    """
    Отображает дашборд с графиками:
    - Количество цитат по типу источника
    - Лайки/дизлайки по типу источника
    - Лайки/дизлайки за последние 7 дней
    - Круговые диаграммы просмотров и лайков
    - Топ авторы по количеству цитат
    """
    type_choices_dict = dict(Quote.TYPE_CHOICES)

    quotes_by_type = list(
        Quote.objects.values('type_of_source').annotate(total=Count('id'))
    )
    for type_item in quotes_by_type:
        type_item['type_of_source'] = type_choices_dict.get(
            type_item['type_of_source'], type_item['type_of_source']
        )
    type_labels = [item['type_of_source'] for item in quotes_by_type]

    stacked_data = []
    for type_item in quotes_by_type:
        type_key = [
            key for key, val in type_choices_dict.items()
            if val == type_item['type_of_source']
        ][0]
        qs = Quote.objects.filter(type_of_source=type_key)
        stacked_data.append({
            'likes': qs.aggregate(total_likes=Sum('likes'))['total_likes']
            or 0,
            'dislikes': qs.aggregate(
                total_dislikes=Sum('dislikes')
            )['total_dislikes'] or 0,
        })

    start_date = now() - timedelta(days=7)
    likes_last_days_qs = (
        QuoteVote.objects.filter(
            vote_type='like', created_at__gte=start_date
        )
        .values('created_at__date')
        .annotate(total=Count('id'))
        .order_by('created_at__date')
    )
    dislikes_last_days_qs = (
        QuoteVote.objects.filter(
            vote_type='dislike', created_at__gte=start_date
        )
        .values('created_at__date')
        .annotate(total=Count('id'))
        .order_by('created_at__date')
    )
    likes_last_days = [
        {'date': item['created_at__date'].strftime('%Y-%m-%d'),
         'total': item['total']}
        for item in likes_last_days_qs
    ]
    dislikes_last_days = [
        {'date': item['created_at__date'].strftime('%Y-%m-%d'),
         'total': item['total']}
        for item in dislikes_last_days_qs
    ]

    views_by_type_qs = list(
        Quote.objects.values('type_of_source').annotate(
            total_views=Sum('views')
        )
    )
    for view_item in views_by_type_qs:
        view_item['type_of_source'] = type_choices_dict.get(
            view_item['type_of_source'], view_item['type_of_source']
        )
    likes_by_type_qs = list(
        Quote.objects.values('type_of_source').annotate(
            total_likes=Sum('likes')
        )
    )
    for like_item in likes_by_type_qs:
        like_item['type_of_source'] = type_choices_dict.get(
            like_item['type_of_source'], like_item['type_of_source']
        )

    top_authors = (
        User.objects.annotate(total_quotes=Count('quotes'))
        .order_by('-total_quotes')[:5]
    )

    context = {
        'type_labels': type_labels,
        'quotes_by_type': quotes_by_type,
        'stacked_data': stacked_data,
        'likes_last_days': likes_last_days,
        'dislikes_last_days': dislikes_last_days,
        'views_by_type': views_by_type_qs,
        'likes_by_type': likes_by_type_qs,
        'top_authors': top_authors,
    }

    return render(request, 'quotes/dashboard.html', context)


@login_required
def edit_quote(request, quote_id):
    """
    Редактирование цитаты автором.
    """
    quote = get_object_or_404(Quote, id=quote_id)

    if quote.author != request.user:
        return redirect('random_quote')

    if request.method == 'POST':
        form = QuoteForm(request.POST, instance=quote)
        if form.is_valid():
            form.save()
            return redirect('random_quote')
    else:
        form = QuoteForm(instance=quote)

    return render(
        request,
        'quotes/edit_quote.html',
        {'form': form, 'quote': quote},
    )
