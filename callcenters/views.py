from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .selectors import get_callcenters_for_user


@login_required
def callcenter_list(request):
    callcenters = get_callcenters_for_user(
        request.user,
    )

    return render(
        request,
        "callcenters/callcenter_list.html",
        {
            "callcenters": callcenters,
        },
    )
