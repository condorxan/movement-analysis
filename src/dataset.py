import time
from numpy import fft
from matplotlib import pyplot as plt
from pickle import BINSTRING
import math
import os
from sklearn import svm
from sklearn import grid_search
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import confusion_matrix

class sample_file:
    def __init__(self, filename):
        self.filename = filename
        with open(filename) as file:
            self.data = []
            lines = [line for line in file]
            for line in lines[2:]:
                parts = [float(measurement.strip()) for measurement in line.split(';')]
                self.data.append(parts)
                
    def get_frequencies(self):
        num_seconds = float(self.data[-1][0] - self.data[0][0]) / float(1000)
        samples_per_second = len(self.data) / num_seconds
        num_samples = len(self.data)
        oscilations_per_sample = [float(oscilations) / num_samples for oscilations in range(0, num_samples)]
        return [ops * samples_per_second for ops in oscilations_per_sample]
    
    def get_buckets(self, num_buckets, hertz_cutoff=float(5)):
        one_dimentional = [column[2] for column in self.data]
        transformed = fft.fft(one_dimentional)
        absolute = [abs(complex) for complex in transformed]
        
        frequencies = self.get_frequencies()
        
        buckets = [0 for i in range(num_buckets)]
        width = hertz_cutoff / num_buckets
        for i in range(1, len(absolute)):
            index = int(frequencies[i] / width)
            if index >= num_buckets:
                break;
            buckets[index] += absolute[i]
#         pyplot.plot([i * width for i in range(num_buckets)], buckets, label = self.filename)
        return buckets
    
    def get_samples(self):
        buckets = self.get_buckets(40)
        return [buckets]
        
class dataset:
    def __init__(self, foldername, filters = {'dancing': 0, 'walking': 1, 'sitting':2}):
        self.data = []
        self.target = []
        self.activities = []
        for activity, number in filters.iteritems():
            samples = get_samples(foldername, filter=activity)
            for sample in samples:
                self.data.append(sample)
                self.target.append(number)
                self.activities.append(activity)
            
def get_samples(foldername, filter=None):
    samples = []
    for file in os.listdir(foldername):
        if filter and file.find(filter) == -1:
            continue
        for sample in sample_file(foldername + '/' + file).get_samples():
            samples.append(sample)
        
    return samples


          
if __name__ == '__main__':
    filters = {'dancing': 0, 'walking': 1, 'sitting':2}
    training = dataset('../datasets/training', filters)
    
    svr = svm.SVC()
    parameters = {'kernel':['linear', 'rbf']}
    clf = grid_search.GridSearchCV(svr, parameters)
    print clf 
    clf.fit(training.data, training.target)

    validation = dataset('../datasets/validation')
    
    predicted = clf.predict(validation.data)
    truedata =  map(lambda x: filters[x], validation.activities)
    # http://scikit-learn.org/stable/auto_examples/calibration/plot_calibration_curve.html
    precision=precision_score(truedata, predicted, average='macro')  
    recall=recall_score(truedata, predicted, average='macro')  

    # XXX Precision/recall should be written into a logfile with a timestamp.
    print "predicted = ", predicted
    print "truedata  = ", truedata
    print "macro precision = ", precision
    print "recall precision = ", recall
    
    ts = time.time()
    record = str(ts) + ", " +  str(precision) + ", " +  str(recall) + "\n";
    with open("../logs/precision-recall-time-evolution.csv", "a") as myfile:
        myfile.write(record)

    # Compute confusion matrix
    cm = confusion_matrix(truedata, predicted)

    print(cm)
    
   # Show confusion matrix in a separate window
    plt.matshow(cm)
    plt.title('Confusion matrix')
    plt.colorbar()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.show()



#     pyplot.legend()
#     pyplot.show()
    
    
    
