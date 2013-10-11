from django.db import models

# Create your models here.
class Collection(models.Model):
	name = models.CharField(max_length=20)

	def __unicode__(self):
		return self.name

class Word(models.Model):
	word = models.CharField(max_length=50, db_index = True)
	pos = models.CharField(max_length=10, db_index = True)
	def __unicode__(self):
		return "[ID:"+ str(self.id) + " " + self.word + "/" + self.pos +"]"


class Relation(models.Model):
	relation = models.CharField(max_length=20, db_index = True)

	def __unicode__(self):
		return self.relation

class Dependency(models.Model):
	gov = models.ForeignKey(Word, related_name="gov", db_index = True)
	dep = models.ForeignKey(Word, related_name="dep", db_index = True)
	relation = models.ForeignKey(Relation, db_index = True)
	def __unicode__(self):
		return self.relation.relation + "(" + self.gov.word + ", " + self.dep.word +")"


class Sentence(models.Model):
	sentence = models.TextField(db_index = True)
	collection = models.ForeignKey(Collection, db_index = True)
	words_in_sentence = models.ManyToManyField(Word, through='WordInSentence', db_index = True)
	dependencies_in_sentence = models.ManyToManyField(Dependency,
		through='DependencyInSentence', db_index = True)
	def __unicode__(self):
		return str(self.id)+": " + self.sentence

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
