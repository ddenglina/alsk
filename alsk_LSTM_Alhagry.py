PARTICIPANT_NUM = 3  # This is constant... this must not be changed
CROSS_VAL = 5  # This is constant... this must not be changed

from dataset.DEAP_DATASET import DEAP_DATASET
from tqdm.auto import trange
from torch.utils.data import DataLoader
import torch.optim as optimizer
import matplotlib.pyplot as plt

from models.lstm import EEGLSTM
from util.train import *
import numpy as np
import os

# Initialize CUDA Device
CUDA = True
gpu_id = '0'
batch_size = 8
device = torch.device("cuda:" + gpu_id if CUDA and torch.cuda.is_available() else "cpu")
print("[SYS] Using", device)
print("")

# MODEL_CONFIG
INPUT_SIZE = 32
HIDDEN_SIZE1 = 64
HIDDEN_SIZE2 = 32
OUTPUT_SIZE = 4

# PATH initialize
EXPORT_PATH_DIR = 'models/saved_weights/lstm/Alhagry_variant/'
mkdir(EXPORT_PATH_DIR)

# TRAINING_CONFIG
CRITERION = torch.nn.MSELoss()
LR = 1e-3
EPCH = 800

print("===========[INFO REPORT]===========")
print("Arch. [%d -> %d]" % (HIDDEN_SIZE1, HIDDEN_SIZE2))
print("<I> Using model config")
print("\tInput size :", INPUT_SIZE)
print("\tExport path :", EXPORT_PATH_DIR)
print("<I> Using training config")
print("\tBatch size :", batch_size)
print("\tLearning Rate :", LR)
print("\tEpochs :", EPCH)
print("\tOptimizer :", "Adam")

print("Please check config...")
input("\tPress ENTER to proceed.")

print("Starting training GRU model...")

# TRAINING VISUALIZE CONFIG
PLOT_EVERY = 500

DATA_SET_PATH = "./dataset"
train_dataset = DEAP_DATASET(DATA_SET_PATH, train=True, part_id=1, cross_val_id=1)
test_dataset = DEAP_DATASET(DATA_SET_PATH, train=False, part_id=1, cross_val_id=1)

train_MSE_Loss_buffer = []
test_MSE_Loss_buffer = []
for p in range(1, PARTICIPANT_NUM + 1):
    print("Participant:", p)
    train_dataset.set_participant_id(p - 1)
    test_dataset.set_participant_id(p - 1)
    for c in range(1, CROSS_VAL + 1):

        model = EEGLSTM(INPUT_SIZE, HIDDEN_SIZE1, HIDDEN_SIZE2, batch_size)
        model.to(device)
        optim = optimizer.Adam(model.parameters(), lr=LR)

        print("Cross val:", c)
        # Directory preparation
        EXPORT_PATH = EXPORT_PATH_DIR + "s" + str(p) + "/"
        EXPORT_PATH_FILE = EXPORT_PATH + "c" + str(c) + ".pth"
        mkdir(EXPORT_PATH)

        train_dataset.set_cross_id(c)
        test_dataset.set_cross_id(c)

        deap_train_loader = DataLoader(train_dataset, shuffle=True, batch_size=batch_size)
        deap_test_loader = DataLoader(test_dataset, shuffle=True, batch_size=batch_size)

        loss_hist = []
        val_loss_hist = []
        if False:
            pass
        else:
            for i in trange(EPCH, desc="Epoch"):

                avg_loss = train_lstm_gru(model, optim, CRITERION, deap_train_loader, device)
                loss_hist.append(avg_loss)
                val_loss = eval_lstm_gru(model, CRITERION, deap_test_loader, device, eval_size=99999)

                if not DBG:
                    export_or_not(val_loss, val_loss_hist, model, EXPORT_PATH_FILE)

                val_loss_hist.append(val_loss)
                # print(val_loss - avg_loss)
                if i % PLOT_EVERY == 0 or i == EPCH - 1:
                    plt.plot(loss_hist, label="Training loss")
                    plt.plot(val_loss_hist, label="Validation loss")
                    plt.title("On participant" + str(p) + "cross id" + str(c))
                    plt.legend()
                    plt.savefig("loss_Alhagry_" + str(p) + "_" + str(c) + ".png")
                    plt.show()

        # After finish training, load the best model
        print(">> Loading previous model from : " + EXPORT_PATH_FILE)
        model.load_state_dict(torch.load(EXPORT_PATH_FILE, map_location=device))
        model.to(device)
        train_loss = eval_lstm_gru(model, CRITERION, deap_train_loader, device, eval_size=99999)
        val_loss = eval_lstm_gru(model, CRITERION, deap_test_loader, device, eval_size=99999)

        train_MSE_Loss_buffer.append(train_loss)
        test_MSE_Loss_buffer.append(val_loss)

print("train_MSE_loss :", np.mean(train_MSE_Loss_buffer))
print("val_MSE_loss :", np.mean(test_MSE_Loss_buffer))
