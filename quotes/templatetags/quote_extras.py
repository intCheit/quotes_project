from django import template

register = template.Library()


@register.filter
def get_vote(votes, user):
    vote = votes.filter(user=user).first()
    return vote.vote_type if vote else ""


@register.filter
def pluck(lst, key):
    return [item.get(key) for item in lst]
