# -*- coding: utf-8 -*-
"""NLP_Assignment_2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1fjFC_ylZSYAlaAVvy95EBQUrIPfqHcxO
"""

#import dataset from the given link

import pandas as pd
URL_Tr = 'https://raw.githubusercontent.com/cacoderquan/Sentiment-Analysis-on-the-Rotten-Tomatoes-movie-review-dataset/master/train.tsv'
dataset = pd.read_csv(URL_Tr, sep='\t')

review = dataset[['Phrase','Sentiment']]

# import necessary libraries and initialise the preprocessing parameters
import re
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
nltk.download('wordnet')
from nltk.stem import WordNetLemmatizer, PorterStemmer, LancasterStemmer
porter = PorterStemmer()
lancaster=LancasterStemmer()
wordnet_lemmatizer = WordNetLemmatizer()
stop_words = stopwords.words("english")

#Function to perform preprocessing of data, stemming lemmatisation, removal of punctuations etc.,

def preprocessing(review,remove_stopwords = True, stem_lem = 'word_net'):
  temp = review
  temp.loc[:,"Phrase"] = temp.Phrase.apply(lambda x : str.lower(x))
  temp.loc[:,"Phrase"] = temp.Phrase.apply(lambda x : " ".join(re.findall('[a-zA-Z]+',x)))
  if remove_stopwords == True:
    temp.loc[:,"Phrase"] = temp.Phrase.apply(lambda x : ' '.join(word for word in x.split() if word not in stop_words))
  if stem_lem =='word_net':
    temp.loc[:,"Phrase"] = temp.Phrase.apply(lambda x: " ".join([wordnet_lemmatizer.lemmatize(word) for word in x.split()]))
  elif stem_lem == 'lancaster':
    temp.loc[:,"Phrase"] = temp.Phrase.apply(lambda x: " ".join([lancaster.stem(word) for word in x.split()]))
  elif stem_lem == 'porter':
    temp.loc[:,"Phrase"] = temp.Phrase.apply(lambda x: " ".join([porter.stem(word) for word in x.split()]))
  return temp

# The entire dataset is preprocessed and this does not result in dataleakage hence done together
preprocessed_review = preprocessing(review,remove_stopwords=True,stem_lem='word_net')

preprocessed_review.head()

# Some rows are null so they are droped
null_index = preprocessed_review[preprocessed_review['Phrase']==''].index
preprocessed_review.drop(null_index,inplace=True)
print(preprocessed_review['Sentiment'].value_counts())

#Converted to list to perform split

phrases = preprocessed_review['Phrase'].values
y = preprocessed_review['Sentiment'].values

#Train test split is done and the training data is feed back to a dataframe

from sklearn.model_selection import train_test_split
phrases_train, phrases_test, y_train, y_test = train_test_split(phrases, y, test_size=0.30, random_state=2003,stratify = y)
print(phrases_train.shape,y_train.shape)
phrases_buffer = pd.DataFrame()
phrases_buffer['Phrase'] = phrases_train.tolist()
phrases_buffer['Sentiment'] = y_train.tolist()
print(phrases_buffer['Sentiment'].value_counts())
phrases_train

#These lines of code was written to experiment upsampling and down-sampling however
#it did not provide good results hence maintained at 1

phrases_train_df = pd.DataFrame()
class_4 = phrases_buffer['Sentiment'] == 4
class_4_dataframe = phrases_buffer[class_4]
phrases_train_df = phrases_train_df.append([class_4_dataframe]*1,ignore_index=True)
class_0 = phrases_buffer['Sentiment'] == 0
class_0_dataframe = phrases_buffer[class_0]
phrases_train_df = phrases_train_df.append([class_0_dataframe]*1,ignore_index=True)
class_1 = phrases_buffer['Sentiment'] == 1
class_1_dataframe = phrases_buffer[class_1]
phrases_train_df = phrases_train_df.append([class_1_dataframe]*1,ignore_index=True)
class_3 = phrases_buffer['Sentiment'] == 3
class_3_dataframe = phrases_buffer[class_3]
phrases_train_df = phrases_train_df.append([class_3_dataframe]*1,ignore_index=True)
class_2 = phrases_buffer['Sentiment'] == 2
class_2_dataframe = phrases_buffer[class_2]
phrases_train_df = phrases_train_df.append([class_2_dataframe]*1,ignore_index=True)

phrases_train_df['Sentiment'].value_counts()

# X_Train and y_train data are ready for keras model

X_train = phrases_train_df[['Phrase']].to_numpy()
y_train = phrases_train_df[['Sentiment']].to_numpy()
X_train = X_train[:,0]
y_train = y_train[:,0]
X_train.shape,y_train.shape

#Keras tokenizer is defined and fit with only the phrases in X_train dataset 


from keras.models import Sequential
from keras import layers
from keras.preprocessing.text import Tokenizer

tokenizer = Tokenizer(num_words=13000) 
tokenizer.fit_on_texts(X_train)

X_train = tokenizer.texts_to_sequences(X_train)
X_test = tokenizer.texts_to_sequences(phrases_test)

# coding for padding
from keras.preprocessing.sequence import pad_sequences
sentence_length = 15
X_train = pad_sequences(X_train, padding='post', maxlen=sentence_length)
X_test = pad_sequences(X_test, padding='post', maxlen=sentence_length)

X_train.shape

# The class values are one-hot-encoded
from keras.utils import to_categorical
y_train = to_categorical(y_train, 5)
y_test = to_categorical(y_test, 5)

# function for creation of embedding matrix as provided by keras documentation.

import numpy as np

def create_embedding_matrix(filepath, word_index, embedding_dim):
    vocab_size = len(word_index) + 1  # Adding again 1 because of reserved 0 index
    embedding_matrix = np.zeros((vocab_size, embedding_dim))

    with open(filepath) as f:
        for line in f:
            word, *vector = line.split()
            if word in word_index:
                idx = word_index[word] 
                embedding_matrix[idx] = np.array(
                    vector, dtype=np.float32)[:embedding_dim]

    return embedding_matrix

# Creating embedding matrix
embedding_dim = 300
embedding_matrix = create_embedding_matrix('/content/glove.6B.300d.txt',tokenizer.word_index, embedding_dim)

# define vocab size
vocab_size = len(tokenizer.word_index) + 1
vocab_size

# Define the classifier model

model = Sequential()
model.add(layers.Embedding(vocab_size, embedding_dim,weights=[embedding_matrix], input_length=sentence_length,trainable=False))
model.add(layers.Conv1D(512, 3, activation='relu'))
model.add(layers.BatchNormalization())
model.add(layers.Dropout(0.5))
model.add(layers.Conv1D(256, 3, activation='relu'))
model.add(layers.BatchNormalization())
model.add(layers.Dropout(0.5))
model.add(layers.Conv1D(128, 3, activation='relu'))
model.add(layers.BatchNormalization())
model.add(layers.Dropout(0.5))
model.add(layers.MaxPool1D())
model.add(layers.Conv1D(64, 3, activation='relu'))
model.add(layers.GlobalMaxPooling1D())
model.add(layers.Dense(128,activation = 'relu'))
model.add(layers.Dense(100, activation='relu'))
model.add(layers.Dense(50, activation='relu'))
model.add(layers.Dense(10, activation='relu'))
model.add(layers.Dense(5, activation='softmax'))
model.compile(optimizer='adam',loss='categorical_crossentropy',metrics=['accuracy'])
model.summary()

# Initialise early stopping
from keras.callbacks import EarlyStopping
es = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=10)

# Train the model
history = model.fit(X_train, y_train,epochs=50,verbose=True,validation_data=(X_test, y_test),batch_size=25,callbacks=[es])

#Plot the training accuracy and loss
import matplotlib.pyplot as plt

training_dict = history.history
accuracy_val = training_dict['acc']
loss_val = training_dict['loss']
epochs = range(1, len(loss_val) + 1)
plt.figure()
plt.xlabel("No of Epochs")
plt.ylabel("Loss")
plt.plot(epochs,loss_val)
plt.savefig('Loss.png')
plt.figure()
plt.xlabel("No of Epochs")
plt.ylabel("Accuracy")
plt.plot(epochs,accuracy_val)
plt.savefig('Accuracy.png')

# Save the model
model.save('1111017_1dconv_reg')

# load the model

from keras.models import load_model
model = load_model('1111017_1dconv_reg')

# Evaluate the model
loss, accuracy = model.evaluate(X_test, y_test, verbose=False)
print("Testing Accuracy:  {:.4f}".format(accuracy))

# Calculate Precision, Recall and F1 score.

from sklearn.metrics import f1_score, precision_score, recall_score, confusion_matrix
import numpy as np

from collections import Counter
rounded_labels=np.argmax(y_test, axis=1)
y_pred1 = model.predict(X_test)
y_pred = np.argmax(y_pred1, axis=1)
print(y_pred)
precision = precision_score(rounded_labels, y_pred , average="macro")
print("The Precision is : %.4f" % precision)
recall = recall_score(rounded_labels, y_pred , average="macro")
print("The Recall is : %.4f" % recall)
f1_score = f1_score(rounded_labels, y_pred , average="macro")
print("The F1_score is : %.4f" % f1_score)

