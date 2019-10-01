import os
import numpy as np
import random
from sklearn.linear_model import LogisticRegression
from auxiliary import data_functions
import shutil
from datetime import datetime
import logging
from sklearn.preprocessing import normalize


logger = logging.getLogger(__name__)

SKLEARN_CLASSIFIERS = {'LogisticRegression': LogisticRegression}


class StemHistClassifier:

    def __init__(self, train_path, threshold=0.4):
        logger.debug(" <- init")

        self.train_path = train_path
        self.threshold = threshold
        self.train_list = self.load_train()
        self.model = None
        self.train_time = None
        self.save_path=None
        logger.debug(" -> init")

    def load_train(self):
        logger.debug(" <- load_train")
        logger.debug(f"loading train data from:{self.train_path}\ncreated from threshold {self.threshold}:")
        ret_list = []
        for label_folder in os.scandir(self.train_path):
            hist_folder = os.path.join(label_folder.path,"stem_data")
            hist_folder = os.path.join(hist_folder, f'thres_{self.threshold}')
            hist_folder = os.path.join(hist_folder, 'histograms')
            for hist_entry in os.scandir(hist_folder):
                ret_list.append((hist_entry, label_folder.name))

        random.shuffle(ret_list)
        logger.debug(" -> load_train")

        return ret_list

    def data_iterator(self):
        for item_entry,item_label in self.train_list:
            hist = np.load(item_entry.path)
            #hist =normalize(hist).flatten()
            hist = normalize(hist[0])
            yield hist, item_label

    def test_data_iterator(self):
        for item_entry in os.scandir(self.histograms_path):
            hist = np.load(item_entry.path)
            hist =normalize(hist).flatten().reshape(1,-1)
            yield item_entry.name, hist

    def train_model(self, model_name, **model_kwargs):
        logger.debug(" <- train_model")
        self.train_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        logger.info(f"model training time {self.train_time}")
        self.save_path = data_functions.create_path(self.test_path, self.train_time)
        data_functions.save_json(model_kwargs, f"{model_name}_input_params.json", self.save_path)
        model = SKLEARN_CLASSIFIERS[model_name](**model_kwargs)
        logger.debug(" starting model_fit")
        x_train, y_train = zip(*self.data_iterator())
        x_train = np.array(x_train)
        model.fit(x_train,y_train)
        self.model = model
        logger.debug(" -> train_model")

    def model_predict(self, orig_images_path,img_extention='.png.jpg'):
        self.test_path = os.path.join(test_path,f"thres_{threshold}")
        self.histograms_path = os.path.join(self.test_path,"hsv_histograms")
        logger.debug(" <- model_predict")
        for name, x in self.test_data_iterator():
            curr_name = name.split('.')[0]+img_extention
            curr_img_path = os.path.join(orig_images_path, curr_name)
            pred = self.model.predict(x)[0]

            save_path = data_functions.create_path(self.save_path, pred)
            _ = shutil.copy(curr_img_path, save_path)
        logger.debug(" -> model_predict")
