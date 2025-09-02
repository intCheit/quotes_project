import random

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import IntegrityError
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from .forms import QuoteForm, CustomUserCreationForm
from .models import Quote, QuoteVote


def random_quote(request):
    """
    Возвращает случайную цитату с учетом веса. Увеличивает счетчик
    просмотров и отображает статус голосования текущего пользователя.
    """
    quotes = list(Quote.objects.all())
    if not quotes:
        return render(request, 'quotes/quote.html', {'quote': None})

    total_weight = sum(q.weight for q in quotes)
    r = random.uniform(0, total_weight)
    upto = 0
    for q in quotes:
        if upto + q.weight >= r:
            selected = q
            break
        upto += q.weight

    selected.views += 1
    selected.save()

    user_vote = None
    if request.user.is_authenticated:
        try:
            vote_obj = QuoteVote.objects.get(user=request.user, quote=selected)
            user_vote = vote_obj.vote_type
        except QuoteVote.DoesNotExist:
            pass

    return render(
        request,
        'quotes/quote.html',
        {'quote': selected, 'user_vote': user_vote}
    )


@login_required
def vote(request, quote_id, vote_type):
    """
    Обрабатывает голосование пользователя (лайк/дизлайк) по цитате.
    """
    quote = get_object_or_404(Quote, id=quote_id)

    if vote_type not in ['like', 'dislike']:
        return JsonResponse({'error': 'Неверный тип голосования'}, status=400)

    try:
        vote_obj, created = QuoteVote.objects.get_or_create(
            user=request.user,
            quote=quote,
            defaults={'vote_type': vote_type}
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
        return JsonResponse({'likes': quote.likes, 'dislikes': quote.dislikes})
    except IntegrityError:
        return JsonResponse({'error': 'Ошибка при сохранении голосования'},
                            status=400)


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


def dashboard(request):
    """
    Дашборд с графиками: количество цитат и лайков/дизлайков по типу
    источника.
    """
    quotes_by_type = Quote.objects.values('type_of_source').annotate(
        total=Count('id')
    )
    likes_by_type = Quote.objects.values('type_of_source').annotate(
        total_likes=Sum('likes')
    )
    dislikes_by_type = Quote.objects.values('type_of_source').annotate(
        total_dislikes=Sum('dislikes')
    )

    context = {
        'quotes_by_type': list(quotes_by_type),
        'likes_by_type': list(likes_by_type),
        'dislikes_by_type': list(dislikes_by_type),
    }
    return render(request, 'quotes/dashboard.html', context)


@login_required
def edit_quote(request, quote_id):
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

    return render(request, 'quotes/edit_quote.html', {'form': form, 'quote': quote})
