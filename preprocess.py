from glob import glob
import pickle
from PIL import Image
import numpy as np
from tqdm import tqdm
import time
from omp import OMP, encode_image, extract_columns
import os
import logging
from utils import generate_population, count_frequency, filter_by_freq, fitness, nextPopulation
from utils import remove_substrings, find_non_overlapping_strings
from graph_utils import get_nodes, merge_nodes

Image.MAX_IMAGE_PIXELS = 1616040000
# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Processor:
    def __init__(self, config):
        self.config = config
        self.design = self.config['design']
        self.node_tech = self.config['node']
        self.increment = self.config['increment']
        self.start_time = time.time()
        self.dataDir = os.path.join(*[self.config['dataRoot'], f'strip_{self.design}_{self.node_tech}'])
        self.encodingDir = os.path.join(*[self.config['encodingPath'], f'{self.design}_{self.node_tech}nm'])
        self.resultDir = os.path.join(*[self.config['resultPath'], f'{self.design}_{self.node_tech}nm'])

        self.files = glob(os.path.join(self.dataDir, '*.bmp'))
        self.n_components = self.config['n_components']

        self.size_bounds = [self.config['lowerSize'], self.config['upperSize']]
        self.population_size = self.config['populationSize']
        self.max_iter = self.config['maxIter']
        self.threshold = self.config['GA_threshold']

        os.makedirs(self.encodingDir, exist_ok=True)
        os.makedirs(self.resultDir, exist_ok=True)
        os.makedirs(os.path.join(self.encodingDir, 'column_dictionary'), exist_ok=True)
        os.makedirs(os.path.join(self.encodingDir, 'image_encodings'), exist_ok=True)

    def concat_images(self):
        logger.info('Concatenating images for processing...')
        images = [Image.open(file) for file in self.files]
        combined_images = Image.fromarray(np.hstack([i for i in images]))
        image = np.array(combined_images)
        logger.info(f'Concatenated {len(images)} images.')

        if self.node_tech == 32:  # removing vcc lines in 32nm
            image[0:5, :] = 0
            image[-5:, :] = 0
            logger.info(f'VCC lines are removed for {self.node_tech}nm designs')

        return image

    def column_selection(self):
        image = self.concat_images()
        logger.info('Extracting all unique columns in concatnated image...')

        if os.path.exists(os.path.join(self.encodingDir,  f'{self.design}_{self.node_tech}nm_unique_columns.npy')):
            unique_columns = np.load(
                os.path.join(self.encodingDir, f'{self.design}_{self.node_tech}nm_unique_columns.npy'))
            counts = np.load(
                os.path.join(self.encodingDir, f'{self.design}_{self.node_tech}nm_column_counts.npy'))
        else:
            unique_columns, counts = extract_columns(image)
            np.save(os.path.join(self.encodingDir, f'{self.design}_{self.node_tech}nm_unique_columns.npy'),
                    unique_columns)
            np.save(os.path.join(self.encodingDir, f'{self.design}_{self.node_tech}nm_column_counts.npy'),
                    counts)

        logger.info('Unique columns extracted. Applying OMP for column selection...')

        info_coverage = OMP(unique_columns, counts, self.encodingDir, self.design, self.node_tech, self.increment)
        coverage = info_coverage['info_capture']
        with open(os.path.join(self.encodingDir, 'info_capture.pkl'), "wb") as f:
            pickle.dump(coverage, f)
        f.close()

        coverage = np.array(coverage)
        dy = coverage[1:] - coverage[:-1]
        pt = np.where(dy <= 0.001)[0][0]
        x = range(10, unique_columns.shape[1], self.increment)
        n_components = x[pt]
        info_capture = coverage[n_components] * 100

        logger.info(f"{n_components} columns are selected, covering {info_capture: 04f}% of column information.")
        return n_components

    def encoding_layout(self):
        self.n_components = self.column_selection()

        logger.info('Initializing for encoding layout...')
        filename = os.path.join(self.encodingDir,
                                f'column_dictionary/{self.design}_{self.node_tech}nm_column_dict_{self.n_components}.pkl')
        with open(filename, 'rb') as f:
            column_dict = pickle.load(f)
        f.close()
        logger.info('Column dictionary loaded, start encoding design layout...')

        encoding = ''
        for file in tqdm(self.files, desc='Encoding strips'):
            strip_image = np.array(Image.open(file, mode='r').convert('L'), dtype='uint8')
            if self.node_tech == 32:
                strip_image[0:5, :] = 0
                strip_image[-5:, :] = 0
            encoding += encode_image(strip_image, column_dict)
            encoding += '\t'
        logger.info('Encoding design layout completed.')

        with open(os.path.join(self.encodingDir, 'image_encodings',
                               f'{self.design}_{self.node_tech}nm_image_encoding_{self.n_components}.pkl'),
                  'wb') as f:
            pickle.dump(encoding, f)
        f.close()
        logger.info('Layout encoding saved.')
        encoding_time = time.time()

        return encoding

    def pattern_search(self):
        encoding_file = os.path.join(*[self.encodingDir, 'image_encodings',
                                       f'{self.design}_{self.node_tech}nm_image_encoding_{self.n_components}.pkl'])
        if os.path.exists(encoding_file):
            with open(encoding_file, 'rb') as f:
                image_encodings = pickle.load(f)
            f.close()
            logger.info('Layout encoding file found and loaded for GA pattern searching')
        else:
            logger.info('Layout encoding file not found, encoding layout image...')
            image_encodings = self.encoding_layout()

        encodings = image_encodings.split('\t')[:-1]

        cells = []
        for i in range(0, len(encodings)):
            logger.info(f"Searching on encoding # {i}...")
            encoding = encodings[i]

            population = generate_population(self.population_size, encoding, self.size_bounds, cells)
            best_population = population
            evals = [-np.inf]
            epoch = 0

            while evals[-1] <= self.threshold and epoch <= self.max_iter:
                frequencies = count_frequency(population, image_encodings)
                filtered_pop, filtered_freq = filter_by_freq(population, frequencies)

                information_coverage, updated_encoding = fitness(encoding, population, frequencies)

                if information_coverage > evals[-1]:
                    evals.append(information_coverage)
                    text_residual = updated_encoding

                    logger.info(f"Improved information coverage: {information_coverage: 04f} at iteration {epoch}")
                    best_population = population

                population = nextPopulation(self.population_size, best_population, self.size_bounds, encoding)
                epoch += 1

        unique_words = remove_substrings(find_non_overlapping_strings(best_population,
                                         count_frequency(best_population, encoding)))

        cells = list(set(unique_words + cells))

        file = os.path.join(*[self.resultDir, f'{self.design}_{self.node_tech}nm_final_cells_{self.n_components}.pkl'])
        with open(file, 'wb') as f:
            pickle.dump(cells, f)
        f.close()

        logger.info('GA searching results saved.')
        return image_encodings, cells

    def post_processing(self):
        encoding_file = os.path.join(*[self.encodingDir, 'image_encodings',
                                       f'{self.design}_{self.node_tech}nm_image_encoding_{self.n_components}.pkl'])
        cell_file = os.path.join(*[self.resultDir, f'{self.design}_{self.node_tech}nm_final_cells_{self.n_components}.pkl'])
        if os.path.exists(cell_file):
            logger.info('Loading GA searching results for post-processing...')
            with open(cell_file, 'rb') as f:
                cells = pickle.load(f)
            f.close()
            with open(encoding_file, 'rb') as f:
                image_encodings = pickle.load(f)
            f.close()
        else:
            image_encodings, cells = self.pattern_search()
        logger.info('Loaded.')
        logger.info('Start post-processing...')
        nodes = get_nodes(image_encodings, cells)
        potential_nodes = merge_nodes(image_encodings, nodes)

        final_result = os.path.join(*[self.resultDir, f'{self.design}_{self.node_tech}nm_final_results_{self.n_components}.pkl'])
        logger.info('Saving final results...')

        with open(final_result, "wb") as f:
            pickle.dump(potential_nodes, f)
        f.close()
        logger.info('Post-processing Completed and final_results saved.')

