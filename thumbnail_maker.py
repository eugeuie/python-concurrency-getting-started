# thumbnail_maker.py
import time
import os
import logging
from urllib.parse import urlparse
from urllib.request import urlretrieve
import threading

import PIL
from PIL import Image

FORMAT = '[%(threadName)s, %(asctime)s, %(levelname)s] %(message)s'
logging.basicConfig(filename='logfile.log', level=logging.DEBUG, format=FORMAT, force=True)

class ThumbnailMakerService(object):
    def __init__(self, home_dir='.'):
        self.home_dir = home_dir
        self.input_dir = self.home_dir + os.path.sep + 'incoming'
        self.output_dir = self.home_dir + os.path.sep + 'outgoing'

    def download_image(self, url):
        # download each image and save to the input dir
        logging.info('downloading image at URl ' + url)
        img_filename = urlparse(url).path.split('/')[-1]
        urlretrieve(url, self.input_dir + os.path.sep + img_filename)
        logging.info('image saved to ' + self.input_dir + os.path.sep + img_filename)

    # IO-bound method
    def download_images(self, img_url_list):
        # validate inputs
        if not img_url_list:
            return
        os.makedirs(self.input_dir, exist_ok=True)
        
        logging.info("beginning image downloads")

        start = time.perf_counter()
        threads = []
        for url in img_url_list:
            t = threading.Thread(target=self.download_image, args=(url,))
            t.start()
            # Calling t.join() here will be a mistake, because what would happen is that in a loop, the main thread will create a new thread, start it, and then wait it to complete before continuing the loop, this isn't what we want. What we want is to create the worker threads, and then wait for all of them to complete. So to accomplish that, we'll create a list that will hold references to the thread objects and then every time we create a thread in the loop, we'll add it to the list.
            threads.append(t)
        # Then after all the threads are started, we'll going to loop through our thread list and call join on each of the threads, so the main thread is forced to wait for all the threads to complete before continuing.
        for t in threads:
            t.join()
        end = time.perf_counter()

        logging.info("downloaded {} images in {} seconds".format(len(img_url_list), end - start))

    # CPU-bound method
    def perform_resizing(self):
        # validate inputs
        if not os.listdir(self.input_dir):
            return
        os.makedirs(self.output_dir, exist_ok=True)

        logging.info("beginning image resizing")
        target_sizes = [32, 64, 200]
        num_images = len(os.listdir(self.input_dir))

        start = time.perf_counter()
        for filename in os.listdir(self.input_dir):
            orig_img = Image.open(self.input_dir + os.path.sep + filename)
            for basewidth in target_sizes:
                img = orig_img
                # calculate target height of the resized image to maintain the aspect ratio
                wpercent = (basewidth / float(img.size[0]))
                hsize = int((float(img.size[1]) * float(wpercent)))
                # perform resizing
                img = img.resize((basewidth, hsize), PIL.Image.LANCZOS)
                
                # save the resized image to the output dir with a modified file name 
                new_filename = os.path.splitext(filename)[0] + \
                    '_' + str(basewidth) + os.path.splitext(filename)[1]
                img.save(self.output_dir + os.path.sep + new_filename)

            os.remove(self.input_dir + os.path.sep + filename)
        end = time.perf_counter()

        logging.info("created {} thumbnails in {} seconds".format(num_images, end - start))

    def make_thumbnails(self, img_url_list):
        logging.info("START make_thumbnails")
        start = time.perf_counter()

        self.download_images(img_url_list)
        # self.perform_resizing()

        end = time.perf_counter()
        logging.info("END make_thumbnails in {} seconds".format(end - start))
    