from django.core.management.base import BaseCommand
from django.db.models import Count
from django.template import Context, Template

from random import choice, shuffle
import os

from collection.models import *

FRAGMENT_WINDOW = 3

html_sentences_template = """
{% autoescape off %}
<ul class="sentence-table">
{% for sentence in sentences %}
<li class="sentence">
{% for word, is_matched, is_in_query in sentence%}{{word.space_before}}<span class="word {% if is_matched %}match{% elif is_in_query %}query{% endif %}" >{{word.surface}}</span>{% endfor %}
</li>
{% endfor %}
</ul>
{% endautoescape %}
"""

baseline_template = """
{% autoescape off %}
<form action="/survey" method="post">
	{% for i, option in options %}
		<span class="label" {% if option.is_selected %} id="checked"{% endif %}>
		<input {% if option.is_selected %}checked="checked"{% endif %} type="radio" name="choice" value="{{i}} {{option.relation__relation}}"/>
		<span class="relation-label">{{option.relation__relation}}</span>
		<span class="explanation">{{option.label}}</span>
		</span>
	{% endfor %}
	{% if not is_example %}
		<button action="submit">Next</button>
	{% endif %}
</form>
{% endautoescape %}
"""

words_template = """
{% autoescape off %}
<form action="/survey" method="post">
	{% for i, option in options %}
		<span class="label" {% if option.is_selected %} id="checked"{% endif %}>
		<input {% if option.is_selected %} checked="checked" {% endif %} type="radio" name="choice" value="{{i}} {{option.relation__relation}}"/>
		<span class="relation-label">{{option.relation__relation}}</span>
		<span class="explanation">{{option.words}}</span><br>
		</span>
	{% endfor %}
	{% if not is_example %}
		<button action="submit">Next</button>
	{% endif %}
</form>
{% endautoescape %}
"""

fragments_template = """
{% autoescape off %}
<form action="/survey" method="post">
	{% for i, option in options %}
		<span class="label" {% if option.is_selected %} id="checked"{% endif %}>
			<input {% if option.is_selected %} checked="checked"{% endif %} type="radio" name="choice" value="{{i}} {{option.relation__relation}}"/>
			<span class="relation-label">{{option.relation__relation}}</span>
			<span class="explanation">{{option.fragments}}</span>
		</span>
	{% endfor %}
	{% if not is_example %}
		<button action="submit">Next</button>
	{% endif %}
	</form>
{% endautoescape %}
"""

HTML_SENTENCE_TEMPLATE = Template(html_sentences_template)

BASELINE_TEMPLATE = Template(baseline_template)

WORDS_TEMPLATE = Template(words_template)

FRAGMENTS_TEMPLATE = Template(fragments_template)

labels_for_relations = {
"conj_and": [ "conjunction: <span class=\"match word\"><span class=\"blank\"></span></span> and {{ option.query_word }} ", "conjunction: {{ option.query_word }} and <span class=\"match word\"><span class=\"blank\"></span></span> "],
"conj_but": [ "conjunction: <span class=\"match word\"><span class=\"blank\"></span></span> but {{ option.query_word }} ", "conjunction: {{ option.query_word }} but <span class=\"match word\"><span class=\"blank\"></span></span> "],
"prep_with": [" preposition: <span class=\"match word\"><span class=\"blank\"></span></span> with {{ option.query_word }} ", "preposition: {{ option.query_word }} with <span class=\"match word\"><span class=\"blank\"></span></span> "],
"prep_to": [" preposition: {{ option.query_word }} to <span class=\"match word\"><span class=\"blank\"></span></span>", "preposition:  {{ option.query_word }} to <span class=\"match word\"><span class=\"blank\"></span></span> "],
"prep_for": [" preposition: {{ option.query_word }} for <span class=\"match word\"><span class=\"blank\"></span></span>", "preposition: {{ option.query_word }} for <span class=\"match word\"><span class=\"blank\"></span></span> "],
"prep_like": [" preposition: {{ option.query_word }} like <span class=\"match word\"><span class=\"blank\"></span></span>", "preposition: {{ option.query_word }} like <span class=\"match word\"><span class=\"blank\"></span></span> "],
"prepc_compared_with": [" preposition: {{ option.query_word }} compared with <span class=\"match word\"><span class=\"blank\"></span></span>", " {{ option.query_word }} compared with <span class=\"match word\"><span class=\"blank\"></span></span> "],
"prep_avast": ["preposition: {{ option.query_word }} avast <span class=\"match word\"><span class=\"blank\"></span></span>", "preposition: {{ option.query_word }} avast <span class=\"match word\"><span class=\"blank\"></span></span> "],
"prep_from": ["preposition: {{ option.query_word }} from <span class=\"match word\"><span class=\"blank\"></span></span> ", "preposition: {{ option.query_word }} from <span class=\"match word\"><span class=\"blank\"></span></span> "],
"prep_of": ["preposition: <span class=\"match word\"><span class=\"blank\"></span></span> of {{ option.query_word }} ", "preposition: {{ option.query_word }} of <span class=\"match word\"><span class=\"blank\"></span></span> "],
"prep_at": ["preposition: <span class=\"match word\"><span class=\"blank\"></span></span> at {{ option.query_word }} ", "preposition: {{ option.query_word }} at <span class=\"match word\"><span class=\"blank\"></span></span> "],
"prep_till": ["preposition: <span class=\"match word\"><span class=\"blank\"></span></span> till {{ option.query_word }} ", "preposition: {{ option.query_word }} till <span class=\"match word\"><span class=\"blank\"></span></span> "],
"prep_on": ["preposition: <span class=\"match word\"><span class=\"blank\"></span></span> on {{ option.query_word }} ", "preposition: {{ option.query_word }} on <span class=\"match word\"><span class=\"blank\"></span></span> "],
"prep_by": ["preposition: <span class=\"match word\"><span class=\"blank\"></span></span> by {{ option.query_word }} ", "preposition: {{ option.query_word }} by <span class=\"match word\"><span class=\"blank\"></span></span> "],
"prep_in": ["preposition: <span class=\"match word\"><span class=\"blank\"></span></span> in {{ option.query_word }} ", "preposition: {{ option.query_word }} in <span class=\"match word\"><span class=\"blank\"></span></span> "],
"abbrev": ["abbreviation: {{ option.query_word }} <span class=\"match word\"><span class=\"blank\"></span></span> ", "abbreviation: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"acomp": [ "adjective complement: <span class=\"match word\"><span class=\"blank\"></span></span>  {{ option.query_word }} ","adjective complement: {{ option.query_word }} <span class=\"match word\"><span class=\"blank\"></span></span> "],
"advmod": [ "adverb: {{ option.query_word }}  <span class=\"match word\"><span class=\"blank\"></span></span>", "adverb: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"advcl": [ "adverbial clause: {{ option.query_word }}  <span class='ellipsis'>...</span>  <span class=\"match word\"><span class=\"blank\"></span></span>", "adverbial clause: <span class=\"match word\"><span class=\"blank\"></span></span>  <span class='ellipsis'>...</span> {{ option.query_word }}"],
"agent": ["agent of verb: {{ option.query_word }} <span class=\"match word\"><span class=\"blank\"></span></span> ", "agent of verb: <span class=\"match word\"><span class=\"blank\"></span></span> "],
"amod": [ "adjective modifier: {{ option.query_word }}  <span class=\"match word\"><span class=\"blank\"></span></span>", "adjective modifier: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"appos": ["apposition: {{ option.query_word }}  <span class=\"match word\"><span class=\"blank\"></span></span>", "apposition: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"attr": [ " attributive: {{ option.query_word }} of <span class=\"match word\"><span class=\"blank\"></span></span> ", "attributive: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"aux": [ " auxiliary verb: {{ option.query_word }} <span class=\"match word\"><span class=\"blank\"></span></span>", " auxiliary verb: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"ccomp": [ "clausal complement: <span class=\"match word\"><span class=\"blank\"></span></span> <span class='ellipsis'>...</span> {{ option.query_word }} ", "clausal complement: {{ option.query_word }} <span class='ellipsis'>...</span> <span class=\"match word\"><span class=\"blank\"></span></span> "],
"complm": [  "complementizer: <span class=\"match word\"><span class=\"blank\"></span></span> <span class='ellipsis'>...</span> <span class=\"match word\"><span class=\"blank\"></span></span>", "complementizer: {{ option.query_word }} <span class='ellipsis'>...</span> <span class=\"match word\"><span class=\"blank\"></span></span> "],
"cop": [ "copula: {{ option.query_word }} <span class='ellipsis'>...</span> <span class=\"match word\"><span class=\"blank\"></span></span>", "copula: <span class=\"match word\"><span class=\"blank\"></span></span>  <span class='ellipsis'>...</span> {{ option.query_word }}"],
"csubj": [ "clausal subject of verb: {{ option.query_word }} <span class='ellipsis'>...</span> <span class=\"match word\"><span class=\"blank\"></span></span> ", "clausal subject of verb: <span class=\"match word\"><span class=\"blank\"></span></span> <span class='ellipsis'>...</span> {{ option.query_word }}"],
"csubjpass": [ "passive clausal subject of verb: <span class=\"match word\"><span class=\"blank\"></span></span> by {{ option.query_word }} ", " passive clausal subject of verb: {{ option.query_word }} by <span class=\"match word\"><span class=\"blank\"></span></span>"],
"det": [ "determiner: {{ option.query_word }} <span class=\"match word\"><span class=\"blank\"></span></span> ", "determiner: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"dobj": ["direct object: <span class=\"match word\"><span class=\"blank\"></span></span> <span class='ellipsis'>...</span> {{ option.query_word }}",  " direct object of verb: {{ option.query_word }} <span class='ellipsis'>...</span> <span class=\"match word\"><span class=\"blank\"></span></span>"],
"expl": [ "expletive: {{ option.query_word }} <span class=\"match word\"><span class=\"blank\"></span></span> ", "expletive: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"infmod": [ "infinive: {{ option.query_word }} <span class=\"match word\"><span class=\"blank\"></span></span> ", "infinitive: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"iobj": [  "indirect object: <span class=\"match word\"><span class=\"blank\"></span></span> <span class='ellipsis'>...</span> {{ option.query_word }}", "indirect object of verb: {{ option.query_word }} <span class='ellipsis'>...</span> <span class=\"match word\"><span class=\"blank\"></span></span> "],
"mwe": [ "multi-word expression: {{ option.query_word }} <span class=\"match word\"><span class=\"blank\"></span></span>", "multi-word expression: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"neg": [ "negation: {{ option.query_word }}  <span class=\"match word\"><span class=\"blank\"></span></span> ", "negation: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"nn": [ "compound noun: {{ option.query_word }} <span class=\"match word\"><span class=\"blank\"></span></span>", "compound noun: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"nsubj": [ " subject of verb: {{ option.query_word }} <span class=\"match word\"><span class=\"blank\"></span></span>", "subject of verb: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"nsubjpass": [" passive subject of verb: {{ option.query_word }}  <span class=\"match word\"><span class=\"blank\"></span></span> ", "passive subject of verb: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"num": [ "numeric expression: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}", "numeric expression <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"number": [ "number: {{ option.query_word }} <span class=\"match word\"><span class=\"blank\"></span></span>", "number: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}",],
"parataxis": [ "parataxis: {{ option.query_word }} <span class='ellipsis'>...</span> <span class=\"match word\"><span class=\"blank\"></span></span> ", "parataxis: <span class=\"match word\"><span class=\"blank\"></span></span>  <span class='ellipsis'>...</span> {{ option.query_word }}"],
"partmod": [ "participle: {{ option.query_word }} <span class=\"match word\"><span class=\"blank\"></span></span>", "participal: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"pcomp": [  "prepositional complement: <span class=\"match word\"><span class=\"blank\"></span></span> <span class=\"match word\"> {{ option.query_word }}", "prepositional complement: {{ option.query_word }} <span class=\"match word\"><span class=\"blank\"></span></span>"],
"pobj": [ " object of preposition: {{ option.query_word }} <span class=\"match word\"><span class=\"blank\"></span></span> ", "object of preposition: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"possessive": [  "possessive: {{ option.query_word }} <span class=\"match word\"><span class=\"blank\"></span></span>",  "possessive: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"poss": [   "possessive: {{ option.query_word }} <span class=\"match word\"><span class=\"blank\"></span></span>","possessive: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"preconj": [ "preconjunct", "preconjunct"],
"predet": [ "predeterminer", "predeterminer"],
"prep": [ "preposition: {{ option.query_word }} <span class=\"match word\"><span class=\"blank\"></span></span> ", "preposition: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"prepc": [ "prepositional clause modifier", "prepositional clause modifier"],
"prt": [ " phrasal verb particle", "phrasal verb particle"],
"punct": [ "punctuation", "punctuation"],
"purpcl": [ "purposal clause modifier: {{ option.query_word }} <span class='ellipsis'>...</span> <span class=\"match word\"><span class=\"blank\"></span></span> ", "purposal clause modifier: <span class=\"match word\"><span class=\"blank\"></span></span> <span class='ellipsis'>...</span> {{ option.query_word }}"],
"quantmod": [ " quantitative modifier: {{ option.query_word }} <span class='ellipsis'>...</span> <span class=\"match word\"><span class=\"blank\"></span></span>", "quantitative modifier: <span class=\"match word\"><span class=\"blank\"></span></span> <span class='ellipsis'>...</span> {{ option.query_word }}"],
"rcmod": [ "relative clause modifier: {{ option.query_word }} <span class='ellipsis'>...</span> <span class=\"match word\"><span class=\"blank\"></span></span> ", "relative clause modifier:  <span class=\"match word\"><span class=\"blank\"></span></span> <span class='ellipsis'>...</span> {{ option.query_word }} "],
"tmod": [ "temporal modifier: {{ option.query_word }} <span class=\"match word\"><span class=\"blank\"></span></span> ", "temporal modifier: <span class=\"match word\"><span class=\"blank\"></span></span> {{ option.query_word }}"],
"xcomp": [ "open clausal complement: <span class=\"match word\"><span class=\"blank\"></span></span> <span class='ellipsis'>...</span> {{ option.query_word }}", "open clausal complement: {{ option.query_word }} <span class='ellipsis'>...</span> <span class=\"match word\"><span class=\"blank\"></span></span> "],
"xsubj": [ "controlling subject of verb: {{ option.query_word }} <span class='ellipsis'>...</span> <span class=\"match word\"><span class=\"blank\"></span></span>", "controlling subject of verb: <span class=\"match word\"><span class=\"blank\"></span></span> <span class='ellipsis'>...</span> {{ option.query_word }}"],
}

class Command(BaseCommand):
	def handle(self, *args, **options):
		collection = args[0]
		task_dirs = args[1:]
		for task_dir in task_dirs:
			self.make_tasks(task_dir, collection)

	def make_tasks(self, task_dir, collection):
		tasks_file = task_dir + os.sep + "tasks.txt"
		shuffled_tasks_file = task_dir + os.sep + "shuffled-tasks.txt"
		out_dir = task_dir + os.sep + "task_materials"
		if not os.path.isdir(out_dir):
			os.mkdir(out_dir)
		tasks_file = open(tasks_file)
		task_number = 0

		descriptors = tasks_file.readlines()
		shuffle(descriptors)
		shuffled = open(shuffled_tasks_file, 'w')
		for line in descriptors:
			shuffled.write(line)
		shuffled.close()

		for line in descriptors:
			components = line.strip().split("\t")
			if len(components) >= 3:
				print "==========================="
				print line
				print "==========================="
				rel = components[0]
				gov = components[1]
				dep = components[2]
				descriptor = "-".join([rel,gov,dep])
				is_example = (len(components) == 4 and components[3] == 'example')
				query_words = []
				filtered = Dependency.objects.all().filter(
					dependencyinsentence__sentence__collection__name=collection)
				option_candidates = Dependency.objects.all()
				if not rel ==  "_":
					filtered = filtered.filter(relation__relation = rel)
				if not gov == "_":
					query_words = Word.objects.filter(word__in=gov.split(","))
					filtered = filtered.filter(
						gov__in = query_words)
					option_candidates = option_candidates.filter(
						gov__in = query_words)
				if not dep == "_":
					query_words = Word.objects.filter(word__in=dep.split(","))
					filtered = filtered.filter(
						dep__in = query_words)
					option_candidates = option_candidates.filter(
						dep__in = query_words)

				choices = option_candidates.values('relation__relation').annotate(
					sentence_count = Count('dependencyinsentence')).order_by(
					'-sentence_count')

				ordered = []
				for option in choices:
					try:
						option['dependencies'] = option_candidates.filter(
							relation__relation = option['relation__relation'])

						## Record the query word
						query_word = gov
						option['label'] = labels_for_relations[
							option['relation__relation']][1]
						if gov == "_":
							query_word = dep
							option['label'] = labels_for_relations[
								option['relation__relation']][0]
						option['query_word'] = ('<span class="query word">' +
							query_word + "</span>")
						option['label'] = option['label'].replace(
							"{{ option.query_word }}", option['query_word'])

						# ## Record the other words that match the relation
						# option['words'] = [w['gov__word'] for w in option[
						# 	'dependencies'].values('gov__word').annotate(
						# 			count=Count('id')).order_by('-count')]
						# if (dep == "_"):
						# 	option['words'] = [w['dep__word'] for w in option[
						# 		'dependencies'].values('dep__word').annotate(
						# 			count=Count('id')).order_by('-count')]
						# option['words'] = option['words'][:5]
						# shuffle(option['words'])


						## Record the fragments that match the relation
						## And the matching words
						fragments = []
						for dependency in option['dependencies']:
							in_sentences = dependency.dependencyinsentence_set.all(
								).order_by('-id')[:1]
							for in_sentence in in_sentences:
								min_index = min(in_sentence.gov_index,
									in_sentence.dep_index) - FRAGMENT_WINDOW
								max_index = max(in_sentence.gov_index,
									in_sentence.dep_index) + FRAGMENT_WINDOW
								fragment = [{
									'word': w['surface'],
									'space_before': w['space_before'],
									'index': w['index']}
									for w in
								 WordInSentence.objects.filter(
									sentence = in_sentence.sentence).filter(
									index__gt = min_index).filter(
									index__lt = max_index).values(
									'space_before', 'index', 'surface'
									).order_by("index")]
								text_of_fragment = ""
								gov_index = in_sentence.gov_index
								dep_index = in_sentence.dep_index

								match_word = ""
								for word in fragment:
									text_of_fragment += word['space_before']
									if ((word['index'] == gov_index and gov != "_")
										or (word['index'] == dep_index and dep != "_")):
										text_of_fragment += (
											'<span class="query word">'
											+ word['word'] + "</span>")
									elif (word['index'] == dep_index  or
										word['index'] == gov_index):
										text_of_fragment += (
											'<span class="match word">'
											+ word['word'] + '</span>')
										match_word = word['word']
									else:
										text_of_fragment += (""
											+ word['word'] +"")
								fragments.append((match_word, ('<span class="fragment">'
									+ text_of_fragment + "</span>"), in_sentence))

						# Only take 4 randomly chosen fragments
						number_of_fragments = 4
						option['fragments'] = []
						matching_words = []
						fragment_sentences = []
						for i in xrange(number_of_fragments):
							if (len(fragments) > 0):
								fragment = choice(fragments)
								fragments.remove(fragment)
								option['fragments'].append(fragment[1])
								matching_words.append(fragment[0])
								fragment_sentences.append(fragment[2].sentence)
						text_of_words = ['<span class="match word">'+w+'</span>'
							for w in matching_words]
						text_of_words = ", ".join(text_of_words)
						option['words'] = (option['label'] +"<br> Examples: "
							+ text_of_words + " etc.")
						option['fragments'] = (option['label']
							+ "<br><div class='fragments'> Patterns like: <ul class='fragments'><li>"
							+ "</li>

<li>".join(option['fragments'])
							+ '</li></ul></div>')

						## Finally
						del option['dependencies']
						if is_example:
							if option['relation__relation'] == rel:
								option['is_selected'] = True
						else:
							option['is_selected'] = False

						if ((option['relation__relation'] == rel)
							or len(ordered)  < 4):
							ordered.append(option)
					except KeyError:
						pass
					except Exception:
						raise

				shuffle(ordered)
				numbered_options = [(i, option) for i, option
					in enumerate(ordered)]

				context = Context({
					'options':numbered_options,
					'is_example': is_example
					})

				baseline_options_out_file = (out_dir + os.sep + descriptor
					+ "_baseline_options.html")
				out = open(baseline_options_out_file, 'w')
				out.write(BASELINE_TEMPLATE.render(context))
				out.close()


				words_options_out_file = (out_dir + os.sep + descriptor
						 + "_words_options.html")
				out = open(words_options_out_file, 'w')
				out.write(WORDS_TEMPLATE.render(context))
				out.close()

				fragments_options_out_file = (out_dir + os.sep
					+ descriptor +  "_fragments_options.html")
				out = open(fragments_options_out_file, 'w')
				out.write(FRAGMENTS_TEMPLATE.render(context))
				out.close()

				matching_sentences = list(Sentence.objects.filter(
					collection__name = collection).filter(
					dependencyinsentence__dependency__in =
					filtered).exclude(
					sentence__in = fragment_sentences
					).distinct().order_by('id'))
				shuffle(matching_sentences)
				matching_sentences = matching_sentences[:8]

				Dependency.objects.filter()
				sents = []
				for sentence in matching_sentences:
					matching_dependencies = DependencyInSentence.objects.filter(
						sentence = sentence).filter(
						dependency__in = filtered);
					words = []
					for word_in_sentence in WordInSentence.objects.filter(
						sentence=sentence):
						for dependency in matching_dependencies:
							is_matched = False
							is_in_query = False
							if word_in_sentence.index == dependency.gov_index:
								if word_in_sentence.word.word in gov:
									is_in_query = True
								else:
									is_matched = True
							if word_in_sentence.index == dependency.dep_index:
								if word_in_sentence.word.word in dep:
									is_in_query = True
								else:
									is_matched = True
						words.append((word_in_sentence, is_matched,
							is_in_query))
					sents.append(words)
				sentence_out_file = (out_dir + os.sep + descriptor
					+ ".html")
				out = open(sentence_out_file, 'w')
				out.write(HTML_SENTENCE_TEMPLATE.render(Context({
						'sentences': sents
					})))
				out.close()
				task_number += 1
		tasks_file.close()
