# -*- coding: utf-8 -*-
"""AlexNet.ipynb

Automatically generated by Colaboratory.

## Modules
"""

!pip3 install 'torch'
!pip3 install 'torchvision'
!pip3 install 'Pillow-SIMD'
!pip3 install 'tqdm'
!pip3 install 'dropbox'

"""## Imports"""

import os
import sys
import logging

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Subset, DataLoader
from torch.backends import cudnn

import torchvision
from torchvision import transforms
from torchvision.models import alexnet

from PIL import Image
from tqdm import tqdm

import numpy as np
import matplotlib.pyplot as plt
import copy
import dropbox
import zipfile
import shutil

import random
import datetime

from google.colab import drive

"""## General Constants"""

# Path where the zipped dropbox repo is downloaded
DRONUTS_ZIP_PATH = "./dronuts.zip"

# Path where the unzipped dropbox repository is saved
DRONUTS_PATH = "./DRONUTS"

# Path of root for download on dropbox side
DRONUTS_DROPBOX_PATH = "/dronuts"

# Path of generated dataset
DATASET_PATH = "./dataset"

# Prefix for distinguish useful dataset images
IMAGE_PREFIX = "DJI_"

# Particular path where remove all images, excluding metadata file
IMAGES_TO_REMOVE_PATH = "./DRONUTS/Dogliani_C001/2021-05-27"

# Data for configuring machine learning algorithms
# Number of classes of dataset
NUM_CLASSES = 2
# Device on which the algorithms are trained and tested
DEVICE = 'cuda'
# Fixed hyperparameters for NN stochastic gradient
MOMENTUM = 0.9
GAMMA = 0.1

"""## Define drive for save output files

In order to allow the mounting, in the output console is necessary to follow the istructions that permits to insert an authentication token.

The mounting give not permission for create directory. For that reason the OUTPUT_FILE_DIRECTORY has to be created before on own drive.
"""

OUTPUT_FILE_DIRECTORY = "./gdrive/MyDrive/ColabOutput/Tesi"

if not os.path.isdir(OUTPUT_FILE_DIRECTORY):
  drive.mount('/content/gdrive')

"""## Import dropbox folder

In the following part the dropbox repository is downloaded and unpacked, in order to extract the images useful for the dataset.
After unpack, the zipped file is removed.
"""

def unpack():
  with zipfile.ZipFile(DRONUTS_ZIP_PATH, 'r') as zip_ref:
    zip_ref.extractall(".")

if not os.path.isfile(DRONUTS_ZIP_PATH) and not os.path.isdir(DRONUTS_PATH):
  dbx = dropbox.Dropbox() # Insert as parameter the dropbox app token
  dbx.files_download_zip_to_file(DRONUTS_ZIP_PATH, DRONUTS_DROPBOX_PATH)

if os.path.isfile(DRONUTS_ZIP_PATH) and not os.path.isdir(DRONUTS_PATH):
  unpack()
  os.remove(DRONUTS_ZIP_PATH)

"""In IMAGES_TO_REMOVE_PATH are removed all the files, excluding *dettagli_immagini.txt* useful for metadata. Custom logic for remove uncut images, not suitable for dataset."""

if os.path.isdir(IMAGES_TO_REMOVE_PATH):
  for file in os.listdir(IMAGES_TO_REMOVE_PATH):
    file_path = f'{IMAGES_TO_REMOVE_PATH}/{file}'
    if os.path.isfile(file_path) and file != "dettagli_immagini.txt":
      os.remove(file_path)

"""## Define dataset directory"""

# In case of error in the next section, permits to remove all directory in order to rerun it
# shutil.rmtree(DATASET_PATH)
# shutil.rmtree(DRONUTS_PATH)

def find_file_descriptor(actual_path: str):
  for file_path in dettagli_immagini_by_path.keys():
    if actual_path.__contains__(file_path):
      return dettagli_immagini_by_path[file_path]

def define_class_from_labels(label_fisio: str, label_pato: str):
  return str(int(label_fisio) | int(label_pato))

def get_label(original_image_name: str, dir_name: str):
  lines = find_file_descriptor(dir_name)["lines"]
  label_fisio_index = lines[0].lower().split('\t').index("label_fisio_(sano-0/malato-1)")
  label_pato_index = lines[0].lower().split('\t').index("label_pato_(sano-0/malato-1)")
  name_index = lines[0].lower().split('\t').index("nome_immagine")
  for line in lines:
    splitted_line = line.split('\t')
    if splitted_line[name_index] == original_image_name:
       return define_class_from_labels(splitted_line[label_fisio_index], splitted_line[label_pato_index])

def set_label(label: str, image_name: str):
  if image_name not in labels_by_image_name:
    labels_by_image_name[image_name] = []
  labels_by_image_name[image_name].append(label)

def get_extension(file_name: str):
  return file_name[file_name.find('.') + 1:]

def get_label_info(file: str, dir_name: str):
  fd = open(f'{dir_name}/{file}', 'r')
  dettagli_immagini_by_path[dir_name] = {
      "lines": fd.readlines(),
      "file_path": f'{dir_name}/{file}'
  }
  fd.close()

def manage_copy_for_dataset(file: str, dirpath: str, label: str):
  base_dest_path = f'{DATASET_PATH}/{label}'
  if not os.path.isdir(base_dest_path):
    os.mkdir(base_dest_path)
  
  source_path = f'{dirpath}/{file}'
  dest_file = file
  dest_path = f'{base_dest_path}/{file}'
  while os.path.isfile(dest_path):
    dest_path = dest_path.replace(".jpg", "_c.jpg")
    dest_path = dest_path.replace(".JPG", "_c.JPG")
    dest_file = dest_file.replace(".jpg", "_c.jpg")
    dest_file = dest_file.replace(".JPG", "_c.JPG")
  shutil.copy(source_path, dest_path)
  return dest_file

"""Generate the dataset from the unzipped dropbox repository. 
At beginning remove possible wrong dataset directory.
After navigates the unzipped dropbox repository in order to extract for each image the right label, taken from metadata file *dettagli_immagini.txt*, in order to create for each possible label a directory in DATASET_PATH.
The images put in dataset are filtered by extension (jpg) and prefix (IMAGE_PREFIX).
"""

dettagli_immagini_by_path = {}; labels_by_image_name = {}

if os.path.isdir(DATASET_PATH):
  shutil.rmtree(DATASET_PATH)

os.mkdir(DATASET_PATH)
for dir_path, _, files in os.walk(DRONUTS_PATH):
  if "dettagli_immagini.txt" in files:
    get_label_info("dettagli_immagini.txt", dir_path)
  for file in files:
    if get_extension(file).lower() == "jpg" and file.startswith(IMAGE_PREFIX):
      label = get_label(file, dir_path)
      new_file_name = manage_copy_for_dataset(file, dir_path, label)
      set_label(label, new_file_name)

print(labels_by_image_name)

# to check number of files
for dir_path, _, files in os.walk(DATASET_PATH):
  if len(files) > 0:
    print(f'{dir_path}: {str(len(files))}')

"""## Base functions"""

def get_base_datasets():
  # Transformation in order to use the NN with pretrained weights
  normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
  compose = transforms.Compose([transforms.Resize((1300, 1600)), transforms.ToTensor(), normalize])

  all_dataset = torchvision.datasets.ImageFolder(DATASET_PATH, transform=compose)
  return get_subsets(all_dataset, 5)

def get_subsets(base_set: torchvision.datasets.ImageFolder, splitting_ratio: int):
  s1_indexes = [idx for idx in range(len(base_set)) if idx % splitting_ratio]
  s2_indexes = [idx for idx in range(len(base_set)) if not idx % splitting_ratio]
  s1_set = Subset(base_set, s1_indexes)
  s2_set = Subset(base_set, s2_indexes)

  return s1_set, s2_set

def calculate_matrix_metrics(actual_labels, predictions, true_positive, true_negative, false_positive, false_negative):
  for index, prediction in enumerate(predictions):
    if actual_labels[index] == 1 and prediction == 1:
      true_positive += 1
    elif actual_labels[index] == 1 and prediction == 0:
      false_negative += 1
    elif actual_labels[index] == 0 and prediction == 1:
      false_positive += 1
    elif actual_labels[index] == 0 and prediction == 0:
      true_negative += 1

  return true_positive, true_negative, false_positive, false_negative

def test_log(ta, tl, ttp, ttn, tfp, tfn, output_file=sys.stdout):
  print(f"""test_accuracy: {test_accuracy}, test_loss: {test_loss},
            test_true_positive {test_true_positive}, 
            test_true_negative: {test_true_negative}, 
            test_false_positive: {test_false_positive},
            test_false_negative: {test_false_negative}""", 
        file=output_file)

def train_val_log(ta, tl, ttp, ttn, tfp, tfn, va, vl, vtp, vtn, vfp, vfn, epoch, tot_epochs, output_file=sys.stdout):
  print(f"""train_accuracy: {ta}, train_loss: {tl}, train_true_positive: {ttp}, 
            train_true_negative: {ttn}, train_false_positive: {tfp}, 
            train_false_negative : {tfn}, val_acc: {va}, val_loss: {vl},
            val_true_positive: {vtp}, val_true_negative: {vtn},
            val_false_positive: {vfp}, val_false_negative: {vfn}
            ({epoch} / {tot_epochs})""", file=output_file)
  
def train_log(ta, tl, ttp, ttn, tfp, tfn, epoch, tot_epochs, output_file=sys.stdout):
    print(f"""train_acc: {ta}, train_loss: {tl}, train_true_positive: {ttp},
              train_true_negative: {ttn}, train_false_positive: {tfp},
              train_false_negative : {tfn}, ({epoch} / {tot_epochs})""", file=output_file)

PLOT_COLORS = ["orangered", "limegreen", "lightseagreen", "navy", "gold", "magenta"]

def plot_multiple_line_graphic(data_arrays, labels, output_file=None):
    fig, ax = plt.subplots()
    for index, data_array in enumerate(data_arrays):
      ax.plot(data_array, label=labels[index], color=PLOT_COLORS[index % len(PLOT_COLORS)])
    ax.legend()
    plt.xlabel("Epochs")
    
    file_name = f"{datetime.datetime.now()}.jpg"
    plt.savefig(f"{OUTPUT_FILE_DIRECTORY}/{file_name}")
    print(file_name)
    if output_file is not None:
      print(file_name, file=output_file)
    
    plt.show()

def train_network(net, parameters_to_optimize, learning_rate, num_epochs, 
                  batch_size, weight_decay, step_size, gamma, train_dataset, 
                  val_dataset=None, verbosity=False, plot=False, output_file=None):
  
    train_dataloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, drop_last=False)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(parameters_to_optimize, lr=learning_rate, momentum=MOMENTUM, weight_decay=weight_decay)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=step_size, gamma=gamma)

    net = net.to(DEVICE)
    best_net = alexnet(pretrained=True)
    best_net.classifier[6] = nn.Linear(4096, NUM_CLASSES)

    train_accuracies = []; train_losses = []; train_true_positives = []; train_true_negatives = [] 
    train_false_positives = []; train_false_negatives = []
    val_accuracies = []; val_losses = []; val_true_positives = []; val_true_negatives = []
    val_false_positives = []; val_false_negatives = []

    best_val_accuracy = best_val_loss = 0.0
    best_val_true_positive = best_val_true_negative = best_val_false_positive = 0
    best_val_false_negative = 0

    current_step = 0

    for epoch in tqdm(range(num_epochs), "Epochs"):

        train_running_corrects = train_true_positive = train_false_negative = 0
        train_false_positive = train_true_negative = 0
        sum_train_losses = 0.0

        for images, labels in tqdm(train_dataloader, f"Train dataLoader of epoch {epoch+1}"):
            images = images.to(DEVICE)
            labels = labels.to(DEVICE)
            net.train()
            optimizer.zero_grad()

            outputs = net(images)
            _, preds = torch.max(outputs.data, 1)
            train_true_positive, train_true_negative, train_false_positive, train_false_negative = \
              calculate_matrix_metrics(labels.data, 
                                        preds, 
                                        train_true_positive, 
                                        train_true_negative, 
                                        train_false_positive, 
                                        train_false_negative)
            train_running_corrects += torch.sum(preds == labels.data).data.item()
            loss = criterion(outputs, labels)
            sum_train_losses += loss.item()*images.size(0)
            
            loss.backward()
            optimizer.step()
            current_step += 1
            torch.cuda.empty_cache()
        
        torch.cuda.empty_cache()

        if val_dataset is not None:
            val_accuracy, val_loss, val_true_positive, val_true_negative, val_false_positive, val_false_negative = \
              test_network(net, val_dataset, TEST_BATCH_SIZE)
            if val_accuracy > best_val_accuracy:
                best_val_accuracy = val_accuracy
                best_val_loss = val_loss
                best_val_true_positive = val_true_positive 
                best_val_true_negative = val_true_negative
                best_val_false_positive = val_false_positive
                best_val_false_negative = val_false_negative
                best_net.load_state_dict(net.state_dict())
            val_accuracies.append(val_accuracy)
            val_losses.append(val_loss)
            val_true_positives.append(val_true_positive)
            val_true_negatives.append(val_true_negative)
            val_false_positives.append(val_false_positive)
            val_false_negatives.append(val_false_negative)

        # Calculate accuracy on train set
        train_accuracy = train_running_corrects / float(len(train_dataset))
        train_accuracies.append(train_accuracy)

        # Calculate loss on training set
        train_loss = sum_train_losses/float(len(train_dataset))
        
        train_losses.append(loss)
        train_true_positives.append(train_true_positive) 
        train_true_negatives.append(train_true_negative) 
        train_false_positives.append(train_false_positive) 
        train_false_negatives.append(train_false_negative)

        if verbosity:
            if val_dataset is not None:
              train_val_log(train_accuracy, train_loss, train_true_positive, 
                            train_true_negative, train_false_positive, 
                            train_false_negative, val_accuracy, val_loss, 
                            val_true_positive, val_true_negative, val_false_positive, 
                            val_false_negative, epoch + 1, num_epochs)
              if output_file is not None:
                train_val_log(train_accuracy, train_loss, train_true_positive, 
                              train_true_negative, train_false_positive, 
                              train_false_negative, val_accuracy, val_loss, 
                              val_true_positive, val_true_negative, val_false_positive, 
                              val_false_negative, epoch + 1, num_epochs, output_file)
            else:
              train_log(train_accuracy, train_loss, train_true_positive, 
                        train_true_negative, train_false_positive, 
                        train_false_negative, epoch + 1, num_epochs)
              if output_file is not None:
                train_log(train_accuracy, train_loss, train_true_positive, 
                          train_true_negative, train_false_positive, 
                          train_false_negative, epoch + 1, num_epochs, output_file)

        scheduler.step()
        torch.cuda.empty_cache()

    if plot:
      plot_multiple_line_graphic([train_losses, train_accuracies], 
                                 ["Loss on training set", "Accuracy on training set"],
                                 output_file)

      plot_data = [train_accuracies]
      plot_labels = ["Accuracy on training set"]

      if val_dataset is not None:
        plot_multiple_line_graphic([val_losses, train_losses], 
                                   ["Loss on validation set", "Loss on training set"],
                                   output_file)
        plot_multiple_line_graphic([val_true_positives, val_true_negatives, val_false_positives, val_false_negatives],
                                   ["Validation true positives", "Validation true negatives", "Validation false positives", "Validation false negatives"],
                                   output_file)
        plot_data.append(val_accuracies)
        plot_labels.append("Accuracy on validation set")

      plot_multiple_line_graphic(plot_data, plot_labels, output_file)
      plot_multiple_line_graphic([train_true_positives, train_true_negatives, train_false_positives, train_false_negatives],
                                 ["Training true positives", "Training true negatives", "Training false positives", "Traning false negatives"],
                                 output_file)

    if val_dataset is None:
      best_net.load_state_dict(net.state_dict())

    return best_net, best_val_accuracy, best_val_loss, best_val_true_positive, best_val_true_negative, best_val_false_positive, best_val_false_negative

def test_network(net, test_dataset, batch_size):
    test_dataloader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    net.train(False)

    criterion = nn.CrossEntropyLoss()

    sum_test_losses = 0.0
    running_corrects = true_positive = false_negative = false_positive = true_negative = 0

    for images, labels in tqdm(test_dataloader, f"Test dataLoader"):
      images = images.to(DEVICE)
      labels = labels.to(DEVICE)

      # Forward Pass
      outputs = net(images)

      # Get predictions
      _, preds = torch.max(outputs.data, 1)
      test_loss = criterion(outputs, labels)
      sum_test_losses += test_loss.item()*images.size(0)

      # Update metrics
      running_corrects += torch.sum(preds == labels.data).data.item()
      true_positive, true_negative, false_positive, false_negative = \
        calculate_matrix_metrics(labels.data,
                                  preds,
                                  true_positive, 
                                  true_negative,
                                  false_positive,
                                  false_negative)

      torch.cuda.empty_cache()

    # Calculate Accuracy
    accuracy = running_corrects / float(len(test_dataset))

    # Calculate loss
    test_loss = sum_test_losses / float(len(test_dataset))

    torch.cuda.empty_cache()

    return accuracy, test_loss, true_positive, true_negative, false_positive, false_negative

"""## Random search

### Constants
"""

TENTATIVE_NUMBERS = 1
BATCH_SIZE = 2
TEST_BATCH_SIZE = 1
EPOCHS_NUMBER = 2

"""### Dataset extraction"""

train_and_val_dataset, test_dataset = get_base_datasets()

print('training & validation set {}'.format(len(train_and_val_dataset)))
print('test set {}'.format(len(test_dataset)))

train_dataset, val_dataset = get_subsets(train_and_val_dataset, 5)

print('training set {}'.format(len(train_dataset)))
print('validation set {}'.format(len(val_dataset)))

"""### Execution"""

def single_iteration_log(iteration, lr, wd, gamma, va, vl, vtp, vtn, vfp, vfn, output_file=sys.stdout):
  print(f"Tentative {iteration}: lr {lr}, decay {wd}, gamma {gamma}", file=output_file)
  print(f"""val_accuracy: {va}, val_loss: {vl}, val_true_positive: {vtp},
            val_true_negative: {vtn}, val_false_positive: {vfp}, 
            val_false_negative: {vfn} [{iteration} / {TENTATIVE_NUMBERS}]""", 
        file=output_file)
  
def final_log(bs, ba, bl, btp, btn, bfp, bfn, vas, vls, vtps, vtns, vfps, vfns, output_file=sys.stdout):
  print(f"""{bs}, best_val_accuracy: {ba}, best_val_loss: {bl}, best_true_positives: {btp}, 
            best_true_negatives: {btn}, best_false_positives: {bfp}, best_false_negatives: {bfn}""", 
        file=output_file)
  print(f"val_accuracies: {val_accuracies}", file=output_file)
  print(f"val_losses: {val_losses}", file=output_file)
  print(f"val_true_positives: {val_true_positives}", file=output_file)
  print(f"val_true_negatives: {val_true_negatives}", file=output_file)
  print(f"val_false_positives: {val_false_positives}", file=output_file)
  print(f"val_false_negatives: {val_false_negatives}", file=output_file)

best_accuracy = best_loss = 0.0
best_set = {}
best_true_positives = best_true_negatives = best_false_positives = best_false_negatives = 0

val_accuracies = []; val_losses = []; val_true_positives = []; val_true_negatives = []
val_false_positives = []; val_false_negatives = []

torch.cuda.empty_cache()

with open(f"{OUTPUT_FILE_DIRECTORY}/{datetime.datetime.now()}-output.txt", "w") as f:
  for i in tqdm(range(TENTATIVE_NUMBERS), "Random search tentatives"):
    lr = random.uniform(0.0001, 0.0005)
    weight_decay = random.uniform(0.0002, 0.0008)
    gamma = 10**random.uniform(-2, 0)
    actual_set = {"lr": lr, "weight_decay": weight_decay, "gamma": gamma}

    net = alexnet(pretrained=True)
    net.classifier[6] = nn.Linear(4096, NUM_CLASSES)
    _, val_accuracy, val_loss, val_true_positive, val_true_negative, val_false_positive, val_false_negative = \
      train_network(net, net.parameters(), 
                    lr, EPOCHS_NUMBER, 
                    BATCH_SIZE, weight_decay, 
                    STEP_SIZE, gamma, 
                    train_dataset, 
                    val_dataset=val_dataset, 
                    verbosity=True,
                    output_file=f,
                    plot=True)
    val_accuracies.append(val_accuracy)
    val_losses.append(val_loss)
    val_true_positives.append(val_true_positive)
    val_true_negatives.append(val_true_negative) 
    val_false_positives.append(val_false_positive) 
    val_false_negatives.append(val_false_negative)

    if val_accuracy > best_accuracy:
      best_accuracy = val_accuracy
      best_loss = val_loss
      best_true_positives = val_true_positive
      best_true_negatives = val_true_negative
      best_false_positives = val_false_positive
      best_false_negatives = val_false_negative
      best_set = copy.deepcopy(actual_set)
    
    single_iteration_log(i+1, lr, weight_decay, gamma, val_accuracy, val_loss, 
                         val_true_positive, val_true_negative, val_false_positive, 
                         val_false_negative, f)
    
    single_iteration_log(i+1, lr, weight_decay, gamma, val_accuracy, val_loss, 
                      val_true_positive, val_true_negative, val_false_positive, 
                      val_false_negative)
    
  final_log(best_set, best_accuracy, best_loss, best_true_positives, 
            best_true_negatives, best_false_positives, best_false_negatives,
            val_accuracies, val_losses, val_true_positives, val_true_negatives, 
            val_false_positives, val_false_negatives, f)
  
  final_log(best_set, best_accuracy, best_loss, best_true_positives, 
          best_true_negatives, best_false_positives, best_false_negatives,
          val_accuracies, val_losses, val_true_positives, val_true_negatives, 
          val_false_positives, val_false_negatives)

"""##Specific run

### Constants
"""

BATCH_SIZE = 2
TEST_BATCH_SIZE = 1
NUM_EPOCHS = 2

LR = 0.00034017498684741146
WEIGHT_DECAY = 0.00023276171907154138
GAMMA = 0.09288936004816421

"""### Dataset extraction"""

train_and_val_dataset, test_dataset = get_base_datasets()

print('training & validation set {}'.format(len(train_and_val_dataset)))
print('test set {}'.format(len(test_dataset)))

train_dataset, val_dataset = get_subsets(train_and_val_dataset, 5)

print('training set {}'.format(len(train_dataset)))
print('validation set {}'.format(len(val_dataset)))

"""### Execution"""

def final_log(bva, bvl, bvtp, bvtn, bvfp, bvfn, output_file=sys.stdout):
  print(f"""best_val_accuracy: {bva}, best_val_loss: {bvl},
            best_val_true_positive: {bvtp}, best_val_true_negative: {bvtn},
            best_val_false_positive: {bvfp}, best_val_false_negative: {bvfn}""",
        file=output_file)

net = alexnet(pretrained=True)
net.classifier[6] = nn.Linear(4096, NUM_CLASSES)
torch.cuda.empty_cache()

with open(f"{OUTPUT_FILE_DIRECTORY}/{datetime.datetime.now()}-output.txt", "w") as f:
  best_val_net, best_val_accuracy, best_val_loss, best_val_true_positive, best_val_true_negative, best_val_false_positive, best_val_false_negative = \
    train_network(net, net.parameters(), 
                  LR, NUM_EPOCHS, 
                  BATCH_SIZE, WEIGHT_DECAY, 
                  STEP_SIZE, GAMMA, 
                  train_dataset, 
                  val_dataset=val_dataset, 
                  verbosity=True, plot=True,
                  output_file=f)

  final_log(best_val_accuracy, best_val_loss, best_val_true_positive,
            best_val_true_negative, best_val_false_positive, best_val_false_negative)
  
  final_log(best_val_accuracy, best_val_loss, best_val_true_positive,
            best_val_true_negative, best_val_false_positive, 
            best_val_false_negative, f)

"""## Grid search

### Constants
"""

NUM_EPOCHS = 50
BATCH_SIZE = 2
TEST_BATCH_SIZE = 2

"""### Parameter ranges"""

lr_range = [1e-5]
weight_decay_range = [0, 1e-3, 1e-4, 1e-5]
step_size_range = [15, 20, 35]

"""### Dataset extraction"""

train_and_val_dataset, test_dataset = get_base_datasets()

print('training & validation set {}'.format(len(train_and_val_dataset)))
print('test set {}'.format(len(test_dataset)))

train_dataset, val_dataset = get_subsets(train_and_val_dataset, 5)

print('training set {}'.format(len(train_dataset)))
print('validation set {}'.format(len(val_dataset)))

"""### Execution"""

def single_iteration_log(set_, va, vl, vtp, vtn, vfp, vfn, output_file=sys.stdout):
  print(f"""({set_}): val_accuracy: {va}, val_loss: {vl}, val_true_positive: {vtp},
            val_true_negative: {vtn}, val_false_positive: {vfp}, 
            val_false_negative: {vfn}""", 
        file=output_file)
  
def final_log(best_set, ba, bl, btp, btn, bfp, bfn, all_sets, vas, vls, vtps, vtns, vfps, vfns, output_file=sys.stdout):
  print(f"""({best_set}): best_val_accuracy: {ba}, best_val_loss: {bl}, best_true_positives: {btp}, 
            best_true_negatives: {btn}, best_false_positives: {bfp}, best_false_negatives: {bfn}""", 
        file=output_file)
  print(f"all_sets: {all_sets}", file=output_file)
  print(f"val_accuracies: {val_accuracies}", file=output_file)
  print(f"val_losses: {val_losses}", file=output_file)
  print(f"val_true_positives: {val_true_positives}", file=output_file)
  print(f"val_true_negatives: {val_true_negatives}", file=output_file)
  print(f"val_false_positives: {val_false_positives}", file=output_file)
  print(f"val_false_negatives: {val_false_negatives}", file=output_file)

def plot_heatmap(data_arrays, xaxes_values, yaxes_values, output_file=None):
  fig, ax = plt.subplots()
  im = ax.imshow(data_arrays)

  plt.colorbar(im)
  ax.set_xticks(np.arange(len(xaxes_values)))
  ax.set_yticks(np.arange(len(yaxes_values)))
  ax.set_xticklabels([str(x) for x in xaxes_values])
  ax.set_yticklabels([str(y) for y in yaxes_values])
  
  for i in range(len(xaxes_values)):
    for j in range(len(yaxes_values)):
        text = ax.text(i, j, data_arrays[j, i], ha="center", va="center", color="w")

  file_name = f"{datetime.datetime.now()}.jpg"
  plt.savefig(f"{OUTPUT_FILE_DIRECTORY}/{file_name}")
  print(file_name)
  if output_file is not None:
    print(file_name, file=output_file)

  plt.show()

hyperparameters_sets = []

for lr in lr_range:
    for weight_decay in weight_decay_range:
      for step_size in step_size_range:
        set_ = {'lr': lr, 'weight_decay': weight_decay, 'step_size': step_size}
        hyperparameters_sets.append(set_)
        
print(hyperparameters_sets)

best_accuracy = best_loss = 0.0
best_set = {}
best_true_positives = best_true_negatives = best_false_positives = best_false_negatives = 0

val_accuracies = []; val_losses = []; val_true_positives = []; val_true_negatives = []
val_false_positives = []; val_false_negatives = []

with open(f"{OUTPUT_FILE_DIRECTORY}/{datetime.datetime.now()}-output.txt", "w") as f:
  for set_ in hyperparameters_sets:
    net = alexnet(pretrained=True)
    net.classifier[6] = nn.Linear(4096, NUM_CLASSES)
    torch.cuda.empty_cache()

    _, val_accuracy, val_loss, val_true_positive, val_true_negative, val_false_positive, val_false_negative = \
      train_network(net, net.parameters(), 
                    set_['lr'], NUM_EPOCHS, 
                    BATCH_SIZE, set_['weight_decay'], 
                    set_['step_size'], GAMMA, 
                    train_dataset, 
                    val_dataset=val_dataset, 
                    verbosity=True, plot=True,
                    output_file=f)
      
    val_accuracies.append(val_accuracy)
    val_losses.append(val_loss)
    val_true_positives.append(val_true_positive)
    val_true_negatives.append(val_true_negative) 
    val_false_positives.append(val_false_positive) 
    val_false_negatives.append(val_false_negative)

    if val_accuracy > best_accuracy:
      best_accuracy = val_accuracy
      best_loss = val_loss
      best_true_positives = val_true_positive
      best_true_negatives = val_true_negative
      best_false_positives = val_false_positive
      best_false_negatives = val_false_negative
      best_set = copy.deepcopy(set_)
    
    single_iteration_log(set_, val_accuracy, val_loss, 
                         val_true_positive, val_true_negative, val_false_positive, 
                         val_false_negative, f)
    
    single_iteration_log(set_, val_accuracy, val_loss, 
                         val_true_positive, val_true_negative, val_false_positive, 
                         val_false_negative)
    
    f.flush()
    
  final_log(best_set, best_accuracy, best_loss, best_true_positives, 
            best_true_negatives, best_false_positives, best_false_negatives,
            hyperparameters_sets, val_accuracies, val_losses, val_true_positives, 
            val_true_negatives, val_false_positives, val_false_negatives, f)
  
  final_log(best_set, best_accuracy, best_loss, best_true_positives, 
            best_true_negatives, best_false_positives, best_false_negatives,
            hyperparameters_sets, val_accuracies, val_losses, val_true_positives, 
            val_true_negatives, val_false_positives, val_false_negatives)
  
  for step_size in step_size_range:
    indexes_per_lr_value = np.empty([len(lr_range), len(weight_decay_range)], dtype=int)
    for index, set_ in enumerate(hyperparameters_sets): 
      if set_['step_size'] == step_size:
        lr_index = [lr_idx for lr_idx, lr in enumerate(lr_range) if lr == set_['lr']][0]
        wd_index = [wd_idx for wd_idx, wd in enumerate(weight_decay_range) if wd == set_['weight_decay']][0]
        indexes_per_lr_value[lr_index][wd_index] = index

    np_val_accuracies = np.array([round(va, 2) for va in val_accuracies])
    val_accuracies_heatmap = np.empty([len(lr_range), len(weight_decay_range)])
    for idx, indexes in enumerate(indexes_per_lr_value):
      val_accuracies_heatmap[idx] = np_val_accuracies[indexes]
  
  plot_heatmap(val_accuracies_heatmap, lr_range, weight_decay_range, f)

"""##Specific run for testing

### Constants
"""

BATCH_SIZE = 2
TEST_BATCH_SIZE = 1
EPOCHS_NUMBER = 2

LR = 0.00034017498684741146
WEIGHT_DECAY = 0.00023276171907154138
GAMMA = 0.09288936004816421

"""### Dataset extraction"""

train_dataset, test_dataset = get_base_datasets()

print('training set {}'.format(len(train_dataset)))
print('test set {}'.format(len(test_dataset)))

"""### Execution"""

net = alexnet(pretrained=True)
net.classifier[6] = nn.Linear(4096, NUM_CLASSES)
torch.cuda.empty_cache()

with open(f"{OUTPUT_FILE_DIRECTORY}/{datetime.datetime.now()}-output.txt", "w") as f:
  best_net, _, _, _, _, _, _ = train_network(net, net.parameters(), 
                                  LR, EPOCHS_NUMBER,
                                  BATCH_SIZE, WEIGHT_DECAY, 
                                  STEP_SIZE, GAMMA,
                                  train_dataset,
                                  verbosity=True, plot=True,
                                  output_file=f)
  
  torch.cuda.empty_cache()
  best_net.to(DEVICE)
  test_accuracy, test_loss, test_true_positive, test_true_negative, test_false_positive, test_false_negative = \
    test_network(best_net, test_dataset, TEST_BATCH_SIZE)

  test_log(test_accuracy, test_loss, test_true_positive, test_true_negative,
           test_false_positive, test_false_negative, f)
  
  test_log(test_accuracy, test_loss, test_true_positive, test_true_negative,
          test_false_positive, test_false_negative)

"""## Flush mounted drive"""

drive.flush_and_unmount()