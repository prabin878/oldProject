import logging 
import configparser
import os
#from commonfunctions import *

class Logger:
    def logger(modulename):
        config= configparser.ConfigParser()
        config= config ['LOG']['logs']
        config.read('properties.ini')
        logs=config 
        log_path= os.path.abspath(logs)
    
        # create logger
        logg = logging.getLogger(modulename)
        logg.setLevel(logging.DEBUG)
        # create file handler and set level to debug
        fh = logging.FileHandler(log_path,'w')
        fh.setLevel(logging.DEBUG)
        # create formatter
        formatter =logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # add formatter to fh
        fh.setFormatter(formatter)
        # add fh to logger
        logg.addHandler(fh)

        return logg

    
    




    

    
    




    


    









    

    
