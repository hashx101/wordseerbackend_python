from django.core.management.base import BaseCommand
from django.db.models import Count

from collection.models import *
from nltk.corpus import stopwords

STOP_WORDS = stopwords.words('english')

class Command(BaseCommand):
	def handle(self, *args, **options):
		collection = args[0]
		dependencies = Dependency.objects.filter(
			dependencyinsentence__sentence__collection__name = collection).exclude(
				gov__word__in = STOP_WORDS
			).exclude(
				dep__word__in = STOP_WORDS
			);
		most_frequent_relations = dependencies.values('relation__relation').annotate(
			count = Count('dependencyinsentence')).order_by(
			 '-count' );

		for info in most_frequent_relations:
			print info['relation__relation'] + " : (" + str(info['count']) +")"
			relation_dependencies =  dependencies.filter(
				relation__relation=info['relation__relation'])
			gov_counts = relation_dependencies.values('gov__word').annotate(
				count = Count('dependencyinsentence')).order_by('-count')
			print "\t\t----gov:-----"
			for gov_info in gov_counts[:15]:
				print "\t\t" + gov_info['gov__word'] +" : (" + str(gov_info['count']) +")"
				dep_counts = relation_dependencies.filter(
					gov__word = gov_info['gov__word']
					).values('dep__word').annotate(count = Count('dep__word')).order_by('-count')
				for dep_info in dep_counts[:10]:
					print "\t\t\t" + dep_info['dep__word'] +" (" + str(dep_info['count']) +")"
			print "\t\t----dep:-----"
			dep_counts = relation_dependencies.values('dep__word').annotate(
				count = Count('dependencyinsentence')).order_by('-count')
			for dep_info in dep_counts[:15]:
				print "\t\t" + dep_info['dep__word'] +" : (" + str(dep_info['count']) +")"
				gov_counts = relation_dependencies.filter(
					dep__word = dep_info['dep__word']
					).values('gov__word').annotate(count = Count('gov__word')).order_by('-count')
				for gov_info in gov_counts[:10]:
					print "\t\t\t" + gov_info['gov__word'] +" (" + str(gov_info['count']) +")"





