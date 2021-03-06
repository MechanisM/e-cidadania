# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 Cidadanía Coop.
# Written by: Oscar Carballal Prego <info@oscarcp.com>
#
# This file is part of e-cidadania.
#
# e-cidadania is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# e-cidadania is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with e-cidadania. If not, see <http://www.gnu.org/licenses/>.

"""
Proposal module views.
"""

# Generic class-based views
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView

from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.template import RequestContext
from django.views.decorators.http import require_POST
from django.db.models import Count

from django.views.generic.create_update import update_object
from django.db.models import F
from django.http import HttpResponse

from e_cidadania.apps.proposals.models import Proposal
from e_cidadania.apps.proposals.forms import ProposalForm, VoteProposal
from e_cidadania.apps.spaces.models import Space

@require_POST
def vote_proposal(request, space_name):

    """
    Increment support votes for the proposal in 1.
    """
    prop = get_object_or_404(Proposal, pk=request.POST['propid'])
#    if Proposal.objects.filter(support_votes__contains=request.user):
#        return HttpResponse("You already voted")
#    else:
    prop.support_votes.add(request.user)
    return HttpResponse("Vote emmited.")

class ListProposals(ListView):

    """
    List all proposals stored whithin a space. Inherits from django :class:`ListView`
    generic view.

    :rtype: Object list
    :context: proposal
    """
    paginate_by = 50
    context_object_name = 'proposal'

    def get_queryset(self):
        place = get_object_or_404(Space, url=self.kwargs['space_name'])
        objects = Proposal.objects.all().filter(space=place.id).order_by('pub_date')
        return objects

    def get_context_data(self, **kwargs):
        context = super(ListProposals, self).get_context_data(**kwargs)
        context['get_place'] = get_object_or_404(Space, url=self.kwargs['space_name'])
        return context


class ViewProposal(DetailView):

    """
    Detail view of a proposal. Inherits from django :class:`DetailView` generic
    view.

    :rtype: object
    :context: proposal
    """
    context_object_name = 'proposal'
    template_name = 'proposals/proposal_detail.html'

    def get_object(self):
        prop_id = self.kwargs['prop_id']
        return get_object_or_404(Proposal, pk = prop_id)

    def get_context_data(self, **kwargs):
        context = super(ViewProposal, self).get_context_data(**kwargs)
        support_votes_count = Proposal.objects.annotate(Count('support_votes'))
        current_proposal = int(self.kwargs['prop_id']) - 1
        context['get_place'] = get_object_or_404(Space, url=self.kwargs['space_name'])
        context['support_votes_count'] = support_votes_count[current_proposal].support_votes__count
        return context


@permission_required('proposals.add_proposal')
def add_proposal(request, space_name):

    """
    Create a new proposal.

    :rtype: HTML Form
    :context: form, get_place
    """
    prop_space = get_object_or_404(Space, url=space_name)
    prop_form = ProposalForm(request.POST or None)

    if request.method == 'POST':
        if prop_form.is_valid():
            prop_form_uncommited = prop_form.save(commit=False)
            prop_form_uncommited.space = prop_space
            prop_form_uncommited.author = request.user
            prop_form_uncommited.save()

            return redirect('/spaces/' + space_name)

    return render_to_response('proposals/proposal_add.html',
                              {'form': prop_form, 'get_place': prop_space},
                              context_instance = RequestContext(request))


@permission_required('proposals.edit_proposal')
def edit_proposal(request, space_name, prop_id):

    """
    The proposal can be edited by space and global admins, but also by their
    creator.

    :rtype: HTML Form
    :context: get_place
    """
    current_space = get_object_or_404(Space, url=space_name)
    current_proposal = get_object_or_404(Proposal, id=prop_id)
    current_user = request.user.username

    can_edit = request.user.has_perm('Proposal.edit_proposal')

    allow_edit = 0

    if can_edit or current_user == current_proposal.author:
        return update_object(request,
                             model = Proposal,
                             object_id = prop_id,
                             login_required = True,
                             template_name = 'proposals/proposal_edit.html',
                             post_save_redirect = '../',
                             extra_context = {'get_place': current_space})


class DeleteProposal(DeleteView):

    """
    Delete a proposal.

    :rtype: Confirmation
    :context: get_place
    """
    def get_object(self):
        return get_object_or_404(Proposal, pk = self.kwargs['prop_id'])

    def get_success_url(self):
        current_space = self.kwargs['space_name']
        return '/spaces/{0}'.format(current_space)

    def get_context_data(self, **kwargs):
        context = super(DeleteProposal, self).get_context_data(**kwargs)
        context['get_place'] = get_object_or_404(Space, url=self.kwargs['space_name'])
        return context

