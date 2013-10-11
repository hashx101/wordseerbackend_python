This was part of a django app I wrote for another research project.

In the collection/management/commands directory, you'll find scripts that use the models in collection/models.py to extract and store the linguistic information in the sentences in a given novel (found in the texts/ directory).

You can run them with "python manage.py <file name> <arguments>" for example

python manage.py create_collection austen-emmma

and then

python manage.py process_collection austen-emma

To use the python wrapper for the stanford NLP tools in the corenlp/ directory you need to

1. Download and unzip the stanford core nlp tools into a directory
2. Alter line 40 of corenlp/corenlp.py to point to that directory.
