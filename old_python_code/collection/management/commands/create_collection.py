from django.core.management.base import BaseCommand

from nltk.corpus import gutenberg
import os

CORPUS_DIR = "collection/texts"

class Command(BaseCommand):
	def handle(self, *args, **options):
		for fileid in gutenberg.fileids():
			out_dir = CORPUS_DIR + os.sep + fileid.replace(".txt", "")
			if not os.path.isdir(out_dir):
				os.makedirs(out_dir)
			f = open(out_dir + os.sep + "sentences.txt", 'w')
			f.write(gutenberg.raw(fileid))
			f.close()
