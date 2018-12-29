from django import forms
from .models import Topic, Post

class NewTopicForm(forms.ModelForm):
	# message = forms.CharField(widget=forms.Textarea(), max_length=2000)
	message = forms.CharField(
		widget=forms.Textarea(
			attrs={'rows': 5, 'placeholder': 'What is on your mind?'}
		),
		max_length = 2000,
		help_text = 'The max length of the text is 2000'
	)

	class Meta:
		model = Topic
		fields = ['subject', 'message']

class ReplyForm(forms.ModelForm):
	class Meta:
		model = Post
		fields = ['message',]