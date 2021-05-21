# -*- coding: utf-8 -*-
"""Thesis goed

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/15RIB9qns4uLPVzPLYZbJ9DlA2OZIcuua

# **Import** **packages**
"""

#importpackages
import datetime
import pandas as pd
import numpy as np
from tabulate import tabulate
import matplotlib.pyplot as plt
from matplotlib import pyplot
from google.colab import drive
import seaborn as sns
import sys
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Flatten
from tensorflow.keras.layers import GRU, SimpleRNN, Activation, LSTM
from keras.layers import Dropout
from keras.layers.convolutional import Conv1D
from keras.layers.convolutional import MaxPooling1D
import tensorflow as tf
from keras.utils import to_categorical
from keras.preprocessing.sequence import pad_sequences
from sklearn.metrics import confusion_matrix
from sklearn.datasets import make_circles
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.metrics import cohen_kappa_score
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_curve
from sklearn.linear_model import LogisticRegression
from sklearn import metrics
from sklearn.metrics import classification_report
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

print(tf.test.gpu_device_name())
!nvidia-smi
!cat /proc/cpuinfo
# !cat /proc/meminfo

"""# **Load data**"""

#Mount drive
drive.mount('/content/drive')

#Open dataset from specific filepath
with open('/content/drive/MyDrive/....', 'rb') as f:
  #store in pandas dataframe
    df = pd.read_csv(f)

"""# **First Look at data**"""

#First look at the raw dataset
print(df.shape)
print(tabulate(df.head(), headers = 'keys', tablefmt = 'fancy_grid'))

#info regarding the dtypes of the columns
df.info()

#basic info
df.describe(include=np.object)

#shape of the dataframe
df.shape

"""# **Label product events and drop columns**"""

#drop columns not needed
coldrop = [1,3,4,5]
  # columns that are dropped:
    # event_type
    # product_skus_hash
    # server_timestamp_epoch_ms
    # hashed_url

df.drop(df.columns[coldrop], axis=1, inplace=True)

print(tabulate(df.head(), headers = 'keys', tablefmt = 'fancy_grid'))

#convert nan to view
df = df.fillna(value='view')

#convert product_action column values to numbers:
# 1 = view
# 2 = detail
# 3 = click
# 4 = remove
# 5 = purchase
# 6 = add


df["product_action"].replace({"view": 1, "detail": 2,"add": 6, "remove": 4,"purchase": 5, "click": 3}, inplace=True)

#check if it worked
print(tabulate(df.head(), headers = 'keys', tablefmt = 'fancy_grid'))

"""# **EDA**"""

#show the distribution off the different events
df["product_action"].hist(bins=50)
plt.show

# statistics of the dataset
print("Total unique events: ", df['session_id_hash'].count())
print("Total unique sessions: ", df['session_id_hash'].nunique())
print("Total unique product actions: ", df['product_action'].nunique())

# counting the different events in the product_action column
df["product_action"].value_counts()



"""# **Add target column, trim sequences to event before add to cart if available and trim the total lenght of the sequences**"""

df2 = df

# create new sequence grouped by session_id_hash and sequence of product_action
sequence = df2.groupby('session_id_hash')['product_action'].apply(list)
sequence = sequence.reset_index()
#add add_to_cart target value
sequence['add_to_cart'] = sequence['product_action'].apply(lambda x: 1 if 6 in x else 0)
#remove sequences with lenght 1
sequence = sequence[sequence['product_action'].map(len)> 1]

#show result
print('Total number of records=', sequence.shape[0])
print(tabulate(sequence.head(), headers = 'keys', tablefmt = 'fancy_grid'))

#remove 6 from sequences
sequence['product_action']= sequence.product_action.apply(lambda row: list(filter(lambda a: a != 6, row)))

#show result
print('Total number of records=', sequence.shape[0])
print(tabulate(sequence.head(5), headers = 'keys', tablefmt = 'fancy_grid'))



# add lenght of sequences column
sequence['lenght'] = sequence['product_action'].map(len).to_list()

#show result
print(tabulate(sequence.head(), headers = 'keys', tablefmt = 'fancy_grid'))
sequence.shape

# store lenght in variable
length = sequence['product_action'].map(len).to_list()

#plot the lenght of the sequences before trimming to lenght >= 5 and lenght =< 155
sns.distplot(length)

#trim. sequences to lenght > 5 and lenght < 155
sequence = sequence.drop(sequence[sequence.lenght < 5].index)
sequence = sequence.drop(sequence[sequence.lenght > 155].index)
sequence.shape

#drop sequence lenght column
sequence.drop(sequence.columns[3], axis=1, inplace=True)

#plot the lenght of the sequences after trimming to lenght > 5 and lenght < 155
length = sequence['product_action'].map(len).to_list()
sns.distplot(length)

"""# **Pad sequences and train test and one hot encoding for LSTM, GRU and Conv1d models + balance data**"""

#padding the sequences
pad_sequence = sequence['product_action']

pad_input = tf.keras.preprocessing.sequence.pad_sequences(pad_sequence, padding="post")

print('pad_input shape=', pad_input.shape)

# hot encoding
hot_encoded = to_categorical(pad_input, num_classes=6)
print(hot_encoded.shape)

# define y and calculate the percentage of add to cart sessions
from collections import Counter

y = sequence['add_to_cart']

z=np.sum(y)/len(y)

print('Percentage of add to cart sessions=',z*100,"%")

# define function for Train Test split
def prepare_train_test_data(data,y):
  #train test split 70/30
  X_train, X_test, y_train, y_test = train_test_split(data, y, test_size=0.3, random_state=101)

  #reshaping X_train and X_test
  X_train = X_train.reshape((X_train.shape[0],X_train.shape[1],6))
  X_test = X_test.reshape((X_test.shape[0],X_test.shape[1],6))
  return (X_train,X_test,y_train,y_test)

#create train and testing data
X_train, X_test, y_train, y_test=prepare_train_test_data(hot_encoded,y)

X_test, X_val, y_test, y_val = train_test_split(X_test, y_test, test_size=0.5, random_state=101)

print(X_train.shape, y_train.shape, X_test.shape, y_test.shape )
print(X_val.shape,y_val.shape)

# define oversampler
from imblearn.over_sampling import RandomOverSampler 
oversampler = RandomOverSampler(sampling_strategy=1, random_state=101)

# oversample the data

X = X_train.reshape(len(X_train),-1)
y = y_train

X_oversampled, y_oversampled = oversampler.fit_resample(X, y)
print(Counter(y_oversampled))
print(y_oversampled.shape)
print(X_oversampled.shape)

#shuffle so that de add to cart sessions occur random
from sklearn.utils import shuffle
X_oversampled,y_oversampled = shuffle(X_oversampled, y_oversampled, random_state=0)
z=np.sum(y_oversampled)/len(y_oversampled)
print('Percentage of add to cart sessions=',z*100,"%")

#reshape the data for the LSTM, GRU and Conv1d model
X_oversampled = X_oversampled.reshape(len(X_oversampled),155,6)
print(X_oversampled.shape)

"""# **plot functions and eva methods**"""

from matplotlib import pyplot
def plot_history(history):
  # plot model fitting process
  print(history.history.keys())
  

  # plot train and validation loss
  pyplot.plot(history.history['loss'])
  pyplot.plot(history.history['val_loss'])
  pyplot.title('model train vs validation loss')
  pyplot.ylabel('loss')
  pyplot.xlabel('epoch')
  pyplot.legend(['train', 'validation'], loc='upper right')
  pyplot.show()

  # summarize accuracy history
  pyplot.plot(history.history['acc'])
  pyplot.plot(history.history['val_acc'])
  pyplot.title('model train acc vs validation acc')
  pyplot.ylabel('acc')
  pyplot.xlabel('epoch')
  pyplot.legend(['train', 'validation'], loc='lower right')
  pyplot.show()



def evaluate_on_test(X_test, y_test, training_model):
  #eveluate on test data
  g_preds=training_model.predict_classes(X_test)
  gaccuracy = accuracy_score(y_test, g_preds)
  print('Accuracy: %f' % gaccuracy)
  # precision tp / (tp + fp)
  gprecision = precision_score(y_test, g_preds)
  print('Precision: %f' % gprecision)
  # recall: tp / (tp + fn)
  grecall = recall_score(y_test, g_preds)
  print('Recall: %f' % grecall)
  # f1: 2 tp / (2 tp + fp + fn)
  gf1 = f1_score(y_test, g_preds)
  print('F1 score: %f' % gf1)
  # ROC and AUC
  auc_roc_0 = str(roc_auc_score(y_test, g_preds))
  print('AUC: \n' + auc_roc_0)
  
  print(classification_report(y_test, g_preds))

  cm = metrics.confusion_matrix(y_test, g_preds)

  #confusion matrix
  plt.figure(figsize=(9,9))
  sns.heatmap(cm, annot=True, fmt=".3f", linewidths=.5, square = True, cmap = 'Blues_r');
  plt.ylabel('Actual label');
  plt.xlabel('Predicted label');
  all_sample_title = 'Auc: {0}'.format(auc_roc_0)
  plt.title(all_sample_title, size = 15);

  #roc curve
  fpr, tpr, thresholds = roc_curve(y_test, training_model.predict_classes(X_test))
  plt.figure()
  plt.plot(fpr, tpr, label='(area = %0.2f)' % roc_auc_score(y_test, g_preds))
  plt.plot([0, 1], [0, 1],'r--')
  plt.xlim([0.0, 1.0])
  plt.ylim([0.0, 1.05])
  plt.xlabel('False Positive Rate')
  plt.ylabel('True Positive Rate')
  plt.title('Receiver operating characteristic')
  plt.legend(loc="lower right")
  plt.savefig('Log_ROC')
  plt.show()

#compute class weights
from sklearn.utils import class_weight
class_weights = class_weight.compute_class_weight(None,
                                                 np.unique(y_oversampled),
                                                 y_oversampled)

class_weights = dict(enumerate(class_weights))
print(class_weights)

early_stopping = tf.keras.callbacks.EarlyStopping(
    monitor='val_loss', 
    verbose=1,
    patience=10,
    mode='min',
    restore_best_weights=True)

"""# **LSTM**"""

#Build the model sequence to label
def LSTM_model(neurons):
    

    model = Sequential()
    model.add(LSTM(neurons,return_sequences=False, input_shape = (155,6)))
    model.add(Dropout(0.1))
    model.add(Dense(1, activation='sigmoid'))
    
    model.compile(optimizer=(tf.keras.optimizers.Adam(learning_rate=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-07, amsgrad=False,name='Adam') ), loss='binary_crossentropy', metrics=[tf.keras.metrics.Recall(),tf.keras.metrics.Precision(),'acc'])

    return model

#show model
tf.keras.backend.clear_session()
training_model = LSTM_model(100)
training_model.summary()

#train the model
with tf.device('/gpu:0'): 
              lstm_history =       training_model.fit(X_oversampled, y_oversampled,
                    epochs=20,
                    batch_size=16,
                    callbacks=[early_stopping],
                    validation_data = (X_val,y_val),
                    class_weight=class_weights)

#Use plot_history function to plot the model curves for loss and accuracy
plot_history(lstm_history)

# Use evaluate_on_test function to note accuracy, precision, recall and F1 score on test data
evaluate_on_test(X_test, y_test, training_model)

"""# **GRU**"""

#define GRU
def GRU_model(neurons):

    model = Sequential()
    model.add(GRU(neurons, return_sequences = False, input_shape = (155,6)))
    model.add(Dropout(0.1))
    model.add(Dense(1, activation='sigmoid'))

    model.compile(optimizer=(tf.keras.optimizers.Adam(learning_rate=0.01, beta_1=0.9, beta_2=0.999, epsilon=1e-07, amsgrad=False,name='Adam') ), loss='binary_crossentropy', metrics=[tf.keras.metrics.Recall(),tf.keras.metrics.Precision(),'acc'])
    return model

#Visualize the Model 
tf.keras.backend.clear_session()
G_model = GRU_model(100)
G_model.summary()

#Train the G_model
with tf.device('/gpu:0'): 
  g_history = G_model.fit(X_oversampled, y_oversampled,
                    epochs=20,
                    batch_size=64,
                    callbacks=[early_stopping],
                    validation_data = (X_val,y_val),
                    class_weight=class_weights)

#plot the model curves for loss and accuracy
plot_history(g_history)

# Use evaluate_on_test 
evaluate_on_test(X_test, y_test, G_model)

"""# **Conv1D + LSTM**"""

#define GRU
def CLSTM_model(neurons):

    model = Sequential()
    model.add(Conv1D(filters=32, kernel_size=3, padding='valid', activation='relu', input_shape=(155,6)))
    model.add(MaxPooling1D(pool_size=2))
    model.add(LSTM(neurons, return_sequences = False))
    model.add(Dropout(0.1))
    model.add(Dense(1, activation='sigmoid'))

    model.compile(optimizer=(tf.keras.optimizers.Adam(learning_rate=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-07, amsgrad=False,name='Adam') ), loss='binary_crossentropy', metrics=[tf.keras.metrics.Recall(),tf.keras.metrics.Precision(),'acc'])
    return model

tf.keras.backend.clear_session()
CLSTMmodel = CLSTM_model(100)
CLSTMmodel.summary()

#train the model
with tf.device('/gpu:0'): 
              clstm_history =       CLSTMmodel.fit(X_oversampled, y_oversampled,
                    epochs=20,
                    batch_size=32,
                    callbacks=[early_stopping],
                    validation_data = (X_val,y_val),
                    class_weight=class_weights)

#plot the model curves for loss and accuracy
plot_history(clstm_history)

# Use evaluate_on_test 
evaluate_on_test(X_test, y_test, CLSTMmodel)

"""# **Conv1D + GRU**"""

def CGRU_model(neurons):

    model = Sequential()
    model.add(Conv1D(filters=32, kernel_size=3, padding='valid', activation='relu', input_shape=(155,6)))
    model.add(MaxPooling1D(pool_size=2))
    model.add(GRU(neurons, return_sequences = False))
    model.add(Dropout(0.1))
    model.add(Dense(1, activation='sigmoid'))

    model.compile(optimizer=(tf.keras.optimizers.Adam(learning_rate=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-07, amsgrad=False,name='Adam') ), loss='binary_crossentropy', metrics=[tf.keras.metrics.Recall(),tf.keras.metrics.Precision(),'acc'])
    return model

tf.keras.backend.clear_session()
CG_model = CGRU_model(100)
CG_model.summary()

#Train 
with tf.device('/gpu:0'): 
  cg_history = CG_model.fit(X_oversampled, y_oversampled,
                    epochs=20,
                    batch_size=64,
                    callbacks=[early_stopping],
                    validation_data = (X_val,y_val),
                    class_weight=class_weights)

#plot the model curves for loss and accuracy
plot_history(cg_history)

# Use evaluate_on_test 
evaluate_on_test(X_test, y_test, CG_model)

"""# **Train test split Random forests and Logistic regression + balance data**"""

y = np.array(sequence['add_to_cart'])

# define function for Train Test split
def prepare_train_test_data(data,y):
  #train test split 70/30
  X_train, X_test, y_train, y_test = train_test_split(data, y, test_size=0.3)

  #reshaping X_train and X_test
  X_train = X_train.reshape((X_train.shape[0],  X_train.shape[1]))
  X_test = X_test.reshape((X_test.shape[0],  X_test.shape[1]))
  return (X_train,X_test,y_train,y_test)

X_train, X_test, y_train, y_test=prepare_train_test_data(np.array(pad_input),y)
print(X_train.shape, y_train.shape, X_test.shape, y_test.shape )

# define oversampler
from imblearn.over_sampling import RandomOverSampler 
oversampler = RandomOverSampler(sampling_strategy=1, random_state=101)

# oversample the data

X = X_train
y = y_train

X_oversampled, y_oversampled = oversampler.fit_resample(X, y)
print(Counter(y_oversampled))
print(y_oversampled.shape)
print(X_oversampled.shape)

#shuffle so that de add to cart sessions occur random
from sklearn.utils import shuffle
X_train,y_train = shuffle(X_oversampled, y_oversampled, random_state=0)
z=np.sum(y_train)/len(y_train)
print('Percentage of add to cart sessions=',z*100,"%")

"""# **Random forests**"""

rfc1=RandomForestClassifier(random_state=101, n_jobs= -1, n_estimators= 100)

rfc1.fit(X_train, y_train)

probab_pred = rfc1.predict_proba(X_test)
predictions = rfc1.predict(X_test)
score = rfc1.score(X_test, y_test)

print(score)

cm = metrics.confusion_matrix(y_test, predictions)
print(classification_report(y_test, predictions))

auc_roc_0 = str(roc_auc_score(y_test, predictions))
print('AUC: \n' + auc_roc_0)


cm = metrics.confusion_matrix(y_test, predictions)

plt.figure(figsize=(9,9))
sns.heatmap(cm, annot=True, fmt=".3f", linewidths=.5, square = True, cmap = 'Blues_r');
plt.ylabel('Actual label');
plt.xlabel('Predicted label');
all_sample_title = 'Auc: {0}'.format(auc_roc_0)
plt.title(all_sample_title, size = 15);

logit_roc_auc = roc_auc_score(y_test, rfc1.predict(X_test))
fpr, tpr, thresholds = roc_curve(y_test, rfc1.predict_proba(X_test)[:,1])
plt.figure()
plt.plot(fpr, tpr, label='random forests (area = %0.2f)' % logit_roc_auc)
plt.plot([0, 1], [0, 1],'r--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver operating characteristic')
plt.legend(loc="lower right")
plt.savefig('Log_ROC')
plt.show()

"""# **logistic regression**"""

logisticRegr = LogisticRegression(max_iter = 1000 , solver='saga', verbose =1, n_jobs=-1, C = 1 )

logisticRegr.fit(X_train, y_train)

predictions = logisticRegr.predict(X_test)
score = logisticRegr.score(X_test, y_test)

print(score)

cm = metrics.confusion_matrix(y_test, predictions)
print(classification_report(y_test, predictions))

plt.figure(figsize=(9,9))
sns.heatmap(cm, annot=True, fmt=".3f", linewidths=.5, square = True, cmap = 'Blues_r');
plt.ylabel('Actual label');
plt.xlabel('Predicted label');
all_sample_title = 'Accuracy Score: {0}'.format(score)
plt.title(all_sample_title, size = 15);

logit_roc_auc = roc_auc_score(y_test, logisticRegr.predict(X_test))
fpr, tpr, thresholds = roc_curve(y_test, logisticRegr.predict_proba(X_test)[:,1])
plt.figure()
plt.plot(fpr, tpr, label='Logistic Regression (area = %0.2f)' % logit_roc_auc)
plt.plot([0, 1], [0, 1],'r--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver operating characteristic')
plt.legend(loc="lower right")
plt.savefig('Log_ROC')
plt.show()

auc_roc_0 = str(roc_auc_score(y_test, predictions))
print('AUC: \n' + auc_roc_0)