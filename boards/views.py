from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Board, Topic, Post
from django.http import Http404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.generic import UpdateView, ListView, CreateView, DeleteView
from django.utils import timezone
from django.utils.decorators import method_decorator
from .forms import NewTopicForm, ReplyForm

# Create your views here.
def home(request):
	# boards_names = list()
	# boards = Board.objects.all()

	# for board in boards:
	# 	boards_names.append(board.name)

	# output = '<br>'.join(boards_names)

	# return HttpResponse(output)
	boards = Board.objects.all()
	return render(request, 'home.html', {'boards': boards})

def board_topics(request, pk):	
	board = get_object_or_404(Board, pk=pk)
	topics = board.topics.order_by('-last_updated').annotate(replies=Count('posts')-1)
	return render(request, 'topics.html', {'board': board, 'topics': topics})

@login_required
def new_topic(request, pk):
	board = get_object_or_404(Board, pk=pk)
	# user = User.objects.first()

	if request.method == 'POST':
		form = NewTopicForm(request.POST)
		if form.is_valid():
			topic = form.save(commit=False)
			topic.starter = request.user
			topic.board = board
			topic.save()
			
			post = Post.objects.create(
				message = form.cleaned_data.get('message'),
				created_by = request.user,
				topic = topic
			)

			return redirect('topic_posts', pk=pk, topic_pk=topic.pk)
	else:
		form = NewTopicForm()
	return render(request, 'new_topic.html', {'board': board, 'form': form})

def topic_posts(request, pk, topic_pk):
	topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
	topic.views += 1
	topic.save()
	return render(request, 'topic_posts.html', 
		{'topic': topic})

def reply_topic(request, pk, topic_pk):
	topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)

	if request.method == 'POST':
		form = ReplyForm(request.POST)
		if form.is_valid():
			post = form.save(commit = False)
			post.topic = topic
			post.created_by = request.user
			post.save()
			return redirect('topic_posts', pk=pk, topic_pk=topic_pk)
	else:
		form = ReplyForm()
	return render(request, 'reply_topic.html', {'topic': topic,'form': form})

class BoardListView(ListView):
	model = Board
	context_object_name = 'boards'
	template_name = 'home.html'

# Lop nay se tuong duong voi board_topics phia tren
# goi du lieu ra templates la: topics va board
class TopicListView(ListView):
	model = Topic      #model su dung
	context_object_name = 'topics'	#du lieu goi ra template de hien thi
	template_name = 'topics.html'   #template su dung
	paginate_by = 5    #1 trang gom bao nhieu record?

	def get_queryset(self):
		#lay thuoc board dua vao tham so 'pk' tren url
		self.board = get_object_or_404(Board, pk=self.kwargs.get('pk'))
		#gia tri lay duoc se duoc dua vao topics de hien thi
		queryset = self.board.topics.order_by('-last_updated').annotate(replies=Count('posts') - 1)
		return queryset

	# ngoai topics can bien board de dua ra template
	def get_context_data(self, **kwargs):
		kwargs['board'] = self.board
		return super().get_context_data(**kwargs)

class PostListView(ListView):
	model = Post
	context_object_name = 'posts'
	template_name = 'topic_posts_cbv.html'
	paginate_by = 2

	def get_queryset(self):
		self.topic = get_object_or_404(Topic,board__pk=self.kwargs.get('pk'), 
			pk=self.kwargs.get('topic_pk'))
		queryset = self.topic.posts.order_by('-created_at')
		return queryset

	def get_context_data(self, **kwargs):
		self.topic.views += 1
		self.topic.save()
		kwargs['topic'] = self.topic
		return super().get_context_data(**kwargs)

#decorate cho CBV khac voi FBV
# name='function_here': which method should be decorated
# In class-based views it’s common to decorate the dispatch method.
# t’s an internal method Django use (defined inside the View class). 
# All requests pass through this method,
@method_decorator(login_required, name='dispatch')
class PostUpdateView(UpdateView):
	model = Post  #model dc cap nhat
	fields = ('message',)    # cac truong tren form de cap nhat
	template_name = 'edit_post.html'  #template duoc su dung
	pk_url_kwarg = 'post_pk'   #tren url co nhieu tham so, chon tham so nao? pk, topic_pk va post_pk
	context_object_name = 'post'   #khi lay gia tri post cu hien thi tren template - form, se duoc luu trong bien nao?

	#han che user chinh sua post khong phai cua minh
	#neu khong co thi user co the edit bat ki post nao
	#voi created_by=self.request.user	
	# filtering the post using the logged in user,
	def get_queryset(self):
		queryset = super().get_queryset()
		return queryset.filter(created_by=self.request.user)

	#truoc khi luu xuong db can thuc hien cac cong viec gi thi dua vao day
	def form_valid(self, form):
		post = form.save(commit=False)
		post.updated_by = self.request.user
		post.updated_at = timezone.now()
		post.save()
		return redirect('topic_posts', post.topic.board.pk, post.topic.pk)