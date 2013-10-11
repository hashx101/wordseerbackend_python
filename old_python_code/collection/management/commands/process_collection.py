from django.core.management.base import BaseCommand

from collection.models import *
from collection.management.commands.create_collection import CORPUS_DIR
from nltk.tokenize import sent_tokenize

import os

global collection

from collection.corenlp import StanfordCoreNLP
CORE_NLP_DIR = "collection/stanford-corenlp-full-2013-06-20/"
PARSER = StanfordCoreNLP(CORE_NLP_DIR)

class Command(BaseCommand):
	def handle(self, *args, **options):
		global collection
		collection_name = args[0]
		if len(collection_name) > 20:
			collection_name = collection_name[:20]
		collection = Collection.objects.get_or_create(name=collection_name)[0]
		print collection
		collection_dir = CORPUS_DIR + os.sep + collection_name
		in_file = collection_dir +"/sentences.txt"
		text = open(in_file, 'r').read()
		sentences = sent_tokenize(text)
		for i, sentence in enumerate(sentences):
			try:
				parse = PARSER.raw_parse(sentence)
				if i%50 == 0:
					print " Entered sentence " + str(i) + " of " + str(len(sentences))
				self.write_parse_products(parse['sentences'][0])
			except Exception:
				print "Error on sentence:\n\t " + sentence + " \n "
				pass

	def write_parse_products(self, parse):
		words = parse['words']
		word_objects = []
		sentence = Sentence(collection=collection)
		sentence.save()
		text = ""
		for i, word_info in enumerate(words):
			properties = word_info[1]
			token = word_info[0].lower().strip()
			surface = word_info[0].strip()
			pos = properties['PartOfSpeech']
			space_before = ""
			if i > 0:
				after_previous_word = int(words[i-1][1]['CharacterOffsetEnd'])
				space_before = " "*(int(properties['CharacterOffsetBegin']) -
					after_previous_word)
			word = Word.objects.get_or_create(word=token, pos=pos)[0]
			word.save()
			word_objects.append(word)
			text += space_before + surface
			word_in_sentence = WordInSentence(word=word, sentence=sentence,
				surface=surface, index=i, space_before=space_before)
			word_in_sentence.save()

		sentence.sentence = text.replace("(", "(").replace(")", ")").replace("``", "\"").replace("\"\"", "\"")
		sentence.save()

		for dependency_info in parse['dependencies']:
			relation_name = dependency_info[0]
			gov_index = int(dependency_info[2]) - 1
			gov = word_objects[gov_index]
			dep_index = int(dependency_info[4]) - 1
			dep = word_objects[dep_index]
			relation = None
			relation = Relation.objects.get_or_create(relation=relation_name)[0]
			relation.save()

			dependency = Dependency.objects.get_or_create(relation=relation,
					gov=gov, dep=dep)[0]
			dependency.save()

			dependency_in_sentence = DependencyInSentence(dependency=dependency,
				sentence=sentence, gov_index=gov_index, dep_index=dep_index)
			dependency_in_sentence.save()


