from django.core.mail import send_mail
from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage,PageNotAnInteger

# import models
from .models import Post, Comment

# import forms
from .forms import EmailPostForm, CommentForm

# third-party imports
from taggit.models import Tag

# Create your views here.

def post_list(request , tag_slug=None):
    object_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])
    paginator = Paginator(object_list, 3) # 3 posts in each page
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer deliver the first page
        posts = paginator.page(1)
    except EmptyPage:
        # If page is out of range deliver last page of results
        posts = paginator.page(paginator.num_pages)
    template_name = 'post/list.html'
    context = {
        'posts' : posts,
        'page' : page,
        'tag': tag
    }
    return render(request, template_name, context)


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post,
        status='published',
        publish__year=year,
        publish__month=month,
        publish__day=day
    )
    # List of active comments for this post
    comments = post.comments.filter(active=True)
    if request.method == 'POST':
        # A comment was posted
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Create Comment object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # Assign the current post to the comment
            new_comment.post = post
            # Save the comment to the database
            new_comment.save()
    else:
        comment_form = CommentForm()
    template_name = 'post/detail.html'
    # List of similar posts
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids)\
    .exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags'))\
    .order_by('-same_tags','-publish')[:4]
    context = {
        'post' : post,
        'comments': comments,
        'comment_form': comment_form,
        'similar_posts': similar_posts
    }
    return render(request, template_name, context)

def post_share(request, post_id):
    template_name = 'post/share.html'
    # Retrieve post by id
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False
    if request.method == 'POST':
        # Form was submitted
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Form fields passed validation
            cd = form.cleaned_data
            # ... send email
            post_url = request.build_absolute_uri(
            post.get_absolute_url())
            subject = f"{cd['name']} recommends you read " f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n" f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'admin@myblog.com',
            [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    context = {
        'post' : post,
        'form' : form,
        'sent' : sent
    }
    return render(request, template_name, context)