import logging
import argparse
from preprocess import Processor

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description='Parameters for pipeline.')
parser.add_argument('--data_root', type=str, default='./data', help='Data root directory')
parser.add_argument('--design', type=str, default='des', help='layout design')
parser.add_argument('--node', type=int, default=32, help='node technology')
parser.add_argument('--increment', type=int, default=5, help='increment for OMP')
parser.add_argument('--n_components', type=int, default=0, help='number of selected columns')
parser.add_argument('--encodingPath', type=str, default='./encodings', help='dir for saving encodings')
parser.add_argument('--resultPath', type=str, default='./results', help='dir for saving results')
parser.add_argument('--population_size', type=int, default=200, help='population size for GA')
parser.add_argument('--upper_size', type=int, default=40, help='upper size bound for GA')
parser.add_argument('--lower_size', type=int, default=3, help='lower size bound for GA')
parser.add_argument('--GA_threshold', type=int, default=0.90, help='random seed')
parser.add_argument('--max_iter', type=int, default=1000, help='maximum number of iterations for GA')

args = parser.parse_args()

config = {'dataRoot': args.data_root,
          'design': args.design,
          'node': args.node,
          'increment': args.increment,
          'n_components': args.n_components,
          'encodingPath': args.encodingPath,
          'resultPath': args.resultPath,
          'populationSize': args.population_size,
          'upperSize': args.upper_size,
          'lowerSize': args.lower_size,
          'GA_threshold': args.GA_threshold,
          'maxIter': args.max_iter}


def run_preprocess():
    processor = Processor(config)
    processor.post_processing()


if __name__ == '__main__':
    run_preprocess()
