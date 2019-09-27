from auxiliary import data_functions
import os
import cv2
import numpy as np
from tqdm import tqdm
import shutil

import logging


logger = logging.getLogger(__name__)

from auxiliary.custom_image import CustomImage

OPENCV_METHODS = (
    ("Correlation", cv2.HISTCMP_CORREL),
    ("Chi-Squared", cv2.HISTCMP_CHISQR),
    ("Intersection", cv2.HISTCMP_INTERSECT),
    ("Hellinger", cv2.HISTCMP_BHATTACHARYYA))


class PredictionHolder:

    def __init__(self,img_name,img_path,predcition_path,threshold):
        self.img_name = img_name
        self.img_path = img_path
        self.predcition_path = predcition_path
        self.threshold = threshold

    def get_raw_pred(self):
        res = np.load(self.predcition_path)[..., np.newaxis]
        res = 255 * (res > self.threshold).astype(np.uint8)
        res = cv2.resize(res,self)


class StemExtractor:

    def __init__(self, img_path, mask_path, src_path, threshold=125):

        self.img_path = img_path
        self.mask_path = mask_path
        self.threshold = threshold

        self.save_path = data_functions.create_path(src_path,"stem_data")
        self.thres_save_path = data_functions.create_path(src_path, f"thres_{threshold}")

        self.threshold_masks_path = None

        self.sharp_masks_path = None
        self.cut_image_path = None


        self.groud_truth_hist_dict = None



    @staticmethod
    def get_clases_dict(classes_path):
        classes_dict = {}
        for img_entry in os.scandir(classes_path):
            img_color = cv2.imread(img_entry.path, cv2.IMREAD_COLOR)
            img_color = img_color[0, 0]
            class_name = img_entry.name.split('.')[0]
            classes_dict[class_name] = img_color
        return classes_dict


    def raw_mask_loader(self):
        for file_entry in os.scandir(self.mask_path):
            file_name,file_type = file_entry.name.rsplit(".",1)

            if file_type != 'npy':
                continue
            loaded_pred = np.load(file_entry.path,allow_pickle=True)
            orig_shape = loaded_pred[0]
            pred_raw = loaded_pred[1]

            res = 255 * (pred_raw > self.threshold).astype(np.uint8)
            res = cv2.resize(res,orig_shape)[...,np.newaxis]
            yield res, file_name


    def get_threshold_masks(self,save_type='jpg'):
        self.threshold_masks_path = data_functions.create_path(self.thres_save_path, f'binary')
        for image,image_name in tqdm(self.raw_mask_loader()):
            full_img_name=f'{image_name}.{save_type}'
            img_save_path = os.path.join(self.threshold_masks_path,full_img_name)
            cv2.imwrite(img_save_path, image)


    def get_stems(self,type_flag='orig'):
        if type_flag == 'orig':
            self.cut_image_path = data_functions.create_path(self.thres_save_path, f'orig_stems')
            for img in tqdm(self.image_obj_iterator()):
                img.cut_via_mask()
                cv2.imwrite(os.path.join(self.cut_image_path, img.image_name), img.image_cut)

        if type_flag == 'sharp':
            self.cut_image_path = data_functions.create_path(self.thres_save_path, f'sharp_stems')
            for img in tqdm(self.image_obj_iterator()):
                img.get_sharp_mask()
                img.cut_via_mask()
                cv2.imwrite(os.path.join(self.cut_image_path, img.image_name), img.grayscale_mask)


    def get_mean_h(self,type_flag='orig'):
        if type_flag == 'orig':
            self.mean_h_path = data_functions.create_path(self.thres_save_path, f'orig_mean_h')
            for img in tqdm(self.image_obj_iterator()):
                img.get_mean_hue()
                cv2.imwrite(os.path.join(self.mean_h_path, img.image_name), img.mask_mean_h)

        if type_flag == 'sharp':
            self.mean_h_path = data_functions.create_path(self.thres_save_path, f'sharp_mean_h')
            for img in tqdm(self.image_obj_iterator()):
                img.get_sharp_mask()
                img.get_mean_hue()
                cv2.imwrite(os.path.join(self.mean_h_path, img.image_name), img.mask_mean_h)

    def get_mean_color(self, type_flag='orig'):
        if type_flag == 'orig':
            self.mean_color_path = data_functions.create_path(self.thres_save_path, f'orig_mean_color')
            for img in tqdm(self.image_obj_iterator()):
                img.get_mean_color()
                cv2.imwrite(os.path.join(self.mean_color_path, img.image_name), img.mask_mean_color)

        if type_flag == 'sharp':
            self.mean_color_path = data_functions.create_path(self.thres_save_path, f'sharp_mean_color')
            for img in tqdm(self.image_obj_iterator()):
                img.get_sharp_mask()
                img.get_mean_color()
                cv2.imwrite(os.path.join(self.mean_color_path, img.image_name), img.mask_mean_color)



    def image_obj_iterator(self):
        for img_entry in os.scandir(self.img_path):
            mask_path = os.path.join(self.mask_path, img_entry.name)
            img = Image(img_entry.path, mask_path,threshold=self.threshold)
            yield img


    def calc_hists(self,mask_type='orig'):
        dest_path = data_functions.create_path(self.thres_save_path, f'hist_{mask_type}')
        for img in tqdm(self.image_obj_iterator()):
            img_raw_name = img.image_name.split('.')[0]
            curr_dest_path = os.path.join(dest_path,f"{img_raw_name}.npy")
            fig_big_hist, _ = img.get_hist_via_mask(return_hist=True, display_flag=False)
            np.save(curr_dest_path,fig_big_hist)

    def load_ground_truth(self,groud_truth_path):
        self.groud_truth_hist_dict=dict()
        for item_entry in os.scandir(groud_truth_path):
            self.groud_truth_hist_dict[item_entry.name]=np.load(item_entry.path)

    def compare_hists(self,mask_type='orig'):
        dest_path = data_functions.create_path(self.thres_save_path, f'hist_{mask_type}_scores')
        for img in tqdm(self.image_obj_iterator()):
            fig_big_hist, _ = img.get_hist_via_mask(return_hist=True, display_flag=False)
            label=self.get_hist_score(fig_big_hist)

            curr_dest_path = data_functions.create_path(dest_path,label)
            _ = shutil.copy(img.img_path, curr_dest_path)


    def get_hist_score(self,src_image_hist):
        final_res = []
        for method_name, method in OPENCV_METHODS:

            results = {}
            reverse = False

            if method_name in ("Correlation", "Intersection"):
                reverse = True

            for (image_name, hist) in  self.groud_truth_hist_dict.items():

                res = cv2.compareHist(src_image_hist, hist, method)
                results[image_name] = res

            # sort the results
            results = sorted(results.items(),key=lambda item:item[1], reverse = reverse)[0][0]
            final_res.append(results)

        most_common=max(set( final_res), key =  final_res.count)
        return most_common.split('.')[0]


    def score_results(self,score_type='heu',mask_type='orig'):

        #res_dict = dict()
        if score_type=='heu':
            src_path = self.mean_h_path
            dest_path = data_functions.create_path(self.thres_save_path,f'mean_h_{mask_type}_scores')
            curr_classes_dict = self.h_classes_dict
        elif score_type =='color':
            src_path = self.mean_color_path
            dest_path = data_functions.create_path(self.thres_save_path,f'mean_color_{mask_type}_scores')
            curr_classes_dict = self.color_classes_dict
        else:
            message = "wrong_flag_type"
            logger.info("wrong_flag_type")
            raise IOError(message)


        for img_class,_ in curr_classes_dict.items():
            data_functions.create_path(dest_path,img_class)

        for img_entry in os.scandir(src_path):

            img_color = cv2.imread(img_entry.path, cv2.IMREAD_COLOR)
            img_color = img_color[0, 0]
            res = data_functions.find_closest(img_color, curr_classes_dict)
            #res_dict[img_entry.name] = res
            curr_dest_path = os.path.join(dest_path,res)
            _ = shutil.copy(img_entry.path, curr_dest_path)







