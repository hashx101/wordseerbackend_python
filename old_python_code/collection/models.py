from django.db import models

# Create your models here.
class Collection(models.Model):
	name = models.CharField(max_length=20)

	def __unicode__(self):
		return self.name

class Document(models.Model):
	collection = models.ForeignKey(Collection, db_index = True)
	title = models.TextField(db_index = True)
	sentence_count = models.IntegerField()

class Word(models.Model):
	word = models.CharField(max_length = 50, db_index = True)
	pos = models.CharField(max_length = 10, db_index = True)
	similar_words = models.ManyToManyField(Word, through='Synset', db_index = True)
	def __unicode__(self):
		return "[ID:"+ str(self.id) + " " + self.word + "/" + self.pos +"]"

class Synset(models.Model):
	word1 = models.ForeignKey(Word, related_name = 'word1', db_index = True)
	word2 = models.ForeignKey(Word, related_name = 'word2', db_index = True)
	similarity_score = models.FloatField(db_index = True)

class Relation(models.Model):
	relation = models.CharField(max_length = 20, db_index = True)

	def __unicode__(self):
		return self.relation

class Dependency(models.Model):
	gov = models.ForeignKey(Word, related_name = "gov", db_index = True)
	dep = models.ForeignKey(Word, related_name = "dep", db_index = True)
	relation = models.ForeignKey(Relation, db_index = True)
	def __unicode__(self):
		return self.relation.relation + "(" + self.gov.word + ", " + self.dep.word +")"

class Sequence(models.Model):
	sequence = models.CharField(max_length = 200, db_index = True)
	lemmatized = models.BooleanField(db_index = True)
	has_function_words = models.BooleanField(db_index = True)
	all_function_words = models.BooleanField(db_index = True)
	length = models.IntegerField(db_index = True)
	sentence_count = models.IntegerField(db_index = True)
	document_count = models.IntegerField(db_index = True)

class Sentence(models.Model):
	sentence = models.TextField(db_index = True)
	document = models.ForeignKey(Document, db_index = True)
	collection = models.ForeignKey(Collection, db_index = True)
	words_in_sentence = models.ManyToManyField(Word, through='WordInSentence', db_index = True)
	dependencies_in_sentence = models.ManyToManyField(Dependency,
		through = 'DependencyInSentence', db_index = True)
	sequences_in_sentnece = models.ManyToManyField(Sequence,
		through = 'SequenceInSentence', db_index = True)
	def __unicode__(self):
		return str(self.id)+": " + self.sentence


class SequenceInSentence(models.Model):
	sequence = models.ForeignKey(Sequence, db_index = True)
	sentence = models.ForeignKey(Sentence, db_index = True)
	document = models.ForeignKey(Document, db_index = True)
	start_position = models.IntegerField()


class WordInSentence(models.Model):
	word = models.ForeignKey(Word, db_index = True)
	sentence = models.ForeignKey(Sentence)
	surface = models.CharField(max_length=50, db_index = True)
	space_before = models.CharField(max_length=2)
	index = models.IntegerField(db_index = True)

	def __unicode__(self):
		return str(self.word) + " in " + str(self.sentence)

class DependencyInSentence(models.Model):
	dependency = models.ForeignKey(Dependency, db_index = True)
	sentence = models.ForeignKey(Sentence, db_index = True)
	gov_index = models.IntegerField(db_index = True)
	dep_index = models.IntegerField(db_index = True)

	def __unicode__(self):
		return str(self.dependency) + " in " + str(self.sentence)

class Unit(models.Model):
	unit_name = models.CharField(max_length = 100, db_index = True)
	unit_number = models.FloatField(db_index = True)
	parent = models.ForeignKey(Unit, db_index = True)
	document = models.ForeignKey(Document)
	sentences_in_unit = models.ManyToManyField(Sentence, db_index = True)

## The two metadata classes: Property and Value.
## Each Property (e.g. 'Act Number') can have
## multiple Values (e.g. 'Act 1', 'Act 2', etc). For each Value, there are Units
## that match that value.
class Property(models.Model):
	name = models.CharField(max_length = 100)
	unit_name = models.CharField(max_length = 100)
	value_is_displayed = models.BooleanField()
	name_is_displayed = models.BooleanField()
	name_to_display = models.CharField(max_length = 100)
	type = models.CharField(max_length = 100)
	format = models.CharField(max_length = 100)
	is_category = models.BooleanField()

class Value(models.Model):
	property = models.ForeignKey(Property)
	value = models.CharField(max_length = 100, db_index = True)
	document = models.ForeignKey(Document)
	matching_units = models.ManyToManyField(Unit, db_index = true)

class WordSet(models.Model):
	words = models.ManyToManyField(Word, db_index = True)
	name = models.CharField(max_length = 100, db_index = True)
	user = models.ForeignKey(User)
	date = models.DateField()
	parent = models.ForeignKey(WordSet)

class SentenceSet(models.Model):
	words = models.ManyToManyField(Sentence, db_index = True)
	name = models.CharField(max_length = 100, db_index = True)
	user = models.ForeignKey(User)
	date = models.DateField()
	parent = models.ForeignKey(SentenceSet)

class DocumentSet(models.Model):
	words = models.ManyToManyField(Document, db_index = True)
	name = models.CharField(max_length = 100, db_index = True)
	user = models.ForeignKey(User)
	date = models.DateField()
	parent = models.ForeignKey(DocumentSet)

