"""Module trains chosen algorithms and then classifies text inputs.
@author: Jan Balaz
"""

import os
import gensim
#import logging
from gensim.corpora import wikicorpus


class GensimAPIError(Exception):
    """Base exception class for other exception from this module.  """
    pass


class NotSupportedError(GensimAPIError):
    """Raised when given algorithm is not supported in this API.  """
    pass


class NotTrainedError(GensimAPIError):
    """Raised when algorithm was not trained or properly loaded.  """
    pass


class GensimAPI(object):
    """API for Gensim library. Manages training of classification algorithm and process of text classification.  """
    
    #logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")
    TF_IDF = "tfidf.mm"
    WORD_IDS = "wordids.txt.bz2"
    ALGOS = {"lsi": gensim.models.lsimodel.LsiModel,
             "lda": gensim.models.ldamodel.LdaModel #TODO train this algo
            }

    def __init__(self, trained=True, algo="lda", topics=100):
        """Loads training data depending on classification algorithm.Raises exception if algo is not supported.  """
        if algo.lower() not in self.ALGOS.keys():
            raise NotSupportedError("Training algorithm used for classification is not supported by this application.")
        self.model, self.dictionary = self._get_trained_algo(algo) if trained else self._train_algo(algo, topics)
        if self.model is None or self.dictionary is None:
            raise NotTrainedError("Training of algorithm was not successful, cannot be used for classification.")
        
    def classify_text(self, text, dimension=10):
        """Classifies text, adjusts result vector to given dimension or smaller.  
        Vector of possible themes is a list of tuples (theme id, suitability).  
        Returns vector sorted by suitability descending.  
        """
        classified = self.model[self._get_query(text)]
        themes = list(sorted(classified, key=lambda x: x[1], reverse=True))
        #self._print_themes(themes) #DEBUG only
        return themes[:dimension]
    
    def _train_algo(self, algo, topics):
        """Trains Gensim library with selected algorithm, uses English Wikipedia dump.  """
        try:
            dictionary = gensim.corpora.Dictionary.load_from_text(os.path.join(self.PATH, self.WORD_IDS))
            mm = gensim.corpora.MmCorpus(os.path.join(self.PATH, self.TF_IDF))
            model = self._get_model(self.ALGOS[algo], mm, dictionary, topics)
            self._persist(model, algo)
        except Exception:
            return None, None
        else:
            return model, dictionary
        
    def _persist(self, model, algo):
        """Saves trained model to disc.  """
        model.save(os.path.join(self.PATH, 'trained.' + str(algo).lower()))
        
    def _get_model(self, func, mm, id2word, topics):
        """Returns model for given classification algorithm by func parameter.  """
        return func(corpus=mm, id2word=id2word, num_topics=topics)    
    
    def _get_trained_algo(self, algo):
        """Loads trained data as object of given algorithm.  """
        try:
            model = gensim.models.ldamodel.LdaModel.load(self.PATH + "\\trained." + str(algo).lower())
            dictionary = gensim.corpora.Dictionary.load_from_text(os.path.join(self.PATH, self.WORD_IDS))
        except Exception:
            return None, None
        else:
            return model, dictionary
    
    def _get_query(self, text):
        """Preprocess and tokenize text, return it as BOW (bag of words).  """
        return self.dictionary.doc2bow(wikicorpus.tokenize(text))
    
    def _print_themes(self, themes):
        """Print suitable themes for debugging purpose. Delete before production.  """
        for theme in themes:
            print(str(theme[0]) + ": " + self.model.print_topic(theme[0]))
            
    def _get_all_themes(self):
        """Themes for debugging purpose. Delete before production.  """
        themes = self.model.print_topics(100)
        return themes
            